# Face ID + Blockchain Verification

A hackathon-ready verification studio that combines face detection, ArcFace embeddings, real reverse-image search, social candidate comparison, deterministic SHA-256 records, and tamper-evident Polygon Amoy anchoring.

Similarity is evidence for review, not proof of identity.

## 1. Project Overview

The system accepts one source image, finds possible public references through Google reverse image search via SerpApi, compares accessible candidate faces with InsightFace, and anchors only a genuine verified match on Polygon Amoy.

## 2. Problem Statement

Images are copied, reposted, and detached from their original context. A reviewer needs a repeatable way to compare a source face with public references and preserve the result without putting biometric data on-chain.

## 3. Solution

The application produces a structured verification record containing the candidate URL, platform, similarity, threshold, provider, and status. It hashes that canonical record with SHA-256 and stores only the hash plus public reference metadata in a Solidity contract.

## 4. Architecture

```text
Image
  -> OpenCV
  -> InsightFace face detection
  -> ArcFace embedding
  -> Google reverse image search via SerpApi
  -> Social candidate filter
  -> Candidate face comparison
  -> VerificationRecord
  -> Canonical JSON
  -> SHA-256
  -> Solidity contract
  -> Polygon Amoy
  -> Transaction receipt
  -> Local and on-chain report
```

## 5. Tech Stack

- Python 3.11
- OpenCV
- InsightFace and ONNX Runtime
- NumPy
- SerpApi
- Pydantic
- web3.py
- Solidity `^0.8.20`
- Polygon Amoy, chain ID `80002`
- Streamlit
- pytest

## 6. Installation

Use the tested Conda environment on Windows:

```powershell
$conda = "C:\Users\Ashish\Miniconda3\Scripts\conda.exe"
& $conda create -n fbv python=3.11 -y
& $conda run -n fbv python -m pip install -r requirements.txt
```

Run all tests:

```powershell
& $conda run -n fbv python -m pytest tests -q
```

## 7. Environment Variables

Create `face-blockchain-verification/.env` locally. Start from `.env.example` and never commit `.env`.

```text
SERPAPI_KEY=your_serpapi_key
FACE_SIMILARITY_THRESHOLD=0.65
USE_GPU=0
SERPAPI_TIMEOUT=30
MAX_IMAGE_DOWNLOAD_BYTES=5242880
POLYGON_RPC_URL=https://your-amoy-rpc-endpoint
WALLET_ADDRESS=your_test_wallet_address
PRIVATE_KEY=your_test_wallet_private_key
CONTRACT_ADDRESS=your_deployed_contract_address
CHAIN_ID=80002
```

Private keys and API keys are loaded only from the local environment and are never displayed, hashed, uploaded, or written to reports.

## 8. SerpApi Setup

Create a SerpApi account and place the key in `.env` as `SERPAPI_KEY`. The reverse-search client uploads the image to a temporary direct-image host, then calls:

```text
GET https://serpapi.com/search.json
engine=google_reverse_image
image_url=<temporary public image URL>
```

The live response is parsed without hardcoded search results.

## 9. InsightFace Setup

The first face-detection run downloads the `buffalo_l` model into:

```text
C:\Users\Ashish\.insightface\models\buffalo_l
```

The model runs through CPU ONNX Runtime unless GPU mode is explicitly configured.

## 10. Polygon Amoy Setup

Use a dedicated test wallet on Polygon Amoy. Chain ID is `80002`. Obtain test POL from the Polygon faucet:

https://faucet.polygon.technology/

## 11. Smart Contract Deployment

1. Open https://remix.ethereum.org.
2. Create `FaceVerification.sol` using `../contracts/FaceVerification.sol`.
3. Compile with Solidity `0.8.20`.
4. Connect MetaMask using Polygon Amoy.
5. Choose `Injected Provider - MetaMask`.
6. Deploy `FaceVerification`.
7. Copy the deployed address into `.env` as `CONTRACT_ADDRESS`.

The contract stores a record hash, post URL, platform, and timestamp. It never stores images, embeddings, biometric vectors, keys, or API tokens.

## 12. Run the CLI

From the application directory:

```powershell
cd "C:\Users\Ashish\OneDrive\Desktop\projects\Face ID + Blockchain Verification\face-blockchain-verification"
& "C:\Users\Ashish\Miniconda3\Scripts\conda.exe" run -n fbv python main.py --image "C:\path\to\image.jpg"
```

Production mode keeps the `0.65` threshold. A blockchain transaction occurs only after a real candidate face passes that gate.

## 13. Run Streamlit

```powershell
cd "C:\Users\Ashish\OneDrive\Desktop\projects\Face ID + Blockchain Verification\face-blockchain-verification"
& "C:\Users\Ashish\Miniconda3\Scripts\conda.exe" run -n fbv streamlit run ui/app.py
```

Open the local URL shown by Streamlit, normally `http://localhost:8501`.

The UI provides upload, progress, face crop, search metrics, candidate details, match status, blockchain receipt details, and a sanitized report download.

## 14. Example Output

```text
Face Detection: ✓
Reverse Image Search: ✓
Social Media Candidates: 5
Face Similarity: 0.93
Verification: VERIFIED VISUAL MATCH ✓
SHA-256: <64-character hash>
Blockchain: Polygon Amoy
Transaction: <real transaction hash>
Block: <real block number>
Gas used: <real gas used>
Blockchain Status: CONFIRMED ✓
On-chain record verification: PASS
```

A no-match run prints `SHA-256: not generated`, `Transaction: not sent`, and `Blockchain Status: NOT_ATTEMPTED`.

## 15. Security

- `.env` is ignored by Git.
- Private keys and API keys are never printed or logged.
- Embeddings are used in memory only.
- Embeddings and images are never sent to the contract.
- Reports contain only public verification metadata and hashes.
- Use a test wallet with test POL, never a production wallet.

## 16. Privacy

The image is processed locally for face detection. Reverse-image search requires a temporary public image URL so the external search provider can access the image. Do not upload sensitive images without permission. Temporary-host retention and third-party search policies apply.

## 17. Limitations

- Reverse-image search only sees pages indexed by Google and exposed through SerpApi.
- Private, deleted, blocked, or unindexed posts cannot be found.
- Candidate images may be inaccessible or unsuitable for face detection.
- Lighting, pose, occlusion, resolution, and compression affect similarity.
- Similarity can produce false positives and false negatives.
- The `0.65` threshold is a configured engineering decision, not a universal identity standard.
- Polygon Amoy is a testnet; RPC availability, gas rules, and test POL are not production guarantees.
- A blockchain record proves that a specific result hash was stored; it does not prove a person's real-world identity.

## 18. Future Improvements

- User-controlled consent and retention policies.
- Multiple candidate ranking and reviewer approval.
- Better provider adapters and retry handling.
- Contract deployment automation with audited artifacts.
- Production key management through a secrets manager.
- Human review workflows and signed reviewer attestations.

## Repository Layout

```text
contracts/FaceVerification.sol
face-blockchain-verification/
  blockchain/       Polygon client and contract interaction
  face/             detection, embeddings, similarity
  reverse_search/   SerpApi and social filtering
  verification/     pipeline, models, hashing
  tests/            unit and integration-boundary tests
  ui/app.py         Streamlit Verification Studio
  main.py           CLI entrypoint
```
