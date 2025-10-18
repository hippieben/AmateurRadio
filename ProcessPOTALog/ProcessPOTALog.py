#!/usr/bin/env python3
import re
import argparse
from pathlib import Path

ALLOWED_FIELDS_ORDER = [
    "CALL", "QSO_DATE", "TIME_ON", "FREQ", "BAND", "MODE", "SUBMODE",
    "STATION_CALLSIGN", "OPERATOR", "MY_SIG", "MY_SIG_INFO"
]
ALLOWED_FIELDS = set(ALLOWED_FIELDS_ORDER)

# ADIF field pattern: <TAG[:length][:extra]?>value
FIELD_RE = re.compile(
    r"<\s*([A-Za-z0-9_]+)"           # tag
    r"(?:\s*:\s*(\d+))?"             # optional length
    r"(?:\s*:\s*[^>]+)?"             # optional :type/enum/etc
    r"\s*>\s*"
    r"([^<]*)",                      # value (until next '<')
    re.IGNORECASE
)

def parse_fields(record: str):
    """Return dict of {TAG_UPPER: value} from a QSO record string."""
    fields = {}
    for m in FIELD_RE.finditer(record):
        tag = m.group(1).upper()
        val = m.group(3)
        fields[tag] = val
    return fields

def build_record(fields: dict) -> str:
    """Build an ADIF record string from dict using ALLOWED_FIELDS_ORDER and recomputed lengths."""
    pieces = []
    for tag in ALLOWED_FIELDS_ORDER:
        if tag in fields:
            val = fields[tag] if fields[tag] is not None else ""
            pieces.append(f"<{tag}:{len(val)}>{val}")
    return " ".join(pieces)

def process_record(record: str, sig_info_value: str) -> str:
    """
    Clean one QSO record:
    - keep only allowed fields
    - ALWAYS set MY_SIG='POTA' and MY_SIG_INFO to sig_info_value
    """
    src = parse_fields(record)

    # Keep only allowed fields
    kept = {k: v for k, v in src.items() if k in ALLOWED_FIELDS}

    # Always enforce MY_SIG and MY_SIG_INFO
    kept["MY_SIG"] = "POTA"
    kept["MY_SIG_INFO"] = sig_info_value

    return build_record(kept)

def split_header(content: str):
    """Return (header_with_EOH, records_section). Insert <EOH> if missing."""
    parts = re.split(r"(?i)<EOH>", content, maxsplit=1)
    if len(parts) == 2:
        header = parts[0].strip()
        records = parts[1]
        header_out = (header + "\n<EOH>\n") if header else "<EOH>\n"
        return header_out, records
    # No EOH found — synthesize a header line
    return "<EOH>\n", content

def iter_records(records_section: str):
    """Yield raw record strings (without the <EOR> tag)."""
    chunks = re.split(r"(?i)<EOR>", records_section)
    for chunk in chunks:
        rec = chunk.strip()
        if rec:
            yield rec

def sanitize_for_filename(value: str) -> str:
    """Allow only safe filename characters; remove spaces; keep @ - _ ."""
    cleaned = re.sub(r"\s+", "", value or "")
    cleaned = re.sub(r"[^A-Za-z0-9@._-]", "", cleaned)
    return cleaned if cleaned else "UNKNOWN"

def infer_output_name(records_section: str, mysiginfo: str) -> str:
    """
    Build filename {STATION_CALLSIGN}@-{MY_SIG_INFO}-{QSO_DATE}.adi
    Use first record that yields values; fall back to CALL or placeholders.
    """
    station = None
    date = None

    for rec in iter_records(records_section):
        fields = parse_fields(rec)
        station = fields.get("STATION_CALLSIGN") or fields.get("CALL")
        date = fields.get("QSO_DATE")
        if station or date:
            break

    station = sanitize_for_filename(station or "UNKNOWN")
    date = sanitize_for_filename(date or "UNKNOWNDATE")
    mysiginfo = sanitize_for_filename(mysiginfo)

    return f"{station}@-{mysiginfo}-{date}.adi"

def process_adif(input_file: Path, output_file: Path | None, sig_info_value: str):
    text = input_file.read_text(encoding="utf-8", errors="replace")

    header, records_section = split_header(text)

    out_records = []
    for rec in iter_records(records_section):
        cleaned = process_record(rec, sig_info_value=sig_info_value)
        if cleaned:
            out_records.append(cleaned + " <EOR>")

    output_text = header + "\n".join(out_records) + ("\n" if out_records else "")

    # Auto-generate filename if none provided
    if output_file is None:
        auto_name = infer_output_name(records_section, sig_info_value)
        output_path = input_file.parent / auto_name
    else:
        output_path = output_file

    output_path.write_text(output_text, encoding="utf-8")
    print(f"Processed ADIF saved to {output_path}")

def main():
    p = argparse.ArgumentParser(
        description="Filter ADIF fields, force MY_SIG='POTA' and MY_SIG_INFO=<value>, and auto-name the output."
    )
    p.add_argument("input_adif", help="Path to the input ADIF file")
    p.add_argument("sig_info_value", help="Value for MY_SIG_INFO field (e.g., US-6666)")
    p.add_argument(
        "-o", "--output", "--output_adif",
        dest="output_adif",
        default=None,
        help="Optional path to the output ADIF file. If omitted, name is STATION_CALLSIGN@-MY_SIG_INFO-QSO_DATE.adi"
    )
    args = p.parse_args()

    input_path = Path(args.input_adif)
    output_path = Path(args.output_adif) if args.output_adif else None
    process_adif(
        input_file=input_path,
        output_file=output_path,
        sig_info_value=args.sig_info_value,
    )

if __name__ == "__main__":
    main()
