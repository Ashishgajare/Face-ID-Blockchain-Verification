
"""Face modules package.

Note: avoid heavy imports (cv2/insightface) at package import time so unit tests
that only import lightweight modules (e.g. `face.similarity`) don't trigger
native library loading. Import `face.detector` lazily in callers instead.
"""

