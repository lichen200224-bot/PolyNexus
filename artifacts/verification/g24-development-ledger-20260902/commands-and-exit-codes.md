# G24 Current Verification Commands

This file records current G24 commands and actual process exit codes. Historical
WP evidence is referenced by `ledger.json` and remains `HISTORICAL`.

| Command | Result | Exit code | Classification |
|---|---|---:|---|
| `git rev-parse --show-toplevel` | isolated G24 lane | 0 | current start gate |
| `git branch --show-current` | expected feature branch | 0 | current start gate |
| `git rev-parse HEAD` | exact predecessor SHA before edits | 0 | current start gate |
| `git status --short --branch` | clean before edits | 0 | current start gate |
| `git diff --name-status` | empty before edits | 0 | current start gate |
| `git diff --cached --name-status` | empty before edits | 0 | current start gate |
| `git diff --check` | clean before edits | 0 | current start gate |
| `git ls-remote D:/GitBackup/PolyNexus_Backup.git refs/heads/feature/g24-g30-development-completion-routing` | exact predecessor matched | 0 | current start gate |

Post-edit validation rows are appended after execution. No row authorizes
stage, commit, push, or G25.

## Post-edit validation

| Command | Result | Exit code | Classification |
|---|---|---:|---|
| `node -p [full text in section below, command 1]` | validator field-name mismatch (`records` use uppercase schema keys) | 1 | reviewer/tool failure; corrected below |
| `node -p [full text in section below, command 2]` | current docs contain G24–G30, exact predecessor, 59/100; no stale G24 WAIT marker | 0 | current deterministic |
| `node -p [full text in section below, command 3]` | Markdown/HTML panels and 22-record ledger complete | 0 | current deterministic |
| `node -p [full text in section below, command 4]` | seven Goal prompts, Human gate, redaction fields, stop guards present | 0 | current deterministic |
| `node -p [full text in section below, corrected command 5]` | project score shape mismatch (`project_score` is an object) | 1 | reviewer/tool failure; corrected below |
| `node -p [full text in section below, corrected command 6]` | 22 records; WP weights 70 + CP-00/02 base 30; total 100; earned 59 | 0 | current deterministic |
| `node -p [full text in section below, command 7]` | current Markdown/HTML blocks have no stale WAIT or combined WP status; review marker present | 0 | current deterministic |
| independent read-only reviewer | docs-only diff, ledger, score, boundaries, validators; no findings; BLOCKER/MAJOR/MINOR 0 | N/A | independent review; process exit not applicable |
| `node -p [full text in section below, current-panel command 7]` | current panel has no stale WAIT or combined invalid WP status | 0 | current deterministic |
| `C:\temp_pn_venv2\Scripts\python.exe -B scripts\validate_baseline.py` (sandbox attempt) | controlled launcher could not create process | 1 | environment blocker; retried elevated |
| `C:\temp_pn_venv2\Scripts\python.exe -B scripts\validate_baseline.py` (approved elevated retry) | 11 required files; workflows valid; MV3 manifest valid | 0 | current deterministic |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\validate-polynexus-governance.ps1 -RepoRoot "C:\Users\hikar\.codex\visualizations\2026\09\02\01a061a4-b06c-7183-88f8-4e4ab76d10bb\g24-lane"` | governance files, manifest, JSON, protected exclusions valid | 0 | current deterministic |
| `git diff --check` | clean | 0 | current deterministic |
| `git diff --name-status` | nine tracked documentation files modified | 0 | current deterministic |
| `git diff --cached --name-status` | empty | 0 | current gate |
| `git status --short --ignored` | tracked changes plus ignored G24 artifact directory; no staged changes | 0 | current deterministic |
| independent reviewer attempt 1 | reviewer opened protected primary; no G24 review performed | N/A | reviewer routing failure; NEED_FIX BLOCKER=1 |
| independent reviewer reroute to exact G24 lane | VERIFIED_PASS; BLOCKER=0; MAJOR=0; MINOR=0; no files modified | N/A | current independent review |

The ignored artifact directory is intentional under the repository's existing
`artifacts/` ignore rule and must be included explicitly with `git add -f` only
if the Human authorizes this exact final allowlist.

7. `node -p "const fs=require('fs'); const files=['docs/11_PROJECT_STATE.md','docs/12_HANDOFF_CURRENT.md','docs/28_MASTER_DEVELOPMENT_ROADMAP.md','docs/31_COMPATIBILITY_MATRIX.md','docs/32_KNOWN_LIMITATIONS.md','docs/GOAL_COMPLETION_CONTROL_PANEL.md','docs/GOAL_COMPLETION_CONTROL_PANEL.html']; const s=files.map(f=>fs.readFileSync(f,'utf8')).join('\\n'); for(const x of ['G24','G30','59/100','NOTE_ONLY_NON_SCORING','fde4c8f1d017992755c6af2bd600c9bd715efd6b','VERIFIED_PASS_PENDING_HUMAN']) if(!s.includes(x)) throw Error('missing '+x); if(s.includes('G24_STATUS: WAIT')||s.includes('G24_START_SHA: PENDING')) throw Error('stale G24 marker'); const current=fs.readFileSync('docs/GOAL_COMPLETION_CONTROL_PANEL.md','utf8').split('## G23 final reconciliation')[0]; if(current.includes('WAIT_FOR_PLANNING_CHECKPOINT')||current.includes('HUMAN_ACCEPTED / BOUNDED')||current.includes('PLANNED / EXTERNAL_LATE')) throw Error('stale current panel status'); console.log('CURRENT_STATE_MARKER_PASS files='+files.length+' current-panel-boundary=clean')"`

## Full command text

The following are the complete inline Node.js commands represented by post-edit
validation commands 1–4 above. Command 1 exposed a field-name mismatch in the
first assertion and returned exit code `1`; corrected command 5 uses the
ledger's uppercase record keys and initially exposed the project-score object
shape, returning exit code `1`; corrected command 6 validates that object and
returned exit code `0`. Commands 2–4 also returned exit code `0`.

1. `node -p "const j=require('./artifacts/verification/g24-development-ledger-20260902/ledger.json'); const allowed=['PLANNED','IMPLEMENTING','IMPLEMENTED_PENDING_REVIEW','READY_FOR_INDEPENDENT_REVIEW','NEED_ACTION','FAIL','VERIFIED_PASS_PENDING_HUMAN','HUMAN_ACCEPTED','CHECKPOINTED']; if(j.records.length!==22) throw Error('records'); const wp=j.records.reduce((n,r)=>n+r.point_weight,0); const base=j.checkpoint_allocations.reduce((n,r)=>n+r.point_weight,0); const earned=j.records.reduce((n,r)=>n+r.accepted_points,0)+j.checkpoint_allocations.reduce((n,r)=>n+r.accepted_points,0); for(const r of j.records){if(!allowed.includes(r.current_status)) throw Error(r.wp_id+' status'); for(const k of ['wp_id','checkpoint','point_weight','current_status','accepted_points','implementation_ref','review_ref','acceptance_ref','checkpoint_sha','test_commands','actual_exit_codes','artifact_refs','known_limitations','unverified','adr_impact','scope_deviation','last_updated']) if(!(k in r)) throw Error(r.wp_id+' '+k); if(!['HUMAN_ACCEPTED','CHECKPOINTED'].includes(r.current_status) && r.accepted_points!==0) throw Error(r.wp_id+' score');} if(wp+base!==100||earned!==59||j.goal_score_delta!==0||j.project_score!==59||j.competition.track!=='NOTE_ONLY_NON_SCORING') throw Error('score'); console.log('LEDGER_SCHEMA_SCORE_PASS records='+j.records.length+' wp_weights='+wp+' base_weights='+base+' weights='+(wp+base)+' earned='+earned)"`

2. `node -p "const fs=require('fs'); const files=['docs/11_PROJECT_STATE.md','docs/12_HANDOFF_CURRENT.md','docs/28_MASTER_DEVELOPMENT_ROADMAP.md','docs/31_COMPATIBILITY_MATRIX.md','docs/32_KNOWN_LIMITATIONS.md','docs/GOAL_COMPLETION_CONTROL_PANEL.md','docs/GOAL_COMPLETION_CONTROL_PANEL.html']; const s=files.map(f=>fs.readFileSync(f,'utf8')).join('\\n'); for(const x of ['G24','G30','59/100','NOTE_ONLY_NON_SCORING','fde4c8f1d017992755c6af2bd600c9bd715efd6b','VERIFIED_PASS_PENDING_HUMAN']) if(!s.includes(x)) throw Error('missing '+x); if(s.includes('G24_STATUS: WAIT')||s.includes('G24_START_SHA: PENDING')) throw Error('stale G24 marker'); console.log('CURRENT_STATE_MARKER_PASS files='+files.length)"`

3. `node -p "const fs=require('fs'); const j=require('./artifacts/verification/g24-development-ledger-20260902/ledger.json'); for(const f of ['docs/GOAL_COMPLETION_CONTROL_PANEL.md','docs/GOAL_COMPLETION_CONTROL_PANEL.html']){const s=fs.readFileSync(f,'utf8'); for(const x of ['WP-11','WP-32','59/100','G24','G30']) if(!s.includes(x)) throw Error(f+' missing '+x);} const fields=['WP_ID','CHECKPOINT','POINT_WEIGHT','CURRENT_STATUS','ACCEPTED_POINTS','IMPLEMENTATION_REF','REVIEW_REF','ACCEPTANCE_REF','CHECKPOINT_SHA','TEST_COMMANDS','ACTUAL_EXIT_CODES','ARTIFACT_REFS','KNOWN_LIMITATIONS','UNVERIFIED','ADR_IMPACT','SCOPE_DEVIATION','LAST_UPDATED']; const raw=fs.readFileSync('./artifacts/verification/g24-development-ledger-20260902/ledger.json','utf8'); for(const f of fields) if(!raw.toUpperCase().includes(f)) throw Error('field '+f); if(j.records.length!==22) throw Error('ledger records'); console.log('PANEL_COMPLETENESS_PASS markdown/html/ledger records='+j.records.length)"`

4. `node -p "const fs=require('fs'); const s=fs.readFileSync('docs/tasks/G24-G30-DEVELOPMENT-COMPLETION-ROUTING.md','utf8').replaceAll(String.fromCharCode(10),' '); for(const g of ['G24','G25','G26','G27','G28','G29','G30']) if(!s.includes(g)) throw Error('goal '+g); for(const x of ['MODEL PROFILE','PREDECESSOR_SHA','OUTPUT_SHA','ACCEPT_AND_COMMIT_PUSH','Do not start G25','Do not start G30','credential','cookie','token','EXIT_CODE: N/A']) if(!s.includes(x)) throw Error('schema '+x); console.log('PROMPT_SCHEMA_PASS goals=7 human-gate=present redaction=N/A')"`

5. `node -p "const j=require('./artifacts/verification/g24-development-ledger-20260902/ledger.json'); const records=j.records.map(r=>({...r,wp_id:r.WP_ID,point_weight:r.POINT_WEIGHT,current_status:r.CURRENT_STATUS,accepted_points:r.ACCEPTED_POINTS})); const allowed=['PLANNED','IMPLEMENTING','IMPLEMENTED_PENDING_REVIEW','READY_FOR_INDEPENDENT_REVIEW','NEED_ACTION','FAIL','VERIFIED_PASS_PENDING_HUMAN','HUMAN_ACCEPTED','CHECKPOINTED']; if(records.length!==22) throw Error('records'); const wp=records.reduce((n,r)=>n+r.point_weight,0); const base=j.checkpoint_allocations.reduce((n,r)=>n+r.point_weight,0); const earned=records.reduce((n,r)=>n+r.accepted_points,0)+j.checkpoint_allocations.reduce((n,r)=>n+r.accepted_points,0); for(const r of records){if(!allowed.includes(r.current_status)) throw Error(r.wp_id+' status'); const original=j.records.find(x=>x.WP_ID===r.WP_ID); for(const k of ['WP_ID','CHECKPOINT','POINT_WEIGHT','CURRENT_STATUS','ACCEPTED_POINTS','IMPLEMENTATION_REF','REVIEW_REF','ACCEPTANCE_REF','CHECKPOINT_SHA','TEST_COMMANDS','ACTUAL_EXIT_CODES','ARTIFACT_REFS','KNOWN_LIMITATIONS','UNVERIFIED','ADR_IMPACT','SCOPE_DEVIATION','LAST_UPDATED']) if(!(k in original)) throw Error(r.wp_id+' '+k); if(!['HUMAN_ACCEPTED','CHECKPOINTED'].includes(r.current_status) && r.accepted_points!==0) throw Error(r.wp_id+' score');} if(wp+base!==100||earned!==59||j.goal_score_delta!==0||j.project_score!==59||j.competition.track!=='NOTE_ONLY_NON_SCORING') throw Error('score'); console.log('LEDGER_SCHEMA_SCORE_PASS records='+records.length+' wp_weights='+wp+' base_weights='+base+' weights='+(wp+base)+' earned='+earned)"`

6. `node -p "const j=require('./artifacts/verification/g24-development-ledger-20260902/ledger.json'); const records=j.records.map(r=>({...r,wp_id:r.WP_ID,point_weight:r.POINT_WEIGHT,current_status:r.CURRENT_STATUS,accepted_points:r.ACCEPTED_POINTS})); const allowed=j.allowed_statuses; if(records.length!==22) throw Error('records'); const wp=records.reduce((n,r)=>n+r.point_weight,0); const base=j.checkpoint_allocations.reduce((n,r)=>n+r.POINT_WEIGHT,0); const earned=records.reduce((n,r)=>n+r.accepted_points,0)+j.checkpoint_allocations.reduce((n,r)=>n+r.ACCEPTED_POINTS,0); for(const r of records){if(!allowed.includes(r.current_status)) throw Error(r.wp_id+' status'); const original=j.records.find(x=>x.WP_ID===r.WP_ID); for(const k of ['WP_ID','CHECKPOINT','POINT_WEIGHT','CURRENT_STATUS','ACCEPTED_POINTS','IMPLEMENTATION_REF','REVIEW_REF','ACCEPTANCE_REF','CHECKPOINT_SHA','TEST_COMMANDS','ACTUAL_EXIT_CODES','ARTIFACT_REFS','KNOWN_LIMITATIONS','UNVERIFIED','ADR_IMPACT','SCOPE_DEVIATION','LAST_UPDATED']) if(!(k in original)) throw Error(r.wp_id+' '+k); if(!['HUMAN_ACCEPTED','CHECKPOINTED'].includes(r.current_status) && r.accepted_points!==0) throw Error(r.wp_id+' score');} if(wp+base!==100||earned!==59||j.goal_score_delta!==0||j.project_score.earned!==59||j.project_score.weight!==100||j.competition.track!=='NOTE_ONLY_NON_SCORING'||j.competition.project_progress_impact!=='NONE'||j.competition.delivery_owner!=='HUMAN') throw Error('score'); console.log('LEDGER_SCHEMA_SCORE_PASS records='+records.length+' wp_weights='+wp+' base_weights='+base+' weights='+(wp+base)+' earned='+earned)"`

7. `node -p "const fs=require('fs'); const md=fs.readFileSync('docs/GOAL_COMPLETION_CONTROL_PANEL.md','utf8'); const current=md.split('## G23 final reconciliation')[0]; const html=fs.readFileSync('docs/GOAL_COMPLETION_CONTROL_PANEL.html','utf8'); const htmlCurrent=html.split('<h2>G23 final reconciliation')[0]; for(const s of [current,htmlCurrent]) for(const x of ['WAIT_FOR_PLANNING_CHECKPOINT','HUMAN_ACCEPTED / BOUNDED','PLANNED / EXTERNAL_LATE']) if(s.includes(x)) throw Error('stale current marker '+x); if(!current.includes('G24')||!current.includes('VERIFIED_PASS_PENDING_HUMAN')||!current.includes('INDEPENDENT_REVIEW')||!htmlCurrent.includes('VERIFIED_PASS')) throw Error('review/current'); console.log('CURRENT_BOUNDARY_PASS no-stale-current-WAIT-or-combined-status')"`
