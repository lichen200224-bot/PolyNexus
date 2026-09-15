"""Bounded, provider-neutral ACP v1 JSON-RPC over an owned stdio process.

The client advertises no filesystem or terminal capabilities. Agent-side
requests therefore fail closed; session updates are observations, not
authorization or source-change proof.
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from polynexus_core.runtime.external_contracts import ExternalContractError


class ACPTransport:
    def __init__(self, job: object) -> None:
        self.job = job
        self.session_id: str | None = None
        self.protocol_version: int | None = None
        self.events: list[dict[str, Any]] = []
        self._next_id = 0

    async def request(self, method: str, params: dict[str, Any], *, timeout: float) -> dict[str, Any]:
        if timeout <= 0 or timeout > 300:
            raise ExternalContractError("acp_timeout_invalid")
        request_id = self._next_id
        self._next_id += 1
        payload = json.dumps(
            {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params},
            separators=(",", ":"), ensure_ascii=False,
        ).encode("utf-8") + b"\n"
        try:
            await asyncio.to_thread(self.job.send_line, payload)
        except Exception as exc:
            raise ExternalContractError("acp_send_failed") from exc
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ExternalContractError("acp_response_timeout")
            try:
                line = await asyncio.to_thread(self.job.read_line, remaining)
            except TimeoutError as exc:
                raise ExternalContractError("acp_response_timeout") from exc
            try:
                if len(line) > 1024 * 1024:
                    raise ValueError("oversized ACP line")
                message = json.loads(line)
            except Exception as exc:
                raise ExternalContractError("acp_message_malformed") from exc
            if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
                raise ExternalContractError("acp_message_malformed")
            if "method" in message:
                if "id" in message:
                    raise ExternalContractError("acp_agent_request_unsupported")
                if message["method"] != "session/update" or self.session_id is None:
                    raise ExternalContractError("acp_notification_unexpected")
                update = message.get("params")
                if not isinstance(update, dict) or update.get("sessionId") != self.session_id:
                    raise ExternalContractError("acp_session_mismatch")
                self.events.append(message)
                if len(self.events) > 4096:
                    raise ExternalContractError("acp_event_limit")
                continue
            if message.get("id") != request_id or "result" not in message or "error" in message:
                raise ExternalContractError("acp_response_mismatch")
            result = message["result"]
            if not isinstance(result, dict):
                raise ExternalContractError("acp_result_malformed")
            return result

    async def initialize(self, *, timeout: float = 30.0) -> dict[str, Any]:
        result = await self.request(
            "initialize",
            {
                "protocolVersion": 1,
                "clientCapabilities": {
                    "fs": {"readTextFile": False, "writeTextFile": False},
                    "terminal": False,
                },
                "clientInfo": {"name": "polynexus-core", "title": "PolyNexus Core", "version": "1.0.0"},
            },
            timeout=timeout,
        )
        if result.get("protocolVersion") != 1:
            raise ExternalContractError("acp_version_unsupported")
        self.protocol_version = 1
        return result

    async def new_session(self, cwd: str, *, timeout: float = 30.0) -> dict[str, Any]:
        if self.protocol_version != 1:
            raise ExternalContractError("acp_initialize_required")
        result = await self.request("session/new", {"cwd": cwd, "mcpServers": []}, timeout=timeout)
        session_id = result.get("sessionId")
        if not isinstance(session_id, str) or not session_id or len(session_id) > 256:
            raise ExternalContractError("acp_session_invalid")
        self.session_id = session_id
        return result

    async def prompt(self, text: str, *, timeout: float = 180.0) -> dict[str, Any]:
        if self.session_id is None or not isinstance(text, str) or not text or len(text) > 16384:
            raise ExternalContractError("acp_prompt_invalid")
        result = await self.request(
            "session/prompt",
            {"sessionId": self.session_id, "prompt": [{"type": "text", "text": text}]},
            timeout=timeout,
        )
        if result.get("stopReason") != "end_turn":
            raise ExternalContractError("acp_prompt_not_completed")
        return result

    def close_input(self) -> None:
        self.job.close_stdin()
