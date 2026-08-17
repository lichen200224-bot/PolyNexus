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

The localhost API security/pairing implementation belongs to the Core security boundary and will be added during the Web Integration phase. Never add vendor DOM selectors to Core.
