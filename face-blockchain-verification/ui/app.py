from __future__ import annotations

import hashlib
import json
import re
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
    page_title="TraceFace",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "activity_log" not in st.session_state:
    st.session_state.activity_log = []
if "stage_index" not in st.session_state:
    st.session_state.stage_index = 0
if "stage_failed" not in st.session_state:
    st.session_state.stage_failed = False


def log_activity(message: str, level: str = "INFO") -> None:
    st.session_state.activity_log.append(
        {
            "time": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
            "level": level,
            "message": message,
        }
    )
    st.session_state.activity_log = st.session_state.activity_log[-20:]


def render_activity(target) -> None:
    if st.session_state.activity_log:
        entries = "".join(
            f'<div class="activity-entry"><span class="activity-time">{item["time"]}</span><span class="activity-level">{item["level"]}</span><span>{item["message"]}</span></div>'
            for item in reversed(st.session_state.activity_log)
        )
    else:
        entries = '<div class="activity-entry"><span class="activity-time">--:--:--</span><span class="activity-level">IDLE</span><span>Ready for a source image.</span></div>'
    target.markdown(f'<div class="activity-log">{entries}</div>', unsafe_allow_html=True)


def update_stage(message: str) -> None:
    text = message.lower()
    if "detect" in text:
        st.session_state.stage_index = max(st.session_state.stage_index, 1)
    if "embedding" in text:
        st.session_state.stage_index = max(st.session_state.stage_index, 2)
    if "search" in text or "result(s)" in text or "candidate(s)" in text:
        st.session_state.stage_index = max(st.session_state.stage_index, 3)
    if "compar" in text or "similarity" in text or "match" in text:
        st.session_state.stage_index = max(st.session_state.stage_index, 4)
    if "hash" in text or "record" in text:
        st.session_state.stage_index = max(st.session_state.stage_index, 5)
    if "polygon" in text or "blockchain" in text:
        st.session_state.stage_index = max(st.session_state.stage_index, 6)


def render_stages(target) -> None:
    stages = ["Detect", "Embed", "Search", "Compare", "Hash", "Polygon"]
    cells = []
    for index, name in enumerate(stages, start=1):
        state = "done" if index < st.session_state.stage_index else "active" if index == st.session_state.stage_index else "pending"
        if st.session_state.stage_failed and index == st.session_state.stage_index:
            state = "failed"
        glyph = "✓" if state == "done" else str(index).zfill(2)
        cells.append(f'<div class="stage {state}"><div class="stage-dot">{glyph}</div><div class="stage-name">{name}</div></div>')
    target.markdown(f'<div class="stage-rail">{"".join(cells)}</div>', unsafe_allow_html=True)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    :root { --ink:#fff15a; --paper:#075c36; --canvas:#075c36; --green:#fff15a; --green-soft:#064a2c; --muted:#d8df91; --line:rgba(255,241,90,.55); --orange:#ff2f92; --hot:#ff2f92; }
    .stApp { background:var(--canvas); color:var(--ink); }
    .block-container { max-width:1440px; padding:1rem 2rem 3rem; }
    header[data-testid="stHeader"] { background:rgba(7,92,54,.96); border-bottom:1px solid var(--line); }
    [data-testid="stToolbar"] { visibility:hidden; }
    h1,h2,h3,p,label,button,div { font-family:'Space Grotesk',sans-serif; }
    h1,h2,h3,p { color:var(--ink); }
    h1 { font-family:Georgia,'Times New Roman',serif; font-size:clamp(4rem,10vw,8rem); line-height:.86; letter-spacing:-.06em; font-weight:700; margin:0; text-align:center; text-transform:none; }
    h2 { font-family:Georgia,'Times New Roman',serif; font-size:clamp(1.8rem,4vw,3.2rem); line-height:.95; letter-spacing:-.04em; margin:0; }
    h3 { letter-spacing:-.02em; }
    .mono { font-family:'DM Mono',monospace; text-transform:uppercase; letter-spacing:.06em; font-size:.78rem; }
    .topline { display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--line); padding:.8rem 0; margin-bottom:1.3rem; color:var(--ink); }
    .hero { display:flex; flex-direction:column; align-items:center; gap:1.2rem; padding:3rem 0 3.8rem; border-bottom:1px solid var(--line); position:relative; }
    .hero-kicker,.section-tag { color:var(--green); }
    .hero-copy { color:#f4f6bf; max-width:42rem; font-size:1.05rem; line-height:1.55; margin:.8rem 0 0; text-align:center; }
    .hero-mark { color:var(--hot); font-size:clamp(5rem,10vw,9rem); line-height:.55; text-align:center; letter-spacing:-.14em; position:absolute; top:42%; right:12%; transform:rotate(-8deg); }
    .ticker { overflow:hidden; white-space:nowrap; border-bottom:1px solid var(--line); color:var(--ink); padding:.55rem 0; margin-bottom:1.5rem; font-family:'DM Mono',monospace; font-size:.68rem; }
    .section-head { display:flex; justify-content:space-between; align-items:end; gap:1rem; margin:1.4rem 0 .65rem; }
    .workspace-rail { background:#064a2c; border:1px solid var(--line); padding:1rem; min-height:100%; }
    .rail-title { color:var(--hot); font-family:'DM Mono',monospace; font-size:.68rem; text-transform:uppercase; letter-spacing:.1em; margin-bottom:1rem; }
    .rail-item { border-left:2px solid transparent; padding:.7rem .6rem; color:var(--muted); font-family:'DM Mono',monospace; font-size:.7rem; text-transform:uppercase; letter-spacing:.05em; }
    .rail-item.active { border-left-color:var(--hot); color:var(--ink); background:rgba(255,241,90,.08); }
    .inspector { background:#064a2c; border:1px solid var(--line); padding:1rem; min-height:100%; }
    .inspector-row { display:flex; justify-content:space-between; gap:.5rem; border-bottom:1px solid rgba(255,241,90,.2); padding:.65rem 0; font-family:'DM Mono',monospace; font-size:.68rem; }
    .inspector-row span:first-child { color:var(--muted); }
    .inspector-row span:last-child { color:var(--ink); text-align:right; }
    .panel { background:#f8ed8b; color:#075c36; padding:1.2rem; min-height:100%; border:2px solid var(--ink); border-radius:0; box-shadow:6px 6px 0 var(--ink); }
    .panel * { color:var(--ink) !important; }
    .panel-dark { background:#064a2c; border:1px solid var(--line); border-radius:0; padding:1.2rem; min-height:100%; box-shadow:4px 4px 0 rgba(0,0,0,.16); }
    .panel-dark * { color:var(--ink) !important; }
    .panel-label { font-family:'DM Mono',monospace; font-size:.68rem; text-transform:uppercase; color:var(--hot) !important; letter-spacing:.1em; }
    .panel-value { font-size:2.6rem; font-weight:700; line-height:.95; margin:1.1rem 0 .6rem; }
    [data-testid="stFileUploaderDropzone"] { background:#fff8b5; border:2px dashed #075c36; padding:1.1rem; border-radius:0; }
    [data-testid="stFileUploaderDropzoneInstructions"] { color:var(--ink); }
    .stButton > button { background:var(--hot); border:2px solid var(--ink); border-radius:0; color:#fff; font-family:'DM Mono',monospace; text-transform:uppercase; letter-spacing:.06em; font-weight:500; padding:.72rem 1rem; box-shadow:4px 4px 0 var(--ink); }
    .stButton > button:hover { background:#ff63b0; color:#fff; }
    .metric-row { display:grid; grid-template-columns:repeat(4,1fr); gap:1px; background:var(--line); margin-top:1rem; border:1px solid var(--line); border-radius:.6rem; overflow:hidden; }
    .metric { background:#064a2c; padding:.85rem; min-height:5.5rem; }
    .metric .value { font-size:1.8rem; font-weight:600; margin-top:.75rem; }
    .status { border-left:4px solid var(--hot); padding:.85rem 1rem; background:var(--green-soft); margin-top:1rem; border-radius:0; }
    .status.good { border-color:var(--green); }
    .status p { margin:.25rem 0; }
    .timeline { display:grid; grid-template-columns:repeat(6,1fr); margin:1rem 0 1.5rem; border:1px solid var(--line); background:#064a2c; border-radius:0; padding:1rem; box-shadow:4px 4px 0 rgba(0,0,0,.16); }
    .step { padding:.35rem .7rem 0 0; border-right:1px solid var(--line); min-height:4.8rem; }
    .step:last-child { border-right:0; }
    .step-no { color:var(--orange); font-family:'DM Mono',monospace; }
    .step-name { margin-top:1.1rem; font-weight:600; font-size:.95rem; color:var(--ink); }
    .footer { border-top:1px solid var(--line); margin-top:5rem; padding-top:1rem; color:var(--muted); display:flex; justify-content:space-between; }
    .activity-log { border:1px solid var(--line); background:#064a2c; border-radius:0; padding:.65rem 1rem; margin-top:.5rem; max-height:14rem; overflow-y:auto; box-shadow:0 4px 12px rgba(0,0,0,.14); }
    .activity-entry { display:grid; grid-template-columns:8rem 5rem 1fr; gap:1rem; padding:.5rem 0; border-bottom:1px solid rgba(255,241,90,.18); font-size:.88rem; line-height:1.35; }
    .activity-entry:last-child { border-bottom:0; }
    .activity-time,.activity-level { color:#e8edaa; font-family:'DM Mono',monospace; font-size:.72rem; text-transform:uppercase; }
    .activity-level { color:var(--green); }
    .stage-rail { display:grid; grid-template-columns:repeat(6,1fr); gap:.45rem; margin:.4rem 0 1.4rem; }
    .stage { display:grid; grid-template-columns:2rem 1fr; gap:.5rem; align-items:center; border-top:2px solid var(--line); padding-top:.55rem; opacity:.55; }
    .stage.active { border-color:var(--orange); opacity:1; }
    .stage.done { border-color:var(--acid); opacity:.9; }
    .stage.failed { border-color:#ff4d5e; opacity:1; }
    .stage-dot { width:1.7rem; height:1.7rem; border-radius:50%; display:grid; place-items:center; background:#292929; color:var(--muted); font-family:'DM Mono',monospace; font-size:.62rem; }
    .stage.active .stage-dot { background:var(--hot); color:#fff; box-shadow:0 0 0 .25rem rgba(255,47,146,.2); }
    .stage.done .stage-dot { background:var(--ink); color:#075c36; }
    .stage.failed .stage-dot { background:#ffb4c8; color:#7d1238; }
    .stage-name { font-family:'DM Mono',monospace; text-transform:uppercase; font-size:.75rem; letter-spacing:.05em; color:var(--ink); }
    .stMarkdown p, .stCaption, [data-testid="stFileUploaderDropzoneInstructions"] { line-height:1.45; }
    .stCaption { color:#e8edaa !important; }
    .stAlert p { color:var(--ink) !important; }
    .stAlert { border-radius:.6rem; }
    @media (max-width:1100px) { .workspace-rail,.inspector { min-height:auto; } }
    @media (max-width:800px) { .hero-mark{right:4%;font-size:6rem}.metric-row{grid-template-columns:repeat(2,1fr)}.timeline{grid-template-columns:repeat(2,1fr)}.step:nth-child(2n){border-right:0} }
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
    safe_message = re.sub(r"(?i)(serpapi_key|private_key|api[_ -]?key)=?[^\s,;]+", r"\1=[redacted]", message)
    if "exactly one face" in lowered:
        if "found: 0" in lowered:
            return "Face detection", "No face was detected. Upload a clear image containing one face."
        return "Face detection", "Multiple faces were detected. Upload an image containing exactly one face."
    if "unable to read" in lowered or "unsupported or corrupt" in lowered:
        return "Input image", "The image is invalid, unsupported, or corrupt."
    if "face detection failed" in lowered or "insightface" in lowered or "onnx" in lowered or "model" in lowered:
        return "Face detection/model", f"The face model stage failed: {safe_message}"
    if "serpapi_key" in lowered:
        return "Reverse-image search", "SERPAPI_KEY is missing from the local environment."
    if "serpapi" in lowered or "reverse" in lowered:
        return "Reverse-image search", "The reverse-image search request failed."
    if "rpc" in lowered or "blockchain" in lowered or "gas" in lowered:
        return "Blockchain", "Polygon could not confirm the verification transaction."
    return "Verification", f"The pipeline could not complete this verification: {safe_message}"


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
    <div class="topline"><span class="mono">TraceFace / Verification Studio</span><span class="mono">AMOY 80002&nbsp;&nbsp; · &nbsp;&nbsp;LIVE</span></div>
    <section class="hero"><div><div class="mono hero-kicker">Identity, with receipts.</div><h1>TraceFace</h1><p class="hero-copy">A live visual verification studio for finding, comparing, and sealing evidence records on-chain. Similarity is evidence, not identity proof.</p></div><div class="hero-mark">✳</div></section>
    <div class="ticker">LIVE VERIFICATION / FACE DETECTION / REVERSE SEARCH / ARCFACE / SHA-256 / POLYGON AMOY / LIVE VERIFICATION /</div>
    <div class="section-head"><div><div class="mono section-tag">Evidence pipeline</div><h2>Six steps to<br>the receipt.</h2></div><div class="mono">Production gate / 0.65</div></div>
    <div class="timeline"><div class="step"><div class="step-no">01</div><div class="step-name">Detect</div><div class="mono">Face signal</div></div><div class="step"><div class="step-no">02</div><div class="step-name">Embed</div><div class="mono">ArcFace vector</div></div><div class="step"><div class="step-no">03</div><div class="step-name">Search</div><div class="mono">SerpApi Lens</div></div><div class="step"><div class="step-no">04</div><div class="step-name">Compare</div><div class="mono">Similarity gate</div></div><div class="step"><div class="step-no">05</div><div class="step-name">Hash</div><div class="mono">Canonical JSON</div></div><div class="step"><div class="step-no">06</div><div class="step-name">Anchor</div><div class="mono">Polygon Amoy</div></div></div>
    <div class="section-head"><div><div class="mono section-tag">01 / Input</div><h2>Bring the<br>evidence.</h2></div><div class="mono">One face. One source image.</div></div>
    """,
    unsafe_allow_html=True,
)

nav, center, inspector = st.columns([.2, .58, .22], gap="medium")
with nav:
    st.markdown(
        """
        <div class="workspace-rail">
          <div class="rail-title">TraceFace / Workspace</div>
          <div class="rail-item active">01 / Verify</div>
          <div class="rail-item">02 / Sources</div>
          <div class="rail-item">03 / Audit trail</div>
          <div class="rail-item">04 / Network</div>
          <div style="height:1rem"></div>
          <div class="mono" style="color:var(--muted)">Production mode<br>Gate 0.65<br>Polygon Amoy</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with center:
    st.markdown('<div class="panel"><div class="panel-label">Drop zone / source image</div>', unsafe_allow_html=True)
    upload = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)
    if upload:
        st.image(upload, caption=f"SOURCE / {upload.name}", use_container_width=True)
with inspector:
    st.markdown(
        f"""
        <div class="inspector">
          <div class="panel-label">Forensic inspector</div>
          <div class="inspector-row"><span>Protocol</span><span>Production</span></div>
          <div class="inspector-row"><span>Face model</span><span>ArcFace</span></div>
          <div class="inspector-row"><span>Search</span><span>SerpApi Lens</span></div>
          <div class="inspector-row"><span>Threshold</span><span>{FACE_SIMILARITY_THRESHOLD:.2f}</span></div>
          <div class="inspector-row"><span>Network</span><span>Amoy / 80002</span></div>
          <div class="inspector-row"><span>Biometrics</span><span>Off-chain only</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="panel-dark"><div class="panel-label">Production protocol</div><div class="panel-value">{FACE_SIMILARITY_THRESHOLD:.2f}</div><p>Similarity threshold. Production mode only.</p><div class="mono" style="margin-top:2rem;color:#aaa69e">No match. No hash. No transaction.</div></div>', unsafe_allow_html=True)
    run = st.button("Run Verification", type="primary", use_container_width=True, disabled=upload is None)

st.markdown('<div class="section-head"><div><div class="mono section-tag">Live / Activity</div><h2>What is<br>happening.</h2></div><div class="mono">Session only / safe events</div></div>', unsafe_allow_html=True)
stage_slot = st.empty()
render_stages(stage_slot)
activity_slot = st.empty()
render_activity(activity_slot)

if run and upload:
    st.session_state.stage_index = 1
    st.session_state.stage_failed = False
    render_stages(stage_slot)
    def pipeline_progress(message: str, level: str = "INFO") -> None:
        update_stage(message)
        render_stages(stage_slot)
        log_activity(message, level)
        render_activity(activity_slot)

    pipeline_progress(f"Source image received: {Path(upload.name).suffix.lower() or 'image'}")
    suffix = Path(upload.name).suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(upload.getbuffer())
        temp_path = temp_file.name
    try:
        with st.status("Running production verification...", expanded=True) as progress:
            progress.write("Loading image and detecting exactly one face")
            progress.write("Generating embedding and searching reverse image sources")
            progress.write("Comparing real candidate faces against the 0.65 gate")
            result = run_pipeline(
                temp_path,
                threshold=FACE_SIMILARITY_THRESHOLD,
                use_gpu=USE_GPU,
                progress_callback=pipeline_progress,
            )
            progress.update(label="Verification complete", state="complete", expanded=False)
        pipeline_progress(f"Verification complete: {result.get('input_faces', 0)} face(s), {result.get('reverse_results_count', 0)} search result(s)")
    except Exception as exc:
        heading, message = _friendly_error(exc)
        st.session_state.stage_failed = True
        update_stage(f"{heading} failed")
        log_activity(f"{heading}: {message}", "ERROR")
        render_stages(stage_slot)
        render_activity(activity_slot)
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

        st.markdown('<div class="section-head"><div><div class="mono section-tag">Sources / All returned candidates</div><h3>Every signal in the room.</h3></div><div class="mono">Ranked by similarity</div></div>', unsafe_allow_html=True)
        candidates = sorted(
            result.get("candidate_details", []),
            key=lambda item: item.get("best_similarity", 0),
            reverse=True,
        )
        if candidates:
            for index, candidate in enumerate(candidates, start=1):
                similarity_value = candidate.get("best_similarity", 0)
                decision = "MATCH" if candidate.get("matched") else "NO MATCH"
                state = "good" if candidate.get("matched") else ""
                url = candidate.get("url") or ""
                link = f'<a href="{url}" target="_blank">Open source ↗</a>' if url else "No URL"
                st.markdown(
                    f'<div class="panel-dark" style="padding:.8rem 1rem;margin:.45rem 0;display:grid;grid-template-columns:2.5rem 1fr auto;gap:1rem;align-items:center;">'
                    f'<div class="mono" style="color:var(--orange)">#{index:02d}</div>'
                    f'<div><strong>{candidate.get("platform", "Unknown")}</strong><br><span class="mono">{link} · {"accessible" if candidate.get("accessible") else "inaccessible"} · {candidate.get("candidate_face_count", 0)} face(s)</span></div>'
                    f'<div class="status {state}" style="margin:0;padding:.5rem .7rem;text-align:right"><div class="mono">{similarity_value:.0%}</div><div class="mono">{decision}</div></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No social candidates were returned by the live search.")

        st.markdown('<div class="section-head"><div><div class="mono section-tag">05 / Blockchain</div><h2>Leave a<br>receipt.</h2></div></div>', unsafe_allow_html=True)
        if blockchain.get("transaction_hash"):
            log_activity("Polygon Amoy transaction confirmed", "CHAIN")
            explorer = blockchain.get("explorer_url")
            st.success("Polygon Amoy transaction confirmed.")
            st.write({"network": "Polygon Amoy", "contract": CONTRACT_ADDRESS, "block": blockchain.get("block_number"), "gas_used": blockchain.get("gas_used"), "getVerification": "PASS" if blockchain.get("record_verified") else "FAIL"})
            st.code(blockchain.get("record_hash", ""), language="text")
            if explorer:
                st.link_button("Open transaction in Polygonscan", explorer)
        elif blockchain.get("status") == "FAILED":
            log_activity("Polygon transaction failed; no confirmation claimed", "ERROR")
            st.error("Blockchain transaction failed. No confirmed record exists.")
            st.caption("The failure was returned by the configured Polygon Amoy client; no confirmation is claimed.")
        elif blockchain.get("status") == "NOT_CONFIGURED":
            st.warning("Blockchain is not configured for this verified result. No transaction was sent.")
        else:
            log_activity("No verified match; blockchain submission skipped", "SAFE")
            st.info("Blockchain Status: NOT_ATTEMPTED. No verified match means no hash and no transaction.")

        report = _safe_report(result, temp_path)
        report_dir = PROJECT_ROOT / "output"
        report_dir.mkdir(exist_ok=True)
        report_path = report_dir / "verification_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        log_activity("Sanitized verification report exported locally", "EXPORT")
        st.download_button("Export local JSON report", data=json.dumps(report, indent=2), file_name="verification_report.json", mime="application/json")
        with st.expander("Safe report fields"):
            st.json(report)
    finally:
        Path(temp_path).unlink(missing_ok=True)

render_activity(activity_slot)

st.markdown('<div class="footer"><span class="mono">LESS NOISE. MORE SIGNAL.</span><span class="mono">Milestone 3 / Final Verification Studio</span></div>', unsafe_allow_html=True)
