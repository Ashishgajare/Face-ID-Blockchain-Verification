from __future__ import annotations
import argparse
from verification.pipeline import run_pipeline
from config import USE_GPU
import sys


def main():
    parser = argparse.ArgumentParser(description="Face ID Verification - Milestone 1")
    parser.add_argument("--image", required=True, help="Path to input image")
    parser.add_argument("--threshold", type=float, help="Override similarity threshold")
    parser.add_argument(
        "--development-test-match",
        action="store_true",
        help="DEVELOPMENT ONLY: promote an existing real candidate for a real blockchain test",
    )
    args = parser.parse_args()

    try:
        print("========================================")
        print("FACE ID + BLOCKCHAIN VERIFICATION")
        print("========================================\n")
        print("[1/6] Loading image              ✓")
        print("[2/6] Detecting face             ...")
        result = run_pipeline(
            args.image,
            threshold=args.threshold,
            use_gpu=USE_GPU,
            development_test_mode=args.development_test_match,
        )
        print("[2/6] Detecting face             ✓")
        print("[3/6] Generating embedding       ✓")
        print("[4/6] Reverse image search       ✓")
        print("[5/6] Finding social candidates  ✓")
        print("[6/6] Comparing candidate faces  ✓\n")

        print(f"Face Detection: {'✓' if result['input_faces'] == 1 else 'FAILED'}")
        print("Reverse Image Search: ✓")
        print(f"Social Media Candidates: {result['social_candidates_count']}")

        best = result.get("best_candidate")
        if best:
            print(f"Face Similarity: {best['similarity']:.2f}")
            if best.get("matched"):
                print("Verification: VERIFIED VISUAL MATCH ✓")
            else:
                print("Verification: NO MATCH")
        else:
            print("Verification: NO MATCH")

        blockchain = result.get("blockchain", {})
        print(f"\nSHA-256: {blockchain.get('record_hash', 'not generated')}")
        print("Blockchain: Polygon Amoy")
        if blockchain.get("transaction_hash"):
            print(f"Transaction: {blockchain['transaction_hash']}")
            print(f"Block: {blockchain.get('block_number')}")
            print(f"Gas used: {blockchain.get('gas_used')}")
            marker = " ✓" if blockchain.get("status") == "CONFIRMED" else ""
            print(f"Blockchain Status: {blockchain.get('status')}{marker}")
            print(f"On-chain record verification: {'PASS' if blockchain.get('record_verified') else 'FAIL'}")
            print(f"Explorer: {blockchain.get('explorer_url')}")
        else:
            print("Transaction: not sent")
            print(f"Blockchain Status: {blockchain.get('status', 'NOT_ATTEMPTED')}")
            if blockchain.get("error"):
                print(f"Blockchain detail: {blockchain['error']}")

        print("========================================")

    except Exception as e:
        print("Error:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
