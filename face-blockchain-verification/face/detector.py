from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
import cv2
import numpy as np
import os
try:
    from insightface.app import FaceAnalysis
except ImportError:  # pragma: no cover - backward compatibility for older insightface builds
    from insightface import FaceAnalysis
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class DetectedFace(BaseModel):
    bbox: List[int]
    score: float
    embedding: Optional[List[float]] = None


class FaceDetectionResult(BaseModel):
    success: bool
    face_count: int
    faces: List[DetectedFace] = []
    error: Optional[str] = None


@lru_cache(maxsize=1)
def get_face_analyzer(use_gpu: bool = False) -> FaceAnalysis:
    # ctx_id=-1 selects CPU for insightface
    ctx_id = 0 if use_gpu else -1
    try:
        fa = FaceAnalysis(name="buffalo_l")
        fa.prepare(ctx_id=ctx_id, det_size=(640, 640))
        return fa
    except Exception as e:
        logger.exception("Failed to initialize FaceAnalysis: %s", e)
        raise


def load_image(path: str) -> np.ndarray:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image not found: {path}")
    img = cv2.imread(path)
    if img is None:
        raise ValueError("Unable to read image (unsupported or corrupt): %s" % path)
    return img


def detect_faces_from_path(path: str, use_gpu: bool = False) -> FaceDetectionResult:
    try:
        img = load_image(path)
    except Exception as e:
        return FaceDetectionResult(success=False, face_count=0, faces=[], error=str(e))

    try:
        fa = get_face_analyzer(use_gpu=use_gpu)
        faces = fa.get(img)
    except Exception as e:
        logger.exception("InsightFace detection failed: %s", e)
        return FaceDetectionResult(success=False, face_count=0, faces=[], error=str(e))

    detected = []
    for f in faces:
        bbox = [int(f.bbox[0]), int(f.bbox[1]), int(f.bbox[2]), int(f.bbox[3])]
        score = float(getattr(f, "det_score", 0.0) or 0.0)
        emb = None
        if hasattr(f, "embedding") and f.embedding is not None:
            emb = [float(x) for x in f.embedding.tolist()]
        detected.append(DetectedFace(bbox=bbox, score=score, embedding=emb))

    return FaceDetectionResult(success=True, face_count=len(detected), faces=detected)
