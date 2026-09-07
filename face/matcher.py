import cv2
import numpy as np
from insightface.app import FaceAnalysis

# Load InsightFace
app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

app.prepare(ctx_id=0, det_size=(640, 640))


# Get face embedding from an image
def get_embedding(image_path):

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    faces = app.get(image)

    if len(faces) == 0:
        raise ValueError(f"No face detected in {image_path}")

    # Select the largest detected face
    face = max(
        faces,
        key=lambda f: (f.bbox[2] - f.bbox[0]) *
                       (f.bbox[3] - f.bbox[1])
    )

    return face.embedding


# Calculate cosine similarity
def cosine_similarity(embedding1, embedding2):

    embedding1 = np.array(embedding1)
    embedding2 = np.array(embedding2)

    similarity = np.dot(embedding1, embedding2) / (
        np.linalg.norm(embedding1) *
        np.linalg.norm(embedding2)
    )

    return float(similarity)


# Main program
if __name__ == "__main__":

    # Your actual image names
    image1 = "test_images/person.jpg"
    image2 = "test_images/person1_different.jpg"
    image3 = "test_images/person2.jpg"

    print("Generating embeddings...")

    embedding1 = get_embedding(image1)
    embedding2 = get_embedding(image2)
    embedding3 = get_embedding(image3)

    print("Embeddings generated ✓")

    print("\nEmbedding dimensions:")
    print("Person 1:", embedding1.shape)
    print("Person 2:", embedding2.shape)
    print("Person 3:", embedding3.shape)

    # Compare the three faces
    similarity_12 = cosine_similarity(embedding1, embedding2)
    similarity_13 = cosine_similarity(embedding1, embedding3)
    similarity_23 = cosine_similarity(embedding2, embedding3)

    print("\nFace Similarity Results:")

    print("\nPerson vs Person1 Different")
    print(f"Similarity: {similarity_12:.4f}")

    print("\nPerson vs Person2")
    print(f"Similarity: {similarity_13:.4f}")

    print("\nPerson1 Different vs Person2")
    print(f"Similarity: {similarity_23:.4f}")
