# Griot Protocol

> *"Damn the man. Save the empire."*

**Immutable proof that no corporation can deny, no server can delete.**

Named for West African griots—oral historians who preserved cultural truth across generations—the Griot Protocol provides blockchain-backed timestamping for research integrity and whistleblower protection.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Seal a document (generates SHA-256 Truth Seal)
python griot_seal.py seal document.pdf

# Verify a document
python griot_seal.py verify document.pdf abc123...

# Batch seal a directory
python griot_seal.py batch ./research_data --recursive
```

## Blockchain Anchoring

The nuclear option. Anchor your documents to public blockchains for immutable timestamping.

### Bitcoin (FREE via OpenTimestamps)

```bash
# Requires: pip install opentimestamps-client
python blockchain_anchor.py seal document.pdf --chain bitcoin
```

- **Cost:** FREE (calendar servers pay the fees)
- **Confirmation:** ~2 hours (Bitcoin block time)
- **Output:** Creates `document.pdf.ots` proof file

### EVM Chains (Polygon, Ethereum, Base, Arbitrum)

```bash
# Setup: Create .env file with your private key
echo "ETH_PRIVATE_KEY=your_private_key_here" > .env

# Anchor to Polygon (cheapest)
python blockchain_anchor.py seal document.pdf --chain polygon

# Multiple chains for redundancy
python blockchain_anchor.py seal document.pdf -c bitcoin -c polygon -c base
```

| Chain | Cost | Speed |
|-------|------|-------|
| Polygon | $0.01-0.05 | Instant |
| Base | $0.001-0.01 | Instant |
| Arbitrum | $0.01-0.10 | Instant |
| Ethereum | $2-15 | 15 seconds |

**How it works:** Sends a 0 ETH transaction to yourself with the document's SHA-256 hash in the `data` field. This creates a permanent, publicly verifiable record on block explorers.

### Verification

```bash
# Verify file against its proof
python blockchain_anchor.py verify document.pdf document.pdf.griot
```

## Git Integration

Auto-seal every commit:

```bash
python blockchain_anchor.py install-hook
```

This creates a post-commit hook that:
1. Captures commit hash, message, author, timestamp
2. Creates a JSON manifest in `.griot/proofs/`
3. Anchors to Bitcoin via OpenTimestamps (if installed)

## MAIF Research Pipeline

For sealing audio research outputs:

```bash
# Process audio files through the pipeline
python maif_griot_pipeline.py process --input ./tracks --output ./results

# Verify a sealed corpus
python maif_griot_pipeline.py verify results/corpus_manifest.json
```

The pipeline:
1. Scans for audio files (mp3, wav, flac, etc.)
2. Runs MAIF analysis (if MAIF_Gen.py is available)
3. Generates Truth Seals for all files
4. Creates per-track manifests
5. Generates a Genesis Seal (root hash of entire corpus)

## Output Files

| File | Description |
|------|-------------|
| `.griot` | Complete proof manifest (JSON) with all anchor details |
| `.ots` | Bitcoin proof file (OpenTimestamps) |
| `*_manifest.json` | Per-file or per-track manifest |
| `corpus_manifest.json` | Master manifest with Genesis Seal |

## Environment Variables

Create a `.env` file:

```bash
# Required for EVM chain anchoring
ETH_PRIVATE_KEY=your_private_key_without_0x_prefix

# Optional: Custom RPC endpoints
# ETH_RPC_URL=https://your-rpc.com
# POLYGON_RPC_URL=https://your-polygon-rpc.com
```

## Security Notes

- Never commit your `.env` file
- The private key only needs minimal funds for gas
- Consider using a dedicated "anchoring" wallet
- All proofs are publicly verifiable on block explorers

## Philosophy

The Griot Protocol is built for:

- **Research Integrity:** Prove when your research existed
- **Whistleblower Protection:** Immutable evidence that can't be deleted
- **Intellectual Property:** Timestamped proof of creation
- **Data Authenticity:** Verify documents haven't been altered

In an age of deepfakes and deniability, we need cryptographic truth.

---

## Standing on Shoulders

The Griot Protocol builds upon and acknowledges the foundational work of others in the cryptographic timestamping space:

### Core Technologies
- **[OpenTimestamps](https://opentimestamps.org/)** - Peter Todd's scalable, trust-minimized Bitcoin timestamping protocol. The Griot Protocol uses OpenTimestamps for free Bitcoin anchoring.
- **[Proof of Existence (POEX.IO)](https://proofofexistence.com/)** - Early pioneer in blockchain document certification.
- **[Chainpoint](https://chainpoint.org/)** - Open standard for anchoring data to Bitcoin via Merkle trees.

### Academic Research
- [Monitoring File Integrity Using Blockchain and Smart Contracts](https://ieeexplore.ieee.org/document/9246586/) - IEEE research on blockchain-based integrity verification
- [Blockchain-based Document Management Frameworks](https://www.sciencedirect.com/science/article/abs/pii/S0926580521004520) - ScienceDirect research on construction document integrity
- [Universal Blockchain Time Protocol (UBTP)](https://www.gate.com/learn/articles/what-is-timestamp-on-blockchain/795) - 2025 standardization efforts

### Philosophy
The name "Griot" honors [West African oral historians](https://en.wikipedia.org/wiki/Griot) who preserved cultural truth across generations without written records. In the digital age, we face the opposite problem: too much can be written, edited, deleted, and denied. Cryptographic timestamping is the modern griot - preserving truth in immutable form.

This is not novel invention. This is synthesis - taking what already exists in the ether and making it accessible for those who need it most: researchers, whistleblowers, journalists, and anyone fighting for truth against power.

---

*"Damn the man. Save the empire."*
