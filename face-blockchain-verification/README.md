# Face ID + Blockchain Verification

This repo contains Milestone 1 plus the Milestone 2 blockchain anchoring layer.

Milestone 1 implements a face detection, embedding, genuine reverse-image search (SerpApi), social candidate filtering, candidate image retrieval and face similarity comparison pipeline.

See the CLI in `main.py` and the orchestrator in `verification/pipeline.py`.

## Blockchain status

The Solidity contract is in `../contracts/FaceVerification.sol`. The Python Web3 client is in `blockchain/client.py` and `blockchain/contract.py`. It records only a deterministic SHA-256 verification hash, post URL, platform, and on-chain timestamp. No face image, embedding, biometric vector, API key, or private key is written to the blockchain.

The local blockchain layer is validated with the test suite. A live Polygon Amoy transaction requires:

1. Deploying `FaceVerification.sol` to Polygon Amoy.
2. Adding the deployed address as `BLOCKCHAIN_CONTRACT_ADDRESS` in `.env`.
3. Adding a funded Polygon Amoy wallet private key as `BLOCKCHAIN_PRIVATE_KEY` in `.env`.
4. Setting `POLYGON_RPC_URL` to a Polygon Amoy RPC endpoint.

Never commit `.env` or share the private key.

## Deploying the contract

1. Open Remix at `https://remix.ethereum.org`.
2. Create `FaceVerification.sol` and paste the contents of `../contracts/FaceVerification.sol`.
3. Compile with Solidity `0.8.20` or another compatible `0.8.x` compiler.
4. In MetaMask, select Polygon Amoy, chain ID `80002`.
5. In Remix, choose `Injected Provider - MetaMask`, select `FaceVerification`, and deploy.
6. Copy the deployed contract address into `.env` as `CONTRACT_ADDRESS`.

Use a dedicated test wallet. Get test POL from the Polygon Amoy faucet at `https://faucet.polygon.technology/` and never use a production private key.

Configure `.env` without committing it:

```text
POLYGON_RPC_URL=https://rpc-amoy.polygon.technology
WALLET_ADDRESS=your_test_wallet_address
PRIVATE_KEY=your_test_wallet_private_key
CONTRACT_ADDRESS=your_deployed_contract_address
CHAIN_ID=80002
```

Run the complete pipeline from the project directory:

```powershell
python -m pytest tests -q
python -m main --image "C:\path\to\image.jpg"
```

The transaction is sent only after a real social candidate is face-verified. A no-match result never sends a transaction. After confirmation, open the printed `explorer_url` at `https://amoy.polygonscan.com/tx/<transaction_hash>` and confirm the transaction status and contract address.
