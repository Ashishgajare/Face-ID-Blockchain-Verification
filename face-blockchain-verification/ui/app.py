from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import cv2
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import CONTRACT_ADDRESS, FACE_SIMILARITY_THRESHOLD, USE_GPU  # noqa: E402
from verification.pipeline import run_pipeline  # noqa: E402


st.set_page_config(
    page_title="Face ID + Blockchain Verification",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    :root { --ink:#121212; --paper:#f2eee4; --orange:#ff5b24; --acid:#d8ff4f; --muted:#aaa69e; --line:rgba(242,238,228,.18); }
    .stApp { background:var(--ink); color:var(--paper); }
    .block-container { max-width:1440px; padding:1.8rem 4vw 4rem; }
    header[data-testid="stHeader"] { background:transparent; }
    [data-testid="stToolbar"] { visibility:hidden; }
    h1,h2,h3,p,label,button,div { font-family:'Space Grotesk',sans-serif; }
    h1,h2,h3,p { color:var(--paper); }
    h1 { font-size:clamp(3.8rem,9vw,9rem); line-height:.86; letter-spacing:-.06em; font-weight:700; margin:0; }
    h2 { font-size:clamp(2rem,5vw,4.8rem); line-height:.9; letter-spacing:-.05em; margin:0; }
    h3 { letter-spacing:-.03em; }
    .mono { font-family:'DM Mono',monospace; text-transform:uppercase; letter-spacing:.08em; font-size:.72rem; }
    .topline { display:flex; justify-content:space-between; border-bottom:1px solid var(--line); padding-bottom:1rem; margin-bottom:4rem; color:var(--muted); }
    .hero { min-height:55vh; display:grid; grid-template-columns:1.2fr .8fr; gap:2rem; align-items:end; padding-bottom:3rem; border-bottom:1px solid var(--line); }
    .hero-kicker,.section-tag { color:var(--orange); }
    .hero-copy { color:var(--muted); max-width:31rem; font-size:1.05rem; line-height:1.4; }
    .hero-mark { color:var(--orange); font-size:clamp(8rem,21vw,22rem); line-height:.55; text-align:right; letter-spacing:-.14em; }
    .ticker { overflow:hidden; white-space:nowrap; border-bottom:1px solid var(--line); color:var(--acid); padding:.85rem 0; margin-bottom:4rem; font-family:'DM Mono',monospace; font-size:.78rem; }
    .section-head { display:flex; justify-content:space-between; align-items:end; gap:1rem; margin:5rem 0 1.5rem; }
    .panel { background:var(--paper); color:var(--ink); padding:1.3rem; min-height:100%; }
    .panel * { color:var(--ink) !important; }
    .panel-dark { border:1px solid var(--line); padding:1.3rem; min-height:100%; }
    .panel-label { font-family:'DM Mono',monospace; font-size:.7rem; text-transform:uppercase; color:var(--orange) !important; letter-spacing:.1em; }
    .panel-value { font-size:3rem; font-weight:700; line-height:.9; margin:1.5rem 0 .6rem; }
    [data-testid="stFileUploaderDropzone"] { background:transparent; border:1px dashed rgba(18,18,18,.35); padding:1.3rem; }
    [data-testid="stFileUploaderDropzoneInstructions"] { color:var(--ink); }
    .stButton > button { background:var(--orange); border:0; border-radius:0; color:var(--ink); font-family:'DM Mono',monospace; text-transform:uppercase; letter-spacing:.08em; font-weight:500; padding:.8rem 1.2rem; }
    .stButton > button:hover { background:var(--acid); color:var(--ink); }
    .metric-row { display:grid; grid-template-columns:repeat(4,1fr); gap:1px; background:var(--line); margin-top:1.5rem; }
    .metric { background:var(--ink); padding:1.1rem; min-height:8rem; }
    .metric .value { font-size:2rem; font-weight:600; margin-top:1rem; }
    .status { border-left:5px solid var(--orange); padding:1rem 1.2rem; background:#211b18; margin-top:1.2rem; }
    .status.good { border-color:var(--acid); }
    .status p { margin:.25rem 0; }
    .timeline { display:grid; grid-template-columns:repeat(6,1fr); margin:2rem 0 4rem; border-top:1px solid var(--line); }
    .step { padding:1rem .7rem 0 0; border-right:1px solid var(--line); min-height:8rem; }
    .step:last-child { border-right:0; }
    .step-no { color:var(--orange); font-family:'DM Mono',monospace; }
    .step-name { margin-top:1.5rem; font-weight:600; }
    .footer { border-top:1px solid var(--line); margin-top:5rem; padding-top:1rem; color:var(--muted); display:flex; justify-content:space-between; }
    @media (max-width:800px) { .hero{grid-template-columns:1fr;min-height:46vh}.hero-mark{text-align:left;font-size:9rem}.metric-row{grid-template-columns:repeat(2,1fr)}.timeline{grid-template-columns:repeat(2,1fr)}.step:nth-child(2n){border-right:0} }
    </style>
    """,
    unsafe_allow_html=True,
)


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as image_file:
        for chunk in iter(lambda: image_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _friendly_error(error: Exception) -> tuple[str, str]:
    message = str(error)
    lowered = message.lower()
    if "exactly one face" in lowered:
        if "found: 0" in lowered:
            return "Face detection", "No face was detected. Upload a clear image containing one face."
        return "Face detection", "Multiple faces were detected. Upload an image containing exactly one face."
    if "unable to read" in lowered or "unsupported or corrupt" in lowered:
        return "Input image", "The image is invalid, unsupported, or corrupt."
    if "serpapi_key" in lowered:
        return "Reverse-image search", "SERPAPI_KEY is missing from the local environment."
    if "serpapi" in lowered or "reverse" in lowered:
        return "Reverse-image search", "The reverse-image search request failed."
    if "rpc" in lowered or "blockchain" in lowered or "gas" in lowered:
        return "Blockchain", "Polygon could not confirm the verification transaction."
    return "Verification", "The pipeline could not complete this verification."


def _safe_report(result: dict, source_path: str) -> dict:
    best = result.get("best_candidate") or {}
    blockchain = result.get("blockchain") or {}
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": best.get("platform"),
        "post_url": best.get("url"),
        "similarity": best.get("similarity"),
        "threshold": FACE_SIMILARITY_THRESHOLD,
        "search_provider": "Google Lens via SerpApi",
        "status": "VERIFIED_MATCH" if best.get("matched") else "NO_MATCH",
        "record_hash": blockchain.get("record_hash"),
        "blockchain_network": "Polygon Amoy",
        "transaction_hash": blockchain.get("transaction_hash"),
        "block_number": blockchain.get("block_number"),
        "gas_used": blockchain.get("gas_used"),
        "source_image_sha256": _sha256(source_path),
    }


st.markdown(
    """
    <div class="topline"><span class="mono">Face ID + Blockchain Verification</span><span class="mono">Studio 03 / Polygon Amoy</span></div>
    <section class="hero"><div><div class="mono hero-kicker">Identity, with receipts.</div><h1>READ<br>THE<br>SIGNAL.</h1><p class="hero-copy">A visual verification studio for finding, comparing, and sealing evidence records on-chain. Similarity is evidence, not identity proof.</p></div><div class="hero-mark">◈</div></section>
    <div class="ticker">LIVE VERIFICATION / FACE DETECTION / REVERSE SEARCH / ARCFACE / SHA-256 / POLYGON AMOY / LIVE VERIFICATION /</div>
    <div class="section-head"><div><div class="mono section-tag">01 / Input</div><h2>Bring the<br>evidence.</h2></div><div class="mono">One face. One source image.</div></div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1.15, .85], gap="large")
with left:
    st.markdown('<div class="panel"><div class="panel-label">Drop zone / source image</div>', unsafe_allow_html=True)
    upload = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)
    if upload:
        st.image(upload, caption=f"SOURCE / {upload.name}", use_container_width=True)
with right:
    st.markdown(f'<div class="panel-dark"><div class="panel-label">Production protocol</div><div class="panel-value">{FACE_SIMILARITY_THRESHOLD:.2f}</div><p>Similarity threshold. Production mode only.</p><div class="mono" style="margin-top:2rem;color:#aaa69e">No match. No hash. No transaction.</div></div>', unsafe_allow_html=True)
    run = st.button("Run Verification", type="primary", use_container_width=True, disabled=upload is None)

st.markdown(
    """
    <div class="section-head"><div><div class="mono section-tag">02 / Sequence</div><h2>The route<br>to proof.</h2></div></div>
    <div class="timeline"><div class="step"><div class="step-no">01</div><div class="step-name">Detect</div><div class="mono">Face signal</div></div><div class="step"><div class="step-no">02</div><div class="step-name">Embed</div><div class="mono">ArcFace vector</div></div><div class="step"><div class="step-no">03</div><div class="step-name">Search</div><div class="mono">Google Lens via SerpApi</div></div><div class="step"><div class="step-no">04</div><div class="step-name">Compare</div><div class="mono">Similarity gate</div></div><div class="step"><div class="step-no">05</div><div class="step-name">Hash</div><div class="mono">Canonical JSON</div></div><div class="step"><div class="step-no">06</div><div class="step-name">Anchor</div><div class="mono">Polygon Amoy</div></div></div>
    """,
    unsafe_allow_html=True,
)

if run and upload:
    suffix = Path(upload.name).suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(upload.getbuffer())
        temp_path = temp_file.name
    try:
        with st.status("Running production verification...", expanded=True) as progress:
            progress.write("Loading image and detecting exactly one face")
            progress.write("Generating embedding and searching reverse image sources")
            progress.write("Comparing real candidate faces against the 0.65 gate")
            result = run_pipeline(temp_path, threshold=FACE_SIMILARITY_THRESHOLD, use_gpu=USE_GPU)
            progress.update(label="Verification complete", state="complete", expanded=False)
    except Exception as exc:
        heading, message = _friendly_error(exc)
        st.error(f"{heading}: {message}")
    else:
        best = result.get("best_candidate") or {}
        blockchain = result.get("blockchain") or {}
        similarity = best.get("similarity")
        bbox = result.get("input_face_bbox")
        image = cv2.imread(temp_path)
        st.markdown('<div class="section-head"><div><div class="mono section-tag">03 / Face detection</div><h2>Find the<br>signal.</h2></div></div>', unsafe_allow_html=True)
        face_col, facts_col = st.columns([.7, 1.3], gap="large")
        with face_col:
            if bbox and image is not None:
                x1, y1, x2, y2 = bbox
                height, width = image.shape[:2]
                crop = image[max(0, y1):min(height, y2), max(0, x1):min(width, x2)]
                if crop.size:
                    st.image(crop, channels="BGR", caption="DETECTED FACE / CROP", use_container_width=True)
        with facts_col:
            st.markdown(f'<div class="metric-row"><div class="metric"><div class="mono">Faces detected</div><div class="value">{result.get("input_faces", 0)}</div></div><div class="metric"><div class="mono">Search results</div><div class="value">{result.get("reverse_results_count", 0)}</div></div><div class="metric"><div class="mono">Social candidates</div><div class="value">{result.get("social_candidates_count", 0)}</div></div><div class="metric"><div class="mono">Similarity</div><div class="value">{f"{similarity:.0%}" if similarity is not None else "--"}</div></div></div>', unsafe_allow_html=True)
            st.markdown('<div class="status good"><div class="mono">Face detected ✓</div><p>Exactly one face is present in the submitted image.</p></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-head"><div><div class="mono section-tag">04 / Reverse search + match</div><h2>Search the<br>trail.</h2></div></div>', unsafe_allow_html=True)
        search_col, match_col = st.columns(2, gap="large")
        with search_col:
            st.markdown(f'<div class="panel-dark"><div class="panel-label">Search provider</div><h3>Google Lens via SerpApi</h3><p>Search status: Completed ✓</p><p>Number of results: <strong>{result.get("reverse_results_count", 0)}</strong></p><p>Social candidates: <strong>{result.get("social_candidates_count", 0)}</strong></p></div>', unsafe_allow_html=True)
        with match_col:
            if best:
                match_status = "VERIFIED VISUAL MATCH ✓" if best.get("matched") else "NO MATCH"
                match_class = "good" if best.get("matched") else ""
                st.markdown(f'<div class="panel-dark"><div class="panel-label">Strongest candidate</div><h3>{best.get("platform", "Unknown")}</h3><p>Similarity: <strong>{best.get("similarity", 0):.0%}</strong></p><p>Threshold: <strong>{FACE_SIMILARITY_THRESHOLD:.0%}</strong></p><div class="status {match_class}"><div class="mono">{match_status}</div><p>Visual similarity is evidence, not identity proof.</p></div></div>', unsafe_allow_html=True)
                if best.get("url"):
                    st.link_button("Open Post", best["url"])
            else:
                st.markdown('<div class="panel-dark"><div class="panel-label">Strongest candidate</div><h3>No social candidate</h3><p>No supported social-media result was returned for this image.</p><div class="status"><div class="mono">NO MATCH</div><p>No face comparison was available.</p></div></div>', unsafe_allow_html=True)
                inaccessible = [item for item in result.get("candidate_details", []) if item.get("error")]
                if inaccessible:
                    st.warning("A returned candidate could not be accessed or compared. No match was claimed.")

        st.markdown('<div class="section-head"><div><div class="mono section-tag">05 / Blockchain</div><h2>Leave a<br>receipt.</h2></div></div>', unsafe_allow_html=True)
        if blockchain.get("transaction_hash"):
            explorer = blockchain.get("explorer_url")
            st.success("Polygon Amoy transaction confirmed.")
            st.write({"network": "Polygon Amoy", "contract": CONTRACT_ADDRESS, "block": blockchain.get("block_number"), "gas_used": blockchain.get("gas_used"), "getVerification": "PASS" if blockchain.get("record_verified") else "FAIL"})
            st.code(blockchain.get("record_hash", ""), language="text")
            if explorer:
                st.link_button("Open transaction in Polygonscan", explorer)
        elif blockchain.get("status") == "FAILED":
            st.error("Blockchain transaction failed. No confirmed record exists.")
            st.caption("The failure was returned by the configured Polygon Amoy client; no confirmation is claimed.")
        elif blockchain.get("status") == "NOT_CONFIGURED":
            st.warning("Blockchain is not configured for this verified result. No transaction was sent.")
        else:
            st.info("Blockchain Status: NOT_ATTEMPTED. No verified match means no hash and no transaction.")

        report = _safe_report(result, temp_path)
        report_dir = PROJECT_ROOT / "output"
        report_dir.mkdir(exist_ok=True)
        report_path = report_dir / "verification_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        st.download_button("Export local JSON report", data=json.dumps(report, indent=2), file_name="verification_report.json", mime="application/json")
        with st.expander("Safe report fields"):
            st.json(report)
    finally:
        Path(temp_path).unlink(missing_ok=True)

st.markdown('<div class="footer"><span class="mono">LESS NOISE. MORE SIGNAL.</span><span class="mono">Milestone 3 / Final Verification Studio</span></div>', unsafe_allow_html=True)
