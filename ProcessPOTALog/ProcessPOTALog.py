import re
import argparse

# List of fields to keep
ALLOWED_FIELDS = {
    "CALL", "QSO_DATE", "TIME_ON", "FREQ", "BAND", "MODE", "SUBMODE", 
    "STATION_CALLSIGN", "OPERATOR", "MY_SIG", "MY_SIG_INFO"
}

def clean_qso_record(record, sig_info_value):
    """Keeps only allowed fields in a QSO record and adds MY_SIG and MY_SIG_INFO."""
    fields = re.findall(r"<([^:>]+):(\d+)>([^<]*)", record)  # Extract field data

    cleaned_record = {}

    # Filter only the allowed fields
    for field_name, field_length, field_value in fields:
        if field_name.upper() in ALLOWED_FIELDS:
            cleaned_record[field_name.upper()] = (field_length, field_value)

    # Ensure MY_SIG and MY_SIG_INFO exist
    cleaned_record["MY_SIG"] = (4, "POTA")
    cleaned_record["MY_SIG_INFO"] = (len(sig_info_value), sig_info_value)

    # Reconstruct the cleaned QSO record
    new_record = " ".join(f"<{key}:{length}>{value}" for key, (length, value) in cleaned_record.items())
    
    return new_record

def process_adif(input_file, output_file, sig_info_value):
    """Reads an ADIF file, filters QSO records, adds MY_SIG and MY_SIG_INFO, and saves it."""
    with open(input_file, "r", encoding="utf-8") as file:
        content = file.read()

    # Split ADIF into header and records (case-insensitive <EOH>)
    parts = re.split(r"(?i)<EOH>", content, 1)
    if len(parts) < 2:
        print("Error: Invalid ADIF file format (missing <EOH>).")
        return

    header, records_section = parts
    header = header.strip() + "\n<EOH>\n"  # Preserve formatting

    # Split records using case-insensitive <EOR>
    records = re.split(r"(?i)(<EOR>)", records_section)

    updated_records = []
    for i in range(0, len(records) - 1, 2):  # Process in (record, <EOR>) pairs
        record = records[i].strip()
        eor_tag = records[i + 1]

        if record:
            cleaned_record = clean_qso_record(record, sig_info_value)
            updated_records.append(cleaned_record + " " + eor_tag)

    # Save the updated content
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(header + "\n".join(updated_records) + "\n")

    print(f"Processed ADIF saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter and modify an ADIF log file.")
    parser.add_argument("input_adif", help="Path to the input ADIF file")
    parser.add_argument("sig_info_value", help="Value for MY_SIG_INFO field")
    parser.add_argument("--output_adif", default="updated_log.adi", help="Path to the output ADIF file (default: updated_log.adi)")

    args = parser.parse_args()

    process_adif(args.input_adif, args.output_adif, args.sig_info_value)

