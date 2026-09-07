import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("SEPOLIA_RPC_URL")

if not RPC_URL:
    raise ValueError("SEPOLIA_RPC_URL is missing from .env")

w3 = Web3(Web3.HTTPProvider(RPC_URL))

print("\n================================")
print("TRACEFACE BLOCKCHAIN CONNECTION")
print("================================")

print("Connected:", w3.is_connected())

if w3.is_connected():
    print("Network Chain ID:", w3.eth.chain_id)
    print("Latest Block:", w3.eth.block_number)

print("\n================================")