# Definition of Done by Maturity

## CORE DoD
- End-to-end usable path exists.
- Unit + integration tests.
- Error/failure path tested.
- Persistent schema/version defined where applicable.
- Documentation updated.
- No known blocker in Golden Path.

## BASELINE DoD
- Real user path works.
- Required fallback exists.
- Known limitations documented.
- At least targeted integration tests.
- Failure does not corrupt Core state.

## COMPATIBILITY DoD
- Real adapter/driver/profile exists or real standard protocol route exists.
- Health/detection/version captured.
- Conformance result recorded.
- Maturity correctly marked; not falsely labeled Supported.

## FUTURE DoD
No product implementation required. Only stable boundary/domain placeholder when doing so has low current cost and prevents obvious future refactor.

## Release DoD
- 10/18 feature freeze respected.
- No critical security/data routing issue.
- Backup/restore/migration tested.
- Golden workflows pass actual acceptance matrix.
- Compatibility matrix & known limitations published.
- All claimed PASS backed by current evidence.
