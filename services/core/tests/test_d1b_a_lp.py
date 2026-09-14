from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from polynexus_core.api import dependencies
from polynexus_core.app import create_app
from polynexus_core.domain.d1b import capture_mapping
from polynexus_core.persistence.d1b import D1bRepository, HumanProtocolError
from polynexus_core.persistence.models import HumanDecisionEventRow, HumanTrustKeyRow
from polynexus_core.security.a_lp import (
    _P256_G,
    _P256_N,
    _p256_mul,
    b64u_encode,
)
from polynexus_core.storage.content import ContentStore


ORIGIN = "http://127.0.0.1:5173"
RP_ID = "127.0.0.1"
INSTALLATION_ID = "sha256:" + "a" * 64


def _upgrade(path: Path) -> None:
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
    config.set_main_option("sqlalchemy.url", "sqlite:///" + path.as_posix())
    command.upgrade(config, "head")


def _cbor_length(major: int, length: int) -> bytes:
    if length < 24:
        return bytes([(major << 5) | length])
    if length <= 0xFF:
        return bytes([(major << 5) | 24, length])
    if length <= 0xFFFF:
        return bytes([(major << 5) | 25]) + length.to_bytes(2, "big")
    raise AssertionError("test_cbor_value_too_large")


def _cbor(value: object) -> bytes:
    if value is False:
        return b"\xf4"
    if value is True:
        return b"\xf5"
    if value is None:
        return b"\xf6"
    if isinstance(value, int):
        if value >= 0:
            return _cbor_length(0, value)
        return _cbor_length(1, -1 - value)
    if isinstance(value, bytes):
        return _cbor_length(2, len(value)) + value
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return _cbor_length(3, len(encoded)) + encoded
    if isinstance(value, dict):
        return _cbor_length(5, len(value)) + b"".join(
            _cbor(key) + _cbor(item) for key, item in value.items()
        )
    raise AssertionError(f"test_cbor_type:{type(value)!r}")


def _der_integer(value: int) -> bytes:
    raw = value.to_bytes((value.bit_length() + 7) // 8 or 1, "big")
    if raw[0] & 0x80:
        raw = b"\x00" + raw
    return b"\x02" + bytes([len(raw)]) + raw


def _der_signature(r: int, s: int) -> bytes:
    body = _der_integer(r) + _der_integer(s)
    return b"\x30" + bytes([len(body)]) + body


def _key_material(private: int = 0x123456789ABCDEF123456789ABCDEF123456789ABCDEF123456789ABCDEF) -> tuple[int, bytes]:
    point = _p256_mul(_P256_G, private)
    assert point is not None
    public = b"\x04" + point[0].to_bytes(32, "big") + point[1].to_bytes(32, "big")
    return private, public


def _sign(private: int, message: bytes, nonce: int) -> bytes:
    digest = int.from_bytes(hashlib.sha256(message).digest(), "big")
    point = _p256_mul(_P256_G, nonce)
    assert point is not None
    r = point[0] % _P256_N
    s = ((digest + r * private) * pow(nonce, _P256_N - 2, _P256_N)) % _P256_N
    if s > _P256_N // 2:
        s = _P256_N - s
    return _der_signature(r, s)


def _client_data(kind: str, challenge: bytes, *, origin: str = ORIGIN) -> bytes:
    return json.dumps(
        {
            "challenge": b64u_encode(challenge),
            "origin": origin,
            "type": kind,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _credential(
    credential_id: bytes,
    *,
    client_data: bytes,
    authenticator_data: bytes,
    attestation_object: bytes | None = None,
    signature: bytes | None = None,
    browser_aliases: bool = False,
) -> dict[str, object]:
    response: dict[str, object] = {
        "clientDataJSON" if browser_aliases else "client_data_json": b64u_encode(client_data),
    }
    if attestation_object is not None:
        response["attestationObject" if browser_aliases else "attestation_object"] = b64u_encode(attestation_object)
    if authenticator_data:
        response["authenticatorData" if browser_aliases else "authenticator_data"] = b64u_encode(authenticator_data)
    if signature is not None:
        response["signature"] = b64u_encode(signature)
    response["userHandle" if browser_aliases else "user_handle"] = None
    return {
        "id": b64u_encode(credential_id),
        "rawId" if browser_aliases else "raw_id": b64u_encode(credential_id),
        "type": "public-key",
        "response": response,
    }


def _registration_credential(
    challenge: bytes,
    private: int,
    public: bytes,
    credential_id: bytes,
    *,
    browser_aliases: bool = False,
    origin: str = ORIGIN,
    rp_id: str = RP_ID,
) -> dict[str, object]:
    cose_key = {
        1: 2,
        3: -7,
        -1: 1,
        -2: public[1:33],
        -3: public[33:],
    }
    authenticator_data = (
        hashlib.sha256(rp_id.encode("utf-8")).digest()
        + b"\x45"
        + b"\x00\x00\x00\x00"
        + b"\x00" * 16
        + len(credential_id).to_bytes(2, "big")
        + credential_id
        + _cbor(cose_key)
    )
    attestation = _cbor({"fmt": "none", "authData": authenticator_data, "attStmt": {}})
    return _credential(
        credential_id,
        client_data=_client_data("webauthn.create", challenge, origin=origin),
        authenticator_data=b"",
        attestation_object=attestation,
        browser_aliases=browser_aliases,
    )


def _assertion_credential(
    challenge: bytes,
    private: int,
    credential_id: bytes,
    counter: int,
    *,
    browser_aliases: bool = False,
    origin: str = ORIGIN,
    rp_id: str = RP_ID,
    signature_nonce: int = 11,
) -> dict[str, object]:
    authenticator_data = (
        hashlib.sha256(rp_id.encode("utf-8")).digest()
        + b"\x05"
        + counter.to_bytes(4, "big")
    )
    client_data = _client_data("webauthn.get", challenge, origin=origin)
    signature = _sign(
        private,
        authenticator_data + hashlib.sha256(client_data).digest(),
        signature_nonce,
    )
    return _credential(
        credential_id,
        client_data=client_data,
        authenticator_data=authenticator_data,
        signature=signature,
        browser_aliases=browser_aliases,
    )


@pytest.fixture()
def local_alp_db(tmp_path, monkeypatch):
    monkeypatch.delenv("POLYNEXUS_D1B_TEST_MODE", raising=False)
    monkeypatch.setenv("POLYNEXUS_ENVIRONMENT", "LOCAL")
    monkeypatch.setenv("POLYNEXUS_HUMAN_A_LP_ENABLED", "1")
    monkeypatch.setenv("POLYNEXUS_UI_ORIGIN", ORIGIN)
    monkeypatch.setenv("POLYNEXUS_WEBAUTHN_RP_ID", RP_ID)
    monkeypatch.setenv("POLYNEXUS_INSTALLATION_ID", INSTALLATION_ID)
    database = tmp_path / "a-lp.db"
    _upgrade(database)
    engine = create_engine("sqlite:///" + database.as_posix(), future=True)
    with Session(engine) as session:
        yield session, ContentStore(tmp_path / "content"), database
    engine.dispose()


def test_local_a_lp_registration_pairing_session_rotation_and_revoke(local_alp_db, monkeypatch):
    session, store, _database = local_alp_db
    repo = D1bRepository(session, store)
    now = datetime(2026, 9, 14, 2, 0, tzinfo=timezone.utc)
    private, public = _key_material()
    credential_id = b"credential-for-a-lp"

    registration_challenge = repo.issue_enrollment_challenge(ceremony="registration", now=now)
    delayed_registration = repo.issue_enrollment_challenge(ceremony="registration", now=now)
    assert registration_challenge["principal_ref"].startswith("human:")
    assert registration_challenge["allow_credentials"] == []
    registered = repo.register_webauthn_credential(
        challenge_id=registration_challenge["challenge_id"],
        credential=_registration_credential(
            base64.urlsafe_b64decode(registration_challenge["challenge"] + "=="),
            private,
            public,
            credential_id,
        ),
        now=now,
    )
    key_id = registered["key_id"]
    key = session.get(HumanTrustKeyRow, key_id)
    assert key is not None
    assert key.public_key == b64u_encode(public)
    assert private.to_bytes(32, "big") not in key.public_key.encode("ascii")
    with pytest.raises(HumanProtocolError, match="enrollment_rotation_required"):
        repo.register_webauthn_credential(
            challenge_id=delayed_registration["challenge_id"],
            credential=_registration_credential(
                base64.urlsafe_b64decode(delayed_registration["challenge"] + "=="),
                private,
                public,
                b"delayed-bootstrap-credential",
            ),
            now=now,
        )

    authentication_challenge = repo.issue_enrollment_challenge(ceremony="authentication", now=now)
    authentication_bytes = base64.urlsafe_b64decode(authentication_challenge["challenge"] + "==")
    pairing = repo.create_webauthn_pairing(
        challenge_id=authentication_challenge["challenge_id"],
        credential=_assertion_credential(authentication_bytes, private, credential_id, 1),
        expires_at=now + timedelta(hours=1),
        now=now,
    )
    assert pairing["auth_method"] == "d11-a-lp-webauthn"
    assert pairing["key_id"] == key_id
    pairing_token = pairing["pairing_token"]
    assert pairing_token not in session.get(HumanTrustKeyRow, key_id).public_key
    human_session = repo.create_session(
        grant_id=pairing["grant_id"],
        pairing_proof=pairing_token,
        audience="candidate-review",
        csrf_token="csrf-secret",
        now=now,
    )
    assert human_session["principal_ref"] == registered["principal_ref"]

    with pytest.raises(HumanProtocolError, match="enrollment_challenge_replayed"):
        repo.create_webauthn_pairing(
            challenge_id=authentication_challenge["challenge_id"],
            credential=_assertion_credential(authentication_bytes, private, credential_id, 1),
            expires_at=now + timedelta(hours=1),
            now=now,
        )

    tampered_challenge = repo.issue_enrollment_challenge(ceremony="authentication", now=now)
    tampered_bytes = base64.urlsafe_b64decode(tampered_challenge["challenge"] + "==")
    tampered = _assertion_credential(tampered_bytes, private, credential_id, 2)
    tampered["response"]["signature"] = b64u_encode(b"bad-signature")
    with pytest.raises(HumanProtocolError, match="ecdsa_signature_invalid"):
        repo.create_webauthn_pairing(
            challenge_id=tampered_challenge["challenge_id"],
            credential=tampered,
            expires_at=now + timedelta(hours=1),
            now=now,
        )
    valid_pairing = repo.create_webauthn_pairing(
        challenge_id=tampered_challenge["challenge_id"],
        credential=_assertion_credential(tampered_bytes, private, credential_id, 2),
        expires_at=now + timedelta(hours=1),
        now=now,
    )
    assert valid_pairing["grant_id"] != pairing["grant_id"]

    rotation_challenge = repo.issue_enrollment_challenge(
        ceremony="registration",
        key_id=key_id,
        session_id=human_session["session_id"],
        csrf_token="csrf-secret",
        now=now,
    )
    private_two, public_two = _key_material(0x23456789ABCDEF123456789ABCDEF123456789ABCDEF123456789ABCDEF1)
    credential_id_two = b"credential-for-rotation"
    rotated = repo.register_webauthn_credential(
        challenge_id=rotation_challenge["challenge_id"],
        credential=_registration_credential(
            base64.urlsafe_b64decode(rotation_challenge["challenge"] + "=="),
            private_two,
            public_two,
            credential_id_two,
        ),
        now=now,
    )
    assert rotated["principal_ref"] == registered["principal_ref"]
    assert session.get(HumanTrustKeyRow, key_id).status == "RETIRING"

    rotated_authentication = repo.issue_enrollment_challenge(
        ceremony="authentication",
        key_id=rotated["key_id"],
        now=now,
    )
    rotated_pairing = repo.create_webauthn_pairing(
        challenge_id=rotated_authentication["challenge_id"],
        credential=_assertion_credential(
            base64.urlsafe_b64decode(rotated_authentication["challenge"] + "=="),
            private_two,
            credential_id_two,
            1,
        ),
        expires_at=now + timedelta(hours=1),
        now=now,
    )
    rotated_session = repo.create_session(
        grant_id=rotated_pairing["grant_id"],
        pairing_proof=rotated_pairing["pairing_token"],
        audience="candidate-review",
        csrf_token="rotated-csrf",
        now=now,
    )

    # Exercise the complete v2 pairing -> session -> exact-view challenge ->
    # nonce-bound decision path against a candidate with no verification
    # requirement. The candidate fixture is isolated to TEST mode; the Human
    # session and its WebAuthn trust binding remain the code under test.
    monkeypatch.setenv("POLYNEXUS_D1B_TEST_MODE", "1")
    monkeypatch.setenv("POLYNEXUS_ENVIRONMENT", "TEST")
    requirements = capture_mapping({"requirements.txt": b"requirements-v1"})
    validation = capture_mapping({
        "validation.json": json.dumps(
            {
                "assurance": {"mode": "FLEXIBLE"},
                "checks": [{"applicability": "APPLICABLE", "check_id": "flow", "requiredness": "REQUIRED"}],
                "format": "pn.validation-contract.v1",
                "revision": 1,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode(),
    })
    repo.save_snapshot(requirements)
    repo.save_snapshot(validation)
    published = repo.publish_candidate(
        baseline=capture_mapping({"app.py": b"before\n"}),
        result=capture_mapping({"app.py": b"after\n"}),
        requirements_snapshot_id=requirements.manifest.snapshot_id,
        validation_contract_snapshot_id=validation.manifest.snapshot_id,
        lineage_ref="a-lp-flow",
    )
    decision_challenge = repo.issue_challenge(
        session_id=rotated_session["session_id"],
        candidate_id=published["candidate_id"],
        action="Reject",
        now=now,
    )
    decision_receipt = repo.submit_decision(
        session_id=rotated_session["session_id"],
        challenge_id=decision_challenge["challenge_id"],
        nonce=decision_challenge["nonce"],
        action="Reject",
        candidate_id=published["candidate_id"],
        view_digest=decision_challenge["view_digest"],
        csrf_token="rotated-csrf",
        origin=ORIGIN,
        expected_origin=ORIGIN,
        command_id="a-lp-decision-flow",
        reason="explicit test rejection",
        now=now,
    )
    assert decision_receipt["disposition"] == "REJECTED"
    decision_row = session.get(HumanDecisionEventRow, decision_receipt["decision_id"])
    assert decision_row is not None
    assert decision_row.auth_method == "d11-a-lp-webauthn"
    protocol_evidence = json.loads(decision_row.protocol_evidence_json)
    assert protocol_evidence["key_id"] == rotated["key_id"]
    assert protocol_evidence["enrollment_challenge_id"] == rotated_pairing["enrollment_challenge_id"]
    monkeypatch.setenv("POLYNEXUS_ENVIRONMENT", "LOCAL")
    monkeypatch.delenv("POLYNEXUS_D1B_TEST_MODE", raising=False)
    monkeypatch.delenv("POLYNEXUS_HUMAN_TEST_MODE", raising=False)

    with pytest.raises(HumanProtocolError, match="enrollment_fixture_only"):
        repo.create_pairing(
            principal_ref="human:fixture",
            enrollment_proof="hmac-proof",
            expires_at=now + timedelta(hours=1),
        )

    revoke_rotated_challenge = repo.issue_enrollment_challenge(
        ceremony="revocation",
        key_id=rotated["key_id"],
        session_id=rotated_session["session_id"],
        csrf_token="rotated-csrf",
        now=now,
    )
    revoked_rotated = repo.revoke_webauthn_key(
        challenge_id=revoke_rotated_challenge["challenge_id"],
        key_id=rotated["key_id"],
        credential=_assertion_credential(
            base64.urlsafe_b64decode(revoke_rotated_challenge["challenge"] + "=="),
            private_two,
            credential_id_two,
            2,
        ),
        now=now,
    )
    assert revoked_rotated["status"] == "REVOKED"

    revoke_challenge = repo.issue_enrollment_challenge(
        ceremony="revocation",
        key_id=key_id,
        session_id=human_session["session_id"],
        csrf_token="csrf-secret",
        now=now,
    )
    revoked = repo.revoke_webauthn_key(
        challenge_id=revoke_challenge["challenge_id"],
        key_id=key_id,
        credential=_assertion_credential(
            base64.urlsafe_b64decode(revoke_challenge["challenge"] + "=="),
            private,
            credential_id,
            3,
        ),
        now=now,
    )
    assert revoked["status"] == "REVOKED"
    with pytest.raises(HumanProtocolError, match="human_enrollment_required"):
        repo.issue_enrollment_challenge(ceremony="authentication", now=now)
    with pytest.raises(HumanProtocolError, match="session_invalid|pairing_invalid|human_key_unavailable"):
        repo.issue_challenge(
            session_id=human_session["session_id"],
            candidate_id="candidate-not-reached",
            action="Reject",
            now=now,
        )


def test_local_a_lp_api_uses_browser_aliases_and_rejects_hmac_fixture(monkeypatch, tmp_path):
    database = tmp_path / "a-lp-api.db"
    _upgrade(database)
    monkeypatch.setenv("POLYNEXUS_DATABASE_URL", "sqlite:///" + database.as_posix())
    monkeypatch.setenv("POLYNEXUS_CONTENT_ROOT", str(tmp_path / "content"))
    monkeypatch.delenv("POLYNEXUS_D1B_TEST_MODE", raising=False)
    monkeypatch.setenv("POLYNEXUS_ENVIRONMENT", "LOCAL")
    monkeypatch.setenv("POLYNEXUS_HUMAN_A_LP_ENABLED", "1")
    monkeypatch.setenv("POLYNEXUS_UI_ORIGIN", ORIGIN)
    monkeypatch.setenv("POLYNEXUS_WEBAUTHN_RP_ID", RP_ID)
    monkeypatch.setenv("POLYNEXUS_INSTALLATION_ID", INSTALLATION_ID)
    monkeypatch.setattr(dependencies, "_LOOPBACK_TOKEN", "a-lp-api-token")
    private, public = _key_material()
    credential_id = b"credential-for-api"
    headers = {"X-Loopback-Token": "a-lp-api-token", "Origin": ORIGIN}

    with TestClient(create_app(), client=("127.0.0.1", 50200)) as client:
        missing_origin = client.post(
            "/api/v1/human/enrollment/challenges",
            headers={"X-Loopback-Token": "a-lp-api-token"},
            json={"ceremony": "registration"},
        )
        assert missing_origin.status_code == 409
        assert missing_origin.json()["detail"] == "origin_rejected"

        registration = client.post(
            "/api/v1/human/enrollment/challenges",
            headers=headers,
            json={"ceremony": "registration"},
        )
        assert registration.status_code == 201, registration.text
        registration_value = registration.json()
        registration_bytes = base64.urlsafe_b64decode(registration_value["challenge"] + "==")
        credential = _registration_credential(
            registration_bytes,
            private,
            public,
            credential_id,
            browser_aliases=True,
        )
        registered = client.post(
            "/api/v1/human/enrollment/credentials",
            headers=headers,
            json={"challenge_id": registration_value["challenge_id"], "credential": credential},
        )
        assert registered.status_code == 201, registered.text

        authentication = client.post(
            "/api/v1/human/enrollment/challenges",
            headers=headers,
            json={"ceremony": "authentication"},
        )
        assert authentication.status_code == 201, authentication.text
        authentication_value = authentication.json()
        pairing = client.post(
            "/api/v1/human/pairings",
            headers=headers,
            json={
                "challenge_id": authentication_value["challenge_id"],
                "credential": _assertion_credential(
                    base64.urlsafe_b64decode(authentication_value["challenge"] + "=="),
                    private,
                    credential_id,
                    1,
                    browser_aliases=True,
                ),
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            },
        )
        assert pairing.status_code == 201, pairing.text
        pairing_value = pairing.json()
        created_session = client.post(
            "/api/v1/human/sessions",
            headers=headers,
            json={
                "grant_id": pairing_value["grant_id"],
                "pairing_token": pairing_value["pairing_token"],
                "audience": "candidate-review",
                "csrf_token": "api-csrf",
            },
        )
        assert created_session.status_code == 201, created_session.text

        hmac_fixture = client.post(
            "/api/v1/human/pairings",
            headers=headers,
            json={
                "principal_ref": "human:forbidden-fixture",
                "enrollment_proof": "hmac-proof",
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            },
        )
        assert hmac_fixture.status_code == 403
        assert hmac_fixture.json()["detail"] == "d1b_fixture_route_disabled"

    with Session(create_engine("sqlite:///" + database.as_posix(), future=True)) as session:
        key = session.query(HumanTrustKeyRow).one()
        assert key.public_key == b64u_encode(public)
        assert session.execute(text("SELECT COUNT(*) FROM human_pairing_grants")).scalar_one() == 1
        assert session.execute(text("SELECT COUNT(*) FROM human_sessions")).scalar_one() == 1
