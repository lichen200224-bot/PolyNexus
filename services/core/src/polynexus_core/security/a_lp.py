"""Local A-LP WebAuthn verification primitives.

The browser/OS authenticator owns the private key and the user-presence
ceremony. Core only creates one-time challenges, verifies the WebAuthn
assertion, and stores the resulting public trust material. This module keeps
the verification boundary dependency-light: CBOR and P-256 verification are
implemented locally, while no private key is ever accepted by the API.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlsplit


class ALPVerificationError(ValueError):
    """A malformed, mismatched, replayable, or unsupported A-LP assertion."""


WEBAUTHN_REGISTRATION_TYPE = "webauthn.create"
WEBAUTHN_ASSERTION_TYPE = "webauthn.get"
WEBAUTHN_FORMAT = "none"
COSE_KTY_EC2 = 2
COSE_ALG_ES256 = -7
COSE_CRV_P256 = 1
AUTHENTICATOR_FLAG_UP = 0x01
AUTHENTICATOR_FLAG_UV = 0x04
AUTHENTICATOR_FLAG_AT = 0x40
AUTHENTICATOR_FLAG_ED = 0x80


@dataclass(frozen=True)
class ALPConfig:
    origin: str
    rp_id: str
    installation_id: str


@dataclass(frozen=True)
class WebAuthnCredential:
    credential_id: bytes
    client_data_json: bytes
    authenticator_data: bytes
    signature: bytes | None = None
    attestation_object: bytes | None = None


@dataclass(frozen=True)
class RegisteredCredential:
    credential_id: bytes
    public_key: bytes
    sign_count: int


@dataclass(frozen=True)
class VerifiedAssertion:
    credential_id: bytes
    sign_count: int


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def b64u_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def b64u_decode(value: str, field: str, *, max_length: int = 4096) -> bytes:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > max_length
        or "=" in value
        or re.fullmatch(r"[A-Za-z0-9_-]+", value) is None
    ):
        raise ALPVerificationError(f"{field}_invalid")
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, UnicodeError, binascii.Error) as exc:
        raise ALPVerificationError(f"{field}_invalid") from exc
    if b64u_encode(decoded) != value:
        raise ALPVerificationError(f"{field}_invalid")
    return decoded


def load_config(environ: Mapping[str, str] | None = None) -> ALPConfig:
    source = os.environ if environ is None else environ
    origin = source.get("POLYNEXUS_UI_ORIGIN", "").strip()
    try:
        parts = urlsplit(origin)
        port = parts.port
    except ValueError as exc:
        raise ALPVerificationError("a_lp_origin_invalid") from exc
    hostname = (parts.hostname or "").lower()
    if (
        not origin
        or parts.scheme not in {"http", "https"}
        or not hostname
        or parts.username is not None
        or parts.password is not None
        or parts.path
        or parts.query
        or parts.fragment
        or (port is not None and not 0 < port < 65536)
    ):
        raise ALPVerificationError("a_lp_origin_invalid")
    if parts.scheme == "http" and hostname not in {"127.0.0.1", "localhost"}:
        raise ALPVerificationError("a_lp_origin_requires_tls")
    rp_id = source.get("POLYNEXUS_WEBAUTHN_RP_ID", hostname).strip().lower()
    if (
        not rp_id
        or rp_id != hostname
        or "/" in rp_id
        or ":" in rp_id
        or any(character.isspace() for character in rp_id)
    ):
        raise ALPVerificationError("a_lp_rp_id_invalid")
    installation_id = source.get("POLYNEXUS_INSTALLATION_ID", "").strip()
    if re.fullmatch(r"sha256:[0-9a-f]{64}", installation_id) is None:
        raise ALPVerificationError("a_lp_installation_id_invalid")
    return ALPConfig(origin=origin, rp_id=rp_id, installation_id=installation_id)


class _CBOR:
    def __init__(self, data: bytes):
        if not isinstance(data, bytes) or len(data) > 1_048_576:
            raise ALPVerificationError("cbor_size_invalid")
        self.data = data

    def _read(self, offset: int, size: int) -> tuple[bytes, int]:
        end = offset + size
        if size < 0 or end > len(self.data):
            raise ALPVerificationError("cbor_truncated")
        return self.data[offset:end], end

    def _length(self, additional: int, offset: int) -> tuple[int, int]:
        if additional < 24:
            return additional, offset
        width = {24: 1, 25: 2, 26: 4, 27: 8}.get(additional)
        if width is None:
            raise ALPVerificationError("cbor_indefinite_or_reserved")
        raw, offset = self._read(offset, width)
        value = int.from_bytes(raw, "big")
        if value < 24 and width != 1:
            raise ALPVerificationError("cbor_noncanonical_length")
        if width == 2 and value <= 0xFF:
            raise ALPVerificationError("cbor_noncanonical_length")
        if width == 4 and value <= 0xFFFF:
            raise ALPVerificationError("cbor_noncanonical_length")
        if width == 8 and value <= 0xFFFFFFFF:
            raise ALPVerificationError("cbor_noncanonical_length")
        return value, offset

    def one(self, offset: int = 0, depth: int = 0) -> tuple[Any, int]:
        if depth > 16:
            raise ALPVerificationError("cbor_depth_invalid")
        raw, offset = self._read(offset, 1)
        initial = raw[0]
        major = initial >> 5
        additional = initial & 0x1F
        length, offset = self._length(additional, offset)
        if major == 0:
            return length, offset
        if major == 1:
            return -1 - length, offset
        if major == 2:
            return self._read(offset, length)
        if major == 3:
            raw_text, offset = self._read(offset, length)
            try:
                return raw_text.decode("utf-8"), offset
            except UnicodeDecodeError as exc:
                raise ALPVerificationError("cbor_text_invalid") from exc
        if major == 4:
            if length > 256:
                raise ALPVerificationError("cbor_array_too_large")
            values: list[Any] = []
            for _ in range(length):
                value, offset = self.one(offset, depth + 1)
                values.append(value)
            return values, offset
        if major == 5:
            if length > 256:
                raise ALPVerificationError("cbor_map_too_large")
            values: dict[Any, Any] = {}
            for _ in range(length):
                key, offset = self.one(offset, depth + 1)
                if isinstance(key, (list, dict, set)):
                    raise ALPVerificationError("cbor_map_key_invalid")
                if key in values:
                    raise ALPVerificationError("cbor_duplicate_map_key")
                value, offset = self.one(offset, depth + 1)
                values[key] = value
            return values, offset
        if major == 6:
            raise ALPVerificationError("cbor_tag_unsupported")
        if major == 7 and additional in {20, 21, 22}:
            return {20: False, 21: True, 22: None}[additional], offset
        raise ALPVerificationError("cbor_value_unsupported")


def decode_cbor(data: bytes) -> Any:
    decoder = _CBOR(data)
    value, offset = decoder.one()
    if offset != len(data):
        raise ALPVerificationError("cbor_trailing_bytes")
    return value


def _parse_der_integer(data: bytes, offset: int) -> tuple[int, int]:
    if offset >= len(data) or data[offset] != 0x02:
        raise ALPVerificationError("ecdsa_signature_invalid")
    offset += 1
    if offset >= len(data):
        raise ALPVerificationError("ecdsa_signature_invalid")
    length = data[offset]
    offset += 1
    if length & 0x80:
        width = length & 0x7F
        if width == 0 or width > 2 or offset + width > len(data):
            raise ALPVerificationError("ecdsa_signature_invalid")
        if data[offset] == 0:
            raise ALPVerificationError("ecdsa_signature_invalid")
        length = int.from_bytes(data[offset:offset + width], "big")
        offset += width
        if length < 128 or (width == 2 and length <= 0xFF):
            raise ALPVerificationError("ecdsa_signature_invalid")
    if length == 0 or length > 33 or offset + length > len(data):
        raise ALPVerificationError("ecdsa_signature_invalid")
    raw = data[offset:offset + length]
    if raw[0] & 0x80 or (len(raw) > 1 and raw[0] == 0 and not raw[1] & 0x80):
        raise ALPVerificationError("ecdsa_signature_invalid")
    return int.from_bytes(raw, "big"), offset + length


def parse_ecdsa_der(signature: bytes) -> tuple[int, int]:
    if not isinstance(signature, bytes) or len(signature) > 144 or len(signature) < 8 or signature[0] != 0x30:
        raise ALPVerificationError("ecdsa_signature_invalid")
    offset = 1
    length = signature[offset]
    offset += 1
    if length & 0x80:
        width = length & 0x7F
        if width == 0 or width > 2 or offset + width > len(signature):
            raise ALPVerificationError("ecdsa_signature_invalid")
        if signature[offset] == 0:
            raise ALPVerificationError("ecdsa_signature_invalid")
        length = int.from_bytes(signature[offset:offset + width], "big")
        offset += width
        if length < 128 or (width == 2 and length <= 0xFF):
            raise ALPVerificationError("ecdsa_signature_invalid")
    if length != len(signature) - offset:
        raise ALPVerificationError("ecdsa_signature_invalid")
    r, offset = _parse_der_integer(signature, offset)
    s, offset = _parse_der_integer(signature, offset)
    if offset != len(signature):
        raise ALPVerificationError("ecdsa_signature_invalid")
    return r, s


_P256_P = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
_P256_A = _P256_P - 3
_P256_B = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B
_P256_G = (
    0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296,
    0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5,
)
_P256_N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
_P256_Point = tuple[int, int] | None


def _p256_on_curve(point: _P256_Point) -> bool:
    if point is None:
        return False
    x, y = point
    return (
        0 <= x < _P256_P
        and 0 <= y < _P256_P
        and (y * y - (x * x * x + _P256_A * x + _P256_B)) % _P256_P == 0
    )


def _p256_add(first: _P256_Point, second: _P256_Point) -> _P256_Point:
    if first is None:
        return second
    if second is None:
        return first
    x1, y1 = first
    x2, y2 = second
    if x1 == x2:
        if (y1 + y2) % _P256_P == 0:
            return None
        if y1 == 0:
            return None
        slope = ((3 * x1 * x1 + _P256_A) * pow(2 * y1, _P256_P - 2, _P256_P)) % _P256_P
    else:
        slope = ((y2 - y1) * pow(x2 - x1, _P256_P - 2, _P256_P)) % _P256_P
    x3 = (slope * slope - x1 - x2) % _P256_P
    y3 = (slope * (x1 - x3) - y1) % _P256_P
    return x3, y3


def _p256_mul(point: _P256_Point, scalar: int) -> _P256_Point:
    if point is None or scalar < 0:
        return None
    result: _P256_Point = None
    addend = point
    while scalar:
        if scalar & 1:
            result = _p256_add(result, addend)
        addend = _p256_add(addend, addend)
        scalar >>= 1
    return result


def _raw_public_key(public_key: bytes) -> _P256_Point:
    if not isinstance(public_key, bytes) or len(public_key) != 65 or public_key[0] != 4:
        raise ALPVerificationError("public_key_invalid")
    point = (int.from_bytes(public_key[1:33], "big"), int.from_bytes(public_key[33:], "big"))
    if not _p256_on_curve(point):
        raise ALPVerificationError("public_key_invalid")
    return point


def verify_p256_signature(public_key: bytes, message: bytes, signature: bytes) -> None:
    point = _raw_public_key(public_key)
    r, s = parse_ecdsa_der(signature)
    if not 1 <= r < _P256_N or not 1 <= s < _P256_N:
        raise ALPVerificationError("ecdsa_signature_invalid")
    inverse = pow(s, _P256_N - 2, _P256_N)
    digest = int.from_bytes(hashlib.sha256(message).digest(), "big")
    combined = _p256_add(
        _p256_mul(_P256_G, (digest * inverse) % _P256_N),
        _p256_mul(point, (r * inverse) % _P256_N),
    )
    if combined is None or combined[0] % _P256_N != r:
        raise ALPVerificationError("ecdsa_signature_invalid")


def _parse_client_data(
    client_data_json: bytes,
    *,
    expected_challenge_digest: str,
    expected_origin: str,
    expected_type: str,
) -> dict[str, Any]:
    if not isinstance(client_data_json, bytes) or len(client_data_json) > 64 * 1024:
        raise ALPVerificationError("client_data_invalid")
    try:
        value = json.loads(client_data_json.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ALPVerificationError("client_data_invalid") from exc
    if (
        not isinstance(value, dict)
        or value.get("type") != expected_type
        or value.get("origin") != expected_origin
        or not isinstance(value.get("challenge"), str)
    ):
        raise ALPVerificationError("client_data_binding_invalid")
    challenge = b64u_decode(value["challenge"], "client_data_challenge", max_length=1024)
    if "crossOrigin" in value and value["crossOrigin"] is not False:
        raise ALPVerificationError("client_data_origin_invalid")
    if "topOrigin" in value and value["topOrigin"] != expected_origin:
        raise ALPVerificationError("client_data_origin_invalid")
    if hashlib.sha256(challenge).hexdigest() != expected_challenge_digest:
        raise ALPVerificationError("client_data_challenge_invalid")
    return value


def _parse_authenticator_data(
    authenticator_data: bytes,
    *,
    rp_id: str,
    require_attested: bool,
) -> tuple[int, int, bytes | None, bytes | None]:
    if not isinstance(authenticator_data, bytes) or len(authenticator_data) < 37:
        raise ALPVerificationError("authenticator_data_invalid")
    if authenticator_data[:32] != hashlib.sha256(rp_id.encode("utf-8")).digest():
        raise ALPVerificationError("rp_id_hash_invalid")
    flags = authenticator_data[32]
    if flags & 0x08:
        raise ALPVerificationError("authenticator_flags_invalid")
    if not flags & AUTHENTICATOR_FLAG_UP or not flags & AUTHENTICATOR_FLAG_UV:
        raise ALPVerificationError("user_presence_or_verification_required")
    sign_count = int.from_bytes(authenticator_data[33:37], "big")
    offset = 37
    credential_id: bytes | None = None
    public_key: bytes | None = None
    if flags & AUTHENTICATOR_FLAG_AT:
        if len(authenticator_data) < offset + 18:
            raise ALPVerificationError("attested_credential_data_invalid")
        offset += 16
        credential_length = int.from_bytes(authenticator_data[offset:offset + 2], "big")
        offset += 2
        if credential_length < 16 or credential_length > 1024:
            raise ALPVerificationError("credential_id_invalid")
        credential_id = authenticator_data[offset:offset + credential_length]
        if len(credential_id) != credential_length:
            raise ALPVerificationError("attested_credential_data_invalid")
        offset += credential_length
        try:
            cose_key, offset = _CBOR(authenticator_data).one(offset)
        except ALPVerificationError:
            raise
        if not isinstance(cose_key, dict):
            raise ALPVerificationError("cose_key_invalid")
        if (
            cose_key.get(1) != COSE_KTY_EC2
            or cose_key.get(3) != COSE_ALG_ES256
            or cose_key.get(-1) != COSE_CRV_P256
            or not isinstance(cose_key.get(-2), bytes)
            or not isinstance(cose_key.get(-3), bytes)
            or len(cose_key[-2]) != 32
            or len(cose_key[-3]) != 32
        ):
            raise ALPVerificationError("cose_key_invalid")
        public_key = b"\x04" + cose_key[-2] + cose_key[-3]
        _raw_public_key(public_key)
    elif require_attested:
        raise ALPVerificationError("attested_credential_required")
    if flags & AUTHENTICATOR_FLAG_ED:
        _, offset = _CBOR(authenticator_data).one(offset)
    if offset != len(authenticator_data):
        raise ALPVerificationError("authenticator_data_trailing_bytes")
    return flags, sign_count, credential_id, public_key


def _parse_registration_credential(value: Mapping[str, Any]) -> WebAuthnCredential:
    if not isinstance(value, Mapping) or value.get("type") != "public-key":
        raise ALPVerificationError("credential_type_invalid")
    credential_id = b64u_decode(value.get("id"), "credential_id", max_length=2048)
    raw_id = b64u_decode(value.get("raw_id"), "raw_id", max_length=2048)
    if credential_id != raw_id:
        raise ALPVerificationError("credential_id_mismatch")
    response = value.get("response")
    if not isinstance(response, Mapping):
        raise ALPVerificationError("credential_response_invalid")
    return WebAuthnCredential(
        credential_id=credential_id,
        client_data_json=b64u_decode(response.get("client_data_json"), "client_data_json", max_length=128 * 1024),
        authenticator_data=b"",
        attestation_object=b64u_decode(response.get("attestation_object"), "attestation_object", max_length=1024 * 1024),
    )


def _parse_assertion_credential(value: Mapping[str, Any]) -> WebAuthnCredential:
    if not isinstance(value, Mapping) or value.get("type") != "public-key":
        raise ALPVerificationError("credential_type_invalid")
    credential_id = b64u_decode(value.get("id"), "credential_id", max_length=2048)
    raw_id = b64u_decode(value.get("raw_id"), "raw_id", max_length=2048)
    if credential_id != raw_id:
        raise ALPVerificationError("credential_id_mismatch")
    response = value.get("response")
    if not isinstance(response, Mapping):
        raise ALPVerificationError("credential_response_invalid")
    user_handle = response.get("user_handle")
    if user_handle is not None:
        b64u_decode(user_handle, "user_handle", max_length=2048)
    return WebAuthnCredential(
        credential_id=credential_id,
        client_data_json=b64u_decode(response.get("client_data_json"), "client_data_json", max_length=128 * 1024),
        authenticator_data=b64u_decode(response.get("authenticator_data"), "authenticator_data", max_length=4096),
        signature=b64u_decode(response.get("signature"), "signature", max_length=1024),
    )


def verify_registration(
    value: Mapping[str, Any],
    *,
    expected_challenge_digest: str,
    expected_origin: str,
    rp_id: str,
) -> RegisteredCredential:
    credential = _parse_registration_credential(value)
    _parse_client_data(
        credential.client_data_json,
        expected_challenge_digest=expected_challenge_digest,
        expected_origin=expected_origin,
        expected_type=WEBAUTHN_REGISTRATION_TYPE,
    )
    try:
        attestation = decode_cbor(credential.attestation_object or b"")
    except ALPVerificationError:
        raise
    if (
        not isinstance(attestation, dict)
        or attestation.get("fmt") != WEBAUTHN_FORMAT
        or attestation.get("attStmt") != {}
        or not isinstance(attestation.get("authData"), bytes)
    ):
        raise ALPVerificationError("attestation_format_unsupported")
    _, sign_count, attested_id, public_key = _parse_authenticator_data(
        attestation["authData"],
        rp_id=rp_id,
        require_attested=True,
    )
    if attested_id != credential.credential_id or public_key is None:
        raise ALPVerificationError("credential_id_mismatch")
    return RegisteredCredential(
        credential_id=credential.credential_id,
        public_key=public_key,
        sign_count=sign_count,
    )


def verify_assertion(
    value: Mapping[str, Any],
    *,
    expected_challenge_digest: str,
    expected_origin: str,
    rp_id: str,
    expected_credential_id: bytes,
    public_key: bytes,
    stored_sign_count: int,
) -> VerifiedAssertion:
    credential = _parse_assertion_credential(value)
    if credential.credential_id != expected_credential_id or credential.signature is None:
        raise ALPVerificationError("credential_id_mismatch")
    _parse_client_data(
        credential.client_data_json,
        expected_challenge_digest=expected_challenge_digest,
        expected_origin=expected_origin,
        expected_type=WEBAUTHN_ASSERTION_TYPE,
    )
    _, sign_count, attested_id, _ = _parse_authenticator_data(
        credential.authenticator_data,
        rp_id=rp_id,
        require_attested=False,
    )
    if attested_id is not None:
        raise ALPVerificationError("assertion_attested_data_unexpected")
    verify_p256_signature(
        public_key,
        credential.authenticator_data + hashlib.sha256(credential.client_data_json).digest(),
        credential.signature,
    )
    if not isinstance(stored_sign_count, int) or stored_sign_count < 0:
        raise ALPVerificationError("sign_count_invalid")
    if stored_sign_count > 0 and (sign_count == 0 or sign_count <= stored_sign_count):
        raise ALPVerificationError("authenticator_counter_invalid")
    return VerifiedAssertion(credential_id=credential.credential_id, sign_count=sign_count)


def credential_fingerprint(public_key: bytes) -> str:
    _raw_public_key(public_key)
    return "sha256:" + hashlib.sha256(public_key).hexdigest()


def challenge_digest(challenge: bytes) -> str:
    if not isinstance(challenge, bytes) or len(challenge) < 16:
        raise ALPVerificationError("challenge_invalid")
    return hashlib.sha256(challenge).hexdigest()
