# Architecture

## End-to-End Flow

```text
Image
  |
  v
OpenCV image loading and decoding
  |
  v
InsightFace face detection
  |
  v
ArcFace embedding
  |
  v
Google reverse image search via SerpApi
  |
  v
Social candidate filter
  |
  v
Candidate face download and comparison
  |
  v
VerificationRecord
  |
  v
Sorted canonical JSON
  |
  v
SHA-256 hash
  |
  v
Solidity FaceVerification contract
  |
  v
Polygon Amoy transaction
  |
  v
Receipt and getVerification readback
```

## Component Boundaries

- `face/`: image loading, detection, embeddings, and cosine similarity.
- `reverse_search/`: temporary image upload, SerpApi request, response parsing, and social-domain filtering.
- `verification/models.py`: structured public verification record.
- `verification/hashing.py`: deterministic JSON-to-SHA-256 conversion.
- `verification/pipeline.py`: orchestration and transaction gate.
- `blockchain/client.py`: Polygon RPC connection, wallet balance, nonce, signing, and receipt waiting.
- `blockchain/contract.py`: ABI and `storeVerification` / `getVerification` calls.
- `contracts/FaceVerification.sol`: minimal on-chain storage for hash and public reference metadata.
- `ui/app.py`: Streamlit presentation and sanitized local report export.

## Transaction Gate

The pipeline never sends a transaction for no face, multiple faces, search failure, no candidate, inaccessible candidate, or similarity below `0.65`. A record is created only after a real candidate passes the production comparison gate. The contract receives no image, embedding, or biometric vector.
