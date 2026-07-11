#!/usr/bin/env python3
"""Collect and filter E2E debug artefacts for CI publication.

This script copies only diagnostic files from known E2E output directories into
one staging folder. It intentionally avoids copying project source/static trees.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import shutil


ALLOWED_SUFFIXES = {
    ".log",
    ".txt",
    ".json",
    ".html",
    ".png",
    ".jpg",
    ".jpeg",
    ".webm",
    ".mp4",
    ".trace",
    ".zip",
}


def _iter_files(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in ALLOWED_SUFFIXES:
            yield path


def _copy_filtered(src_root: Path, backend_root: Path, output_root: Path) -> int:
    copied = 0
    if not src_root.is_dir():
        return copied

    for source_file in _iter_files(src_root):
        rel = source_file.relative_to(backend_root)
        dest = output_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, dest)
        copied += 1

    return copied


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect E2E failure artefacts")
    parser.add_argument("--backend-root", required=True)
    parser.add_argument("--debug-dir", required=True)
    parser.add_argument("--junit", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    backend_root = Path(args.backend_root).resolve()
    debug_dir = Path(args.debug_dir).resolve()
    output_dir = debug_dir / "files"
    logs_dir = debug_dir / "logs"

    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    source_dirs = [
        backend_root / "test-results" / "forced-failures",
        backend_root / "playwright-report",
        backend_root / ".pytest_playwright",
    ]

    copied_total = 0
    for src_dir in source_dirs:
        copied_total += _copy_filtered(src_dir, backend_root, output_dir)

    junit_path = Path(args.junit).resolve()
    if junit_path.is_file():
        shutil.copy2(junit_path, output_dir / "e2e-junit.xml")

    file_list_path = logs_dir / "artifact-file-list.txt"
    all_files = sorted(path.resolve() for path in debug_dir.rglob("*") if path.is_file())
    file_list_path.write_text("\n".join(str(path) for path in all_files) + "\n", encoding="utf-8")

    summary = logs_dir / "collection-summary.txt"
    summary.write_text(
        f"Copied files: {copied_total}\nDebug dir: {debug_dir}\n",
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
