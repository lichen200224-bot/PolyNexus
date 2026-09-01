"""CP-04 WP-17/WP-18 local endpoint and routing gate tests."""
from __future__ import annotations

import asyncio
import json
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Iterator

import pytest

from polynexus_core.domain.enums import (
    AuthOwnership,
    ExecutionTarget,
    TransportKind,
)
from polynexus_core.domain.models import ContextPackage, Task
from polynexus_core.domain.runtime_binding import RuntimeBindingError, RuntimeProfile
from polynexus_core.runtime.contracts import RuntimeCapabilities
import polynexus_core.runtime.doctor as doctor_module
from polynexus_core.runtime.doctor import collect_doctor_report
from polynexus_core.runtime.local_endpoint import (
    LocalEndpointConfig,
    LocalEndpointKind,
    LocalModelEndpointAdapter,
)
from polynexus_core.runtime.registry import (
    RuntimeRegistry,
    register_local_endpoint_profile,
)
from polynexus_core.runtime.routing_policy import (
    DataClassification,
    evaluate_local_route,
)


class _ModelHandler(BaseHTTPRequestHandler):
    server_version = ""
    sys_version = ""

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path == "/v1/models":
            self._send({"data": [{"id": "local-test-model"}]})
            return
        self._send({"error": "not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path != "/v1/chat/completions":
            self._send({"error": "not found"}, status=404)
            return
        size = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(size)
        request = json.loads(body.decode("utf-8"))
        assert request["model"] == "local-test-model"
        self._send({"choices": [{"message": {"content": "local response"}}]})

    def log_message(self, *_args: object) -> None:
        return

    def _send(self, payload: dict[str, object], *, status: int = 200) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class _RedirectHandler(BaseHTTPRequestHandler):
    server_version = ""
    sys_version = ""

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        self.send_response(302)
        self.send_header("Location", "https://external.invalid/model")
        self.end_headers()

    def log_message(self, *_args: object) -> None:
        return


@contextmanager
def _local_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ModelHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


@contextmanager
def _redirect_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _RedirectHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def _config(endpoint_url: str) -> LocalEndpointConfig:
    return LocalEndpointConfig(
        endpoint_url=endpoint_url,
        model_identity="local-test-model",
        endpoint_kind=LocalEndpointKind.OPENAI_COMPATIBLE,
        timeout_seconds=3,
        classification=DataClassification.CONFIDENTIAL,
    )


@pytest.mark.parametrize(
    "endpoint_url",
    [
        "https://example.invalid/v1",
        "http://127.0.0.1:8080/v1?api_key=do-not-echo",
        "http://user:password@127.0.0.1:8080/v1",
    ],
)
def test_external_or_credentialed_endpoint_fails_closed_without_echo(endpoint_url: str) -> None:
    with pytest.raises(RuntimeBindingError) as exc_info:
        LocalModelEndpointAdapter(_config(endpoint_url))
    assert endpoint_url not in str(exc_info.value)
    assert "do-not-echo" not in str(exc_info.value)


def test_local_endpoint_rejects_external_redirect_without_following_it() -> None:
    async def run() -> tuple[bool, object]:
        with _redirect_server() as endpoint_url:
            adapter = LocalModelEndpointAdapter(_config(endpoint_url))
            return await adapter.health(), adapter.route_evidence()

    healthy, evidence = asyncio.run(run())
    assert healthy is False
    assert evidence.safe_error == "local_endpoint_request_failed"
    assert "external.invalid" not in json.dumps(evidence.as_dict())


def test_route_requires_classification_and_capability_compatibility() -> None:
    capabilities = RuntimeCapabilities(timeout_cleanup_verified=False)
    with pytest.raises(RuntimeBindingError, match="classification"):
        evaluate_local_route(
            classification=None,
            endpoint_url="http://127.0.0.1:8080",
            model_identity="local-test-model",
            timeout_seconds=3,
            capabilities=capabilities,
        )
    with pytest.raises(RuntimeBindingError, match="capability"):
        evaluate_local_route(
            classification=DataClassification.RESTRICTED,
            endpoint_url="http://127.0.0.1:8080",
            model_identity="local-test-model",
            timeout_seconds=3,
            capabilities=capabilities,
            required_capabilities=("timeout_cleanup_verified",),
        )

    decision = evaluate_local_route(
        classification="confidential",
        endpoint_url="http://127.0.0.1:8080",
        model_identity="local-test-model",
        timeout_seconds=3,
        capabilities=capabilities,
    )
    assert decision.classification is DataClassification.CONFIDENTIAL
    assert decision.endpoint_identity == "loopback"
    assert decision.route == "LOCAL_ONLY"
    assert decision.timeout_seconds == 3


def test_local_endpoint_lifecycle_is_normalized_and_evidence_is_safe() -> None:
    async def run() -> tuple[LocalModelEndpointAdapter, str, str, str]:
        with _local_server() as endpoint_url:
            adapter = LocalModelEndpointAdapter(_config(endpoint_url))
            assert await adapter.health() is True
            assert await adapter.readiness() is True
            context = ContextPackage(project_id="project_test", version=1)
            task = Task(
                project_id="project_test",
                title="Test local route",
                workflow_id="workflow_test",
                workflow_version=1,
            )
            runtime_ref = await adapter.create_run(context)
            await adapter.submit(runtime_ref, task)
            status = await adapter.status(runtime_ref)
            result = await adapter.result(runtime_ref)
            return adapter, runtime_ref, status.state.value, result.summary

    adapter, runtime_ref, state, summary = asyncio.run(run())
    assert state == "COMPLETED"
    assert summary == "local response"
    evidence = adapter.route_evidence()
    assert evidence.endpoint_identity == "loopback"
    assert evidence.model_identity == "local-test-model"
    assert evidence.route == "LOCAL_ONLY"
    assert evidence.timeout_seconds == 3
    assert evidence.safe_error is None
    assert "127.0.0.1" not in json.dumps(evidence.as_dict())
    assert adapter.version_info() == "local-model-endpoint/openai_compatible/1"
    assert awaitable_false(adapter, runtime_ref) is False


def awaitable_false(adapter: LocalModelEndpointAdapter, runtime_ref: str) -> bool:
    async def check() -> bool:
        assert adapter.capabilities().cancel is False
        assert await adapter.cleanup(runtime_ref) is False
        return adapter.capabilities().timeout_cleanup_verified

    return asyncio.run(check())


def test_ollama_profile_uses_same_local_policy_without_fallback() -> None:
    config = LocalEndpointConfig(
        endpoint_url="http://127.0.0.1:11434",
        model_identity="local-test-model",
        endpoint_kind=LocalEndpointKind.OLLAMA,
    )
    adapter = LocalModelEndpointAdapter(config)
    assert adapter.version_info() == "local-model-endpoint/ollama/1"
    assert adapter.route_evidence().route == "LOCAL_ONLY"


def test_local_profile_requires_explicit_registration_and_preserves_default() -> None:
    registry = RuntimeRegistry()
    profile = RuntimeProfile(
        provider_id="local",
        transport_kind=TransportKind.LOCAL,
        runtime_id="local-model",
        adapter_id="local.endpoint",
        execution_target=ExecutionTarget.LOCAL,
        runtime_profile_ref="local.test",
        auth_ownership=AuthOwnership.NONE,
    )
    register_local_endpoint_profile(registry, profile, lambda: object())  # type: ignore[arg-type]
    assert registry._resolve_selected_profile(explicit_request="local.test") == profile
    with pytest.raises(RuntimeBindingError, match="Unknown or unavailable"):
        registry._resolve_selected_profile(explicit_request="cloud.test")


def test_doctor_reports_current_safe_local_route_facts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(doctor_module, "schema_head_status", lambda: True)

    async def run() -> object:
        with _local_server() as endpoint_url:
            registry = RuntimeRegistry()
            profile = RuntimeProfile(
                provider_id="local",
                transport_kind=TransportKind.LOCAL,
                runtime_id="local-model",
                adapter_id="local.endpoint",
                execution_target=ExecutionTarget.LOCAL,
                runtime_profile_ref="local.test",
                auth_ownership=AuthOwnership.NONE,
            )
            register_local_endpoint_profile(
                registry,
                profile,
                lambda: LocalModelEndpointAdapter(_config(endpoint_url)),
            )
            return await collect_doctor_report(
                registry,
                explicit_request="local.test",
                exact_commit="a" * 40,
                current_commit="a" * 40,
            )

    report = asyncio.run(run())
    claims = {claim.name: claim.value for claim in report.claims}
    assert claims["route.endpoint"] == "loopback"
    assert claims["route.model"] == "local-test-model"
    assert claims["route.policy"] == "LOCAL_ONLY"
    assert claims["route.timeout_seconds"] == 3
    assert report.freshness.value == "CURRENT"
    serialized = json.dumps(report.as_dict(), sort_keys=True)
    assert "127.0.0.1" not in serialized
