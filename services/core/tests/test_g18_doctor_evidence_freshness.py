import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from alembic import command as alembic_cmd
from alembic.config import Config
import pytest

from polynexus_core.runtime import doctor
from polynexus_core.persistence import database
from polynexus_core.runtime.doctor import (
    DoctorClaim,
    DoctorReport,
    EvidenceFreshness,
    EvidenceProvenance,
    MaturityState,
    collect_doctor_report,
)
from polynexus_core.runtime.registry import build_default_registry


NOW = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
CURRENT_COMMIT = "a" * 40


def _collect(**kwargs):
    kwargs.setdefault("generated_at", NOW)
    kwargs.setdefault("now", NOW)
    return asyncio.run(
        collect_doctor_report(
            build_default_registry(),
            exact_commit=CURRENT_COMMIT,
            **kwargs,
        )
    )


def test_current_report_contains_bounded_source_bound_claims(monkeypatch) -> None:
    monkeypatch.setattr(doctor, "schema_head_status", lambda: True)

    report = _collect()
    payload = report.as_dict()
    names = {claim["name"] for claim in payload["claims"]}

    assert report.freshness is EvidenceFreshness.CURRENT
    assert report.maturity is MaturityState.PREVIEW
    assert {"adapter_version", "health", "readiness", "schema_head"} <= names
    assert len(payload["claims"]) <= doctor.MAX_CLAIMS
    for claim in payload["claims"]:
        evidence = claim["evidence"]
        assert evidence["source"]
        assert evidence["exact_commit"] == CURRENT_COMMIT
        assert evidence["generated_at"].endswith("Z")
        assert evidence["command"] in {doctor.DOCTOR_COMMAND, doctor.SCHEMA_COMMAND}
        assert evidence["exit_code"] == 0
        assert evidence["freshness"] == EvidenceFreshness.CURRENT.value
        assert claim["maturity"] not in {"CERTIFIED", "SUPPORTED"}
    serialized = json.dumps(payload, sort_keys=True)
    assert "exception" not in serialized.lower()
    assert "reference.local" in serialized


def test_stale_evidence_cannot_produce_current_or_certified_maturity(monkeypatch) -> None:
    monkeypatch.setattr(doctor, "schema_head_status", lambda: True)

    report = _collect(generated_at=NOW - timedelta(hours=1), now=NOW)

    assert report.freshness is EvidenceFreshness.UNVERIFIED
    assert report.maturity is MaturityState.UNVERIFIED
    assert all(
        claim.evidence.freshness is EvidenceFreshness.STALE
        for claim in report.claims
        if claim.name != "schema_head"
    )


def test_historical_or_invalid_provenance_is_fail_closed_without_echo(monkeypatch) -> None:
    monkeypatch.setattr(doctor, "schema_head_status", lambda: True)
    historical = asyncio.run(
        collect_doctor_report(
            build_default_registry(),
            exact_commit="b" * 40,
            current_commit=CURRENT_COMMIT,
            generated_at=NOW,
            now=NOW,
        )
    )
    invalid = asyncio.run(
        collect_doctor_report(
            build_default_registry(),
            exact_commit=r"C:\private\secret-token",
            explicit_request="authorization.token",
            generated_at=NOW,
            now=NOW,
        )
    )

    assert historical.freshness is EvidenceFreshness.UNVERIFIED
    assert historical.maturity is MaturityState.UNVERIFIED
    assert all(
        claim.evidence.freshness is EvidenceFreshness.HISTORICAL
        for claim in historical.claims
        if claim.name != "schema_head"
    )
    invalid_text = json.dumps(invalid.as_dict(), sort_keys=True)
    assert invalid.freshness is EvidenceFreshness.UNVERIFIED
    assert invalid.maturity is MaturityState.UNVERIFIED
    assert r"C:\private\secret-token" not in invalid_text
    assert "authorization.token" not in invalid_text
    assert "secret" not in invalid_text.lower()


def test_unknown_profile_does_not_fallback_to_reference(monkeypatch) -> None:
    monkeypatch.setattr(doctor, "schema_head_status", lambda: True)

    report = _collect(explicit_request="missing.profile")
    payload = report.as_dict()
    serialized = json.dumps(payload, sort_keys=True)

    assert report.freshness is EvidenceFreshness.UNVERIFIED
    assert report.maturity is MaturityState.UNVERIFIED
    assert "reference.local" not in serialized
    profile_claim = next(claim for claim in report.claims if claim.name == "runtime_profile")
    assert profile_claim.value is None
    assert profile_claim.evidence.exit_code == 1


def test_doctor_rejects_self_asserted_certification() -> None:
    evidence = EvidenceProvenance(
        source="runtime.adapter",
        exact_commit=CURRENT_COMMIT,
        generated_at=NOW,
        command="runtime-doctor",
        exit_code=0,
        freshness=EvidenceFreshness.CURRENT,
    )
    with pytest.raises(ValueError):
        DoctorClaim(
            name="runtime",
            value="reference",
            maturity=MaturityState.CERTIFIED,
            evidence=evidence,
        )
    with pytest.raises(ValueError):
        DoctorReport(
            generated_at=NOW,
            freshness=EvidenceFreshness.CURRENT,
            maturity=MaturityState.SUPPORTED,
            claims=(),
        )


def test_schema_head_status_is_safe_boolean_probe(monkeypatch) -> None:
    monkeypatch.setattr(database, "verify_schema_head", lambda: None)
    assert database.schema_head_status() is True

    def fail_schema_check() -> None:
        raise RuntimeError("database path and driver details must not escape")

    monkeypatch.setattr(database, "verify_schema_head", fail_schema_check)
    assert database.schema_head_status() is False


def test_schema_head_status_uses_real_alembic_head(tmp_path) -> None:
    db_path = tmp_path / "doctor-schema.db"
    config = Config()
    config.set_main_option(
        "script_location", str(Path(__file__).parent.parent / "alembic")
    )
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    alembic_cmd.upgrade(config, "head")

    database.init_engine(f"sqlite:///{db_path}")
    try:
        assert database.schema_head_status() is True
    finally:
        database.dispose_engine()
