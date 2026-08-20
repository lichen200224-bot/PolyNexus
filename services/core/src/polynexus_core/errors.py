"""Core exception types for execution command error taxonomy.

These exceptions live in the application/core layer, NOT in the API layer.
API routes map these typed exceptions to HTTP status codes.

Layer boundary:
  - ExecutionService / RunSupervisor raise these exceptions.
  - API routes catch and map to HTTP 404/409/422/5xx.
"""
from __future__ import annotations


class ExecutionError(Exception):
    """Base class for execution command errors."""


class RunNotFoundError(ExecutionError):
    """Run does not exist. API maps to HTTP 404."""


class ResourceNotFoundError(ExecutionError):
    """A referenced resource (Task, ContextPackage) does not exist.
    API maps to HTTP 422 (stored reference broken)."""


class ContractViolationError(ExecutionError):
    """Stored Task/Run/ContextPackage/workflow contract mismatch. API maps to HTTP 422."""


class ClaimConflictError(ExecutionError):
    """Run was already claimed by another caller or is in a conflicting state.
    API maps to HTTP 409."""
