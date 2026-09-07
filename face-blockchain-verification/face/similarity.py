from __future__ import annotations
import numpy as np
from typing import Tuple


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype(float)
    b = b.astype(float)
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def compare_faces(a: np.ndarray, b: np.ndarray, threshold: float) -> Tuple[float, float, bool]:
    """Return (similarity, threshold, matched)"""
    sim = cosine_similarity(a, b)
    return sim, threshold, sim >= threshold
