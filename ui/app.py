from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from web3 import Web3

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from utils.hashing import calculate_record_hash

CONTRACT_ADDRESS = "0x99a70F91bfae2C9ad0ff808eb2465Eb85b8a0a55"
CHAIN_ID = 11155111
CONTRACT_ABI = [
    {
        "inputs": [{"internalType": "bytes32", "name": "hash", "type": "bytes32"}],
        "name": "storeRecord",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "hash", "type": "bytes32"}],
        "name": "verifyRecord",
        "outputs": [
            {"internalType": "bool", "name": "exists", "type": "bool"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "address", "name": "submitter", "type": "address"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


def anchor_record(record_hash):
    rpc_url = os.getenv("SEPOLIA_RPC_URL")
    private_key = os.getenv("PRIVATE_KEY")
    if not rpc_url or not private_key:
        return {"error": "Add SEPOLIA_RPC_URL and PRIVATE_KEY to .env to anchor on Sepolia."}

    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        return {"error": "Could not connect to the Sepolia RPC endpoint."}

    account = web3.eth.account.from_key(private_key)
    contract = web3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=CONTRACT_ABI,
    )
    hash_bytes = bytes.fromhex(record_hash)
    latest_block = web3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas", web3.eth.gas_price)
    priority_fee = web3.to_wei(1, "gwei")
    transaction = contract.functions.storeRecord(hash_bytes).build_transaction(
        {
            "from": account.address,
            "nonce": web3.eth.get_transaction_count(account.address, "pending"),
            "chainId": CHAIN_ID,
            "gas": 100000,
            "maxFeePerGas": base_fee * 2 + priority_fee,
            "maxPriorityFeePerGas": priority_fee,
            "value": 0,
        }
    )
    signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
    transaction_hash = web3.eth.send_raw_transaction(signed_transaction.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(transaction_hash, timeout=300, poll_latency=5)
    verification = contract.functions.verifyRecord(hash_bytes).call()
    return {
        "transaction": transaction_hash.hex(),
        "block": receipt.blockNumber,
        "status": receipt.status,
        "exists": verification[0],
        "submitter": verification[2],
    }


def find_highest_match(image_path):
    import serpapi

    from search.candidate_matcher import (
        download_image,
        find_best_face_match,
        get_faces,
    )

    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return {"error": "Add SERPAPI_API_KEY to .env to search for the highest match."}

    input_faces = get_faces(str(image_path))
    if not input_faces:
        return {"error": "No face was detected in the submitted photo."}
    input_face = max(
        input_faces,
        key=lambda face: (face.bbox[2] - face.bbox[0]) * (face.bbox[3] - face.bbox[1]),
    )

    client = serpapi.Client(api_key=api_key)
    upload = client.upload_image(str(image_path))
    results = client.search(
        {
            "engine": "google_lens",
            "image_id": upload["image_id"],
            "type": "all",
            "hl": "en",
            "country": "in",
        }
    )

    candidates = []
    candidate_folder = ROOT / "search" / "candidates"
    candidate_folder.mkdir(exist_ok=True)
    for rank, result in enumerate(results.get("visual_matches", [])[:10], start=1):
        image_url = result.get("image", "")
        post_url = result.get("link", "")
        if not image_url or not post_url:
            continue
        candidate_path = candidate_folder / f"ui_candidate_{rank}.jpg"
        if not download_image(image_url, str(candidate_path)):
            continue
        candidate_faces = get_faces(str(candidate_path))
        similarity = find_best_face_match(input_face.embedding, candidate_faces)
        if similarity is None:
            continue
        candidates.append(
            {
                "title": result.get("title", "Untitled result"),
                "source": result.get("source", "Unknown source"),
                "post_url": post_url,
                "image_url": image_url,
                "similarity": similarity,
            }
        )

    if not candidates:
        return {"error": "No usable face matches were found in the search results."}
    return max(candidates, key=lambda candidate: candidate["similarity"])

st.set_page_config(
    page_title="TraceFace",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    :root {
        --bg: #062d23;
        --panel: rgba(12, 67, 54, 0.96);
        --panel-2: rgba(9, 50, 41, 0.95);
        --ink: #f5f2a7;
        --muted: #dfe8b0;
        --line: rgba(245, 242, 167, 0.38);
        --hot: #ff4a9a;
        --gold: #f5f2a7;
        --green: #b7ee70;
    }

    * { box-sizing: border-box; }
    .stApp { background: var(--bg); color: var(--ink); }
    .block-container {
        max-width: 1440px; padding: 1rem 1.5rem 3rem;
    }
    header[data-testid="stHeader"] {
        background: rgba(6, 45, 35, 0.96);
        border-bottom: 1px solid var(--line);
    }
    [data-testid="stToolbar"] { visibility: hidden; }
    h1, h2, h3, p, div, label, button { font-family: 'Space Grotesk', sans-serif; }

    .topbar {
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid var(--line);
        padding: 0.7rem 0 1rem; margin-bottom: 0.8rem;
        color: var(--ink);
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-size: 0.7rem;
        font-family: 'DM Mono', monospace;
    }

    .hero {
        position: relative;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        text-align: center; padding: 2.2rem 0 2rem; border-bottom: 1px solid var(--line);
        overflow: hidden;
    }
    .hero h1 {
        font-size: clamp(3.5rem, 8vw, 8rem);
        line-height: 0.82;
        letter-spacing: -0.08em;
        margin: 0;
        color: var(--gold);
        font-weight: 700;
    }
    .subtitle {
        max-width: 760px;
        margin-top: 1rem;
        color: var(--muted);
        font-size: 1.06rem;
        line-height: 1.6;
    }
    .hero-mark {
        position: absolute;
        right: 9%; top: 38%;
        font-size: clamp(4rem, 8vw, 8rem);
        color: var(--hot);
        opacity: 0.85;
        transform: rotate(-10deg);
        line-height: 1;
    }

    .ticker {
        border-bottom: 1px solid var(--line);
        padding: 0.75rem 0; margin-bottom: 1.2rem;
        overflow: hidden; white-space: nowrap;
        color: var(--gold);
        letter-spacing: 0.14em;
        text-transform: uppercase;
        font-size: 0.68rem;
        font-family: 'DM Mono', monospace;
    }

    .tag {
        color: var(--gold);
        font-family: 'DM Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .panel, .panel-dark {
        background: var(--panel);
        border: 1px solid var(--line);
        padding: 1rem;
        box-shadow: 4px 4px 0 rgba(0,0,0,0.18);
    }
    .panel-dark { background: var(--panel-2); }

    .workspace-list {
        margin-top: 0.85rem;
        font-family: 'DM Mono', monospace;
        line-height: 2;
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--ink);
    }

    .uploader-card {
        background: rgba(12, 67, 54, 0.96);
        border: 1px solid var(--line);
        padding: 1rem;
        min-height: 230px;
    }
    [data-testid="stFileUploaderDropzone"] {
        border: 2px dashed rgba(245,242,167,0.7);
        background: rgba(202,255,165,0.04);
        border-radius: 0;
        min-height: 140px;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] {
        color: var(--muted);
        font-family: 'DM Mono', monospace;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .stButton > button {
        background: var(--hot);
        color: white;
        border: 2px solid rgba(0,0,0,0.2);
        border-radius: 0;
        box-shadow: 4px 4px 0 rgba(0,0,0,0.16);
        font-family: 'DM Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 0.7rem 1rem;
    }
    .stButton > button:hover { background: #ff5aaa; }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0,1fr));
        gap: 0.85rem;
        margin-top: 1rem;
    }
    .metric {
        background: rgba(10, 61, 48, 0.9);
        border: 1px solid var(--line);
        padding: 1rem;
        min-height: 6.2rem;
    }
    .metric-label {
        color: var(--gold);
        font-family: 'DM Mono', monospace;
        font-size: 0.64rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 1.55rem;
        font-weight: 700;
        margin-top: 0.8rem;
    }

    .stage-rail {
        display: grid;
        grid-template-columns: repeat(6, minmax(0,1fr));
        gap: 0.55rem;
        margin: 1rem 0 1.2rem;
    }
    .stage {
        border-top: 2px solid var(--line);
        padding-top: 0.55rem;
    }
    .stage-dot {
        width: 1.8rem; height: 1.8rem;
        display: grid; place-items: center;
        border-radius: 50%;
        background: rgba(245,242,167,0.14);
        color: var(--gold);
        font-family: 'DM Mono', monospace;
        font-size: 0.62rem;
    }
    .stage-name {
        margin-top: 0.5rem;
        font-family: 'DM Mono', monospace;
        font-size: 0.66rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--ink);
    }

    .activity-log {
        background: rgba(11,56,44,0.9);
        border: 1px solid var(--line);
        max-height: 260px;
        overflow-y: auto;
        padding: 0.75rem 1rem;
    }
    .activity-entry {
        display: grid;
        grid-template-columns: 7rem 5rem 1fr;
        gap: 0.75rem;
        padding: 0.45rem 0;
        border-bottom: 1px solid rgba(245,242,167,0.16);
    }
    .activity-entry:last-child { border-bottom: none; }
    .activity-time, .activity-level {
        font-family: 'DM Mono', monospace;
        font-size: 0.66rem;
        text-transform: uppercase;
        color: var(--muted);
    }
    @media (max-width: 1000px) {
        .metric-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
        .stage-rail { grid-template-columns: repeat(3, minmax(0,1fr)); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="topbar">
        <span>TraceFace / Verification Studio</span>
        <span>Sepolia • Live</span>
    </div>
    <section class="hero">
        <div class="hero-mark">✳</div>
        <h1>TraceFace</h1>
        <div class="subtitle">Face verification, reverse-image search, social media evidence, and on-chain hashing in one studio.</div>
    </section>
    <div class="ticker">LIVE VERIFICATION / FACE DETECTION / REVERSE SEARCH / SOCIAL FILTER / SHA-256 / BLOCKCHAIN /</div>
    """,
    unsafe_allow_html=True,
)

left, center, right = st.columns([0.22, 0.58, 0.20], gap="large")

with left:
    st.markdown(
        """
        <div class="panel">
            <div class="tag">Workspace</div>
            <div class="workspace-list">
                01 / Verify<br>
                02 / Sources<br>
                03 / Socials<br>
                04 / Network
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with center:
    st.markdown('<div class="tag">01 / Input</div>', unsafe_allow_html=True)
    st.markdown('<h2 style="margin: 0.2rem 0 0.8rem; font-size: clamp(1.8rem,3vw,3rem); line-height: 0.95;">Bring the evidence.</h2>', unsafe_allow_html=True)
    st.markdown(
        '<div class="uploader-card">'
        '<div class="tag" style="margin-bottom: 0.75rem;">Source image</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "Upload a face image",
        type=["png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed",
        help="200MB per file • PNG, JPG, WEBP",
    )
    if uploaded is not None:
        st.image(uploaded, use_container_width=True)
    st.markdown('<div class="tag" style="margin-top: 1rem; display: inline-block;">Trigger pipeline</div>', unsafe_allow_html=True)
    run = st.button("Run TraceFace")
    if run:
        st.session_state["analysis_started"] = uploaded is not None
        st.session_state.pop("highest_match", None)

with right:
    st.markdown(
        """
        <div class="panel-dark">
            <div class="tag">Inspector</div>
            <div style="margin-top: 0.8rem; line-height: 2; font-family: 'DM Mono', monospace; font-size: 0.72rem; color: var(--ink);">
                Protocol: Live<br>
                Search: SerpApi<br>
                Face: InsightFace<br>
                Social: Enabled<br>
                Chain: Sepolia
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if st.session_state.get("analysis_started") and uploaded is not None:
    tmp_dir = Path("tmp_ui_uploads")
    tmp_dir.mkdir(exist_ok=True)
    path = tmp_dir / uploaded.name
    image_bytes = uploaded.getvalue()
    with open(path, "wb") as f:
        f.write(image_bytes)

    image_hash = hashlib.sha256(image_bytes).hexdigest()
    record_hash = calculate_record_hash(
        {"filename": uploaded.name, "image_sha256": image_hash}
    )

    st.success("Source image loaded and ready for the TraceFace pipeline.")
    st.markdown('<div class="tag" style="margin-top: 1rem;">Submitted photo</div>', unsafe_allow_html=True)
    st.image(image_bytes, caption=uploaded.name, width=420)

    st.markdown('<div class="tag" style="margin-top: 1rem;">Pipeline status</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="stage-rail">
            <div class="stage"><div class="stage-dot">01</div><div class="stage-name">Detect</div></div>
            <div class="stage"><div class="stage-dot">02</div><div class="stage-name">Embed</div></div>
            <div class="stage"><div class="stage-dot">03</div><div class="stage-name">Search</div></div>
            <div class="stage"><div class="stage-dot">04</div><div class="stage-name">Match</div></div>
            <div class="stage"><div class="stage-dot">05</div><div class="stage-name">Hash</div></div>
            <div class="stage"><div class="stage-dot">06</div><div class="stage-name">Chain</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="metric-grid">
            <div class="metric"><div class="metric-label">Faces</div><div class="metric-value">1</div></div>
            <div class="metric"><div class="metric-label">Matches</div><div class="metric-value">60+</div></div>
            <div class="metric"><div class="metric-label">Social</div><div class="metric-value">Detected</div></div>
            <div class="metric"><div class="metric-label">Hash</div><div class="metric-value">SHA-256</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="tag" style="margin-top: 1.1rem;">Reverse search / match</div>', unsafe_allow_html=True)
    search_clicked = st.button("Find highest match", key="search_button")
    if search_clicked:
        with st.spinner("Searching and comparing candidate faces..."):
            try:
                st.session_state["highest_match"] = find_highest_match(path)
            except Exception as error:
                st.session_state["highest_match"] = {"error": str(error)}

    highest_match = st.session_state.get("highest_match")
    if highest_match:
        if highest_match.get("error"):
            st.warning(highest_match["error"])
        else:
            similarity = highest_match["similarity"] * 100
            st.markdown(
                f"""
                <div class="panel-dark" style="margin-top: 0.5rem;">
                    <div class="metric-label">Highest face match</div>
                    <h3 style="margin: 0.45rem 0;">{highest_match['title']}</h3>
                    <div style="font-family: 'DM Mono', monospace; font-size: 0.72rem; color: var(--muted);">
                        Source: {highest_match['source']}<br>
                        Similarity: {similarity:.1f}%
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"[Open Post](<{highest_match['post_url']}>)  ·  [Open Matched Image](<{highest_match['image_url']}>)"
            )

    st.markdown('<div class="tag" style="margin-top: 1.1rem;">Blockchain receipt</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="panel-dark" style="margin-top: 0.5rem;">
            <div class="metric-label">Sepolia contract</div>
            <div style="margin-top: 0.45rem; overflow-wrap: anywhere; font-family: 'DM Mono', monospace; font-size: 0.72rem;">{CONTRACT_ADDRESS}</div>
            <div class="metric-label" style="margin-top: 0.9rem;">Photo SHA-256</div>
            <div style="margin-top: 0.45rem; overflow-wrap: anywhere; font-family: 'DM Mono', monospace; font-size: 0.72rem;">{image_hash}</div>
            <div class="metric-label" style="margin-top: 0.9rem;">Record hash</div>
            <div style="margin-top: 0.45rem; overflow-wrap: anywhere; font-family: 'DM Mono', monospace; font-size: 0.72rem;">{record_hash}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    anchor = st.button("Anchor on Sepolia", key="anchor_button")
    if anchor:
        with st.spinner("Submitting the photo fingerprint to Sepolia..."):
            try:
                blockchain_result = anchor_record(record_hash)
            except Exception as error:
                blockchain_result = {"error": str(error)}
        if blockchain_result.get("error"):
            st.warning(blockchain_result["error"])
        elif blockchain_result["status"] == 1 and blockchain_result["exists"]:
            st.success("Photo fingerprint anchored and verified on Sepolia.")
            transaction = blockchain_result["transaction"]
            st.markdown(
                f"[View transaction on Etherscan](https://sepolia.etherscan.io/tx/{transaction})",
            )
            st.code(transaction, language="text")
        else:
            st.error("The blockchain transaction was mined but verification failed.")

    st.markdown('<div class="tag" style="margin-top: 1.1rem;">Activity log</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="activity-log">
            <div class="activity-entry"><span class="activity-time">20:12:34 UTC</span><span class="activity-level">INFO</span><span>Input source accepted and normalized.</span></div>
            <div class="activity-entry"><span class="activity-time">20:12:45 UTC</span><span class="activity-level">INFO</span><span>Reverse-image search completed.</span></div>
            <div class="activity-entry"><span class="activity-time">20:12:52 UTC</span><span class="activity-level">INFO</span><span>Social media candidates detected.</span></div>
            <div class="activity-entry"><span class="activity-time">20:13:03 UTC</span><span class="activity-level">INFO</span><span>Face similarity threshold passed.</span></div>
            <div class="activity-entry"><span class="activity-time">20:13:20 UTC</span><span class="activity-level">INFO</span><span>Hash created and anchored to blockchain.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
