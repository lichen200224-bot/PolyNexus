from enum import StrEnum


class RunState(StrEnum):
    CREATED = "CREATED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"
    ORPHANED = "ORPHANED"


class ResumeMode(StrEnum):
    NATIVE = "NATIVE"
    MANAGED = "MANAGED"
    NONE = "NONE"


class ExecutionTarget(StrEnum):
    LOCAL = "LOCAL"


class TransportKind(StrEnum):
    """How PolyNexus reaches a Runtime (ADR-011 §2.1).

    WEB_INTERACTIVE is boundary-only: it reserves an identity for the
    assisted WebSurface path and creates no execution semantics.
    """

    LOCAL = "LOCAL"
    NATIVE_SUBSCRIPTION = "NATIVE_SUBSCRIPTION"
    OFFICIAL_API = "OFFICIAL_API"
    WEB_INTERACTIVE = "WEB_INTERACTIVE"


class AuthOwnership(StrEnum):
    """Who owns the credential for a Runtime (ADR-011 §6)."""

    RUNTIME_MANAGED = "RUNTIME_MANAGED"
    SECRET_REF = "SECRET_REF"
    BROWSER_PROFILE_MANAGED = "BROWSER_PROFILE_MANAGED"
    NONE = "NONE"


class UsageVisibility(StrEnum):
    """Truthful usage/quota visibility contract (ADR-011 §8)."""

    UNAVAILABLE = "UNAVAILABLE"
    ESTIMATED = "ESTIMATED"
    EXACT = "EXACT"


class EvidenceType(StrEnum):
    AI_OPINION = "AI_OPINION"
    RUNTIME_EVIDENCE = "RUNTIME_EVIDENCE"
    TOOL_EVIDENCE = "TOOL_EVIDENCE"
    DOCUMENT_EVIDENCE = "DOCUMENT_EVIDENCE"
    HUMAN_EVIDENCE = "HUMAN_EVIDENCE"


class EvidenceStatus(StrEnum):
    OBSERVED = "OBSERVED"
    PASS = "PASS"
    FAIL = "FAIL"
    NEED_ACTION = "NEED_ACTION"
    HUMAN_DECISION = "HUMAN_DECISION"


class WorkMode(StrEnum):
    DISCUSS = "DISCUSS"
    REVIEW = "REVIEW"
    VALIDATE = "VALIDATE"


class ArtifactType(StrEnum):
    DOCUMENT = "DOCUMENT"
    TEXT = "TEXT"
    CODE_DIFF = "CODE_DIFF"
    LOG = "LOG"
    REPORT = "REPORT"
    SCREENSHOT = "SCREENSHOT"
    RAW_AI_OUTPUT = "RAW_AI_OUTPUT"
    TEST_RESULT = "TEST_RESULT"
    EVIDENCE_BUNDLE = "EVIDENCE_BUNDLE"
    HANDOFF = "HANDOFF"


class FindingSeverity(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FindingStatus(StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    ACCEPTED = "ACCEPTED"


class AssuranceMode(StrEnum):
    FLEXIBLE = "FLEXIBLE"
    STANDARD = "STANDARD"
    VERIFIED = "VERIFIED"
