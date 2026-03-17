#!/usr/bin/env python3
"""
scripts/ingest_private_files.py

Reads JSON and CSV files from input-dir (e.g. private-files/credentials),
normalizes minimal fields and writes:
  - {out_dir}/credentials.json (array)
  - {out_dir}/credentials_index.json (slug -> id map)
  - {out_dir}/credentials_by_id.json (id -> record)
  - {out_dir}/credentials_by_group/{group_id_num}.json
  - {out_dir}/manifest.json
  - reports/thumb_mapping.json

Usage:
  python scripts/ingest_private_files.py --input-dir private-files/credentials --out-dir docs/data --search-root private-files
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REQUIRED_FIELDS = [
    "id", "slug", "type", "title", "issuer", "issue_date",
    "credential_id", "verification_url", "thumbnail",
    "group_id", "parent_id", "group_role", "tags",
    "visibility", "order", "notes"
]

GENERATOR_VERSION = "ingest-v1.0.0"

def slugify(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s or "item"

def thumb_name_for(idnum: int, slug: str, ext: str = "png", pad: int = 4) -> str:
    return f"{str(idnum).zfill(pad)}-{slug}.{ext}"

def normalize_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for f in REQUIRED_FIELDS:
        v = rec.get(f, "")
        if isinstance(v, str):
            v = v.strip()
        if f in ("id", "parent_id", "order"):
            try:
                out[f] = int(v) if v not in ("", None, "") else None
            except Exception:
                out[f] = None
        elif f == "tags":
            if isinstance(v, str):
                tags = [t.strip().lower() for t in v.split(",") if t.strip()]
                out[f] = tags
            elif isinstance(v, list):
                out[f] = [str(x).strip().lower() for x in v]
            else:
                out[f] = []
        else:
            out[f] = v if v not in ("", None, "") else None
    # preserve extras
    for k, v in rec.items():
        if k not in out:
            out[k] = v
    return out

def read_json_file(p: Path) -> List[Dict[str, Any]]:
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # try to find a top-level list
            for v in data.values():
                if isinstance(v, list):
                    return v
            return [data]
    except Exception as e:
        print(f"Failed to read JSON {p}: {e}", file=sys.stderr)
    return []

def read_csv_file(p: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        with p.open(newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                out.append(dict(row))
    except Exception as e:
        print(f"Failed to read CSV {p}: {e}", file=sys.stderr)
    return out

def gather_records(input_dir: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if not input_dir.exists():
        print(f"Input dir not found: {input_dir}", file=sys.stderr)
        return records
    for p in sorted(input_dir.iterdir()):
        if p.is_dir():
            continue
        if p.suffix.lower() == ".json":
            records.extend(read_json_file(p))
        elif p.suffix.lower() in (".csv", ".tsv"):
            records.extend(read_csv_file(p))
    return records

def find_credentials_dir(proposed: Path) -> Path:
    if proposed.exists():
        return proposed
    parent = proposed.parent
    candidates = [
        parent / "files" / "credentials",
        parent / "data" / "credentials",
        parent / "credentials",
        parent / "source" / "credentials",
    ]
    for c in candidates:
        if c.exists():
            print(f"Auto-discovered credentials dir at: {c}")
            return c
    # recursive search (limit depth)
    for d in parent.glob("**/credentials"):
        if d.is_dir():
            print(f"Discovered credentials dir by search: {d}")
            return d
    return proposed  # not found

def search_for_source_file(record: Dict[str, Any], search_root: Path) -> Optional[Path]:
    """
    Attempt to find a source file (e.g., PDF) under search_root that matches record.
    Heuristics:
      - look for fields 'source_file','file','original_filename','pdf'
      - look for files containing credential_id or slug or id in name
    """
    # candidate fields
    for key in ("source_file", "file", "original_filename", "pdf", "path"):
        val = record.get(key)
        if val:
            p = (search_root / val) if not Path(val).is_absolute() else Path(val)
            if p.exists():
                return p
    slug = record.get("slug") or ""
    cred_id = str(record.get("credential_id") or "")
    idnum = str(record.get("id") or "")
    tokens = [t for t in (slug, cred_id, idnum) if t]
    if not tokens:
        return None
    # search for files containing any token
    for ext in (".pdf", ".PDF", ".png", ".jpg", ".jpeg"):
        for token in tokens:
            for p in search_root.rglob(f"*{token}*{ext}"):
                if p.is_file():
                    return p
    # NO loose fallback: do not return arbitrary pdfs (avoid wrong mappings)
    return None

def write_json_file(p: Path, data: Any):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {p}")

def compute_checksum_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--search-root", required=False, default=None,
                    help="Optional root to search for source files (e.g., private-files)")
    args = ap.parse_args()

    input_dir = Path(args.input_dir)
    # autodiscover if needed
    discovered = find_credentials_dir(input_dir)
    if not discovered.exists():
        print(f"ERROR: Input directory not found (proposed: {input_dir})", file=sys.stderr)
        try:
            print(f"Listing parent directory {input_dir.parent}:", file=sys.stderr)
            for p in input_dir.parent.iterdir():
                print(f" - {p}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(2)

    input_dir = discovered
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    search_root = Path(args.search_root) if args.search_root else input_dir.parent
    if not search_root.exists():
        search_root = input_dir.parent

    raw = gather_records(input_dir)
    print(f"Found {len(raw)} raw records in {input_dir}")

    normalized: List[Dict[str, Any]] = []
    errors: List[str] = []
    for idx, r in enumerate(raw, start=1):
        try:
            nr = normalize_record(r)
            normalized.append(nr)
        except Exception as e:
            errors.append(f"Record #{idx} error: {e}")

    # assign auto ids if missing
    next_id = 1
    existing_ids = {int(x.get("id")) for x in normalized if x.get("id") not in (None, "")}
    while next_id in existing_ids:
        next_id += 1
    for item in normalized:
        if not item.get("id"):
            while next_id in existing_ids:
                next_id += 1
            item["id"] = next_id
            existing_ids.add(next_id)
            next_id += 1

    # ensure slugs
    slug_map: Dict[str, int] = {}
    for item in normalized:
        title = item.get("title") or ""
        desired = item.get("slug") or slugify(title[:80])
        base = desired
        i = 1
        while desired in slug_map:
            i += 1
            desired = f"{base}-{i}"
        item["slug"] = desired
        slug_map[desired] = item["id"]

    # add thumbnail names (predictable)
    for item in normalized:
        padded = str(item["id"]).zfill(4)
        thumb = thumb_name_for(item["id"], item["slug"])
        item["thumbnail"] = f"assets/thumbnails/{thumb}"

    # sort by order then id
    normalized.sort(key=lambda x: (x.get("order") if x.get("order") is not None else 0, x.get("id")))

    # write main credentials.json
    credentials_path = out_dir / "credentials.json"
    write_json_file(credentials_path, normalized)

    # index by slug -> id
    slug_index: Dict[str, Optional[int]] = {}
    by_id: Dict[str, Dict[str, Any]] = {}
    for rec in normalized:
        slug = rec.get("slug") or str(rec.get("id"))
        slug_index[slug] = rec.get("id")
        by_id[str(rec.get("id"))] = rec

    write_json_file(out_dir / "credentials_index.json", slug_index)
    write_json_file(out_dir / "credentials_by_id.json", by_id)

    # by_group files
    group_map: Dict[str, int] = {}
    next_group_num = 1
    groups: Dict[int, List[Dict[str, Any]]] = {}
    for rec in normalized:
        gid = rec.get("group_id") or "ungrouped"
        if gid not in group_map:
            group_map[gid] = next_group_num
            next_group_num += 1
        num = group_map[gid]
        rec_summary = {
            "id": rec.get("id"),
            "slug": rec.get("slug"),
            "title": rec.get("title"),
            "type": rec.get("type"),
            "thumbnail": rec.get("thumbnail"),
            "order": rec.get("order"),
        }
        if rec.get("parent_id"):
            rec_summary["parent_id"] = rec.get("parent_id")
        groups.setdefault(num, []).append(rec_summary)
    by_group_dir = out_dir / "credentials_by_group"
    by_group_dir.mkdir(parents=True, exist_ok=True)
    for num, items in groups.items():
        write_json_file(by_group_dir / f"{num}.json", items)

    # Attempt to map source files to thumbnails
    thumb_mapping: Dict[str, str] = {}
    for rec in normalized:
        src = search_for_source_file(rec, search_root)
        thumb_path = rec.get("thumbnail")
        if src:
            # prefer path relative to search_root to avoid leaking absolute filesystem paths
            try:
                rel = str(src.relative_to(search_root))
            except Exception:
                # fallback: use slug if available, otherwise filename only
                rel = rec.get("slug") or src.name
            thumb_mapping[rel] = thumb_path
        else:
            # Do NOT fallback to arbitrary pdf; record missing mapping for later report.
            errors.append(f"No source file found for id={rec.get('id')} slug={rec.get('slug')}")

    # write thumb mapping to reports
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    write_json_file(reports_dir / "thumb_mapping.json", thumb_mapping)

    # manifest
    try:
        cred_text = credentials_path.read_text(encoding="utf-8")
        checksum = compute_checksum_text(cred_text)
    except Exception:
        checksum = ""
    manifest = {
        "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "record_count": len(normalized),
        "generator_version": GENERATOR_VERSION,
        "data_checksum": checksum,
    }
    write_json_file(out_dir / "manifest.json", manifest)

    # simple reporting of errors
    if errors:
        rpt = reports_dir / "ingest_report.md"
        with rpt.open("w", encoding="utf-8") as fh:
            fh.write("# Ingest report\n\n")
            fh.write(f"Found {len(raw)} raw records\n\n")
            fh.write("Errors:\n\n")
            for e in errors[:200]:
                fh.write(f"- {{e}}\n")
        print(f"Wrote report to {{rpt}}", file=sys.stderr)

    if len(normalized) == 0:
        print("No records were ingested; failing the step.", file=sys.stderr)
        sys.exit(1)

    print(f"Ingest completed: wrote {{credentials_path}}, manifest and reports.")

if __name__ == "__main__":
    main()
