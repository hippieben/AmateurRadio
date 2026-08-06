#!/usr/bin/env python3

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


TABLE_NAME = "qso_table_v008"
COLUMN_NAME = "qsl_received"


def clean_value(value):
    if value is None:
        return None

    entries = value.split(",")
    kept_entries = []

    for entry in entries:
        cleaned_entry = entry.strip()
        lower_entry = cleaned_entry.lower()

        if lower_entry.startswith("eqsl"):
            continue

        if lower_entry.startswith("qrz"):
            continue

        if cleaned_entry:
            kept_entries.append(cleaned_entry)

    return ", ".join(kept_entries)


def create_backup(database_path):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = database_path.with_name(
        f"{database_path.name}.backup-{timestamp}"
    )

    shutil.copy2(database_path, backup_path)
    return backup_path


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Remove eQSL and QRZ entries from the "
            "MacLoggerDX qsl_received column."
        )
    )

    parser.add_argument(
        "database",
        type=Path,
        help="Path to the MacLoggerDX SQLite database",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes. Without this option, only a dry run is performed.",
    )

    args = parser.parse_args()
    database_path = args.database.expanduser().resolve()

    if not database_path.is_file():
        print(f"Database not found: {database_path}")
        return

    connection = sqlite3.connect(database_path)

    try:
        rows = connection.execute(
            f"""
            SELECT rowid, {COLUMN_NAME}
            FROM {TABLE_NAME}
            WHERE {COLUMN_NAME} IS NOT NULL
            """
        ).fetchall()

        changes = []

        for rowid, original_value in rows:
            cleaned_value = clean_value(original_value)

            if cleaned_value != original_value:
                changes.append(
                    (cleaned_value, rowid, original_value)
                )

        print(f"Database: {database_path}")
        print(f"Rows that would change: {len(changes):,}")

        for cleaned_value, rowid, original_value in changes[:10]:
            print()
            print(f"Row {rowid}")
            print(f"Before: {original_value}")
            print(f"After:  {cleaned_value}")

        if not args.apply:
            print()
            print("Dry run only. No data was changed.")
            print("Run again with --apply to make the changes.")
            return

        if not changes:
            print("No changes are required.")
            return

        backup_path = create_backup(database_path)
        print()
        print(f"Backup created: {backup_path}")

        connection.execute("BEGIN IMMEDIATE")

        connection.executemany(
            f"""
            UPDATE {TABLE_NAME}
            SET {COLUMN_NAME} = ?
            WHERE rowid = ?
            """,
            [
                (cleaned_value, rowid)
                for cleaned_value, rowid, _ in changes
            ],
        )

        connection.commit()

        print(f"Updated {len(changes):,} rows successfully.")

    except Exception as error:
        connection.rollback()
        print(f"Error: {error}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
