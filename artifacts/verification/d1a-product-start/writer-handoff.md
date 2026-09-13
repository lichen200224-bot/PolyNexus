# D1a writer handoff

The five D1a evidence files are refreshed for the final technical source
state and are ready for an immutable candidate commit followed by fresh
independent review.

Source binding:

- Branch: `codex/product-d1a`.
- Current HEAD: `1b79c511ec0b7358525d8ca1101d4c07b57551f6`.
- The only source delta after that commit is the uncommitted, test-only repair
  #26 in `services/core/tests/test_baseline_debt_01.py`. It changes the
  cancellation oracle to require one `runtime.routing_policy` audit and zero
  non-policy evidence.
- The browser journey ran on the same product/Web fingerprint at
  `1b79c511ec0b7358525d8ca1101d4c07b57551f6); #26 does not change product or
  Web bytes.

Final evidence:

- Repair #26 targeted: 24 passed, exit 0.
- D1a affected Core: 183 passed, exit 0.
- Policy/security affected Core: 74 passed, exit 0.
- Full Core with the system tempfile root: 873 passed, 193 warnings, exit 0,
  122.25s.
- Web full: 94 passed, exit 0.
- `npm run build`: exit 0.
- Browser journey: observed pass on synthetic local-only data. Readiness,
  explicit generation/context selection, CREATED empty-output semantics,
  offline Retry, restart/reconnect identity, archive write boundaries and
  Abort/Cancel readability were observed. Both probes recorded Core 200, Web
  200, anonymous 403 and wrong-token 403, with zero remaining listeners and
  zero owned instances alive after cleanup.

Case-map status is technical evidence only. No Human product acceptance,
Assurance authority or independent fresh review is claimed. The remaining
non-blocking review note is the P2 API-contract follow-up for
`prepare_claimed_run(commit=False)` denial-audit persistence; the sole
production caller uses an isolated session and current tests prove the
required durable audit. It is not a current observed D1a P0/P1 defect.

No remote push of a new candidate, merge, release/tag, D1b work, MCF adoption
or production database operation was performed. The next owner may commit the
repaired source plus these five evidence files as one explicit immutable
candidate and request fresh review.
