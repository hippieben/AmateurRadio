import re
import sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Avery 5160 Label Layout
LABELS_PER_ROW = 3
LABELS_PER_COLUMN = 10
LABEL_WIDTH = 2.625 * inch
LABEL_HEIGHT = 1.0 * inch
LEFT_MARGIN = 0.1875 * inch
TOP_MARGIN = 0.5 * inch
PAGE_WIDTH, PAGE_HEIGHT = letter
TEXT_LEFT_PADDING = 0.2 * inch
TEXT_TOP_PADDING = 0.8 * inch  # Adjust for better alignment

def extract_field(record, field_name):
    """Extracts a field value from an ADIF record."""
    match = re.search(rf"<{field_name}:\d+>([^<]+)", record, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def format_date(date_str):
    """Formats date from YYYYMMDD to YYYY-MM-DD."""
    if len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str  # Return as is if incorrect format

def format_time(time_str):
    """Formats time from HHMM to HH:MM."""
    if len(time_str) == 4:
        return f"{time_str[:2]}:{time_str[2:]}"
    return time_str  # Return as is if incorrect format

def parse_adif(file_path):
    """Parses an ADIF file and filters QSOs based on the criteria."""
    with open(file_path, "r", encoding="utf-8") as file:
        data = file.read().lower()

    records = re.split(r"<eor>", data)
    filtered_qsos = []

    for record in records:
        if not record.strip():
            continue

        dxcc = extract_field(record, "dxcc")
        qsl_via = extract_field(record, "qsl_via")
        qsl_sent = extract_field(record, "qsl_sent")
        qsl_rcvd = extract_field(record, "qsl_rcvd")
        call = extract_field(record, "call").upper()  # Convert CALL to uppercase
        qso_date = format_date(extract_field(record, "qso_date"))
        time_on = format_time(extract_field(record, "time_on"))
        band_rx = extract_field(record, "band_rx")
        mode = extract_field(record, "mode").upper()  # Convert MODE to uppercase
        rst_sent = extract_field(record, "rst_sent")

        # Default values for missing fields
        call = call if call else "UNKNOWN"
        qso_date = qso_date if qso_date else "0000-00-00"
        time_on = time_on if time_on else "00:00"
        band_rx = band_rx if band_rx else "UNKNOWN"
        mode = mode if mode else "UNKNOWN"
        rst_sent = rst_sent if rst_sent else "N/A"

        # Apply filters
        if dxcc == "291":
            continue
        if "buro" not in qsl_via and "bureau" not in qsl_via:
            continue
        if "cardc:" in qsl_sent or "label printed" in qsl_sent:
            continue
        if "cardc:" in qsl_rcvd or "label printed" in qsl_rcvd:
            continue

        label_text = [
            f"Confirming QSO: {call}",
            f"{qso_date}  {time_on} UTC",
            f"Band: {band_rx}   Mode: {mode}",
            f"RST Sent: {rst_sent}"
        ]

        filtered_qsos.append(label_text)

    return filtered_qsos

def generate_labels(qsos, output_file="qsl_labels.pdf"):
    """Generates a PDF formatted for Avery 5160 labels."""
    c = canvas.Canvas(output_file, pagesize=letter)
    c.setFont("Helvetica", 10)  # Set a readable font size

    x_offset = LEFT_MARGIN
    y_offset = PAGE_HEIGHT - TOP_MARGIN - LABEL_HEIGHT
    label_count = 0

    for label in qsos:
        if label_count > 0 and label_count % (LABELS_PER_ROW * LABELS_PER_COLUMN) == 0:
            c.showPage()  # Start a new page
            y_offset = PAGE_HEIGHT - TOP_MARGIN - LABEL_HEIGHT  # Reset y position

        col = (label_count % LABELS_PER_ROW)
        row = (label_count // LABELS_PER_ROW) % LABELS_PER_COLUMN

        x = x_offset + col * LABEL_WIDTH + TEXT_LEFT_PADDING
        y = y_offset - row * LABEL_HEIGHT + TEXT_TOP_PADDING

        # Draw text on label with proper spacing
        for i, line in enumerate(label):
            c.drawString(x, y - (i * 14), line)  # Adjusted spacing for clarity

        label_count += 1

    c.save()
    print(f"Labels saved to {output_file}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python parse_adif.py <input_file.adi>")
        sys.exit(1)

    adif_file = sys.argv[1]
    filtered_qsos = parse_adif(adif_file)

    if not filtered_qsos:
        print("No QSOs matched the filter criteria.")
        sys.exit(0)

    generate_labels(filtered_qsos, "qsl_labels.pdf")

if __name__ == "__main__":
    main()

