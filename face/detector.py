import cv2
from insightface.app import FaceAnalysis


app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

app.prepare(ctx_id=0, det_size=(640, 640))


def detect_faces(image_path):

    image = cv2.imread(image_path)

    if image is None:
        print("Could not load image.")
        return []

    print("Loading image...")

    faces = app.get(image)

    return faces


if __name__ == "__main__":

    image_path = "test_images/person.jpg"

    faces = detect_faces(image_path)

    if len(faces) == 0:

        print("No face detected ✗")

    else:

        print("Face detected ✓")
        print()
        print(f"Number of faces: {len(faces)}")

        for i, face in enumerate(faces):

            x1, y1, x2, y2 = face.bbox.astype(int)

            width = x2 - x1
            height = y2 - y1

            print()
            print(f"Face {i + 1} bounding box:")
            print(f"x = {x1}")
            print(f"y = {y1}")
            print(f"width = {width}")
            print(f"height = {height}")

            # Get face embedding
            embedding = face.embedding

            print()
            print("Embedding generated ✓")
            print("Embedding dimensions:", embedding.shape)

            print()
            print("First 10 values:")
            print(embedding[:10])
