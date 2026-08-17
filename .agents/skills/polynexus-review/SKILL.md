---
name: polynexus-review
description: Use for independent read-only review of a PolyNexus change, especially when another AI tool was the writer. Focus on diff, contract violations, regressions, security, and missing tests.
---
# PolyNexus Review

1. Stay read-only unless explicitly assigned as writer.
2. Review `git diff` / target commit first; do not re-analyze the whole repository.
3. Load only relevant Contract/SA/SD when a diff touches those boundaries.
4. Report only actionable findings grouped BLOCKER / MAJOR / MINOR.
5. Check: scope drift, vendor logic in Core, state-machine/lifecycle errors, evidence mislabeling, secret leakage, policy bypass, migration compatibility, missing tests.
6. Do not rewrite the full architecture or duplicate the implementation plan.
7. If no blocker, say `NO BLOCKER` and list any residual test recommendation.
