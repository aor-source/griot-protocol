#!/usr/bin/env python3
"""
Griot Protocol - Biter Check (Anti-Plagiarism Tool)

Named for West African griots - oral historians who preserved cultural truth across generations.
"Damn the man. Save the empire." - Expose the biters. Protect the creators.

Compares two documents and generates a detailed report showing:
- What was stolen (unchanged sections)
- What was modified (altered to hide the theft)
- Similarity metrics for legal evidence
- Timeline proof when combined with .griot/.ots files
"""

import argparse
import difflib
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def extract_text(filepath: Path) -> str:
    """Extract text from a file (supports txt, md, py, etc.)."""
    # For now, read as text. Could extend to PDF, DOCX, etc.
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(filepath, "r", encoding="latin-1") as f:
            return f.read()


def normalize_text(text: str, ignore_whitespace: bool = True) -> str:
    """Normalize text for comparison."""
    if ignore_whitespace:
        # Collapse multiple spaces/newlines
        text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()


def get_ngrams(text: str, n: int = 5) -> set:
    """Get n-grams (word sequences) from text for similarity detection."""
    words = text.split()
    if len(words) < n:
        return {tuple(words)}
    return {tuple(words[i:i+n]) for i in range(len(words) - n + 1)}


def jaccard_similarity(set1: set, set2: set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union


def find_stolen_passages(original: str, suspect: str, min_words: int = 10) -> list:
    """Find passages that appear in both documents (potential theft)."""
    original_sentences = re.split(r'[.!?]+', original)
    suspect_sentences = re.split(r'[.!?]+', suspect)

    stolen = []

    for orig_sent in original_sentences:
        orig_clean = normalize_text(orig_sent)
        if len(orig_clean.split()) < min_words:
            continue

        for susp_sent in suspect_sentences:
            susp_clean = normalize_text(susp_sent)

            # Check for exact or near-exact match
            ratio = difflib.SequenceMatcher(None, orig_clean, susp_clean).ratio()

            if ratio > 0.85:  # 85% similarity threshold
                stolen.append({
                    "original": orig_sent.strip(),
                    "suspect": susp_sent.strip(),
                    "similarity": round(ratio * 100, 1),
                    "verdict": "EXACT COPY" if ratio > 0.95 else "MODIFIED COPY"
                })

    return stolen


def generate_diff_html(original: str, suspect: str) -> str:
    """Generate HTML diff showing changes."""
    differ = difflib.HtmlDiff()
    return differ.make_file(
        original.splitlines(),
        suspect.splitlines(),
        fromdesc="ORIGINAL (Your Work)",
        todesc="SUSPECT (Alleged Biter)",
        context=True,
        numlines=3
    )


def print_biter_report(
    original_path: Path,
    suspect_path: Path,
    original_text: str,
    suspect_text: str,
    stolen_passages: list,
    similarity: float,
    original_hash: str,
    suspect_hash: str,
    original_griot: Optional[dict] = None
) -> None:
    """Print a formatted biter report."""
    width = 78

    # Header
    print()
    print("=" * width)
    print("  GRIOT PROTOCOL - BITER CHECK REPORT".center(width))
    print("  \"Expose the Vultures\"".center(width))
    print("=" * width)
    print()

    # Files
    print("FILES ANALYZED")
    print("-" * width)
    print(f"  ORIGINAL: {original_path.name}")
    print(f"  SHA-256:  {original_hash}")
    if original_griot:
        print(f"  SEALED:   {original_griot.get('sealed_at', 'Unknown')}")
        anchors = original_griot.get('anchors', [])
        if anchors:
            print(f"  ANCHORED: {len(anchors)} blockchain(s)")
    print()
    print(f"  SUSPECT:  {suspect_path.name}")
    print(f"  SHA-256:  {suspect_hash}")
    print()

    # Similarity Score
    print("SIMILARITY ANALYSIS")
    print("-" * width)

    if similarity > 0.8:
        verdict = "HIGHLY LIKELY PLAGIARISM"
        color = "\033[91m"  # Red
    elif similarity > 0.5:
        verdict = "SIGNIFICANT OVERLAP - INVESTIGATE"
        color = "\033[93m"  # Yellow
    elif similarity > 0.3:
        verdict = "SOME SIMILARITIES DETECTED"
        color = "\033[93m"  # Yellow
    else:
        verdict = "LOW SIMILARITY"
        color = "\033[92m"  # Green

    reset = "\033[0m"

    print(f"  Overall Similarity: {color}{similarity*100:.1f}%{reset}")
    print(f"  Verdict: {color}{verdict}{reset}")
    print()

    # Stolen Passages
    if stolen_passages:
        print(f"STOLEN PASSAGES DETECTED: {len(stolen_passages)}")
        print("-" * width)

        for i, passage in enumerate(stolen_passages[:10], 1):  # Show first 10
            print(f"\n  [{i}] {passage['verdict']} ({passage['similarity']}% match)")
            print(f"      ORIGINAL: \"{passage['original'][:100]}...\"")
            print(f"      SUSPECT:  \"{passage['suspect'][:100]}...\"")

        if len(stolen_passages) > 10:
            print(f"\n  ... and {len(stolen_passages) - 10} more passages")
        print()
    else:
        print("NO EXACT STOLEN PASSAGES DETECTED")
        print("-" * width)
        print("  The suspect document may have been heavily modified.")
        print("  Check the HTML diff for detailed comparison.")
        print()

    # Legal Notice
    print("FOR LEGAL USE")
    print("-" * width)
    print("  This report provides evidence of textual similarity.")
    print("  Combined with your .griot/.ots timestamp proof, you can establish:")
    print("    1. WHAT: Specific passages that were copied")
    print("    2. WHEN: Your work existed before the suspect's")
    print("    3. HOW MUCH: Quantified similarity percentage")
    print()
    print("  Save this report and the HTML diff for legal proceedings.")
    print()

    # Footer
    print("=" * width)
    print("  \"The Biter is cowardly; they fear the light of scrutiny.\"".center(width))
    print("  \"The Griot Protocol shines a light that cannot be dimmed.\"".center(width))
    print("=" * width)
    print()


def check_for_biting(
    original_path: Path,
    suspect_path: Path,
    output_dir: Optional[Path] = None,
    generate_html: bool = True
) -> dict:
    """Compare two documents for plagiarism."""

    if not original_path.exists():
        print(f"Error: Original file not found: {original_path}", file=sys.stderr)
        sys.exit(1)

    if not suspect_path.exists():
        print(f"Error: Suspect file not found: {suspect_path}", file=sys.stderr)
        sys.exit(1)

    # Extract text
    original_text = extract_text(original_path)
    suspect_text = extract_text(suspect_path)

    # Compute hashes
    original_hash = compute_sha256(original_path)
    suspect_hash = compute_sha256(suspect_path)

    # Check for .griot proof file
    original_griot = None
    griot_path = Path(str(original_path) + ".griot")
    if griot_path.exists():
        with open(griot_path) as f:
            original_griot = json.load(f)

    # Normalize for comparison
    original_norm = normalize_text(original_text)
    suspect_norm = normalize_text(suspect_text)

    # Calculate similarity using multiple methods

    # 1. N-gram Jaccard similarity
    original_ngrams = get_ngrams(original_norm, n=5)
    suspect_ngrams = get_ngrams(suspect_norm, n=5)
    ngram_sim = jaccard_similarity(original_ngrams, suspect_ngrams)

    # 2. Sequence matching
    seq_sim = difflib.SequenceMatcher(None, original_norm, suspect_norm).ratio()

    # Combined similarity (weighted average)
    similarity = (ngram_sim * 0.4) + (seq_sim * 0.6)

    # Find stolen passages
    stolen_passages = find_stolen_passages(original_text, suspect_text)

    # Print report
    print_biter_report(
        original_path,
        suspect_path,
        original_text,
        suspect_text,
        stolen_passages,
        similarity,
        original_hash,
        suspect_hash,
        original_griot
    )

    # Generate HTML diff
    if generate_html:
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            html_path = output_dir / f"biter_check_{original_path.stem}_vs_{suspect_path.stem}.html"
        else:
            html_path = Path(f"biter_check_{original_path.stem}_vs_{suspect_path.stem}.html")

        html_content = generate_diff_html(original_text, suspect_text)
        with open(html_path, "w") as f:
            f.write(html_content)

        print(f"HTML diff saved: {html_path}")
        print()

    # Generate JSON report
    timestamp = datetime.now(timezone.utc).isoformat()

    report = {
        "protocol": "Griot Protocol v1.0",
        "type": "biter_check_report",
        "generated_at": timestamp,
        "original": {
            "filename": original_path.name,
            "filepath": str(original_path.absolute()),
            "sha256": original_hash,
            "word_count": len(original_text.split()),
            "sealed_at": original_griot.get("sealed_at") if original_griot else None,
            "blockchain_anchors": len(original_griot.get("anchors", [])) if original_griot else 0,
        },
        "suspect": {
            "filename": suspect_path.name,
            "filepath": str(suspect_path.absolute()),
            "sha256": suspect_hash,
            "word_count": len(suspect_text.split()),
        },
        "analysis": {
            "overall_similarity": round(similarity * 100, 2),
            "ngram_similarity": round(ngram_sim * 100, 2),
            "sequence_similarity": round(seq_sim * 100, 2),
            "stolen_passages_count": len(stolen_passages),
            "verdict": "HIGHLY LIKELY PLAGIARISM" if similarity > 0.8 else
                      "SIGNIFICANT OVERLAP" if similarity > 0.5 else
                      "SOME SIMILARITIES" if similarity > 0.3 else "LOW SIMILARITY",
        },
        "stolen_passages": stolen_passages[:50],  # Limit to 50 for JSON size
    }

    # Save JSON report
    if output_dir:
        json_path = output_dir / f"biter_check_{original_path.stem}_vs_{suspect_path.stem}.json"
    else:
        json_path = Path(f"biter_check_{original_path.stem}_vs_{suspect_path.stem}.json")

    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"JSON report saved: {json_path}")
    print()
    print("\"Damn the man. Save the empire.\"")
    print()

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Griot Protocol - Biter Check (Anti-Plagiarism Tool)\n\n"
                    "\"Damn the man. Save the empire.\"\n\n"
                    "Compare documents to detect plagiarism and expose the biters.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("original", type=Path, help="Your original work (the source of truth)")
    parser.add_argument("suspect", type=Path, help="The suspect document (alleged biter's work)")
    parser.add_argument("--output", "-o", type=Path, help="Output directory for reports")
    parser.add_argument("--no-html", action="store_true", help="Skip HTML diff generation")

    args = parser.parse_args()

    report = check_for_biting(
        args.original,
        args.suspect,
        output_dir=args.output,
        generate_html=not args.no_html
    )

    # Exit with code based on similarity
    if report["analysis"]["overall_similarity"] > 50:
        sys.exit(1)  # Significant similarity detected
    sys.exit(0)


if __name__ == "__main__":
    main()
