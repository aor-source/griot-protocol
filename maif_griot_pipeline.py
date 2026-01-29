#!/usr/bin/env python3
"""
Griot Protocol - MAIF Research Pipeline

Named for West African griots - oral historians who preserved cultural truth across generations.
"Damn the man. Save the empire." - Immutable proof that no corporation can deny, no server can delete.

Sealing pipeline for MAIF (Music Analysis Interchange Format) research outputs.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Supported audio file extensions
AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg",
    ".wma", ".aiff", ".alac", ".opus", ".webm"
}


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


def find_audio_files(directory: Path, recursive: bool = True) -> list[Path]:
    """Find all audio files in a directory."""
    pattern = "**/*" if recursive else "*"
    files = []
    for filepath in directory.glob(pattern):
        if filepath.is_file() and filepath.suffix.lower() in AUDIO_EXTENSIONS:
            files.append(filepath)
    return sorted(files)


def run_maif_analysis(audio_file: Path, output_dir: Path) -> Optional[dict]:
    """Run MAIF analysis on an audio file if MAIF_Gen.py is available."""
    # Look for MAIF_Gen.py in common locations
    maif_locations = [
        Path.cwd() / "MAIF_Gen.py",
        Path.cwd() / "maif" / "MAIF_Gen.py",
        Path.home() / "MAIF" / "MAIF_Gen.py",
        Path(__file__).parent / "MAIF_Gen.py",
    ]

    maif_script = None
    for loc in maif_locations:
        if loc.exists():
            maif_script = loc
            break

    if not maif_script:
        return None

    try:
        output_file = output_dir / f"{audio_file.stem}_maif.json"
        result = subprocess.run(
            [sys.executable, str(maif_script), str(audio_file), "-o", str(output_file)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per file
        )

        if result.returncode == 0 and output_file.exists():
            with open(output_file) as f:
                return json.load(f)
    except Exception as e:
        print(f"  ⚠ MAIF analysis failed for {audio_file.name}: {e}")

    return None


def create_track_manifest(
    audio_file: Path,
    output_dir: Path,
    maif_data: Optional[dict],
    timestamp: str,
) -> dict:
    """Create a manifest for a single track."""
    audio_hash = compute_sha256(audio_file)
    audio_size = audio_file.stat().st_size

    manifest = {
        "protocol": "Griot Protocol v1.0",
        "type": "track_manifest",
        "audio_file": {
            "filename": audio_file.name,
            "filepath": str(audio_file.absolute()),
            "sha256": audio_hash,
            "size_bytes": audio_size,
        },
        "sealed_at": timestamp,
        "analysis_outputs": [],
    }

    # Add MAIF analysis if available
    if maif_data:
        maif_file = output_dir / f"{audio_file.stem}_maif.json"
        if maif_file.exists():
            manifest["analysis_outputs"].append({
                "type": "maif",
                "filename": maif_file.name,
                "sha256": compute_sha256(maif_file),
            })

    return manifest


def print_truth_seal_box(title: str, content: dict) -> None:
    """Print a formatted truth seal box."""
    width = 70

    print()
    print("╔" + "═" * (width - 2) + "╗")
    print("║" + title.center(width - 2) + "║")
    print("╠" + "═" * (width - 2) + "╣")

    for key, value in content.items():
        if isinstance(value, str) and len(value) > 50:
            # Split long values
            line1 = f"  {key}: {value[:45]}"
            line2 = f"         {value[45:]}"
            print("║" + line1.ljust(width - 2) + "║")
            print("║" + line2.ljust(width - 2) + "║")
        else:
            line = f"  {key}: {value}"
            print("║" + line.ljust(width - 2) + "║")

    print("╚" + "═" * (width - 2) + "╝")


def run_pipeline(
    input_dir: Path,
    output_dir: Path,
    skip_maif: bool = False,
    recursive: bool = True,
) -> dict:
    """Run the complete MAIF Griot pipeline."""
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    proofs_dir = output_dir / "proofs"
    proofs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()

    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                                                                  ║")
    print("║              GRIOT PROTOCOL - MAIF RESEARCH PIPELINE             ║")
    print("║                                                                  ║")
    print("║          \"Damn the man. Save the empire.\"                        ║")
    print("║                                                                  ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()

    # Find audio files
    print(f"Scanning for audio files in: {input_dir}")
    audio_files = find_audio_files(input_dir, recursive)

    if not audio_files:
        print("No audio files found.")
        return {}

    print(f"Found {len(audio_files)} audio file(s)")
    print()

    # Process each track
    track_manifests = []
    all_hashes = []

    for i, audio_file in enumerate(audio_files, 1):
        print(f"[{i}/{len(audio_files)}] Processing: {audio_file.name}")

        # Run MAIF analysis if available and not skipped
        maif_data = None
        if not skip_maif:
            print("  → Running MAIF analysis...")
            maif_data = run_maif_analysis(audio_file, output_dir)
            if maif_data:
                print("  ✓ MAIF analysis complete")
            else:
                print("  ⚠ MAIF analysis skipped (MAIF_Gen.py not found)")

        # Create track manifest
        manifest = create_track_manifest(audio_file, output_dir, maif_data, timestamp)

        # Save track manifest
        manifest_path = proofs_dir / f"{audio_file.stem}.manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        # Generate truth seal for audio file
        audio_hash = manifest["audio_file"]["sha256"]
        all_hashes.append(audio_hash)

        print(f"  ✓ Truth Seal: {audio_hash[:16]}...{audio_hash[-16:]}")
        print(f"  ✓ Manifest: {manifest_path.name}")
        print()

        track_manifests.append({
            "audio_file": audio_file.name,
            "audio_hash": audio_hash,
            "manifest_file": manifest_path.name,
            "has_maif": maif_data is not None,
        })

    # Create master corpus manifest
    print("Creating master corpus manifest...")

    # Genesis seal = hash of all hashes concatenated
    genesis_input = "".join(all_hashes)
    genesis_seal = compute_sha256_string(genesis_input)

    corpus_manifest = {
        "protocol": "Griot Protocol v1.0",
        "type": "corpus_manifest",
        "created_at": timestamp,
        "source_directory": str(input_dir.absolute()),
        "output_directory": str(output_dir.absolute()),
        "track_count": len(track_manifests),
        "tracks": track_manifests,
        "genesis_seal": genesis_seal,
    }

    corpus_path = output_dir / "corpus_manifest.json"
    with open(corpus_path, "w") as f:
        json.dump(corpus_manifest, f, indent=2)

    # Print summary
    print()
    print_truth_seal_box("GENESIS SEAL", {
        "Tracks processed": len(track_manifests),
        "Genesis Seal": genesis_seal,
        "Corpus Manifest": str(corpus_path),
    })

    print()
    print("═" * 70)
    print("NEXT STEPS:")
    print("═" * 70)
    print()
    print("1. Review the generated manifests in:")
    print(f"   {proofs_dir}")
    print()
    print("2. Commit everything to git:")
    print(f"   cd {output_dir}")
    print("   git add .")
    print("   git commit -m \"MAIF research corpus sealed via Griot Protocol\"")
    print()
    print("3. Anchor to blockchain for immutable timestamping:")
    print(f"   python blockchain_anchor.py seal {corpus_path} --chain bitcoin")
    print()
    print("4. For full nuclear option (Bitcoin + Polygon):")
    print(f"   python blockchain_anchor.py seal {corpus_path} -c bitcoin -c polygon")
    print()
    print("\"Damn the man. Save the empire.\"")
    print()

    return corpus_manifest


def verify_corpus(corpus_manifest_path: Path) -> bool:
    """Verify all files in a corpus manifest."""
    if not corpus_manifest_path.exists():
        print(f"Error: Manifest not found: {corpus_manifest_path}", file=sys.stderr)
        sys.exit(1)

    with open(corpus_manifest_path) as f:
        manifest = json.load(f)

    print()
    print("GRIOT PROTOCOL - CORPUS VERIFICATION")
    print("=" * 60)
    print(f"Manifest: {corpus_manifest_path.name}")
    print(f"Created: {manifest.get('created_at', 'Unknown')}")
    print(f"Expected Genesis Seal: {manifest.get('genesis_seal', 'N/A')}")
    print("=" * 60)
    print()

    source_dir = Path(manifest.get("source_directory", "."))
    all_hashes = []
    errors = []

    for track in manifest.get("tracks", []):
        audio_file = source_dir / track["audio_file"]
        expected_hash = track["audio_hash"]

        if not audio_file.exists():
            print(f"  ✗ MISSING: {track['audio_file']}")
            errors.append(f"Missing file: {track['audio_file']}")
            continue

        actual_hash = compute_sha256(audio_file)
        all_hashes.append(actual_hash)

        if actual_hash == expected_hash:
            print(f"  ✓ VERIFIED: {track['audio_file']}")
        else:
            print(f"  ✗ MODIFIED: {track['audio_file']}")
            errors.append(f"Hash mismatch: {track['audio_file']}")

    # Verify genesis seal
    print()
    if all_hashes:
        computed_genesis = compute_sha256_string("".join(all_hashes))
        expected_genesis = manifest.get("genesis_seal", "")

        if computed_genesis == expected_genesis:
            print("✓ GENESIS SEAL VERIFIED")
        else:
            print("✗ GENESIS SEAL MISMATCH")
            errors.append("Genesis seal mismatch")

    print()
    if errors:
        print(f"VERIFICATION FAILED - {len(errors)} error(s)")
        for error in errors:
            print(f"  • {error}")
        return False
    else:
        print("VERIFICATION PASSED - All files intact")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Griot Protocol - MAIF Research Pipeline\n\n"
                    "\"Damn the man. Save the empire.\"\n\n"
                    "Sealing pipeline for MAIF research outputs.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Process command (default)
    process_parser = subparsers.add_parser("process", help="Process audio files through pipeline")
    process_parser.add_argument("--input", "-i", type=Path, required=True, help="Input directory with audio files")
    process_parser.add_argument("--output", "-o", type=Path, required=True, help="Output directory for results")
    process_parser.add_argument("--skip-maif", action="store_true", help="Skip MAIF analysis")
    process_parser.add_argument("--no-recursive", action="store_true", help="Don't search subdirectories")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a corpus manifest")
    verify_parser.add_argument("manifest", type=Path, help="Path to corpus_manifest.json")

    args = parser.parse_args()

    # Default to process if no command given but we have legacy-style args
    if args.command is None:
        # Check for legacy --input/--output style
        parser.print_help()
        print()
        print("Examples:")
        print("  python maif_griot_pipeline.py process --input ./tracks --output ./results")
        print("  python maif_griot_pipeline.py verify results/corpus_manifest.json")
        sys.exit(0)

    if args.command == "process":
        run_pipeline(
            args.input,
            args.output,
            skip_maif=args.skip_maif,
            recursive=not args.no_recursive,
        )

    elif args.command == "verify":
        success = verify_corpus(args.manifest)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
