from blockchain.record import VerificationRecord, verification_record_hash


def test_verification_record_hash_is_deterministic():
    record = VerificationRecord(
        image_sha256="a" * 64,
        matched=True,
        similarity=0.91,
        threshold=0.65,
        candidate_url="https://example.com/profile",
        created_at="2026-09-07T00:00:00+00:00",
    )
    assert verification_record_hash(record) == verification_record_hash(record.model_dump())
    assert len(verification_record_hash(record)) == 64


def test_verification_record_rejects_invalid_similarity():
    try:
        VerificationRecord(
            image_sha256="a" * 64,
            matched=False,
            similarity=1.1,
            threshold=0.65,
        )
    except ValueError:
        return
    raise AssertionError("invalid similarity should be rejected")
