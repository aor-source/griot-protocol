#!/usr/bin/env python3
"""
Griot Protocol - Blockchain Anchor

Named for West African griots - oral historians who preserved cultural truth across generations.
"Damn the man. Save the empire." - Immutable proof that no corporation can deny, no server can delete.

Multi-chain blockchain timestamping using:
- Bitcoin (via OpenTimestamps) - FREE, ~2 hour confirmation
- EVM chains (Polygon, Ethereum, Base, Arbitrum) - via 0 ETH self-transaction
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Optional imports - graceful degradation if not installed
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

try:
    from web3 import Web3
    from eth_account import Account
    HAS_WEB3 = True
except ImportError:
    HAS_WEB3 = False


# Chain configurations
CHAIN_CONFIGS = {
    "ethereum": {
        "chain_id": 1,
        "name": "Ethereum Mainnet",
        "explorer": "https://etherscan.io",
        "rpcs": [
            "https://eth.llamarpc.com",
            "https://rpc.ankr.com/eth",
            "https://ethereum.publicnode.com",
        ],
        "cost": "$2-15",
    },
    "polygon": {
        "chain_id": 137,
        "name": "Polygon Mainnet",
        "explorer": "https://polygonscan.com",
        "rpcs": [
            "https://polygon.llamarpc.com",
            "https://rpc.ankr.com/polygon",
            "https://polygon-bor.publicnode.com",
        ],
        "cost": "$0.01-0.05",
    },
    "base": {
        "chain_id": 8453,
        "name": "Base Mainnet",
        "explorer": "https://basescan.org",
        "rpcs": [
            "https://mainnet.base.org",
            "https://base.llamarpc.com",
            "https://rpc.ankr.com/base",
        ],
        "cost": "$0.001-0.01",
    },
    "arbitrum": {
        "chain_id": 42161,
        "name": "Arbitrum One",
        "explorer": "https://arbiscan.io",
        "rpcs": [
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum.llamarpc.com",
            "https://rpc.ankr.com/arbitrum",
        ],
        "cost": "$0.01-0.10",
    },
}


def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_env_file() -> None:
    """Load environment variables from .env file."""
    if HAS_DOTENV:
        # Check multiple locations for .env
        env_locations = [
            Path.cwd() / ".env",
            Path.home() / ".griot" / ".env",
            Path(__file__).parent / ".env",
        ]
        for env_path in env_locations:
            if env_path.exists():
                load_dotenv(env_path)
                return


def get_private_key() -> Optional[str]:
    """Get Ethereum private key from environment."""
    load_env_file()
    key = os.environ.get("ETH_PRIVATE_KEY") or os.environ.get("PRIVATE_KEY")
    if key and key.startswith("0x"):
        key = key[2:]
    return key


def anchor_bitcoin(filepath: Path, file_hash: str) -> Optional[dict]:
    """Anchor to Bitcoin using OpenTimestamps (FREE)."""
    # Check if ots is available
    if not shutil.which("ots"):
        print("  ⚠ OpenTimestamps CLI not found. Install with: pip install opentimestamps-client")
        print("    Skipping Bitcoin anchor.")
        return None

    print(f"  → Anchoring to Bitcoin via OpenTimestamps...")

    # Create a temp file with just the hash if we want to stamp the hash
    # Or stamp the actual file
    try:
        result = subprocess.run(
            ["ots", "stamp", str(filepath)],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            print(f"  ✗ OpenTimestamps failed: {result.stderr}")
            return None

        ots_file = Path(str(filepath) + ".ots")
        if ots_file.exists():
            print(f"  ✓ Bitcoin anchor created: {ots_file.name}")
            print(f"    Note: Full confirmation takes ~2 hours (Bitcoin block time)")
            return {
                "chain": "bitcoin",
                "method": "opentimestamps",
                "proof_file": str(ots_file),
                "status": "pending_confirmation",
                "note": "Upgrade proof after ~2 hours with: ots upgrade " + str(ots_file),
            }
        else:
            print(f"  ✗ OTS file not created")
            return None

    except subprocess.TimeoutExpired:
        print("  ✗ OpenTimestamps timed out")
        return None
    except Exception as e:
        print(f"  ✗ OpenTimestamps error: {e}")
        return None


def anchor_evm(filepath: Path, file_hash: str, chain: str) -> Optional[dict]:
    """Anchor to an EVM chain using 0 ETH self-transaction."""
    if not HAS_WEB3:
        print(f"  ⚠ web3.py not installed. Install with: pip install web3")
        print(f"    Skipping {chain} anchor.")
        return None

    private_key = get_private_key()
    if not private_key:
        print(f"  ⚠ No private key found. Set ETH_PRIVATE_KEY in .env file")
        print(f"    Skipping {chain} anchor.")
        return None

    config = CHAIN_CONFIGS.get(chain)
    if not config:
        print(f"  ✗ Unknown chain: {chain}")
        return None

    print(f"  → Anchoring to {config['name']} (cost: {config['cost']})...")

    # Try each RPC until one works
    w3 = None
    for rpc in config["rpcs"]:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 30}))
            if w3.is_connected():
                break
        except Exception:
            continue

    if not w3 or not w3.is_connected():
        print(f"  ✗ Could not connect to any {chain} RPC")
        return None

    try:
        account = Account.from_key(private_key)
        address = account.address

        # Check balance
        balance = w3.eth.get_balance(address)
        if balance == 0:
            print(f"  ✗ Wallet has zero balance on {chain}")
            print(f"    Address: {address}")
            return None

        # Build the transaction
        # The document hash goes in the data field
        tx = {
            'to': address,  # Send to yourself
            'value': 0,     # Zero value
            'data': bytes.fromhex(file_hash),  # Document hash as input data
            'gas': 25000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(address),
            'chainId': config["chain_id"],
        }

        # Estimate gas (in case 25000 isn't enough)
        try:
            estimated_gas = w3.eth.estimate_gas(tx)
            tx['gas'] = int(estimated_gas * 1.2)  # 20% buffer
        except Exception:
            pass  # Keep default

        # Sign and send
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_hash_hex = tx_hash.hex()

        explorer_url = f"{config['explorer']}/tx/0x{tx_hash_hex}"

        print(f"  ✓ Transaction sent: 0x{tx_hash_hex[:16]}...")
        print(f"    Explorer: {explorer_url}")

        return {
            "chain": chain,
            "chain_name": config["name"],
            "chain_id": config["chain_id"],
            "method": "self_transaction",
            "tx_hash": f"0x{tx_hash_hex}",
            "explorer_url": explorer_url,
            "from_address": address,
            "data_field": file_hash,
            "status": "submitted",
        }

    except Exception as e:
        print(f"  ✗ {chain} transaction failed: {e}")
        return None


def seal_file(
    filepath: Path,
    chains: list[str],
    output_path: Optional[Path] = None,
) -> dict:
    """Seal a file and anchor to specified blockchains."""
    if not filepath.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.now(timezone.utc).isoformat()
    file_hash = compute_sha256(filepath)
    file_size = filepath.stat().st_size

    print()
    print("GRIOT PROTOCOL - BLOCKCHAIN ANCHOR")
    print("=" * 60)
    print(f"File: {filepath.name}")
    print(f"Size: {file_size:,} bytes")
    print(f"SHA-256: {file_hash}")
    print("=" * 60)
    print()
    print("Anchoring to blockchains...")
    print()

    anchors = []

    for chain in chains:
        if chain == "bitcoin":
            result = anchor_bitcoin(filepath, file_hash)
        else:
            result = anchor_evm(filepath, file_hash, chain)

        if result:
            anchors.append(result)
        print()

    # Create .griot proof file
    griot_data = {
        "protocol": "Griot Protocol v1.0",
        "type": "blockchain_anchor",
        "filename": filepath.name,
        "filepath": str(filepath.absolute()),
        "sha256": file_hash,
        "size_bytes": file_size,
        "sealed_at": timestamp,
        "anchors": anchors,
    }

    if output_path:
        griot_path = output_path
    else:
        griot_path = Path(str(filepath) + ".griot")

    with open(griot_path, "w") as f:
        json.dump(griot_data, f, indent=2)

    print("=" * 60)
    print(f"Proof file saved: {griot_path}")
    print(f"Successful anchors: {len(anchors)}/{len(chains)}")
    print()
    print("\"Damn the man. Save the empire.\"")
    print()

    return griot_data


def verify_anchor(filepath: Path, griot_path: Path) -> bool:
    """Verify a file against its .griot proof."""
    if not filepath.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    if not griot_path.exists():
        print(f"Error: Proof file not found: {griot_path}", file=sys.stderr)
        sys.exit(1)

    with open(griot_path) as f:
        proof = json.load(f)

    current_hash = compute_sha256(filepath)
    expected_hash = proof.get("sha256", "")

    print()
    print("GRIOT PROTOCOL - VERIFICATION")
    print("=" * 60)
    print(f"File: {filepath.name}")
    print(f"Proof: {griot_path.name}")
    print(f"Sealed at: {proof.get('sealed_at', 'Unknown')}")
    print("=" * 60)
    print()
    print(f"Expected hash: {expected_hash}")
    print(f"Current hash:  {current_hash}")
    print()

    if current_hash == expected_hash:
        print("✓ HASH VERIFIED - Document integrity confirmed")
        print()

        # Show anchor details
        anchors = proof.get("anchors", [])
        if anchors:
            print("Blockchain anchors:")
            for anchor in anchors:
                chain = anchor.get("chain", "unknown")
                if chain == "bitcoin":
                    print(f"  • Bitcoin (OpenTimestamps)")
                    print(f"    Proof: {anchor.get('proof_file', 'N/A')}")
                    if anchor.get("status") == "pending_confirmation":
                        print(f"    Status: Pending (upgrade with 'ots upgrade')")
                else:
                    print(f"  • {anchor.get('chain_name', chain)}")
                    print(f"    TX: {anchor.get('tx_hash', 'N/A')}")
                    print(f"    Explorer: {anchor.get('explorer_url', 'N/A')}")
        print()
        return True
    else:
        print("✗ HASH MISMATCH - Document may have been altered!")
        print()
        return False


def install_git_hook() -> None:
    """Install a git post-commit hook for automatic anchoring."""
    # Find git directory
    git_dir = Path.cwd() / ".git"
    if not git_dir.exists():
        print("Error: Not a git repository (no .git directory found)", file=sys.stderr)
        sys.exit(1)

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    hook_path = hooks_dir / "post-commit"
    griot_dir = Path.cwd() / ".griot" / "proofs"

    hook_script = f'''#!/bin/bash
# Griot Protocol - Git Post-Commit Hook
# "Damn the man. Save the empire."

set -e

GRIOT_DIR="{griot_dir}"
mkdir -p "$GRIOT_DIR"

# Get commit details
COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_SHORT=$(git rev-parse --short HEAD)
COMMIT_MSG=$(git log -1 --pretty=%B)
COMMIT_DATE=$(git log -1 --format=%cI)
AUTHOR=$(git log -1 --format="%an <%ae>")

# Create manifest
MANIFEST_FILE="$GRIOT_DIR/commit-$COMMIT_SHORT.json"

cat > "$MANIFEST_FILE" << EOF
{{
  "protocol": "Griot Protocol v1.0",
  "type": "git_commit",
  "commit_hash": "$COMMIT_HASH",
  "commit_short": "$COMMIT_SHORT",
  "commit_date": "$COMMIT_DATE",
  "author": "$AUTHOR",
  "message": $(echo "$COMMIT_MSG" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))')
}}
EOF

echo "Griot: Created commit manifest at $MANIFEST_FILE"

# Anchor to Bitcoin via OpenTimestamps if available
if command -v ots &> /dev/null; then
    ots stamp "$MANIFEST_FILE" 2>/dev/null && echo "Griot: Bitcoin anchor created" || true
fi

echo "Griot: Commit sealed. \"Damn the man. Save the empire.\""
'''

    # Check if hook already exists
    if hook_path.exists():
        with open(hook_path) as f:
            existing = f.read()
        if "Griot Protocol" in existing:
            print("Griot git hook is already installed.")
            return
        else:
            print("Warning: Existing post-commit hook found.")
            print("Please manually integrate Griot into your existing hook.")
            print()
            print("Add this to your post-commit hook:")
            print("-" * 40)
            print(hook_script)
            print("-" * 40)
            return

    with open(hook_path, "w") as f:
        f.write(hook_script)

    # Make executable
    hook_path.chmod(0o755)

    print()
    print("GRIOT PROTOCOL - GIT HOOK INSTALLED")
    print("=" * 50)
    print(f"Hook location: {hook_path}")
    print(f"Proofs directory: {griot_dir}")
    print()
    print("Every commit will now be automatically sealed.")
    print("Bitcoin anchoring via OpenTimestamps (if installed).")
    print()
    print("\"Damn the man. Save the empire.\"")
    print()


def list_chains() -> None:
    """List available blockchain chains."""
    print()
    print("GRIOT PROTOCOL - AVAILABLE CHAINS")
    print("=" * 60)
    print()
    print("Bitcoin (FREE via OpenTimestamps):")
    print("  • bitcoin - ~2 hour confirmation, requires 'ots' CLI")
    print()
    print("EVM Chains (requires ETH_PRIVATE_KEY in .env):")
    for name, config in CHAIN_CONFIGS.items():
        print(f"  • {name} - {config['name']}, cost: {config['cost']}")
    print()
    print("Usage: blockchain_anchor.py seal FILE --chain bitcoin --chain polygon")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Griot Protocol - Blockchain Anchor\n\n"
                    "\"Damn the man. Save the empire.\"\n\n"
                    "Immutable blockchain timestamping for document integrity.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Seal command
    seal_parser = subparsers.add_parser("seal", help="Anchor a file to blockchain(s)")
    seal_parser.add_argument("file", type=Path, help="File to anchor")
    seal_parser.add_argument(
        "--chain", "-c",
        action="append",
        dest="chains",
        choices=["bitcoin", "ethereum", "polygon", "base", "arbitrum"],
        help="Blockchain to anchor to (can specify multiple)"
    )
    seal_parser.add_argument("--output", "-o", type=Path, help="Output path for .griot file")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a file against its proof")
    verify_parser.add_argument("file", type=Path, help="File to verify")
    verify_parser.add_argument("proof", type=Path, help="The .griot proof file")

    # Install hook command
    subparsers.add_parser("install-hook", help="Install git post-commit hook")

    # List chains command
    subparsers.add_parser("chains", help="List available blockchain chains")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "seal":
        chains = args.chains or ["bitcoin"]  # Default to Bitcoin (free)
        seal_file(args.file, chains, args.output)

    elif args.command == "verify":
        success = verify_anchor(args.file, args.proof)
        sys.exit(0 if success else 1)

    elif args.command == "install-hook":
        install_git_hook()

    elif args.command == "chains":
        list_chains()


if __name__ == "__main__":
    main()
