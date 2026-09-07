from __future__ import annotations

from typing import Any, Optional

from web3 import Web3


class PolygonClient:
    """Small Web3 client for Polygon Amoy transactions."""

    def __init__(
        self,
        rpc_url: str,
        wallet_address: Optional[str],
        private_key: Optional[str],
        chain_id: int = 80002,
        web3: Optional[Web3] = None,
    ) -> None:
        self.rpc_url = rpc_url
        self.wallet_address = wallet_address
        self.private_key = private_key
        self.chain_id = chain_id
        self.web3 = web3 or Web3(Web3.HTTPProvider(rpc_url))

    def connect(self) -> "PolygonClient":
        if not self.rpc_url:
            raise RuntimeError("POLYGON_RPC_URL is not configured")
        if not self.web3.is_connected():
            raise ConnectionError("Unable to connect to Polygon RPC URL")
        actual_chain_id = int(self.web3.eth.chain_id)
        if actual_chain_id != self.chain_id:
            raise ConnectionError(
                f"Connected to chain {actual_chain_id}, expected chain {self.chain_id}"
            )
        return self

    def _require_wallet(self) -> str:
        if not self.wallet_address:
            raise RuntimeError("WALLET_ADDRESS is not configured")
        if not self.private_key:
            raise RuntimeError("PRIVATE_KEY is not configured")
        if not self.web3.is_address(self.wallet_address):
            raise ValueError("WALLET_ADDRESS is invalid")
        return Web3.to_checksum_address(self.wallet_address)

    def get_balance(self) -> int:
        address = self._require_wallet()
        return int(self.web3.eth.get_balance(address))

    def get_nonce(self) -> int:
        address = self._require_wallet()
        return int(self.web3.eth.get_transaction_count(address))

    def send_transaction(self, transaction: dict[str, Any]) -> str:
        address = self._require_wallet()
        transaction = dict(transaction)
        transaction.setdefault("from", address)
        transaction.setdefault("nonce", self.get_nonce())
        transaction.setdefault("chainId", self.chain_id)
        signed = self.web3.eth.account.sign_transaction(transaction, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex()

    def wait_for_receipt(self, transaction_hash: str, timeout: int = 180) -> Any:
        return self.web3.eth.wait_for_transaction_receipt(transaction_hash, timeout=timeout)

    def explorer_url(self, transaction_hash: str) -> str:
        return f"https://amoy.polygonscan.com/tx/{transaction_hash}"
