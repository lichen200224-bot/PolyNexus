"""CP06 WP29 deterministic security, policy, egress, and provenance checks."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

import pytest

from polynexus_core.domain.enums import ResumeMode, RunState
from polynexus_core.domain.runtime_binding import RuntimeBindingError
from polynexus_core.runtime import doctor
from polynexus_core.runtime.contracts import RuntimeCapabilities
from polynexus_core.runtime.doctor import EvidenceFreshness, MaturityState, collect_doctor_report
from polynexus_core.runtime.local_endpoint import LocalEndpointConfig, LocalModelEndpointAdapter
from polynexus_core.runtime.registry import build_default_registry
from polynexus_core.runtime.routing_policy import (
    DataClassification,
    evaluate_local_route,
)


NOW = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
CURRENT_COMMIT = "c" * 40


def test_current_doctor_evidence_is_bounded_and_source_bound(monkeypatch) -> None:
    monkeypatch.setattr(doctor, "schema_head_status", lambda: True)
    report = asyncio.run(
        collect_doctor_report(
            build_default_registry(),
            exact_commit=CURRENT_COMMIT,
            current_commit=CURRENT_COMMIT,
            generated_at=NOW,
            now=NOW,
            exit_code=0,
        )
    )

    payload = report.as_dict()
    assert report.freshness is EvidenceFreshness.CURRENT
    assert report.maturity is MaturityState.PREVIEW
    assert len(payload["claims"]) <= doctor.MAX_CLAIMS
    for claim in payload["claims"]:
        evidence = claim["evidence"]
        assert evidence["source"]
        assert evidence["exact_commit"] == CURRENT_COMMIT
        assert evidence["generated_at"].endswith("Z")
        assert evidence["command"] in {doctor.DOCTOR_COMMAND, doctor.SCHEMA_COMMAND}
        assert evidence["exit_code"] == 0
        assert evidence["freshness"] == EvidenceFreshness.CURRENT.value
    serialized = json.dumps(payload, sort_keys=True).lower()
    assert "authorization" not in serialized
    assert "bearer" not in serialized
    assert "cookie" not in serialized
    assert "secret" not in serialized
    assert "token" not in serialized
    assert "exception" not in serialized


@pytest.mark.parametrize(
    "endpoint_url",
    (
        "https://external.invalid/model",
        "http://127.0.0.1:8080/v1?credential=fixture-only",
    ),
)
def test_external_or_credentialed_endpoint_fails_before_egress(endpoint_url: str) -> None:
    with pytest.raises(RuntimeBindingError) as exc_info:
        LocalModelEndpointAdapter(
            LocalEndpointConfig(
                endpoint_url=endpoint_url,
                model_identity="local-test-model",
            )
        )

    assert str(exc_info.value) == "Local endpoint policy rejected the endpoint"
    assert endpoint_url not in str(exc_info.value)


def test_policy_and_capability_mismatch_fail_closed_without_downgrade() -> None:
    with pytest.raises(RuntimeBindingError) as classification_error:
        evaluate_local_route(
            classification="UNKNOWN",
            endpoint_url="http://127.0.0.1:8080",
            model_identity="local-test-model",
            timeout_seconds=3,
            capabilities=RuntimeCapabilities(),
        )
    assert str(classification_error.value) == "Runtime route classification is unsupported"

    with pytest.raises(RuntimeBindingError) as capability_error:
        evaluate_local_route(
            classification=DataClassification.CONFIDENTIAL,
            endpoint_url="http://127.0.0.1:8080",
            model_identity="local-test-model",
            timeout_seconds=3,
            capabilities=RuntimeCapabilities(resume=ResumeMode.NONE),
            required_capabilities=("resume",),
        )
    assert str(capability_error.value) == "Runtime route capability compatibility check failed"


def test_historical_or_failed_evidence_never_becomes_supported() -> None:
    report = asyncio.run(
        collect_doctor_report(
            build_default_registry(),
            exact_commit="d" * 40,
            current_commit=CURRENT_COMMIT,
            generated_at=NOW,
            now=NOW,
            exit_code=1,
        )
    )

    assert report.freshness is EvidenceFreshness.UNVERIFIED
    assert report.maturity is MaturityState.UNVERIFIED
    assert all(
        claim.maturity not in {MaturityState.CERTIFIED, MaturityState.SUPPORTED}
        for claim in report.claims
    )
    assert all(
        claim.evidence.freshness is EvidenceFreshness.UNVERIFIED
        for claim in report.claims
    )
