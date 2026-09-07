import os

from dotenv import load_dotenv
from web3 import Web3
from solcx import compile_source, install_solc


load_dotenv()

RPC_URL = os.getenv("SEPOLIA_RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

if not RPC_URL:
    raise ValueError("SEPOLIA_RPC_URL is missing from .env")

if not PRIVATE_KEY:
    raise ValueError("PRIVATE_KEY is missing from .env")


# Connect to Sepolia
w3 = Web3(Web3.HTTPProvider(RPC_URL))

print("\n================================")
print("TRACEFACE CONTRACT DEPLOYMENT")
print("================================")

print("Connected:", w3.is_connected())
print("Chain ID:", w3.eth.chain_id)


# Load wallet
account = w3.eth.account.from_key(PRIVATE_KEY)
wallet_address = account.address

print("Wallet:", wallet_address)


# Check balance
balance = w3.eth.get_balance(wallet_address)

print(
    "Balance:",
    w3.from_wei(balance, "ether"),
    "SepoliaETH"
)

if balance == 0:
    raise ValueError("Wallet has no SepoliaETH.")


# Read Solidity contract
with open("contracts/TraceFace.sol", "r") as file:
    contract_source = file.read()


# Compile
print("\nCompiling TraceFace.sol...")

install_solc("0.8.20")

compiled = compile_source(
    contract_source,
    solc_version="0.8.20"
)

contract_interface = compiled["<stdin>:TraceFace"]

bytecode = contract_interface["bin"]
abi = contract_interface["abi"]

print("Compilation successful.")


# Create contract object
TraceFace = w3.eth.contract(
    abi=abi,
    bytecode=bytecode
)


# Get nonce
nonce = w3.eth.get_transaction_count(wallet_address)

print("Nonce:", nonce)


# Get current gas price
gas_price = w3.eth.gas_price

print(
    "Gas price:",
    w3.from_wei(gas_price, "gwei"),
    "Gwei"
)


# Build deployment transaction
print("\nBuilding deployment transaction...")

transaction = TraceFace.constructor().build_transaction({
    "from": wallet_address,
    "nonce": nonce,
    "chainId": 11155111,
    "gas": 3000000,
    "gasPrice": gas_price,
    "value": 0
})


# Sign
print("Signing transaction...")

signed = w3.eth.account.sign_transaction(
    transaction,
    PRIVATE_KEY
)


# Send
print("Sending transaction...")

tx_hash = w3.eth.send_raw_transaction(
    signed.raw_transaction
)

print("\nTransaction hash:")
print(tx_hash.hex())


# Wait
print("\nWaiting for confirmation...")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash)


# Result
print("\n================================")
print("CONTRACT DEPLOYED")
print("================================")

print("Contract address:")
print(receipt.contractAddress)

print("\nTransaction hash:")
print(tx_hash.hex())

print("\nBlock number:")
print(receipt.blockNumber)

print("\nGas used:")
print(receipt.gasUsed)

print("\n================================")
print("DEPLOYMENT COMPLETE ✓")
print("================================")