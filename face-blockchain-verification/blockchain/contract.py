from __future__ import annotations

from typing import Any, Dict

from web3 import Web3

from .client import PolygonClient


FACE_VERIFICATION_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "recordHash", "type": "bytes32"},
            {"internalType": "string", "name": "postUrl", "type": "string"},
            {"internalType": "string", "name": "platform", "type": "string"},
        ],
        "name": "storeVerification",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "recordHash", "type": "bytes32"}],
        "name": "getVerification",
        "outputs": [
            {"internalType": "bytes32", "name": "storedHash", "type": "bytes32"},
            {"internalType": "string", "name": "postUrl", "type": "string"},
            {"internalType": "string", "name": "platform", "type": "string"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "bool", "name": "exists", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


class FaceVerificationContract:
    """Client for an already deployed FaceVerification contract."""

    def __init__(self, client: PolygonClient, contract_address: str) -> None:
        if not Web3.is_address(contract_address):
            raise ValueError("CONTRACT_ADDRESS is invalid")
        self.client = client
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.contract = client.web3.eth.contract(
            address=self.contract_address,
            abi=FACE_VERIFICATION_ABI,
        )

    @staticmethod
    def _hash_bytes(record_hash: str) -> bytes:
        value = record_hash.removeprefix("0x")
        if len(value) != 64:
            raise ValueError("record_hash must be a 32-byte SHA-256 hex digest")
        try:
            return bytes.fromhex(value)
        except ValueError as exc:
            raise ValueError("record_hash must contain only hexadecimal characters") from exc

    def store_verification(self, record_hash: str, post_url: str, platform: str) -> Dict[str, Any]:
        try:
            function_call = self.contract.functions.storeVerification(
                self._hash_bytes(record_hash), post_url, platform
            )
            gas_estimate = function_call.estimate_gas({"from": self.client.wallet_address})
            transaction = function_call.build_transaction(
                {
                    "from": self.client.wallet_address,
                    "nonce": self.client.get_nonce(),
                    "chainId": self.client.chain_id,
                    "gas": max(250_000, (int(gas_estimate) * 125) // 100),
                    "maxFeePerGas": self.client.web3.to_wei(100, "gwei"),
                    "maxPriorityFeePerGas": self.client.web3.to_wei(25, "gwei"),
                }
            )
            transaction_hash = self.client.send_transaction(transaction)
            receipt = self.client.wait_for_receipt(transaction_hash)
            block_number = int(receipt["blockNumber"] if isinstance(receipt, dict) else receipt.blockNumber)
            status = int(receipt["status"] if isinstance(receipt, dict) else receipt.status)
            gas_used = int(receipt["gasUsed"] if isinstance(receipt, dict) else receipt.gasUsed)
            return {
                "success": status == 1,
                "transaction_hash": transaction_hash,
                "block_number": block_number,
                "gas_used": gas_used,
                "contract_address": self.contract_address,
                "chain_id": self.client.chain_id,
                "explorer_url": self.client.explorer_url(transaction_hash),
                "error": None if status == 1 else "Transaction receipt reported failure",
            }
        except Exception as exc:
            return {
                "success": False,
                "transaction_hash": None,
                "block_number": None,
                "contract_address": self.contract_address,
                "chain_id": self.client.chain_id,
                "explorer_url": None,
                "error": str(exc),
            }

    def get_verification(self, record_hash: str) -> Dict[str, Any]:
        result = self.contract.functions.getVerification(self._hash_bytes(record_hash)).call()
        return {
            "record_hash": "0x" + result[0].hex(),
            "post_url": result[1],
            "platform": result[2],
            "timestamp": int(result[3]),
            "exists": bool(result[4]),
        }
