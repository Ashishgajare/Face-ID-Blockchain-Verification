import os
import re
import serpapi

from dotenv import load_dotenv
from web3 import Web3

from search.candidate_matcher import (
    get_faces,
    find_best_face_match,
    download_image
)

from utils.hashing import calculate_record_hash


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
RPC_URL = os.getenv("SEPOLIA_RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

IMAGE_PATH = "test_images/person_compressed.jpg"

CONTRACT_ADDRESS = "0x99a70F91bfae2C9ad0ff808eb2465Eb85b8a0a55"

CHAIN_ID = 11155111

# Minimum face similarity required before accepting a match.
# This is a demo safeguard, NOT a universal identity threshold.
MIN_FACE_SIMILARITY = 0.50


# ============================================================
# SMART CONTRACT ABI
# ============================================================

CONTRACT_ABI = [
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


# ============================================================
# URL CLEANING FUNCTION
# ============================================================

def clean_url(url):
    """
    Clean URLs returned by search engines.
    Handles normal URLs, Markdown URLs,
    escaped URLs, and extra whitespace.
    """

    if not url:
        return ""

    url = str(url).strip()

    # Handle Markdown links:
    # [https://example.com](https://example.com)
    markdown_match = re.search(
        r"\]\((https?://[^)]+)\)",
        url
    )

    if markdown_match:
        url = markdown_match.group(1)

    # Extract the first normal URL if brackets/extra text exist
    bracket_match = re.search(
        r"(https?://[^\s\]]+)",
        url
    )

    if bracket_match:
        url = bracket_match.group(1)

    # Remove trailing Markdown/HTML characters
    url = url.rstrip(")]}>\"'")

    # Replace escaped characters
    url = url.replace("\\/", "/")

    return url

# ============================================================
# MAIN FUNCTION
# ============================================================

def main():

    print("=" * 70)
    print("TRACEFACE - FACE IDENTIFICATION & BLOCKCHAIN VERIFICATION")
    print("=" * 70)

    # ========================================================
    # PHASE 1 - INPUT IMAGE
    # ========================================================

    print("\n[1] Checking input image...")

    if not os.path.exists(IMAGE_PATH):

        print("ERROR: Input image not found:")
        print(IMAGE_PATH)

        return

    print(
        "Input image:",
        IMAGE_PATH
    )

    # ========================================================
    # PHASE 2 - FACE DETECTION
    # ========================================================

    print("\n[2] Detecting face...")

    input_faces = get_faces(
        IMAGE_PATH
    )

    if not input_faces:

        print(
            "ERROR: No face detected in input image."
        )

        return

    print(
        "Faces detected:",
        len(input_faces)
    )

    # Select largest detected face
    input_face = max(
        input_faces,
        key=lambda face: face.bbox[2] - face.bbox[0]
    )

    input_embedding = input_face.embedding

    print(
        "Input face embedding shape:",
        input_embedding.shape
    )

    # ========================================================
    # PHASE 3 - GOOGLE LENS SEARCH
    # ========================================================

    print(
        "\n[3] Searching the web using Google Lens..."
    )

    if not SERPAPI_API_KEY:

        print(
            "ERROR: SERPAPI_API_KEY is missing from .env"
        )

        return

    client = serpapi.Client(
        api_key=SERPAPI_API_KEY
    )

    try:

        upload_result = client.upload_image(
            IMAGE_PATH
        )

        image_id = upload_result["image_id"]

        results = client.search({
            "engine": "google_lens",
            "image_id": image_id,
            "type": "all",
            "hl": "en",
            "country": "in"
        })

    except Exception as e:

        print(
            "ERROR during Google Lens search:"
        )

        print(e)

        return

    visual_matches = results.get(
        "visual_matches",
        []
    )

    print(
        "Google Lens visual matches found:",
        len(visual_matches)
    )

    if not visual_matches:

        print(
            "ERROR: No visual matches found."
        )

        return

    # ========================================================
    # PHASE 4 - DOWNLOAD AND COMPARE CANDIDATES
    # ========================================================

    print(
        "\n[4] Comparing candidate images..."
    )

    candidate_folder = "search/candidates"

    os.makedirs(
        candidate_folder,
        exist_ok=True
    )

    match_results = []

    # Analyze first 10 Google Lens candidates
    candidates_to_check = visual_matches[:10]

    for rank, result in enumerate(
        candidates_to_check,
        start=1
    ):

        image_url = result.get(
            "image",
            ""
        )

        title = result.get(
            "title",
            "Unknown title"
        )

        source = result.get(
            "source",
            "Unknown source"
        )

        raw_post_url = result.get(
            "link",
            ""
        )

        # Clean URL
        post_url = clean_url(
            raw_post_url
        )

        print(
            f"\nCandidate {rank}: {title}"
        )

        # ----------------------------------------------------
        # CHECK IMAGE URL
        # ----------------------------------------------------

        if not image_url:

            print(
                f"Candidate {rank}: No image URL"
            )

            continue

        candidate_path = os.path.join(
            candidate_folder,
            f"candidate_{rank}.jpg"
        )

        # ----------------------------------------------------
        # DOWNLOAD IMAGE
        # ----------------------------------------------------

        success = download_image(
            image_url,
            candidate_path
        )

        if not success:

            print(
                f"Candidate {rank}: Download failed"
            )

            continue

        # ----------------------------------------------------
        # DETECT FACE
        # ----------------------------------------------------

        candidate_faces = get_faces(
            candidate_path
        )

        if not candidate_faces:

            print(
                f"Candidate {rank}: No face detected"
            )

            continue

        # ----------------------------------------------------
        # FACE SIMILARITY
        # ----------------------------------------------------

        similarity = find_best_face_match(
            input_embedding,
            candidate_faces
        )

        if similarity is None:

            print(
                f"Candidate {rank}: "
                "Could not calculate similarity"
            )

            continue

        print(
            f"Candidate {rank}: "
            f"Face similarity = {similarity:.4f}"
        )

        # ----------------------------------------------------
        # COMBINED SEARCH + FACE SCORE
        # ----------------------------------------------------

        search_score = 1 / rank

        combined_score = (
            0.70 * similarity
            + 0.30 * search_score
        )

        match_results.append({
            "rank": rank,
            "title": title,
            "source": source,
            "post_url": post_url,
            "image_url": image_url,
            "face_similarity": similarity,
            "combined_score": combined_score
        })

    # ========================================================
    # PHASE 5 - CHECK WHETHER ANY MATCH EXISTS
    # ========================================================

    print(
        "\n[5] Selecting best match..."
    )

    if not match_results:

        print(
            "ERROR: No usable candidate matches found."
        )

        return

    # Sort candidates by combined score
    match_results.sort(
        key=lambda x: x["combined_score"],
        reverse=True
    )

    best_match = match_results[0]

    # ========================================================
    # IMPORTANT: REJECT WEAK MATCHES
    # ========================================================

    if (
        best_match["face_similarity"]
        < MIN_FACE_SIMILARITY
    ):

        print("\n" + "=" * 70)
        print("NO RELIABLE FACE MATCH FOUND")
        print("=" * 70)

        print(
            "Best candidate:",
            best_match["title"]
        )

        print(
            "Face similarity:",
            f"{best_match['face_similarity']:.4f}"
        )

        print(
            "Required minimum:",
            f"{MIN_FACE_SIMILARITY:.2f}"
        )

        print(
            "\nBlockchain upload cancelled."
        )

        print(
            "This prevents weak/random search results "
            "from being recorded as verified matches."
        )

        return

    # ========================================================
    # PHASE 6 - DISPLAY BEST MATCH
    # ========================================================

    print("\n" + "=" * 70)
    print("BEST MATCH FOUND")
    print("=" * 70)

    print(
        "Title:",
        best_match["title"]
    )

    print(
        "Source:",
        best_match["source"]
    )

    print(
        "URL:",
        best_match["post_url"]
    )

    print(
        "Face similarity:",
        f"{best_match['face_similarity']:.4f}"
    )

    print(
        "Combined score:",
        f"{best_match['combined_score']:.4f}"
    )

    # ========================================================
    # PHASE 7 - CREATE POST RECORD
    # ========================================================

    print(
        "\n[6] Creating discovered post record..."
    )

    discovered_post = {
        "title": best_match["title"],
        "source": best_match["source"],
        "post_url": best_match["post_url"]
    }

    print(
        "\nDiscovered post:"
    )

    print(
        discovered_post
    )

    # ========================================================
    # PHASE 8 - SHA-256 HASH
    # ========================================================

    print(
        "\n[7] Calculating SHA-256 hash..."
    )

    post_hash = calculate_record_hash(
        discovered_post
    )

    print(
        "SHA-256:",
        post_hash
    )

    print(
        "Hash length:",
        len(post_hash)
    )

    # ========================================================
    # PHASE 9 - CONNECT TO SEPOLIA
    # ========================================================

    print(
        "\n[8] Connecting to Ethereum Sepolia..."
    )

    if not RPC_URL:

        print(
            "ERROR: SEPOLIA_RPC_URL is missing from .env"
        )

        return

    if not PRIVATE_KEY:

        print(
            "ERROR: PRIVATE_KEY is missing from .env"
        )

        return

    w3 = Web3(
        Web3.HTTPProvider(
            RPC_URL
        )
    )

    if not w3.is_connected():

        print(
            "ERROR: Could not connect to Sepolia."
        )

        return

    print(
        "Connected to Sepolia."
    )

    print(
        "Chain ID:",
        w3.eth.chain_id
    )

    # ========================================================
    # PHASE 10 - WALLET
    # ========================================================

    account = w3.eth.account.from_key(
        PRIVATE_KEY
    )

    print(
        "Wallet:",
        account.address
    )

    balance = w3.eth.get_balance(
        account.address
    )

    print(
        "Balance:",
        w3.from_wei(
            balance,
            "ether"
        ),
        "SepoliaETH"
    )

    # ========================================================
    # PHASE 11 - SMART CONTRACT
    # ========================================================

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(
            CONTRACT_ADDRESS
        ),
        abi=CONTRACT_ABI
    )

    print(
        "Contract:",
        CONTRACT_ADDRESS
    )

    # ========================================================
    # PHASE 12 - SUBMIT HASH
    # ========================================================

    print(
        "\n[9] Submitting hash to blockchain..."
    )

    # Get pending nonce
    nonce = w3.eth.get_transaction_count(
        account.address,
        "pending"
    )

    print(
        "Using nonce:",
        nonce
    )

    # Get latest block
    latest_block = w3.eth.get_block(
        "latest"
    )

    base_fee = latest_block.get(
        "baseFeePerGas",
        w3.eth.gas_price
    )

    # EIP-1559 gas settings
    max_priority_fee = w3.to_wei(
        1,
        "gwei"
    )

    max_fee = (
        base_fee * 2
        + max_priority_fee
    )

    print(
        "Base fee:",
        w3.from_wei(
            base_fee,
            "gwei"
        ),
        "Gwei"
    )

    print(
        "Max fee:",
        w3.from_wei(
            max_fee,
            "gwei"
        ),
        "Gwei"
    )

    # Convert SHA-256 hex string to bytes32
    hash_bytes = bytes.fromhex(
        post_hash
    )

    # Build blockchain transaction
    transaction = contract.functions.storeRecord(
        hash_bytes
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "chainId": CHAIN_ID,
        "gas": 100000,
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": max_priority_fee,
        "value": 0
    })

    # Sign transaction
    signed_tx = w3.eth.account.sign_transaction(
        transaction,
        private_key=PRIVATE_KEY
    )

    # Send transaction
    tx_hash = w3.eth.send_raw_transaction(
        signed_tx.raw_transaction
    )

    print(
        "\nTransaction submitted:"
    )

    print(
        tx_hash.hex()
    )

    # ========================================================
    # PHASE 13 - WAIT FOR CONFIRMATION
    # ========================================================

    print(
        "\nWaiting for blockchain confirmation..."
    )

    try:

        receipt = w3.eth.wait_for_transaction_receipt(
            tx_hash,
            timeout=300,
            poll_latency=5
        )

    except Exception as e:

        print(
            "\nWARNING: Transaction confirmation timed out."
        )

        print(
            "Transaction hash:",
            tx_hash.hex()
        )

        print(
            "Error:",
            e
        )

        return

    # ========================================================
    # PHASE 14 - CHECK TRANSACTION STATUS
    # ========================================================

    if receipt.status != 1:

        print(
            "\nERROR: Blockchain transaction failed."
        )

        print(
            "Transaction hash:",
            tx_hash.hex()
        )

        return

    print(
        "\nTransaction confirmed!"
    )

    print(
        "Block:",
        receipt.blockNumber
    )

    print(
        "Gas used:",
        receipt.gasUsed
    )

    # ========================================================
    # PHASE 15 - VERIFY HASH
    # ========================================================

    print(
        "\n[10] Verifying hash on blockchain..."
    )

    verification = contract.functions.verifyRecord(
        hash_bytes
    ).call()

    exists = verification[0]
    timestamp = verification[1]
    submitter = verification[2]

    print(
        "\nBlockchain verification:"
    )

    print(
        "Exists:",
        exists
    )

    print(
        "Timestamp:",
        timestamp
    )

    print(
        "Submitter:",
        submitter
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print("\n" + "=" * 70)
    print("TRACEFACE PIPELINE COMPLETE")
    print("=" * 70)

    if exists:

        print(
            "\nSUCCESS!"
        )

        print(
            "✓ Face detected"
        )

        print(
            "✓ Web search completed"
        )

        print(
            "✓ Matching content discovered"
        )

        print(
            "✓ Face similarity passed minimum threshold"
        )

        print(
            "✓ SHA-256 fingerprint generated"
        )

        print(
            "✓ Hash stored on Ethereum Sepolia"
        )

        print(
            "✓ Hash verified against blockchain record"
        )

        print(
            "\nTransaction hash:"
        )

        print(
            tx_hash.hex()
        )

    else:

        print(
            "\nBlockchain verification failed."
        )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
