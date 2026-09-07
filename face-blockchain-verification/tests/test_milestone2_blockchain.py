from __future__ import annotations

from pathlib import Path

import pytest

import config
import verification.pipeline as pipeline
from reverse_search.social_filter import SocialMediaCandidate
from verification.hashing import hash_verification_record
from verification.models import VerificationRecord


def make_record(**changes):
    values = {
        "platform": "Instagram",
        "post_url": "https://instagram.com/p/example",
        "similarity": 0.82,
        "threshold": 0.65,
        "status": "VERIFIED_MATCH",
        "timestamp": "2026-09-07T00:00:00+00:00",
    }
    values.update(changes)
    return VerificationRecord(**values)


def test_changed_record_changes_hash():
    first = make_record()
    second = make_record(similarity=0.83)
    assert hash_verification_record(first) != hash_verification_record(second)


def test_production_mode_rejects_similarity_below_threshold():
    assert pipeline.production_match(0.64, 0.65) is False


def test_production_mode_accepts_similarity_at_threshold():
    assert pipeline.production_match(0.65, 0.65) is True


def test_development_mode_promotes_existing_real_candidate():
    candidate = SocialMediaCandidate(
        platform="Instagram",
        url="https://instagram.com/p/example",
        title="example",
        image_url="https://example.com/image.jpg",
        raw={},
    )
    result = pipeline.CandidateVerificationResult(candidate)
    result.accessible = True
    result.candidate_face_count = 1
    result.best_similarity = 0.64

    pipeline._apply_development_test_match(result, 0.65)

    assert result.matched is True
    assert result.best_similarity == 0.65


def test_missing_credentials_does_not_send_transaction(monkeypatch, tmp_path: Path):
    image = tmp_path / "input.jpg"
    image.write_bytes(b"test image")
    candidate = SocialMediaCandidate(
        platform="Instagram",
        url="https://instagram.com/p/example",
        title="example",
        image_url=None,
        raw={},
    )
    best = pipeline.CandidateVerificationResult(candidate)
    best.best_similarity = 0.82
    best.matched = True

    monkeypatch.setattr(config, "POLYGON_RPC_URL", None)
    monkeypatch.setattr(config, "WALLET_ADDRESS", None)
    monkeypatch.setattr(config, "PRIVATE_KEY", None)
    monkeypatch.setattr(config, "CONTRACT_ADDRESS", None)

    result = pipeline._anchor_verified_match(str(image), best, 0.65)

    assert result["status"] == "NOT_CONFIGURED"
    assert result["transaction_hash"] is None
    assert "POLYGON_RPC_URL" in result["error"]


def test_blockchain_failure_is_reported_without_fake_transaction(monkeypatch, tmp_path: Path):
    image = tmp_path / "input.jpg"
    image.write_bytes(b"test image")
    candidate = SocialMediaCandidate(
        platform="Instagram",
        url="https://instagram.com/p/example",
        title="example",
        image_url=None,
        raw={},
    )
    best = pipeline.CandidateVerificationResult(candidate)
    best.best_similarity = 0.82
    best.matched = True

    for name, value in {
        "POLYGON_RPC_URL": "https://rpc.example",
        "WALLET_ADDRESS": "0x0000000000000000000000000000000000000001",
        "PRIVATE_KEY": "test-private-key",
        "CONTRACT_ADDRESS": "0x0000000000000000000000000000000000000002",
    }.items():
        monkeypatch.setattr(config, name, value)

    class FailingClient:
        def __init__(self, **kwargs):
            pass

        def connect(self):
            raise ConnectionError("RPC unavailable")

    monkeypatch.setattr(pipeline, "PolygonClient", FailingClient)
    result = pipeline._anchor_verified_match(str(image), best, 0.65)

    assert result["status"] == "FAILED"
    assert result["transaction_hash"] is None
    assert result["error"] == "RPC unavailable"


def test_development_write_path_uses_real_client_boundary(monkeypatch, tmp_path: Path):
    image = tmp_path / "input.jpg"
    image.write_bytes(b"test image")
    candidate = SocialMediaCandidate(
        platform="Instagram",
        url="https://instagram.com/p/example",
        title="example",
        image_url=None,
        raw={},
    )
    best = pipeline.CandidateVerificationResult(candidate)
    best.best_similarity = 0.65
    best.matched = True

    for name, value in {
        "POLYGON_RPC_URL": "https://rpc.example",
        "WALLET_ADDRESS": "0x0000000000000000000000000000000000000001",
        "PRIVATE_KEY": "test-private-key",
        "CONTRACT_ADDRESS": "0x0000000000000000000000000000000000000002",
    }.items():
        monkeypatch.setattr(config, name, value)

    class FakeClient:
        def __init__(self, **kwargs):
            self.wallet_address = kwargs["wallet_address"]
            self.chain_id = kwargs["chain_id"]

        def connect(self):
            return self

    class FakeContract:
        def __init__(self, client, address):
            self.client = client
            self.address = address

        def store_verification(self, record_hash, post_url, platform):
            return {
                "success": True,
                "transaction_hash": "0x" + "1" * 64,
                "block_number": 123,
                "gas_used": 98765,
                "contract_address": self.address,
                "chain_id": self.client.chain_id,
                "explorer_url": "https://amoy.polygonscan.com/tx/0x" + "1" * 64,
                "error": None,
            }

        def get_verification(self, record_hash):
            return {
                "record_hash": "0x" + record_hash,
                "post_url": best.candidate.url,
                "platform": best.candidate.platform,
                "timestamp": 1,
                "exists": True,
            }

    monkeypatch.setattr(pipeline, "PolygonClient", FakeClient)
    monkeypatch.setattr(pipeline, "FaceVerificationContract", FakeContract)
    result = pipeline._anchor_verified_match(str(image), best, 0.65)

    assert result["status"] == "CONFIRMED"
    assert result["transaction_hash"].startswith("0x")
    assert result["record_verified"] is True


def test_no_match_never_calls_blockchain(monkeypatch, tmp_path: Path):
    image = tmp_path / "input.jpg"
    image.write_bytes(b"test image")
    candidate = SocialMediaCandidate(
        platform="Instagram",
        url="https://instagram.com/p/example",
        title="example",
        image_url=None,
        raw={},
    )
    best = pipeline.CandidateVerificationResult(candidate)
    best.best_similarity = 0.64
    best.matched = False

    def fail_if_called(*args, **kwargs):
        raise AssertionError("blockchain must not be called for NO MATCH")

    monkeypatch.setattr(pipeline, "PolygonClient", fail_if_called)
    monkeypatch.setattr(pipeline, "FaceVerificationContract", fail_if_called)
    result = pipeline._anchor_verified_match(str(image), best, 0.65)

    assert result == {"status": "NOT_ATTEMPTED", "reason": "No verified match"}


def test_invalid_rpc_connection():
    class DisconnectedWeb3:
        class eth:
            chain_id = 80002

        def is_connected(self):
            return False

    from blockchain.client import PolygonClient

    with pytest.raises(ConnectionError, match="Unable to connect"):
        PolygonClient(
            rpc_url="https://rpc.example",
            wallet_address=None,
            private_key=None,
            web3=DisconnectedWeb3(),
        ).connect()
