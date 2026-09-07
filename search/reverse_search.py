import os
import serpapi
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()

API_KEY = os.getenv("SERPAPI_API_KEY")

if not API_KEY:
    raise ValueError("SERPAPI_API_KEY not found in .env")


def reverse_image_search(image_path):

    print("Uploading image to SerpApi...")

    # Create SerpApi client
    client = serpapi.Client(api_key=API_KEY)

    # Upload local image
    upload = client.upload_image(image_path)

    image_id = upload["image_id"]

    print("Image uploaded ✓")
    print("Image ID received ✓")

    print("\nSearching Google Lens...")

    # Search Google Lens
    results = client.search({
        "engine": "google_lens",
        "image_id": image_id,
        "type": "all",
        "hl": "en",
        "country": "in"
    })

    print("Google Lens search complete ✓")

    return results


if __name__ == "__main__":

    # Use the compressed image
    image_path = "test_images/person_compressed.jpg"

    results = reverse_image_search(image_path)

    # Get visual matches
    visual_matches = results.get("visual_matches", [])

    print("\n================================")
    print("GOOGLE LENS RESULTS")
    print("================================")

    print(f"\nVisual matches found: {len(visual_matches)}")

    for i, result in enumerate(visual_matches[:10], start=1):

        print(f"\n--- RESULT {i} ---")

        print("Title:", result.get("title", "N/A"))
        print("Source:", result.get("source", "N/A"))
        print("Link:", result.get("link", "N/A"))
        print("Image:", result.get("image", "N/A"))
