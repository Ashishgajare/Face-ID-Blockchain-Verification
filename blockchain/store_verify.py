import os
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

RPC_URL = os.getenv("SEPOLIA_RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

CONTRACT_ADDRESS = "0x99a70F91bfae2C9ad0ff808eb2465Eb85b8a0a55"

POST_HASH = "6c443b9fcff709b896531a477f2f6adb1dc7db92aa5096bfdef8518ed42a5588"

ABI = [
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "hash",
                "type": "bytes32"
            }
        ],
        "name": "storeRecord",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
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

w3 = Web3(Web3.HTTPProvider(RPC_URL))

print("\n================================")
print("TRACEFACE BLOCKCHAIN VERIFICATION")
print("================================")

print("Connected:", w3.is_connected())
print("Chain ID:", w3.eth.chain_id)

account = w3.eth.account.from_key(PRIVATE_KEY)

print("Wallet:", account.address)

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=ABI
)

# Convert SHA-256 hex string to bytes32
hash_bytes = bytes.fromhex(POST_HASH)

print("\nSHA-256:")
print(POST_HASH)

# --------------------------------
# STORE HASH
# --------------------------------

print("\nStoring hash on blockchain...")

nonce = w3.eth.get_transaction_count(account.address)

transaction = contract.functions.storeRecord(
    hash_bytes
).build_transaction({
    "from": account.address,
    "nonce": nonce,
    "chainId": 11155111,
    "gas": 200000,
    "gasPrice": w3.eth.gas_price,
    "value": 0
})

signed = w3.eth.account.sign_transaction(
    transaction,
    PRIVATE_KEY
)

tx_hash = w3.eth.send_raw_transaction(
    signed.raw_transaction
)

print("\nTransaction hash:")
print(tx_hash.hex())

print("\nWaiting for confirmation...")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print("Confirmed in block:", receipt.blockNumber)

# --------------------------------
# VERIFY HASH
# --------------------------------

print("\n================================")
print("VERIFYING HASH")
print("================================")

exists, timestamp, submitter = contract.functions.verifyRecord(
    hash_bytes
).call()

print("Exists:", exists)
print("Timestamp:", timestamp)
print("Submitter:", submitter)

print("\n================================")
print("BLOCKCHAIN VERIFICATION COMPLETE ✓")
print("================================")