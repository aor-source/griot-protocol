#!/usr/bin/env python3
"""
Griot Protocol - Truth Seal Generator

Named for West African griots - oral historians who preserved cultural truth across generations.
"Damn the man. Save the empire." - Immutable proof that no corporation can deny, no server can delete.

Basic CLI for SHA-256 hash generation and verification.
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Box drawing characters for pretty output
BOX_TOP_LEFT = "╔"
BOX_TOP_RIGHT = "╗"
BOX_BOTTOM_LEFT = "╚"
BOX_BOTTOM_RIGHT = "╝"
BOX_HORIZONTAL = "═"
BOX_VERTICAL = "║"
BOX_T_LEFT = "╠"
BOX_T_RIGHT = "╣"


def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def compute_sha256_string(data: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def print_truth_seal(
    filepath: Path,
    file_hash: str,
    timestamp: str,
    file_size: int
) -> None:
    """Print a pretty-formatted Truth Seal."""
    width = 72
    inner_width = width - 4  # Account for box borders and padding

    def pad_line(text: str) -> str:
        return f"{BOX_VERTICAL} {text.ljust(inner_width)} {BOX_VERTICAL}"

    def center_line(text: str) -> str:
        return f"{BOX_VERTICAL} {text.center(inner_width)} {BOX_VERTICAL}"

    def divider() -> str:
        return f"{BOX_T_LEFT}{BOX_HORIZONTAL * (width - 2)}{BOX_T_RIGHT}"

    print()
    print(f"{BOX_TOP_LEFT}{BOX_HORIZONTAL * (width - 2)}{BOX_TOP_RIGHT}")
    print(center_line(""))
    print(center_line("▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀"))
    print(center_line("GRIOT PROTOCOL - TRUTH SEAL"))
    print(center_line("▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄"))
    print(center_line(""))
    print(divider())
    print(pad_line(""))
    print(pad_line(f"FILE: {filepath.name}"))
    print(pad_line(f"PATH: {filepath.absolute()}"))
    print(pad_line(f"SIZE: {file_size:,} bytes"))
    print(pad_line(""))
    print(divider())
    print(pad_line(""))
    print(pad_line("SHA-256 HASH:"))
    print(pad_line(f"  {file_hash[:32]}"))
    print(pad_line(f"  {file_hash[32:]}"))
    print(pad_line(""))
    print(divider())
    print(pad_line(""))
    print(pad_line(f"SEALED: {timestamp}"))
    print(pad_line(""))
    print(center_line("\"Damn the man. Save the empire.\""))
    print(center_line(""))
    print(f"{BOX_BOTTOM_LEFT}{BOX_HORIZONTAL * (width - 2)}{BOX_BOTTOM_RIGHT}")
    print()


def seal_file(filepath: Path, output_json: bool = False) -> dict:
    """Generate a Truth Seal for a file."""
    if not filepath.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    if not filepath.is_file():
        print(f"Error: Not a file: {filepath}", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.now(timezone.utc).isoformat()
    file_hash = compute_sha256(filepath)
    file_size = filepath.stat().st_size

    seal_data = {
        "protocol": "Griot Protocol v1.0",
        "type": "truth_seal",
        "filename": filepath.name,
        "filepath": str(filepath.absolute()),
        "sha256": file_hash,
        "size_bytes": file_size,
        "sealed_at": timestamp,
    }

    if output_json:
        print(json.dumps(seal_data, indent=2))
    else:
        print_truth_seal(filepath, file_hash, timestamp, file_size)

    return seal_data


def verify_file(filepath: Path, expected_hash: str) -> bool:
    """Verify a file against an expected hash."""
    if not filepath.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    actual_hash = compute_sha256(filepath)
    expected_hash = expected_hash.lower().strip()

    print()
    print("GRIOT PROTOCOL - VERIFICATION")
    print("=" * 50)
    print(f"File: {filepath.name}")
    print(f"Expected: {expected_hash}")
    print(f"Actual:   {actual_hash}")
    print("=" * 50)

    if actual_hash == expected_hash:
        print("✓ VERIFIED - Hashes match. Document integrity confirmed.")
        print()
        return True
    else:
        print("✗ FAILED - Hashes do not match. Document may have been altered.")
        print()
        return False


def batch_seal(directory: Path, output_dir: Optional[Path] = None, recursive: bool = False) -> list:
    """Seal all files in a directory."""
    if not directory.exists():
        print(f"Error: Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    if not directory.is_dir():
        print(f"Error: Not a directory: {directory}", file=sys.stderr)
        sys.exit(1)

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    pattern = "**/*" if recursive else "*"
    files = [f for f in directory.glob(pattern) if f.is_file()]

    if not files:
        print(f"No files found in {directory}")
        return []

    timestamp = datetime.now(timezone.utc).isoformat()
    seals = []

    print()
    print("GRIOT PROTOCOL - BATCH SEAL")
    print("=" * 60)
    print(f"Directory: {directory.absolute()}")
    print(f"Files found: {len(files)}")
    print(f"Recursive: {recursive}")
    print("=" * 60)
    print()

    for filepath in sorted(files):
        file_hash = compute_sha256(filepath)
        file_size = filepath.stat().st_size

        seal_data = {
            "protocol": "Griot Protocol v1.0",
            "type": "truth_seal",
            "filename": filepath.name,
            "filepath": str(filepath.absolute()),
            "relative_path": str(filepath.relative_to(directory)),
            "sha256": file_hash,
            "size_bytes": file_size,
            "sealed_at": timestamp,
        }
        seals.append(seal_data)

        rel_path = filepath.relative_to(directory)
        print(f"  ✓ {rel_path}")
        print(f"    SHA-256: {file_hash[:16]}...{file_hash[-16:]}")

    # Create manifest
    manifest = {
        "protocol": "Griot Protocol v1.0",
        "type": "batch_manifest",
        "source_directory": str(directory.absolute()),
        "sealed_at": timestamp,
        "file_count": len(seals),
        "seals": seals,
    }

    # Compute genesis seal (hash of all hashes)
    combined_hashes = "".join(s["sha256"] for s in seals)
    manifest["genesis_seal"] = compute_sha256_string(combined_hashes)

    # Save manifest
    if output_dir:
        manifest_path = output_dir / "batch_manifest.griot.json"
    else:
        manifest_path = directory / "batch_manifest.griot.json"

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print()
    print("=" * 60)
    print(f"Genesis Seal: {manifest['genesis_seal']}")
    print(f"Manifest saved: {manifest_path}")
    print()
    print("\"Damn the man. Save the empire.\"")
    print()

    return seals


def main():
    parser = argparse.ArgumentParser(
        description="Griot Protocol - Truth Seal Generator\n\n"
                    "\"Damn the man. Save the empire.\"\n\n"
                    "Named for West African griots - oral historians who preserved "
                    "cultural truth across generations.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Seal command
    seal_parser = subparsers.add_parser("seal", help="Generate a Truth Seal for a file")
    seal_parser.add_argument("file", type=Path, help="File to seal")
    seal_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a file against an expected hash")
    verify_parser.add_argument("file", type=Path, help="File to verify")
    verify_parser.add_argument("expected_hash", help="Expected SHA-256 hash")

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Seal all files in a directory")
    batch_parser.add_argument("directory", type=Path, help="Directory to seal")
    batch_parser.add_argument("--output", "-o", type=Path, help="Output directory for manifest")
    batch_parser.add_argument("--recursive", "-r", action="store_true", help="Include subdirectories")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "seal":
        seal_file(args.file, output_json=args.json)

    elif args.command == "verify":
        success = verify_file(args.file, args.expected_hash)
        sys.exit(0 if success else 1)

    elif args.command == "batch":
        batch_seal(args.directory, args.output, args.recursive)


if __name__ == "__main__":
    main()
