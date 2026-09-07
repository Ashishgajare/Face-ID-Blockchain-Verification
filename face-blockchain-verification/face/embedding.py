from __future__ import annotations
import numpy as np
from typing import Sequence


def normalize_embedding(emb: Sequence[float]) -> np.ndarray:
    arr = np.array(emb, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm == 0:
        return arr
    return arr / norm


def to_numpy(emb: Sequence[float]) -> np.ndarray:
    return np.array(emb, dtype=np.float32)
