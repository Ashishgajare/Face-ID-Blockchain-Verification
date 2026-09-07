import numpy as np
from face.similarity import cosine_similarity, compare_faces


def test_cosine_similarity_identical():
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([1.0, 0.0, 0.0])
    assert abs(cosine_similarity(a, b) - 1.0) < 1e-6


def test_cosine_similarity_orthogonal():
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([0.0, 1.0, 0.0])
    assert abs(cosine_similarity(a, b)) < 1e-6


def test_compare_faces_threshold():
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([0.8, 0.6, 0.0])
    sim, thr, matched = compare_faces(a, b, 0.9)
    assert isinstance(sim, float)
    assert thr == 0.9
    assert matched is False
