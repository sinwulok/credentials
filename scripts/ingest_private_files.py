#!/usr/bin/env python3
"""
Ingest private credentials data from JSON/CSV/TSV files.

Reads files from private-files/credentials directory, normalizes records,
and writes output to docs/data/credentials.json and auxiliary index files.

Requires Python 3.9+ for modern type annotations.

Usage:
  python scripts/ingest_private_files.py --input-dir private-files/credentials --out-dir docs/data
"""
from __future__ import annotations

import os
import sys
import json
import csv
import argparse
from typing import Any, Dict, List, Iterable
from pathlib import Path


# Default order value for records without an explicit order
# Large number ensures unordered items appear last when sorted
DEFAULT_ORDER = 999999


# Required fields for each credential record
REQUIRED_FIELDS = [
    "id",
    "slug",
    "type",
    "title",
    "issuer",
    "issue_date",
    "credential_id",
    "verification_url",
    "thumbnail",
    "group_id",
    "parent_id",
    "group_role",
    "tags",
    "visibility",
    "order",
    "notes",
]


def normalize_record(raw: Dict[str, Any], auto_id: int) -> tuple[Dict[str, Any], int]:
    """
    Normalize a raw record to include all required fields with appropriate types.
    
    - Coerce id/parent_id/order to int where possible
    - Normalize tags to list of lowercase strings
    - Auto-assign id if missing
    - Fill missing fields with None or appropriate defaults
    
    Returns tuple of (normalized_record, actual_id_used)
    """
    record = {}
    
    # Handle ID
    actual_id = auto_id
    if "id" in raw and raw["id"] not in (None, "", "null"):
        try:
            actual_id = int(raw["id"])
            record["id"] = actual_id
        except (ValueError, TypeError):
            record["id"] = auto_id
    else:
        record["id"] = auto_id
    
    # Copy other fields
    for field in REQUIRED_FIELDS:
        if field == "id":
            continue  # already handled
        
        if field in raw:
            value = raw[field]
        else:
            value = None
        
        # Special handling for certain fields
        if field in ("parent_id", "order"):
            if value not in (None, "", "null"):
                try:
                    record[field] = int(value)
                except (ValueError, TypeError):
                    record[field] = None
            else:
                record[field] = None
        
        elif field == "tags":
            # Normalize tags to list of lowercase strings
            if value is None or value == "":
                record[field] = []
            elif isinstance(value, str):
                # Split by comma or semicolon
                tags = [t.strip().lower() for t in value.replace(";", ",").split(",") if t.strip()]
                record[field] = tags
            elif isinstance(value, list):
                record[field] = [str(t).strip().lower() for t in value if str(t).strip()]
            else:
                record[field] = []
        
        else:
            # Default: copy as-is, convert empty strings to None
            if value == "" or value == "null":
                record[field] = None
            else:
                record[field] = value
    
    return record, actual_id


def read_json_file(path: str) -> List[Dict[str, Any]]:
    """Read a JSON file and return list of records."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Support both single object and array of objects
    if isinstance(data, dict):
        return [data]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"JSON file must contain object or array: {path}")


def read_csv_file(path: str, delimiter: str = ",") -> List[Dict[str, Any]]:
    """Read a CSV/TSV file and return list of records."""
    records = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            records.append(dict(row))
    return records


def collect_data_files(input_dir: str) -> List[str]:
    """Collect all JSON, CSV, and TSV files from input directory."""
    files = []
    for root, _, filenames in os.walk(input_dir):
        for filename in filenames:
            lower = filename.lower()
            if lower.endswith((".json", ".csv", ".tsv")):
                files.append(os.path.join(root, filename))
    files.sort()
    return files


class IngestProcessor:
    """Process data files and produce normalized output."""
    
    def __init__(self, input_dir: str, out_dir: str, max_errors: int = 50):
        self.input_dir = input_dir
        self.out_dir = out_dir
        self.max_errors = max_errors
        self.records = []
        self.errors = []
        self.next_auto_id = 1
        self.max_id_seen = 0
    
    def process_file(self, path: str) -> None:
        """Process a single data file."""
        rel_path = os.path.relpath(path, self.input_dir)
        try:
            if path.lower().endswith(".json"):
                raw_records = read_json_file(path)
            elif path.lower().endswith(".csv"):
                raw_records = read_csv_file(path, delimiter=",")
            elif path.lower().endswith(".tsv"):
                raw_records = read_csv_file(path, delimiter="\t")
            else:
                return
            
            for i, raw in enumerate(raw_records):
                try:
                    record, actual_id = normalize_record(raw, self.next_auto_id)
                    self.records.append(record)
                    # Update tracking: ensure next auto_id is always > max ID seen
                    self.max_id_seen = max(self.max_id_seen, actual_id)
                    self.next_auto_id = self.max_id_seen + 1
                except Exception as e:
                    if len(self.errors) < self.max_errors:
                        self.errors.append({
                            "file": rel_path,
                            "record_index": i,
                            "error": str(e),
                        })
        
        except Exception as e:
            if len(self.errors) < self.max_errors:
                self.errors.append({
                    "file": rel_path,
                    "record_index": None,
                    "error": f"File read error: {e}",
                })
    
    def process_all(self) -> int:
        """Process all data files and return number of records ingested."""
        if not os.path.isdir(self.input_dir):
            raise FileNotFoundError(f"Input directory not found: {self.input_dir}")
        
        files = collect_data_files(self.input_dir)
        print(f"Found {len(files)} data file(s) in {self.input_dir}")
        
        for path in files:
            self.process_file(path)
        
        print(f"Found {len(self.records)} raw record(s)")
        
        # Sort records by order, then by id
        # Records without order get DEFAULT_ORDER to appear last
        self.records.sort(key=lambda r: (r.get("order") or DEFAULT_ORDER, r.get("id") or 0))
        
        return len(self.records)
    
    def write_outputs(self) -> None:
        """Write output files."""
        os.makedirs(self.out_dir, exist_ok=True)
        
        # Write main credentials.json
        creds_path = os.path.join(self.out_dir, "credentials.json")
        with open(creds_path, "w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(self.records)} record(s) to {creds_path}")
        
        # Write credentials_index.json (list of ids)
        index_path = os.path.join(self.out_dir, "credentials_index.json")
        ids = [r["id"] for r in self.records]
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(ids, f, indent=2)
        print(f"Wrote index with {len(ids)} id(s) to {index_path}")
        
        # Write credentials_by_id.json (dict keyed by id)
        by_id_path = os.path.join(self.out_dir, "credentials_by_id.json")
        by_id = {str(r["id"]): r for r in self.records}
        with open(by_id_path, "w", encoding="utf-8") as f:
            json.dump(by_id, f, indent=2, ensure_ascii=False)
        print(f"Wrote by-id lookup with {len(by_id)} record(s) to {by_id_path}")
    
    def write_error_report(self) -> None:
        """Write error report if there were any errors."""
        if not self.errors:
            return
        
        report_dir = "reports"
        os.makedirs(report_dir, exist_ok=True)
        
        report_path = os.path.join(report_dir, "ingest_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Ingestion Error Report\n\n")
            f.write(f"Found {len(self.errors)} error(s) during ingestion:\n\n")
            
            for err in self.errors:
                f.write(f"- **File:** `{err['file']}`\n")
                if err['record_index'] is not None:
                    f.write(f"  **Record index:** {err['record_index']}\n")
                f.write(f"  **Error:** {err['error']}\n\n")
            
            if len(self.errors) >= self.max_errors:
                f.write(f"\n*Note: Only first {self.max_errors} errors are shown.*\n")
        
        print(f"Wrote error report to {report_path}")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest credentials data from private files.")
    p.add_argument("--input-dir", required=True, help="Directory containing JSON/CSV/TSV files")
    p.add_argument("--out-dir", required=True, help="Directory to write output JSON files")
    p.add_argument("--max-errors", type=int, default=50, help="Max errors to collect (default 50)")
    return p.parse_args(list(argv))


def main(argv: Iterable[str] = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    
    processor = IngestProcessor(
        input_dir=args.input_dir,
        out_dir=args.out_dir,
        max_errors=args.max_errors,
    )
    
    try:
        count = processor.process_all()
        
        if count == 0:
            print("ERROR: No records were ingested. Check input directory path.", file=sys.stderr)
            return 1
        
        processor.write_outputs()
        
        if processor.errors:
            processor.write_error_report()
            print(f"WARNING: {len(processor.errors)} error(s) occurred during ingestion.", file=sys.stderr)
        
        return 0
    
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: Unhandled exception: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
