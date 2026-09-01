"""Loopback-only LocalModelEndpoint adapter for CP-04 WP-17.

The standard library is used deliberately so this gate adds no production
dependency.  LM Studio, Ollama, and generic OpenAI-compatible details remain
inside this adapter; Core receives only normalized lifecycle values.
"""
from __future__ import annotations

import asyncio
import ipaddress
import json
import socket
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import SplitResult
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import uuid4

from polynexus_core.domain.enums import AuthOwnership, ResumeMode, RunState, UsageVisibility
from polynexus_core.domain.models import Artifact, ContextPackage, Task
from polynexus_core.domain.runtime_binding import RuntimeBindingError
from polynexus_core.runtime.contracts import RuntimeCapabilities, RuntimeResult, RuntimeStatus
from polynexus_core.runtime.redaction import redact_text
from polynexus_core.runtime.routing_policy import (
    DataClassification,
    LocalRouteDecision,
    LocalRouteEvidence,
    evaluate_local_route,
    validate_loopback_endpoint,
)

MAX_RESPONSE_BYTES = 1_048_576
MAX_RESPONSE_TEXT = 4096
MAX_REQUEST_TEXT = 4096
_REQUEST_FAILURE = "local_endpoint_request_failed"
_RESPONSE_FAILURE = "local_endpoint_response_invalid"
_TIMEOUT_FAILURE = "local_endpoint_timeout"
_CANCEL_FAILURE = "local_endpoint_cancel_unsupported"


class LocalEndpointKind(StrEnum):
    LM_STUDIO = "lm_studio"
    OLLAMA = "ollama"
    OPENAI_COMPATIBLE = "openai_compatible"


@dataclass(frozen=True, slots=True)
class LocalEndpointConfig:
    """In-memory endpoint configuration; endpoint URL is never represented."""

    endpoint_url: str = field(repr=False)
    model_identity: str
    endpoint_kind: LocalEndpointKind = LocalEndpointKind.OPENAI_COMPATIBLE
    timeout_seconds: float = 30.0
    classification: DataClassification = DataClassification.INTERNAL
    required_capabilities: tuple[str, ...] = ()


@dataclass
class _LocalRun:
    context: ContextPackage
    state: RunState = RunState.CREATED
    result: RuntimeResult | None = None
    error: str | None = None
    cleaned: bool = False


class LocalEndpointError(RuntimeError):
    """Fixed safe adapter error; raw transport/vendor details are excluded."""


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, *_args: object, **_kwargs: object) -> None:
        raise LocalEndpointError(_REQUEST_FAILURE)


class LocalModelEndpointAdapter:
    """Normalized adapter for a user-selected loopback model endpoint."""

    def __init__(self, config: LocalEndpointConfig) -> None:
        self._config = config
        self._endpoint = validate_loopback_endpoint(config.endpoint_url)
        self._runs: dict[str, _LocalRun] = {}
        self._route: LocalRouteDecision = evaluate_local_route(
            classification=config.classification,
            endpoint_url=config.endpoint_url,
            model_identity=config.model_identity,
            timeout_seconds=config.timeout_seconds,
            capabilities=self.capabilities(),
            required_capabilities=config.required_capabilities,
        )
        self._last_evidence = LocalRouteEvidence(
            endpoint_identity=self._route.endpoint_identity,
            model_identity=self._route.model_identity,
            route=self._route.route,
            timeout_seconds=self._route.timeout_seconds,
        )

    def capabilities(self) -> RuntimeCapabilities:
        # A synchronous HTTP request cannot prove cancellation or cleanup of
        # work already accepted by a local server.  Report the conservative
        # truth so a caller cannot claim verified cancellation.
        return RuntimeCapabilities(
            cancel=False,
            resume=ResumeMode.NONE,
            artifacts=False,
            timeout_cleanup_verified=False,
            usage_visibility=UsageVisibility.UNAVAILABLE,
            auth_ownership=AuthOwnership.NONE,
        )

    async def health(self) -> bool:
        try:
            models = await self._discover_models()
            return bool(models)
        except Exception:
            self._set_error(_REQUEST_FAILURE)
            return False

    async def readiness(self) -> bool:
        try:
            models = await self._discover_models()
            ready = self._config.model_identity in models
            if not ready:
                self._set_error(_RESPONSE_FAILURE)
            else:
                self._clear_error()
            return ready
        except Exception:
            self._set_error(_REQUEST_FAILURE)
            return False

    async def create_run(self, context: ContextPackage) -> str:
        runtime_ref = f"local:{uuid4().hex}"
        self._runs[runtime_ref] = _LocalRun(context=context)
        return runtime_ref

    async def submit(self, runtime_ref: str, task: Task) -> None:
        record = self._get(runtime_ref)
        if record.state is not RunState.CREATED:
            raise LocalEndpointError("local_endpoint_request_failed")
        record.state = RunState.RUNNING
        try:
            response = await self._chat_completion(record.context, task)
            record.result = RuntimeResult(
                summary=redact_text(response, max_length=MAX_RESPONSE_TEXT)
                or "Local model returned an empty response"
            )
            record.state = RunState.COMPLETED
            record.error = None
            self._clear_error()
        except asyncio.TimeoutError:
            record.state = RunState.TIMED_OUT
            record.error = _TIMEOUT_FAILURE
            self._set_error(_TIMEOUT_FAILURE)
            raise LocalEndpointError(_TIMEOUT_FAILURE) from None
        except LocalEndpointError as exc:
            record.state = RunState.FAILED
            record.error = str(exc)
            self._set_error(record.error)
            raise
        except Exception:
            record.state = RunState.FAILED
            record.error = _REQUEST_FAILURE
            self._set_error(_REQUEST_FAILURE)
            raise LocalEndpointError(_REQUEST_FAILURE) from None

    async def status(self, runtime_ref: str) -> RuntimeStatus:
        record = self._get(runtime_ref)
        return RuntimeStatus(state=record.state, error=record.error)

    async def result(self, runtime_ref: str) -> RuntimeResult:
        record = self._get(runtime_ref)
        if record.state is not RunState.COMPLETED or record.result is None:
            raise LocalEndpointError(record.error or _RESPONSE_FAILURE)
        return record.result

    async def cancel(self, runtime_ref: str) -> None:
        self._get(runtime_ref)
        raise LocalEndpointError(_CANCEL_FAILURE)

    async def resume(self, runtime_ref: str, checkpoint: str | None = None) -> None:
        del checkpoint
        self._get(runtime_ref)
        raise LocalEndpointError("local_endpoint_resume_unsupported")

    async def artifacts(self, runtime_ref: str) -> tuple[Artifact, ...]:
        self._get(runtime_ref)
        return ()

    async def cleanup(self, runtime_ref: str) -> bool:
        record = self._get(runtime_ref)
        # No claim of cleanup is safe for a remote-accepted HTTP request.
        record.cleaned = False
        return False

    def version_info(self) -> str:
        return f"local-model-endpoint/{self._config.endpoint_kind.value}/1"

    def route_evidence(self) -> LocalRouteEvidence:
        """Return only bounded, non-secret route evidence for Doctor/tests."""

        return self._last_evidence

    async def _discover_models(self) -> tuple[str, ...]:
        if self._config.endpoint_kind is LocalEndpointKind.OLLAMA:
            payload = await self._request_json("/api/tags", None)
            raw_models = payload.get("models") if isinstance(payload, dict) else None
            names = self._extract_names(raw_models)
        else:
            payload = await self._request_json("/v1/models", None)
            raw_models = payload.get("data") if isinstance(payload, dict) else None
            names = self._extract_names(raw_models)
        return tuple(names)

    async def _chat_completion(self, context: ContextPackage, task: Task) -> str:
        prompt = self._prompt(context, task)
        if self._config.endpoint_kind is LocalEndpointKind.OLLAMA:
            payload = {
                "model": self._config.model_identity,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            }
            response = await self._request_json("/api/chat", payload)
            message = response.get("message") if isinstance(response, dict) else None
            return self._extract_content(message.get("content") if isinstance(message, dict) else None)
        payload = {
            "model": self._config.model_identity,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        response = await self._request_json("/v1/chat/completions", payload)
        choices = response.get("choices") if isinstance(response, dict) else None
        first = choices[0] if isinstance(choices, list) and choices else None
        message = first.get("message") if isinstance(first, dict) else None
        return self._extract_content(message.get("content") if isinstance(message, dict) else None)

    def _prompt(self, context: ContextPackage, task: Task) -> str:
        parts = [f"Task: {redact_text(task.title, max_length=1024)}"]
        for label, values in (
            ("Instructions", context.instructions),
            ("Constraints", context.constraints),
        ):
            if values:
                parts.append(f"{label}: " + "; ".join(redact_text(item, max_length=768) for item in values[:8]))
        return redact_text("\n".join(parts), max_length=MAX_REQUEST_TEXT)

    @staticmethod
    def _extract_names(raw_models: object) -> tuple[str, ...]:
        if not isinstance(raw_models, list):
            raise LocalEndpointError(_RESPONSE_FAILURE)
        names: list[str] = []
        for item in raw_models[:64]:
            if not isinstance(item, dict):
                continue
            raw_name = item.get("name", item.get("id"))
            if isinstance(raw_name, str) and raw_name == raw_name.strip():
                try:
                    from polynexus_core.runtime.routing_policy import validate_model_identity

                    names.append(validate_model_identity(raw_name))
                except RuntimeBindingError:
                    continue
        return tuple(names)

    @staticmethod
    def _extract_content(value: object) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            chunks = [item.get("text") for item in value[:64] if isinstance(item, dict)]
            return "".join(item for item in chunks if isinstance(item, str))
        raise LocalEndpointError(_RESPONSE_FAILURE)

    async def _request_json(self, suffix: str, payload: dict[str, Any] | None) -> object:
        url = self._build_url(suffix)
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        return await asyncio.to_thread(self._request_json_sync, url, body, headers)

    def _request_json_sync(
        self,
        url: str,
        body: bytes | None,
        headers: dict[str, str],
    ) -> object:
        request = Request(url, data=body, headers=headers, method="POST" if body else "GET")
        try:
            self._assert_resolved_loopback()
            # Ignore environment proxy configuration: local-only routing must
            # never turn a loopback request into an external egress request.
            opener = build_opener(ProxyHandler({}), _NoRedirectHandler)
            with opener.open(request, timeout=self._route.timeout_seconds) as response:
                content_length = response.headers.get("Content-Length")
                if content_length is not None and int(content_length) > MAX_RESPONSE_BYTES:
                    raise LocalEndpointError(_RESPONSE_FAILURE)
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except TimeoutError:
            raise asyncio.TimeoutError from None
        except (HTTPError, URLError, OSError, ValueError):
            raise LocalEndpointError(_REQUEST_FAILURE) from None
        if len(raw) > MAX_RESPONSE_BYTES:
            raise LocalEndpointError(_RESPONSE_FAILURE)
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise LocalEndpointError(_RESPONSE_FAILURE) from None

    def _build_url(self, suffix: str) -> str:
        base = self._config.endpoint_url.rstrip("/")
        endpoint_path = self._endpoint.path.rstrip("/")
        for known_prefix in ("/v1", "/api"):
            if endpoint_path == known_prefix and suffix.startswith(known_prefix + "/"):
                return base + suffix[len(known_prefix):]
        return f"{base}{suffix}"

    def _assert_resolved_loopback(self) -> None:
        hostname = self._endpoint.hostname
        if hostname is None:
            raise LocalEndpointError(_REQUEST_FAILURE)
        port = self._endpoint.port or (443 if self._endpoint.scheme == "https" else 80)
        try:
            addresses = socket.getaddrinfo(
                hostname,
                port,
                type=socket.SOCK_STREAM,
            )
        except OSError:
            raise LocalEndpointError(_REQUEST_FAILURE) from None
        if not addresses:
            raise LocalEndpointError(_REQUEST_FAILURE)
        for address in addresses:
            try:
                resolved = ipaddress.ip_address(address[4][0])
            except (ValueError, IndexError, TypeError):
                raise LocalEndpointError(_REQUEST_FAILURE) from None
            if not resolved.is_loopback:
                raise LocalEndpointError(_REQUEST_FAILURE)

    def _set_error(self, safe_error: str) -> None:
        self._last_evidence = LocalRouteEvidence(
            endpoint_identity=self._route.endpoint_identity,
            model_identity=self._route.model_identity,
            route=self._route.route,
            timeout_seconds=self._route.timeout_seconds,
            safe_error=safe_error,
        )

    def _clear_error(self) -> None:
        self._last_evidence = LocalRouteEvidence(
            endpoint_identity=self._route.endpoint_identity,
            model_identity=self._route.model_identity,
            route=self._route.route,
            timeout_seconds=self._route.timeout_seconds,
        )

    def _get(self, runtime_ref: str) -> _LocalRun:
        try:
            return self._runs[runtime_ref]
        except KeyError:
            raise LocalEndpointError(_REQUEST_FAILURE) from None
