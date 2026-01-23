#!/usr/bin/env python3
"""
Thumbnail generator: PyMuPDF + Pillow version.

Design highlights:
- Pure functions for logic (collect_pdfs, sha_name).
- Side-effects (filesystem writes) centralized in ThumbnailWriter.
- Renderer is injected; can be replaced for testing.
- Idempotent by default (skips existing thumbnails), --force to overwrite.
- Optional concurrency via --workers.

Usage:
  python scripts/generate_thumbnails_and_redact.py --input-dir private-files --out-dir docs/assets/thumbnails
"""
from __future__ import annotations

import os
import sys
import argparse
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, List, Tuple
from PIL import Image

try:
    import fitz  # PyMuPDF
except Exception as e:
    fitz = None  # keep import error visible at runtime

# -----------------------
# Pure, testable helpers
# -----------------------
def sha_name(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

def collect_pdfs(input_dir: str) -> List[str]:
    """Return list of absolute paths to pdf files under input_dir (deterministic order)."""
    pdfs = []
    for root, _, files in os.walk(input_dir):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdfs.append(os.path.join(root, f))
    pdfs.sort()
    return pdfs

# -----------------------
# Renderer (injected)
# -----------------------
def render_first_page_to_pil(pdf_path: str, target_width: int = 320) -> Image.Image | None:
    """Render first page of PDF to a PIL Image. May raise exceptions on failure."""
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) not available. Ensure PyMuPDF is installed.")
    doc = fitz.open(pdf_path)
    try:
        if doc.page_count < 1:
            return None
        page = doc.load_page(0)
        # render at somewhat higher resolution for quality
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        w, h = img.size
        if w != target_width:
            new_h = int((target_width / w) * h)
            img = img.resize((target_width, new_h), Image.LANCZOS)
        return img
    finally:
        doc.close()

# -----------------------
# Side-effect manager
# -----------------------
class ThumbnailWriter:
    """Encapsulate filesystem side-effects for thumbnails."""
    def __init__(self, out_dir: str):
        self.out_dir = out_dir

    def ensure_out_dir(self) -> None:
        os.makedirs(self.out_dir, exist_ok=True)

    def thumbnail_path(self, hash_name: str) -> str:
        return os.path.join(self.out_dir, f"{hash_name}.png")

    def exists(self, hash_name: str) -> bool:
        return os.path.isfile(self.thumbnail_path(hash_name))

    def write(self, img: Image.Image, hash_name: str, force: bool = False) -> None:
        out_path = self.thumbnail_path(hash_name)
        if os.path.isfile(out_path) and not force:
            # idempotent: skip if already exists and not forcing
            return
        # ensure dir exists
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        img.save(out_path, format="PNG")

# -----------------------
# Orchestrator
# -----------------------
class ThumbnailGenerator:
    """
    Orchestrates collecting PDFs, rendering, and writing thumbnails.
    Renderer and writer are injected to support testing/substitution.
    """
    def __init__(
        self,
        input_dir: str,
        writer: ThumbnailWriter,
        renderer: Callable[[str, int], Image.Image | None],
        target_width: int = 320,
        force: bool = False,
        workers: int = 1,
    ):
        self.input_dir = input_dir
        self.writer = writer
        self.renderer = renderer
        self.target_width = target_width
        self.force = force
        self.workers = max(1, int(workers))

    def _process_pdf(self, pdf_path: str) -> Tuple[str, bool, str]:
        """Process single PDF. Returns (relpath, created_bool, message)."""
        rel = os.path.relpath(pdf_path, self.input_dir)
        h = sha_name(rel)
        try:
            if not self.force and self.writer.exists(h):
                return (rel, False, "skipped (exists)")
            img = self.renderer(pdf_path, self.target_width)
            if img is None:
                return (rel, False, "no pages")
            self.writer.write(img, h, force=self.force)
            return (rel, True, "created")
        except Exception as e:
            return (rel, False, f"error: {e}")

    def process_all(self) -> int:
        """Process all PDFs and return number of thumbnails created."""
        if not os.path.isdir(self.input_dir):
            raise FileNotFoundError(self.input_dir)
        self.writer.ensure_out_dir()
        pdfs = collect_pdfs(self.input_dir)
        created = 0
        if self.workers == 1:
            for pdf in pdfs:
                rel, ok, msg = self._process_pdf(pdf)
                print(f"{rel}: {msg}")
                if ok:
                    created += 1
        else:
            # concurrency handled here; side-effects still go through writer
            with ThreadPoolExecutor(max_workers=self.workers) as ex:
                futures = {ex.submit(self._process_pdf, pdf): pdf for pdf in pdfs}
                for fut in as_completed(futures):
                    rel, ok, msg = fut.result()
                    print(f"{rel}: {msg}")
                    if ok:
                        created += 1
        return created

# -----------------------
# CLI entrypoint
# -----------------------
def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate thumbnails from PDFs (idempotent).")
    p.add_argument("--input-dir", required=True, help="Directory containing PDFs (checked out private repo)")
    p.add_argument("--out-dir", required=True, help="Directory to write thumbnails into")
    p.add_argument("--patterns-file", default=None, help="(ignored) placeholder for compatibility")
    p.add_argument("--width", type=int, default=320, help="Thumbnail width in px")
    p.add_argument("--force", action="store_true", help="Force overwrite existing thumbnails")
    p.add_argument("--workers", type=int, default=1, help="Number of worker threads (default 1)")
    return p.parse_args(list(argv))

def main(argv: Iterable[str] = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    input_dir = args.input_dir
    out_dir = args.out_dir

    if not os.path.isdir(input_dir):
        print(f"Input directory does not exist: {input_dir}", file=sys.stderr)
        return 2

    writer = ThumbnailWriter(out_dir=out_dir)
    # Inject renderer and writer — makes unit testing simple
    gen = ThumbnailGenerator(
        input_dir=input_dir,
        writer=writer,
        renderer=render_first_page_to_pil,
        target_width=args.width,
        force=args.force,
        workers=args.workers,
    )

    try:
        created = gen.process_all()
        print(f"Done. {created} thumbnail(s) written to {out_dir}")
        return 0
    except FileNotFoundError as e:
        print(f"Input directory not found: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Unhandled error: {e}", file=sys.stderr)
        return 3

if __name__ == "__main__":
    raise SystemExit(main())
