import os
import hashlib
import json

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

RPC_URL = os.getenv("SEPOLIA_RPC_URL")

CONTRACT_ADDRESS = "0x99a70F91bfae2C9ad0ff808eb2465Eb85b8a0a55"

ABI = [
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "hash",
                "type": "bytes32"
            }
        ],
        "name": "verifyRecord",
        "outputs": [
            {
                "internalType": "bool",
                "name": "exists",
                "type": "bool"
            },
            {
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            },
            {
                "internalType": "address",
                "name": "submitter",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]


def calculate_hash(record):
    canonical = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":")
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


w3 = Web3(Web3.HTTPProvider(RPC_URL))

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=ABI
)

# Original record
original_record = {
    "title": "Women's black top - Free Photo on Unsplash",
    "source": "Unsplash",
    "post_url": "https://unsplash.com/photos/womens-black-top-25WM4IEnPIg"
}

# Tampered record
tampered_record = {
    "title": "Women's black top - Free Photo on Unsplash",
    "source": "Unsplash",
    "post_url": "https://unsplash.com/photos/FAKE-CHANGED-URL"
}

original_hash = calculate_hash(original_record)
tampered_hash = calculate_hash(tampered_record)

print("\n================================")
print("TRACEFACE TAMPER DETECTION")
print("================================")

print("\nOriginal SHA-256:")
print(original_hash)

print("\nTampered SHA-256:")
print(tampered_hash)

# Verify original hash
original_exists, _, _ = contract.functions.verifyRecord(
    bytes.fromhex(original_hash)
).call()

# Verify tampered hash
tampered_exists, _, _ = contract.functions.verifyRecord(
    bytes.fromhex(tampered_hash)
).call()

print("\n================================")
print("RESULT")
print("================================")

print("Original hash exists:", original_exists)
print("Tampered hash exists:", tampered_exists)

if original_exists and not tampered_exists:
    print("\n✓ TAMPER DETECTED")
    print("Original data matches blockchain record.")
    print("Modified data does NOT match blockchain record.")
else:
    print("\n✗ TAMPER TEST FAILED")

print("\n================================")