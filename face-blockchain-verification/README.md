 TraceFace

A Python-based face identification and blockchain verification pipeline that detects a face in an input image, searches for likely public matches, compares candidate faces using similarity, hashes a canonical verification record, and stores the hash on Polygon Amoy.

# 1. Overview

This project takes a single face image as input, detects and embeds the face with InsightFace, performs a reverse-image search through SerpApi, filters social-media candidates, downloads and compares candidate faces, and then creates a structured verification record. The project does not store biometric data or original content on-chain; it stores a SHA-256 hash of a canonical record together with a public reference URL and platform name.

The combination is useful because face matching alone is not enough to prove trust or provenance. Reverse search helps find candidate public references, face similarity provides an evidence signal, and the blockchain provides a permanent, tamper-evident fingerprint for that verification result.

# 2. Problem Statement

A face image can be reposted, cropped, reused, or detached from its original context. The challenge is to answer a practical question: does this source face visually match a likely public reference, and can that result be stored in a way that later lets someone verify the hash without trusting a single central system?

This project tries to solve that by giving a repeatable process for:

- detecting a face from a source image,
- generating a numerical embedding,
- finding public web candidates through reverse-image search,
- comparing candidate faces with the source,
- creating a canonical structured record,
- hashing that record,
- and anchoring the hash on a blockchain.

# 3. Solution

The repository implements a small verification pipeline in Python. It detects a face from an input image, normalizes the embedding, calls SerpApi with Google reverse-image search, filters social-media result domains, downloads candidate images, computes cosine similarity between the source face and each candidate face, and promotes the strongest candidate if it clears the configured threshold.

When a verified match is found, it creates a `VerificationRecord` model, turns it into canonical JSON, generates a SHA-256 hash, and sends the hash plus public metadata to the Solidity contract. The actual on-chain record is not the original image, the embedding, or the full discovered page data. It is a compact record fingerprint and public reference fields.

# 4. End-to-End Pipeline

text
Input Image
  -> Face Detection
  -> Face Embedding
  -> Google Lens Search
  -> Candidate Collection
  -> Face Similarity Comparison
  -> Best Match
  -> Record Creation
  -> SHA-256 Hash
  -> Ethereum/Polygon Transaction
  -> Blockchain Verification


# 5. How It Works

# Face detection

The project uses InsightFace via `face/detector.py`. The code loads an input image, runs the `buffalo_l` model, and returns face bounding boxes and embeddings for each detected face. The pipeline requires exactly one input face before continuing.

# Face embedding

`face/embedding.py` contains the embedding helpers. It converts embedding values to NumPy arrays and normalizes them before comparison. The input face and each candidate face are reduced to a comparable vector representation.

# Reverse image search

The reverse search layer is implemented in `reverse_search/serpapi_client.py` and `reverse_search/result_parser.py`. The application uploads the input image to a temporary public URL and sends the image URL to SerpApi using the Google reverse-image engine. The response is parsed into result objects with title, link, source, thumbnail, and raw metadata.

# Candidate image analysis

In `verification/pipeline.py`, each candidate result is filtered through `reverse_search/social_filter.py`. Only supported social domains are kept. For each candidate, the project attempts to download the candidate image, decode it with OpenCV, run face detection again, and compare the candidate face encoding to the source face.

# Cosine similarity

The comparison logic is in `face/similarity.py`. It computes cosine similarity between two normalized face embeddings. The function returns a score between 0 and 1, plus the threshold and whether the result met the match rule.

# Candidate ranking

The pipeline evaluates every candidate that can be downloaded and processed, keeps the strongest similarity score, and marks the result as `matched` only if it is above the configured threshold. The `best_candidate` is then used as the verification basis.

# Record creation

A `VerificationRecord` is built in `verification/models.py` with fields such as:

- `platform`
- `post_url`
- `similarity`
- `threshold`
- `search_provider`
- `status`
- `image_sha256`

This record is structured and intended to be canonical and deterministic.

# SHA-256 hashing

The actual hash logic is implemented in `verification/hashing.py`. It takes the model data, converts it to compact canonical JSON using `sort_keys=True` and `separators=(",", ":")`, and then computes:

python
hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


Because the JSON is canonicalized, different record content yields a different hash, and the same record content yields the same hash.

# Blockchain storage

The blockchain client is in `blockchain/client.py` and the contract client wrapper is in `blockchain/contract.py`. The project connects to Polygon Amoy using `web3.py`, signs a transaction from the configured wallet, and calls `storeVerification(recordHash, postUrl, platform)` on the Solidity contract.

The code and docs in this repo target Polygon Amoy, not Ethereum Sepolia. The environment variables use `POLYGON_RPC_URL`, `CHAIN_ID=80002`, and the contract address must be configured manually.

# Blockchain verification

After a successful transaction, the code calls `getVerification(recordHash)` and checks that:

- stored hash matches the local hash,
- the stored post URL matches,
- the platform matches,
- and `exists` is `True`.

That readback form is the on-chain verification step in the current implementation.

# Tamper detection

The tamper concept is implemented by design: if the record changes, the canonical JSON changes, so the SHA-256 digest changes. That means the blockchain lookup must be performed against the new hash, not the original one. The project’s logic is consistent with this pattern:

text
Original record -> Original SHA-256 -> Blockchain lookup -> Match
Modified record -> New SHA-256 -> Blockchain lookup -> No match


The code performs this check by hashing a fresh canonical record and comparing the resulting hash to what is stored on-chain.

# 6. Technology Stack

The repository uses the following technologies and libraries:

- Python 3
- OpenCV (`opencv-python`)
- InsightFace (`insightface`)
- NumPy (`numpy`)
- SerpApi / Google reverse-image search
- Requests (`requests`)
- Pydantic (`pydantic`)
- `web3.py` (`web3`)
- Solidity
- Ethereum-compatible Polygon Amoy testnet
- Streamlit (`streamlit`)
- pytest (`pytest`)
- Python dotenv (`python-dotenv`)

The actual blockchain configuration in the code is for Polygon Amoy, not Sepolia.

# 7. Project Structure

text
.
├── contracts/
│   └── FaceVerification.sol
├── docs/
│   ├── architecture.md
│   ├── demo.md
│   └── limitations.md
├── face-blockchain-verification/
│   ├── .env.example
│   ├── .gitignore
│   ├── README.md
│   ├── RUN_INSTRUCTIONS.txt
│   ├── config.py
│   ├── main.py
│   ├── requirements.txt
│   ├── blockchain/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── contract.py
│   │   └── record.py
│   ├── face/
│   │   ├── __init__.py
│   │   ├── detector.py
│   │   ├── embedding.py
│   │   └── similarity.py
│   ├── reverse_search/
│   │   ├── __init__.py
│   │   ├── result_parser.py
│   │   ├── serpapi_client.py
│   │   └── social_filter.py
│   ├── tests/
│   │   ├── test_blockchain_record.py
│   │   ├── test_milestone2_blockchain.py
│   │   ├── test_similarity.py
│   │   └── test_social_filter.py
│   ├── ui/
│   │   └── app.py
│   ├── verification/
│   │   ├── __init__.py
│   │   ├── hashing.py
│   │   ├── models.py
│   │   └── pipeline.py
│   └── output/
└── ...

# Important files

- `contracts/FaceVerification.sol` — Solidity contract for storing verification metadata and a hash.
- `face-blockchain-verification/main.py` — CLI entry point for running the pipeline.
- `face-blockchain-verification/config.py` — environment configuration and threshold settings.
- `face-blockchain-verification/verification/pipeline.py` — orchestration logic for detection, search, comparison, hashing, and blockchain submission.
- `face-blockchain-verification/face/detector.py` — InsightFace face detection and embedding extraction.
- `face-blockchain-verification/face/similarity.py` — cosine similarity comparison logic.
- `face-blockchain-verification/reverse_search/serpapi_client.py` — SerpApi image search call.
- `face-blockchain-verification/reverse_search/social_filter.py` — filtering of social-media candidate results.
- `face-blockchain-verification/blockchain/client.py` — blockchain connection, nonce, signing, and receipt handling.
- `face-blockchain-verification/blockchain/contract.py` — ABI wrapper for `storeVerification` and `getVerification`.
- `face-blockchain-verification/verification/hashing.py` — canonical JSON → SHA-256 hashing.
- `face-blockchain-verification/ui/app.py` — Streamlit demo interface.
- `face-blockchain-verification/tests/` — small verification tests for similarity and blockchain-related logic.

# 8. Installation and Setup

These instructions are for macOS/Linux.

# 1) Clone the repository

```bash
git clone <repository-url>
cd <repository-folder>
```

# 2) Create a Python virtual environment

```bash
python3 -m venv .venv
```

# 3) Activate the virtual environment

```bash
source .venv/bin/activate
```

# 4) Install requirements

```bash
pip install -r face-blockchain-verification/requirements.txt
```

# 5) Configure `.env`

Create a local `.env` file inside `face-blockchain-verification/` based on `.env.example` and fill in the values for your local environment.

# 6) Run the application

From the project folder:

```bash
cd face-blockchain-verification
python -m main --image "path/to/your/image.jpg"
```

Optional: run the Streamlit UI:

```bash
streamlit run ui/app.py
```

# 9. Environment Variables

The project expects local environment variables such as:

```env
SERPAPI_KEY=your_api_key_here
FACE_SIMILARITY_THRESHOLD=0.65
USE_GPU=0
SERPAPI_TIMEOUT=30
MAX_IMAGE_DOWNLOAD_BYTES=5242880
POLYGON_RPC_URL=https://your_polygon_amoy_rpc_here
WALLET_ADDRESS=your_test_wallet_address
PRIVATE_KEY=your_private_key_here
CONTRACT_ADDRESS=your_deployed_contract_address
CHAIN_ID=80002
```

Important:

- `.env` must never be committed to GitHub.
- Do not paste real private keys or live credentials into source code.
- The repository includes `.gitignore` entries for `.env`, `.venv`, `output/`, and Python cache files.

# 10. Running the Project

The current CLI implementation is started with:

```bash
cd face-blockchain-verification
python -m main --image "path/to/your/image.jpg"
```

The script also supports overriding the similarity threshold:

```bash
python -m main --image "path/to/your/image.jpg" --threshold 0.65
```

The UI version is:

```bash
streamlit run ui/app.py
```

# 11. Blockchain Details

# Blockchain network

The repository is configured for Polygon Amoy testnet. The environment uses `POLYGON_RPC_URL` and `CHAIN_ID=80002` in `config.py` and `.env.example`.

# Smart contract purpose

The Solidity contract in `contracts/FaceVerification.sol` stores a verification record keyed by a hash and exposes:

- `storeVerification(bytes32 recordHash, string postUrl, string platform)`
- `getVerification(bytes32 recordHash)`

The contract stores public metadata and the hash, not the full image or embedding.

# What is stored on-chain

The contract stores:

- `recordHash`
- `postUrl`
- `platform`
- `timestamp`
- `exists`

It does not store the face image, the embedding vector, the input image itself, or any private secret.

# Why the project stores a hash instead of the full record

A full webpage, image, or all metadata would be large, variable, and not necessarily safe to keep on-chain. The code uses a canonical SHA-256 hash of the deterministic record. This gives a compact, tamper-evident fingerprint of the verification record while keeping the actual record content local and transparent.

# How `storeVerification()` works

The contract stores `recordHash`, `postUrl`, and `platform` only if the hash is non-zero and not already present. It also emits `VerificationStored` with the hash, URL, platform, timestamp, and the sender address.

# How `getVerification()` works

The function retrieves the same record by the exact hash key and returns the stored values plus the `exists` flag. The Python client then compares the readback report to the local record before treating it as verified.

There is no deployed contract address committed to the repository; you must deploy the contract and set `CONTRACT_ADDRESS` in your `.env` once the environment is ready.

# 12. Hashing and Verification

The project uses SHA-256 for a very practical reason: the same record produces the same hash, while any modification creates a different hash. That makes the hash an easy way to prove whether the same record is being referenced later.

The hash is calculated from a canonical JSON representation of the `VerificationRecord` object. Any difference in the ordering, content, or value of the record changes the output digest. This is the core tamper-evidence mechanism used by the project.

# 13. Tamper Detection

The repository is designed around the following behavior:

text
Original record -> Original SHA-256 -> Blockchain lookup -> Match
Modified record -> New SHA-256 -> Blockchain lookup -> No match


This is exactly the kind of check that the project is meant to demonstrate. The hash is created from the record structure, not from the face image itself. If any field of the verified record changes — such as the URL, platform, or similarity value — the canonical JSON changes, the SHA-256 digest changes, and the blockchain lookup against the original stored hash will not match.

The project’s Python logic intentionally uses canonical JSON (`sort_keys=True`, compact separators) so the same input record always maps to the same SHA-256 output. That makes tampering visible in a deterministic way.

# 14. Example Output

This is a representative example based on the actual CLI output format used by the project:

 text
========================================
FACE ID + BLOCKCHAIN VERIFICATION
========================================

[1/6] Loading image              ✓
[2/6] Detecting face             ✓
[3/6] Generating embedding       ✓
[4/6] Reverse image search       ✓
[5/6] Finding social candidates  ✓
[6/6] Comparing candidate faces  ✓

Face Detection: ✓
Reverse Image Search: ✓
Social Media Candidates: 3
Face Similarity: 0.88
Verification: VERIFIED VISUAL MATCH ✓

SHA-256: 6d1d1692b0f9d6c8ed38fbbf4f39c8d4d5f0e4e78279b98e4f18cc1f1d6f31a3
Blockchain: Polygon Amoy
Transaction: 0xabc123...
Block: 18542013
Gas used: 189352
Blockchain Status: CONFIRMED ✓
On-chain record verification: PASS
========================================


A no-match run would normally show similar output but without a valid candidate and without an on-chain record:

text
Face Detection: ✓
Reverse Image Search: ✓
Social Media Candidates: 0
Verification: NO MATCH
SHA-256: not generated
Transaction: not sent
Blockchain Status: NOT_ATTEMPTED


# 15. Responsible Use and Limitations

This project is a research and demonstration pipeline, not a guaranteed identity system.

- Face similarity is not the same as guaranteed identity verification.
- Reverse-image search depends on external search-engine results and indexing.
- Search results may include unrelated images or false matches.
- Candidate downloads may fail because of rate limits, temporary host availability, broken URLs, or inaccessible content.
- The blockchain stores a hash and public metadata, not proof that the person actually owns or created the discovered content.
- The system should only be used with images and content that the user is authorized to process.
- This project should not be used for stalking, unauthorized surveillance, or identifying people without appropriate consent.

# 16. Security

- `.env` is ignored by Git.
- API keys and private keys must never be committed to source control.
- Testnet funds are not real money and should only be used on the Polygon Amoy test network.
- Secrets should never be hard-coded into application source files.
- The project uses local environment variables, not a central secret manager.

# 17. Future Improvements

The current implementation is a solid prototype and there are several realistic next steps:

- better candidate ranking and threshold tuning,
- more reverse-search providers beyond SerpApi,
- better handling of images containing multiple faces,
- confidence calibration and reviewer workflows,
- stronger image-download retry and resilience logic,
- support for additional blockchains,
- additional cryptographic metadata alongside the hash,
- and a graphical interface for detailed review if the project expands beyond the current demo scope.

# 18. Demo Flow

This is a practical demo flow for a hackathon or live presentation:

1. Provide the input portrait.
2. Run the pipeline.
3. Show face detection.
4. Show Google Lens / SerpApi candidate results.
5. Show the candidate facial similarity comparison.
6. Show the selected result.
7. Show the generated SHA-256 hash.
8. Show the transaction to Polygon Amoy.
9. Show `Exists: True` during verification.
10. Show the tamper check by changing the record and showing that the new hash does not match the blockchain record.

# 19. Hackathon Relevance

This project directly addresses the face identification and blockchain verification challenge by combining a realistic evidence pipeline with a public, tamper-evident record. It demonstrates:

- face detection and embedding generation,
- reverse-image lookup through real search infrastructure,
- candidate comparison using cosine similarity,
- hashing through a canonical record model,
- and blockchain verification using a Solidity smart contract.

The result is a clear end-to-end story: detect a face, find possible public matches, compare faces, lock the proof hash to a public blockchain, and verify that the stored record still matches the evidence.

# 20. Notes on the Current Repository

This repository includes a working Python pipeline, Solidity contract, and supporting docs. The exact blockchain implementation in the code is configured for Polygon Amoy, and the project expects a valid contract deployment plus environment credentials before any live transaction is submitted.

# Appendix: Command Summary

# CLI

bash
cd face-blockchain-verification
python -m main --image "path/to/your/image.jpg"


# Streamlit UI

bash
cd face-blockchain-verification
streamlit run ui/app.py


# Tests

bash
cd face-blockchain-verification
pytest -q

