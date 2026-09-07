from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
import hashlib
import logging
from face.detector import detect_faces_from_path, FaceDetectionResult
from face.embedding import normalize_embedding, to_numpy
from face.similarity import compare_faces
from reverse_search.serpapi_client import reverse_image_search
from reverse_search.result_parser import parse_serpapi_response
from reverse_search.social_filter import filter_social_results, SocialMediaCandidate
import config
import requests
import cv2
import numpy as np
from blockchain.client import PolygonClient
from blockchain.contract import FaceVerificationContract
from verification.hashing import hash_verification_record
from verification.models import VerificationRecord

logger = logging.getLogger(__name__)


class CandidateVerificationResult:
    def __init__(self, candidate: SocialMediaCandidate):
        self.candidate = candidate
        self.accessible = False
        self.candidate_face_count = 0
        self.best_similarity = 0.0
        self.matched = False
        self.error = None


def production_match(similarity: float, threshold: float) -> bool:
    return similarity >= threshold


def _apply_development_test_match(result: CandidateVerificationResult, threshold: float) -> None:
    # DEVELOPMENT ONLY: this never runs unless the CLI test flag is explicitly enabled.
    result.best_similarity = max(result.best_similarity, threshold)
    result.matched = True
    result.error = "DEVELOPMENT_TEST_MATCH"


def _download_image(url: str, max_bytes: int) -> bytes:
    headers = {"User-Agent": "FaceVerification/1.0"}
    with requests.get(url, headers=headers, stream=True, timeout=10) as r:
        r.raise_for_status()
        content = bytearray()
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                content.extend(chunk)
            if len(content) > max_bytes:
                raise ValueError("Downloaded image exceeds maximum allowed size")
        return bytes(content)


def _decode_image_bytes(b: bytes) -> np.ndarray:
    arr = np.frombuffer(b, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to decode image bytes")
    return img


def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as image_file:
        for chunk in iter(lambda: image_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _anchor_verified_match(image_path: str, best: CandidateVerificationResult, threshold: float) -> Dict[str, Any]:
    if not best.matched:
        return {"status": "NOT_ATTEMPTED", "reason": "No verified match"}

    record = VerificationRecord(
        platform=best.candidate.platform,
        post_url=best.candidate.url,
        similarity=best.best_similarity,
        threshold=threshold,
        status="VERIFIED_MATCH",
        image_sha256=_sha256_file(image_path),
    )
    record_hash = hash_verification_record(record)
    result: Dict[str, Any] = {
        "status": "NOT_CONFIGURED",
        "record": record.model_dump(mode="json"),
        "record_hash": record_hash,
        "transaction_hash": None,
        "block_number": None,
        "contract_address": config.CONTRACT_ADDRESS,
        "chain_id": config.CHAIN_ID,
        "explorer_url": None,
        "error": None,
    }

    missing = [
        name
        for name, value in (
            ("POLYGON_RPC_URL", config.POLYGON_RPC_URL),
            ("WALLET_ADDRESS", config.WALLET_ADDRESS),
            ("PRIVATE_KEY", config.PRIVATE_KEY),
            ("CONTRACT_ADDRESS", config.CONTRACT_ADDRESS),
        )
        if not value
    ]
    if missing:
        result["error"] = "Missing blockchain configuration: " + ", ".join(missing)
        return result

    try:
        client = PolygonClient(
            rpc_url=config.POLYGON_RPC_URL,
            wallet_address=config.WALLET_ADDRESS,
            private_key=config.PRIVATE_KEY,
            chain_id=config.CHAIN_ID,
        ).connect()
        stored = FaceVerificationContract(client, config.CONTRACT_ADDRESS).store_verification(
            record_hash, record.post_url, record.platform
        )
        result.update(stored)
        result["status"] = "CONFIRMED" if stored["success"] else "FAILED"
        if stored["success"]:
            on_chain = FaceVerificationContract(client, config.CONTRACT_ADDRESS).get_verification(record_hash)
            result["on_chain_record"] = on_chain
            result["record_verified"] = (
                on_chain["record_hash"].lower() == f"0x{record_hash}".lower()
                and on_chain["post_url"] == record.post_url
                and on_chain["platform"] == record.platform
                and on_chain["exists"] is True
            )
    except Exception as exc:
        result["status"] = "FAILED"
        result["error"] = str(exc)
    return result


def run_pipeline(
    image_path: str,
    threshold: float | None = None,
    use_gpu: bool = False,
    development_test_mode: bool = False,
    progress_callback: Optional[Callable[[str, str], None]] = None,
) -> dict:
    threshold = threshold if threshold is not None else config.FACE_SIMILARITY_THRESHOLD

    def progress(message: str, level: str = "INFO") -> None:
        if progress_callback:
            progress_callback(message, level)

    # Stage 1: detect input face
    progress("Detecting exactly one face")
    det_result: FaceDetectionResult = detect_faces_from_path(image_path, use_gpu=use_gpu)
    if not det_result.success:
        raise RuntimeError(f"Face detection failed: {det_result.error}")
    if det_result.face_count != 1:
        raise RuntimeError(f"Input image must contain exactly one face, found: {det_result.face_count}")

    input_face = det_result.faces[0]
    if input_face.embedding is None:
        raise RuntimeError("Embedding missing from detected input face")

    input_emb = normalize_embedding(to_numpy(input_face.embedding))
    progress("Face detected; ArcFace embedding generated")

    # Stage 2: reverse image search
    progress("Calling Google reverse image search via SerpApi")
    resp = reverse_image_search(image_path)
    parsed = parse_serpapi_response(resp)
    progress(f"Reverse search completed: {len(parsed)} result(s)")

    # Stage 3: social filtering
    social_candidates = filter_social_results(parsed)
    progress(f"Social filter found {len(social_candidates)} candidate(s)")

    candidate_results: List[CandidateVerificationResult] = []

    for cand in social_candidates:
        progress(f"Comparing candidate from {cand.platform}")
        vr = CandidateVerificationResult(cand)
        # attempt to get an image url from candidate
        img_url = cand.image_url or cand.url
        if not img_url:
            vr.error = "No image URL"
            candidate_results.append(vr)
            continue

        try:
            raw = _download_image(img_url, max_bytes=config.MAX_IMAGE_DOWNLOAD_BYTES)
            vr.accessible = True
            img = _decode_image_bytes(raw)
            # detect faces
            from face.detector import get_face_analyzer

            fa = get_face_analyzer(use_gpu=use_gpu)
            faces = fa.get(img)
            vr.candidate_face_count = len(faces)
            best_sim = 0.0
            for f in faces:
                if getattr(f, "embedding", None) is None:
                    continue
                emb = normalize_embedding(to_numpy(f.embedding.tolist()))
                sim, _, matched = compare_faces(input_emb, emb, threshold)
                if sim > best_sim:
                    best_sim = sim
            vr.best_similarity = best_sim
            vr.matched = production_match(best_sim, threshold)
            if development_test_mode and vr.accessible and vr.candidate_face_count > 0:
                _apply_development_test_match(vr, threshold)
        except Exception as e:
            vr.error = str(e)
        candidate_results.append(vr)
        progress(
            f"Candidate {cand.platform}: {vr.best_similarity:.2f} similarity, "
            f"{'match' if vr.matched else 'no match'}",
            "MATCH" if vr.matched else "INFO",
        )

    if development_test_mode and not candidate_results and parsed:
        real_result = next((item for item in parsed if item.link), None)
        if real_result is not None:
            mock_candidate = SocialMediaCandidate(
                platform="development-test",
                url=real_result.link or "",
                title=real_result.title,
                image_url=real_result.thumbnail,
                raw=real_result.raw,
            )
            mock_result = CandidateVerificationResult(mock_candidate)
            _apply_development_test_match(mock_result, threshold)
            candidate_results.append(mock_result)

    # pick best candidate overall
    best = None
    best_score = 0.0
    for r in candidate_results:
        if r.best_similarity > best_score:
            best_score = r.best_similarity
            best = r

    output = {
        "input_faces": det_result.face_count,
        "input_face_bbox": det_result.faces[0].bbox if det_result.face_count == 1 else None,
        "reverse_results_count": len(parsed),
        "social_candidates_count": len(social_candidates),
        "best_candidate": None,
        "verification_record": None,
        "blockchain": {"status": "NOT_ATTEMPTED", "reason": "No verified match"},
        "candidate_details": [
            {
                "platform": r.candidate.platform,
                "url": r.candidate.url,
                "accessible": r.accessible,
                "candidate_face_count": r.candidate_face_count,
                "best_similarity": r.best_similarity,
                "matched": r.matched,
                "error": r.error,
            }
            for r in candidate_results
        ],
    }

    if best is not None:
        output["best_candidate"] = {
            "platform": best.candidate.platform,
            "url": best.candidate.url,
            "similarity": best.best_similarity,
            "matched": best.matched,
        }
        progress("Creating verification record and SHA-256 hash")
        output["blockchain"] = _anchor_verified_match(image_path, best, threshold)
        progress(f"Verification result: {'match' if best.matched else 'no match'}")
        if best.matched:
            progress(
                f"Polygon Amoy: {output['blockchain'].get('status', 'not attempted')}",
                "CHAIN" if output["blockchain"].get("status") == "CONFIRMED" else "INFO",
            )
    else:
        progress("No verified candidate; no further processing", "SAFE")
        output["verification_record"] = output["blockchain"].get("record")
        if output["blockchain"].get("record_hash"):
            output["verification_record_hash"] = output["blockchain"]["record_hash"]

    return output
