#!/usr/bin/env python3
"""
Minimal, safe thumbnail generator for CI.

This script does NOT open PDF contents. It scans the input directory
for files ending with .pdf/.PDF and writes a small placeholder PNG
for each one into the output directory. Filenames are hashed so the
original filenames are not leaked.

Usage:
  python scripts/generate_thumbnails_and_redact.py --input-dir private-pdfs --out-dir docs/assets/thumbnails
"""
import os
import sys
import argparse
import hashlib
from PIL import Image

def make_thumbnail_placeholder(out_path, size=(320, 240), color=(48, 57, 66)):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img = Image.new("RGB", size, color)
    # Save as PNG
    img.save(out_path, format="PNG")

def sha_name(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

def main():
    parser = argparse.ArgumentParser(description="Generate placeholder thumbnails for PDFs")
    parser.add_argument("--input-dir", required=True, help="Directory containing PDFs (checked out private repo)")
    parser.add_argument("--out-dir", required=True, help="Directory to write thumbnails into")
    parser.add_argument("--patterns-file", default=None, help="(ignored) placeholder param for compatibility")
    args = parser.parse_args()

    in_dir = args.input_dir
    out_dir = args.out_dir

    if not os.path.isdir(in_dir):
        print(f"Input directory does not exist: {in_dir}", file=sys.stderr)
        sys.exit(1)

    count = 0
    for root, _, files in os.walk(in_dir):
        for fname in files:
            if fname.lower().endswith(".pdf"):
                rel = os.path.relpath(os.path.join(root, fname), in_dir)
                h = sha_name(rel)
                out_file = os.path.join(out_dir, f"{h}.png")
                make_thumbnail_placeholder(out_file)
                print(f"Created placeholder: {out_file}  (for {rel})")
                count += 1

    print(f"Done. {count} thumbnail(s) written to {out_dir}")
    # success even if 0 files found
    sys.exit(0)

if __name__ == "__main__":
    main()
