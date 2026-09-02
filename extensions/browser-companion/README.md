# PolyNexus Browser Companion — Baseline

Chrome Manifest V3 thin companion. This directory intentionally contains no workflow/evidence/policy logic.

V1 Level 3A target for each site driver:
- launch
- detect/health
- auto fill
- user-confirmed send
- capture where available
- normalize raw result
- mandatory manual/clipboard fallback

The localhost API security/pairing boundary is split between the Core
authenticated dependency and the session-memory `LoopbackClient`; both are
loopback-only and fail closed. Never add vendor DOM selectors to Core.

Live authenticated vendor journeys and certification remain deferred to G29.
