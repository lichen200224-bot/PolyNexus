# MCF-02 independent semantic / contract / security review

Review target: `030890b30160f1063ac2cef1d36705a9ea70bddb`

Review basis: canonical refs were checked before this review. The review was
read-only. No merge, cherry-pick, copy, or implementation reuse was performed.

## Decision

`REJECTED / NOT ADOPTED` for D2a integration. This is an independent review
result, not Human product acceptance.

## Evidence

All commands below ran from
`C:\Users\shawn\OneDrive\文件\PONYNEXUS\d2a-worktree` and exited `0` unless
stated otherwise.

| Check | Actual result |
| --- | --- |
| `git rev-list --parents -n 1 030890b30160f1063ac2cef1d36705a9ea70bddb` | Parent is `18fab2b092911d9dd1f95eccda29b52dfaedff7d` |
| `git merge-base 4cc88feab4097481fa4725c659521c7431794d46 030890b30160f1063ac2cef1d36705a9ea70bddb` | `f0c0b986380dc21d103d4e856057cb8ac435a8f9`, not the accepted D1a SHA |
| `git diff --stat 4cc88fe... 030890b...` | `148 files changed, 3539 insertions(+), 12130 deletions(-)` |
| `git diff --name-status 4cc88fe... 030890b...` | Deletes accepted `docs/delivery/*`, frozen Track A references, D1a `workspace`, `security`, `persistence`, and execution-path files; adds candidate `external_contracts.py`, `opencode_acp.py`, and MCF-02 tests |
| `git diff --check 4cc88fe... 030890b...` | exit `0`; formatting cleanliness does not repair ancestry or contract loss |
| `git grep -n -E 'fake|Fake|simulat|fixture' 030890b... -- services/core/tests/*mcf02*` | Candidate tests explicitly identify fake ACP / deterministic fixture coverage |

## Findings

### P1 — wrong ancestry and destructive contract surface

The candidate is not descended from the Human-accepted D1a SHA. Its merge base
is an older remote commit, and the candidate diff deletes the accepted delivery
contract set plus D1a persistence, workspace, security, and execution code.
There is no safe bounded integration operation that preserves the accepted
baseline. Adopting it would silently replace the contractual source of truth.

### P1 — no FD-08 real-target evidence

The candidate's MCF-02 tests are fake ACP / deterministic fixture tests. They do
not establish a real executor's cwd, source write, normalized result, cancel,
timeout, child/grandchild cleanup, runtime version, auth ownership, or
provenance. Simulator coverage cannot satisfy the WORK W2 real-target gate.

### P1 — security and contract review cannot promote the candidate

Because the candidate removes the frozen security and delivery references and
does not provide real-target boundary evidence, its external envelope and ACP
claims cannot be accepted as preserving FD-05/06/07 or the frozen secret and
process-tree contract. The candidate is therefore not a source for D2a
implementation.

## Scope limitation

This review establishes the blockers above. It is not a claim that every line
of the candidate is safe or unsafe; the structural blockers are sufficient to
keep the candidate unmerged and unused.
