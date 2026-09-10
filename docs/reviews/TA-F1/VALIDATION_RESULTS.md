# TA-F1 Validation Results

## Pre-commit deterministic validation

- command: `python validate_ta_f1.py <formalization-repo> <accepted-receipt-repo>`
- cwd: `D:/AI_學習教材/PolyNexus/artifacts/worktrees/track-a-formalization-20260910`
- actual exit code: `0`
- result: `PASS`
- mandatory skipped: `[]`
- failed checks: `[]`

PASS checks: exact f34 predecessor; exact changed-file allowlist; formal targets unchanged; product paths unchanged; all 25 required proposal sections; I-01 through I-23 mapping; required M-IDENTITY/M-HUMAN/M-EXECUTION and safety terms; all 13 required fields across nine per-file records; eight accepted receipt-lineage references present; seven current formal references present; future F3 files absent; `git diff --check` clean.

## Candidate-bound validation

The external review package records the immutable Candidate SHA, exact predecessor, exact diff, final changed-file allowlist, product/formal preservation checks, manifest verification, bundle verification, package validation exit code, and ZIP SHA-256. These values cannot be embedded into the Candidate without changing its identity; they are stored in package-root evidence and the external `delivery.json` as required by the canonical review-package skill.
