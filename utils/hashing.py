import hashlib
import json


def calculate_record_hash(record):
    canonical_record = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":")
    )

    hash_value = hashlib.sha256(
        canonical_record.encode("utf-8")
    ).hexdigest()

    return hash_value


if __name__ == "__main__":

    record = {
        "title": "Women's black top - Free Photo on Unsplash",
        "source": "Unsplash",
        "post_url": "https://unsplash.com/photos/womens-black-top-25WM4IEnPIg"
    }

    hash_value = calculate_record_hash(record)

    print("\n================================")
    print("TRACEFACE SHA-256 FINGERPRINT")
    print("================================")

    print("\nDiscovered Post:")
    print(json.dumps(record, indent=4))

    print("\nSHA-256:")
    print(hash_value)

    print("\nHash length:")
    print(len(hash_value))

    print("\n================================")
    print("PHASE 10 COMPLETE ✓")
    print("================================")
