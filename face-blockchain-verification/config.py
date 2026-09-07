from __future__ import annotations
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

SERPAPI_KEY: Optional[str] = os.getenv("SERPAPI_KEY")
FACE_SIMILARITY_THRESHOLD: float = float(os.getenv("FACE_SIMILARITY_THRESHOLD", "0.65"))
USE_GPU: bool = bool(int(os.getenv("USE_GPU", "0")))
SERPAPI_TIMEOUT: int = int(os.getenv("SERPAPI_TIMEOUT", "30"))
MAX_IMAGE_DOWNLOAD_BYTES: int = int(os.getenv("MAX_IMAGE_DOWNLOAD_BYTES", "5242880"))
POLYGON_RPC_URL: Optional[str] = os.getenv("POLYGON_RPC_URL") or os.getenv("BLOCKCHAIN_RPC_URL")
WALLET_ADDRESS: Optional[str] = os.getenv("WALLET_ADDRESS")
PRIVATE_KEY: Optional[str] = os.getenv("PRIVATE_KEY") or os.getenv("BLOCKCHAIN_PRIVATE_KEY")
CONTRACT_ADDRESS: Optional[str] = os.getenv("CONTRACT_ADDRESS") or os.getenv("BLOCKCHAIN_CONTRACT_ADDRESS")
CHAIN_ID: int = int(os.getenv("CHAIN_ID", os.getenv("BLOCKCHAIN_CHAIN_ID", "80002")))

def require_serpapi_key() -> None:
    if not SERPAPI_KEY:
        raise RuntimeError(
            "SERPAPI_KEY is not set. Add it to your .env file (see .env.example)."
        )
