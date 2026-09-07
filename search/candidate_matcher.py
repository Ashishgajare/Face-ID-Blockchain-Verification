import os
import requests
import cv2
import numpy as np
import serpapi

from dotenv import load_dotenv
from insightface.app import FaceAnalysis


# ============================================================
# SETUP
# ============================================================

load_dotenv()

API_KEY = os.getenv("SERPAPI_API_KEY")

if not API_KEY:
    raise ValueError("SERPAPI_API_KEY not found in .env")


# Initialize InsightFace
print("Loading InsightFace model...")

face_app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

face_app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)

print("InsightFace loaded ✓")


# ============================================================
# FACE FUNCTIONS
# ============================================================

def get_faces(image_path):
    """
    Detect all faces in an image.
    """

    image = cv2.imread(image_path)

    if image is None:
        print(f"Could not read image: {image_path}")
        return []

    faces = face_app.get(image)

    return faces


def cosine_similarity(embedding1, embedding2):
    """
    Calculate cosine similarity between two face embeddings.
    """

    embedding1 = np.asarray(embedding1)
    embedding2 = np.asarray(embedding2)

    similarity = np.dot(embedding1, embedding2) / (
        np.linalg.norm(embedding1) *
        np.linalg.norm(embedding2)
    )

    return float(similarity)


def find_best_face_match(input_embedding, candidate_faces):
    """
    Compare the input face with every face detected
    in a candidate image.

    Returns the highest similarity score.
    """

    if not candidate_faces:
        return None

    best_score = -1

    for candidate_face in candidate_faces:

        score = cosine_similarity(
            input_embedding,
            candidate_face.embedding
        )

        if score > best_score:
            best_score = score

    return best_score


# ============================================================
# IMAGE DOWNLOAD
# ============================================================

def download_image(url, output_path):
    """
    Download an image from a URL.
    """

    try:

        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        with open(output_path, "wb") as file:
            file.write(response.content)

        return True

    except Exception as error:

        print(f"Download failed: {error}")

        return False


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # INPUT IMAGE
    # --------------------------------------------------------

    image_path = "test_images/person_compressed.jpg"

    print("\n================================")
    print("TRACEFACE")
    print("FACE + WEB SEARCH")
    print("================================")

    print("\nInput image:")
    print(image_path)


    # --------------------------------------------------------
    # STEP 1 — DETECT INPUT FACE
    # --------------------------------------------------------

    print("\n[1] Detecting face in input image...")

    input_faces = get_faces(image_path)

    print(f"Faces detected: {len(input_faces)}")

    if len(input_faces) == 0:
        raise ValueError(
            "No face detected in the input image."
        )


    # --------------------------------------------------------
    # STEP 2 — SELECT INPUT FACE
    # --------------------------------------------------------

    # If multiple faces exist, use the largest face.

    input_face = max(
        input_faces,
        key=lambda face: (
            face.bbox[2] - face.bbox[0]
        ) * (
            face.bbox[3] - face.bbox[1]
        )
    )

    input_embedding = input_face.embedding

    print("Input face selected ✓")
    print(
        "Embedding shape:",
        input_embedding.shape
    )


    # --------------------------------------------------------
    # STEP 3 — GOOGLE LENS SEARCH
    # --------------------------------------------------------

    print("\n[2] Uploading image to Google Lens...")

    client = serpapi.Client(
        api_key=API_KEY
    )

    upload = client.upload_image(
        image_path
    )

    image_id = upload["image_id"]

    print("Image uploaded ✓")
    print("Image ID received ✓")


    print("\nSearching Google Lens...")

    results = client.search({
        "engine": "google_lens",
        "image_id": image_id,
        "type": "all",
        "hl": "en",
        "country": "in"
    })

    print("Google Lens search complete ✓")


    # --------------------------------------------------------
    # STEP 4 — GET VISUAL MATCHES
    # --------------------------------------------------------

    visual_matches = results.get(
        "visual_matches",
        []
    )

    print(
        f"\nVisual matches found: "
        f"{len(visual_matches)}"
    )

    if len(visual_matches) == 0:
        raise ValueError(
            "No visual matches found."
        )


    # --------------------------------------------------------
    # STEP 5 — CREATE CANDIDATE FOLDER
    # --------------------------------------------------------

    candidate_folder = "search/candidates"

    os.makedirs(
        candidate_folder,
        exist_ok=True
    )


    # --------------------------------------------------------
    # STEP 6 — DOWNLOAD + FACE MATCH
    # --------------------------------------------------------

    match_results = []

    print("\n================================")
    print("ANALYZING CANDIDATES")
    print("================================")


    # Analyze first 10 candidates

    for index, result in enumerate(
        visual_matches[:10],
        start=1
    ):

        print(
            f"\nAnalyzing Candidate {index}..."
        )


        # Get candidate image URL

        image_url = result.get(
            "image",
            ""
        )

        if not image_url:

            print(
                "No image URL found."
            )

            continue


        # Candidate file path

        candidate_path = os.path.join(
            candidate_folder,
            f"candidate_{index}.jpg"
        )


        # Download candidate

        downloaded = download_image(
            image_url,
            candidate_path
        )

        if not downloaded:

            print(
                "Could not download candidate."
            )

            continue


        # Detect faces

        candidate_faces = get_faces(
            candidate_path
        )


        if len(candidate_faces) == 0:

            print(
                "No face detected."
            )

            score = None

        else:

            # Compare faces

            score = find_best_face_match(
                input_embedding,
                candidate_faces
            )

            print(
                f"Face similarity: "
                f"{score:.4f}"
            )


        # Store candidate information

        match_results.append({

            "index": index,

            "title": result.get(
                "title",
                "Unknown"
            ),

            "source": result.get(
                "source",
                "Unknown"
            ),

            "link": result.get(
                "link",
                ""
            ),

            "image": image_url,

            "score": score
        })


    # --------------------------------------------------------
    # STEP 7 — REMOVE CANDIDATES WITHOUT FACES
    # --------------------------------------------------------

    match_results = [
        result
        for result in match_results
        if result["score"] is not None
    ]


    if len(match_results) == 0:

        raise ValueError(
            "No candidate containing a face was found."
        )


    # --------------------------------------------------------
    # STEP 8 — COMBINED RANKING
    # --------------------------------------------------------

    for result in match_results:

        face_score = result["score"]

        search_rank = result["index"]

        # Higher score for candidates appearing
        # earlier in Google Lens results.

        search_score = 1 / search_rank

        # Combine face similarity and search ranking.

        final_score = (
            0.70 * face_score
            +
            0.30 * search_score
        )

        result["final_score"] = final_score


    # Sort highest combined score first

    match_results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )


    # --------------------------------------------------------
    # STEP 8 OUTPUT — RANKED RESULTS
    # --------------------------------------------------------

    print("\n================================")
    print("RANKED CANDIDATES")
    print("================================")


    for rank, result in enumerate(
        match_results,
        start=1
    ):

        print(
            f"\n#{rank} Candidate "
            f"{result['index']}"
        )

        print(
            f"Face Similarity: "
            f"{result['score']:.4f}"
        )

        print(
            f"Search Rank: "
            f"{result['index']}"
        )

        print(
            f"Combined Score: "
            f"{result['final_score']:.4f}"
        )

        print(
            f"Title: "
            f"{result['title']}"
        )

        print(
            f"Source: "
            f"{result['source']}"
        )

        print(
            f"Link: "
            f"{result['link']}"
        )


    # ========================================================
    # PHASE 9 — STORE DISCOVERED POST
    # ========================================================

    # The first result is our best match after ranking.

    best_match = match_results[0]


    # Create a clean record containing the
    # important information about the discovered post.

    discovered_post = {

        "title": best_match["title"],

        "source": best_match["source"],

        "post_url": best_match["link"]

    }


    # --------------------------------------------------------
    # DISPLAY PHASE 9 RESULT
    # --------------------------------------------------------

    print("\n================================")
    print("PHASE 9 — DISCOVERED POST")
    print("================================")

    print(
        "Title:",
        discovered_post["title"]
    )

    print(
        "Source:",
        discovered_post["source"]
    )

    print(
        "Post URL:",
        discovered_post["post_url"]
    )


    # --------------------------------------------------------
    # FINAL STATUS
    # --------------------------------------------------------

    print("\n================================")
    print("PHASE 9 COMPLETE ✓")
    print("================================")

    print(
        "\nThe best matching post has been "
        "stored as a structured record."
    )

    print(
        "\nReady for Phase 10:"
    )

    print(
        "SHA-256 fingerprint generation"
    )
