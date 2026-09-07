# Judge Demo

## 1. Start the application

```powershell
cd "C:\Users\Ashish\OneDrive\Desktop\projects\Face ID + Blockchain Verification\face-blockchain-verification"
& "C:\Users\Ashish\Miniconda3\Scripts\conda.exe" run -n fbv streamlit run ui/app.py
```

Open `http://localhost:8501`.

## 2. Upload an image

Use an image containing exactly one visible face. The UI shows the submitted image and the configured production threshold.

## 3. Detect the face

The app runs OpenCV and InsightFace. It displays the number of faces and a detected face crop when successful.

## 4. Generate the embedding

InsightFace generates an ArcFace embedding in memory. The embedding is never displayed or stored in the report.

## 5. Run reverse-image search

SerpApi calls Google reverse image search using the temporary public image URL. The UI shows provider, status, result count, and social-candidate count.

## 6. Find an actual social-media result

A real result must match the supported social domains and have an accessible candidate image. The UI provides an Open Post link when one exists.

## 7. Verify the candidate face

The candidate image is downloaded and checked with the same InsightFace model. The candidate must pass the production similarity threshold.

## 8. Display similarity

The UI displays the strongest real candidate and its similarity beside the fixed `0.65` threshold. It describes the result as visual evidence, not identity proof.

## 9. Generate SHA-256

For a verified match, the canonical public record is hashed. The UI displays the hash; embeddings and images are excluded.

## 10. Submit the transaction

The client connects to Polygon Amoy, builds and signs `storeVerification`, and sends it using the configured test wallet.

## 11. Wait for confirmation

The UI shows the confirmed block and gas used only from the actual receipt. Failed or pending transactions are not reported as confirmed.

## 12. Show the transaction hash

A confirmed transaction receives a clickable Polygonscan link at `https://amoy.polygonscan.com/tx/<hash>`.

## 13. Open the blockchain explorer

Open the link and show the confirmed transaction, contract address, and Polygon Amoy network.

## 14. Show the stored verification record

The app calls `getVerification(recordHash)` after confirmation and reports whether the on-chain hash, post URL, platform, and existence flag match the local record.

## No-Match Demo

Use an image with no usable candidate. The correct output is `NO MATCH`, no SHA-256 record hash, `Transaction: not sent`, and `Blockchain Status: NOT_ATTEMPTED`.

## Export

Use `Export local JSON report` to download the sanitized `verification_report.json`. The app also writes it locally to `output/verification_report.json`.
