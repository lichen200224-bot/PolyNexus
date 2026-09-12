"""Planning structure and pinned Assurance traceability only; not product/independent PASS."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

FORMAL = '43aa27c8b7a1b950645acc0d41234ec7679b653e'
# These are immutable source identities, not a hard-coded feature/test count.
SOURCE_PINS = {
    'scope': ('00_SCOPE_BASELINE.md', '57558a3643ff37538d84fc560d23e0c9e28b6cee'),
    'prd': ('01_PRD.md', 'fc34c1a734d62e9025eea2f99aaca42bc655b22d'),
    'human': ('35_D11_A_LP_LOCAL_HUMAN_DECISION_PROTOCOL.md', 'e8d143fe1e5e4166ba132a185130b22df54ebbb1'),
}
REQUIRED_CLAUSES = {'SCOPE-BASE-04', 'ASSURANCE-MODE', 'ASSURANCE-STATUS',
                    'FORMAL-PRD-ASSURANCE', 'METRIC-08', 'D11-NO-OVERRIDE'}


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def nonempty(value: Any, where: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{where}: expected nonempty string')


def validate(data: dict[str, Any], requirements: str, trace: dict[str, Any],
             root: Path) -> dict[str, Any]:
    if data.get('product_implementation') != 'HOLD_PENDING_START_GATES':
        raise ValueError('Preparation must not authorize product implementation')
    if data.get('assurance_traceability') != 'ASSURANCE_TRACEABILITY.json':
        raise ValueError('Missing Assurance traceability entry')
    packages = data.get('packages')
    if not isinstance(packages, list) or not packages:
        raise ValueError('Missing packages')
    req_ids = re.findall(r'^\| PN-(\d{3}) \|', requirements, re.MULTILINE)
    if not req_ids or len(req_ids) != len(set(req_ids)):
        raise ValueError('REQUIREMENTS.md missing/duplicate PN rows')
    expected = {int(n) for n in req_ids}
    by_id: dict[str, dict[str, Any]] = {}
    owner: dict[int, str] = {}
    parts: dict[int, list[str]] = {}
    for package in packages:
        ident = package.get('id')
        if not isinstance(ident, str) or not re.fullmatch(r'FD-\d{2}', ident) or ident in by_id:
            raise ValueError(f'Duplicate/invalid package: {ident}')
        by_id[ident] = package
        for key in ('title', 'batch'):
            nonempty(package.get(key), f'{ident}/{key}')
        for key in ('areas', 'forbidden', 'inputs', 'outputs', 'sit_positive', 'sit_negative'):
            value = package.get(key)
            if not isinstance(value, list) or not value:
                raise ValueError(f'{ident}: missing {key}')
            for item in value:
                nonempty(item, f'{ident}/{key}')
        for key in ('deps', 'uat', 'items'):
            if not isinstance(package.get(key), list):
                raise ValueError(f'{ident}: {key} must be array')
        if ident != 'FD-22' and not package['uat']:
            raise ValueError(f'{ident}: product package lacks UAT')
        for uat in package['uat']:
            if uat not in {f'HU-{n:02d}' for n in range(1, 13)}:
                raise ValueError(f'{ident}: unknown UAT {uat}')
        if not package['items']:
            raise ValueError(f'{ident}: no primary requirements')
        for row in package['items']:
            if not isinstance(row, list) or len(row) != 3:
                raise ValueError(f'{ident}: item must be [PN, subitems, limits]')
            number, features, limits = row
            if type(number) is not int or number not in expected or number in owner:
                raise ValueError(f'{ident}: invalid/duplicate PN {number}')
            nonempty(features, f'{ident}/features')
            nonempty(limits, f'{ident}/limits')
            split = [s.strip() for s in features.split('；') if s.strip()]
            if len(split) < 2:
                raise ValueError(f'{ident}/PN-{number:03d}: not decomposed')
            owner[number], parts[number] = ident, split
    if set(owner) != expected:
        raise ValueError('Matrix and REQUIREMENTS.md PN sets differ')
    done: set[str] = set()
    active: set[str] = set()
    order: list[str] = []

    def visit(ident: str) -> None:
        if ident not in by_id:
            raise ValueError(f'Unknown dependency {ident}')
        if ident in active:
            raise ValueError(f'Dependency cycle {ident}')
        if ident in done:
            return
        active.add(ident)
        for dep in by_id[ident]['deps']:
            visit(dep)
        active.remove(ident)
        done.add(ident)
        order.append(ident)

    for ident in by_id:
        visit(ident)
    # Read verified bytes, so copying an enum list into the mutable matrix is not authority.
    texts: dict[str, str] = {}
    sources = trace.get('sources', {})
    for key, (name, pinned) in SOURCE_PINS.items():
        expected_source = {'commit': FORMAL, 'repo_path': f'docs/{name}',
                           'local_path': f'references/formal/{name}', 'blob': pinned}
        if sources.get(key) != expected_source:
            raise ValueError(f'{key}: source mapping differs from pinned authority')
        raw = (root / expected_source['local_path']).read_bytes()
        if blob_sha(raw) != pinned:
            raise ValueError(f'{key}: source bytes differ from pin')
        texts[key] = raw.decode('utf-8')
    scope = texts['scope']
    modes_section = scope.split('### Assurance Mode\n', 1)[1].split('### Assurance Status', 1)[0]
    statuses_section = scope.split('### Assurance Status\n', 1)[1].split('平台不可關閉底線', 1)[0]
    ordered_values = [('mode', value) for value in re.findall(r'^- ([A-Z_]+)$', modes_section, re.M)]
    ordered_values += [('status', value) for value in re.findall(r'^- ([A-Z_]+)$', statuses_section, re.M)]
    wanted = set(ordered_values)
    if not wanted or 'human override' not in texts['prd'] or 'Override Accept' not in texts['human']:
        raise ValueError('Pinned authority sections unavailable')
    clauses = trace.get('clauses', [])
    if len(clauses) != len(REQUIRED_CLAUSES) or {c.get('id') for c in clauses} != REQUIRED_CLAUSES:
        raise ValueError('Missing/duplicate required source-clause mapping')
    expected_clause_owners = {
        'SCOPE-BASE-04': ('scope', {'PN-078'}), 'ASSURANCE-MODE': ('scope', {'PN-078'}),
        'ASSURANCE-STATUS': ('scope', {'PN-078'}), 'FORMAL-PRD-ASSURANCE': ('prd', {'PN-078'}),
        'METRIC-08': ('prd', {'PN-038'}), 'D11-NO-OVERRIDE': ('human', {'PN-038', 'PN-053', 'PN-078'})}
    for clause in clauses:
        src, pns = expected_clause_owners[clause['id']]
        if clause.get('source') != src or set(clause.get('pn', [])) != pns:
            raise ValueError('Required clause/owner/source resolution mismatch')
        if clause.get('source') not in sources:
            raise ValueError('Unresolved clause source')
        nonempty(clause.get('section'), 'source section')
        if not clause.get('pn') or any(int(p[3:]) not in owner for p in clause['pn']):
            raise ValueError('Clause has no mapped PN owner')
    entries = trace.get('values', [])
    keys = [(e.get('kind'), e.get('value')) for e in entries]
    if len(keys) != len(set(keys)) or set(keys) != wanted:
        raise ValueError('Assurance Mode/Status source-value coverage gap')
    contract = (root / 'ASSURANCE_CONTRACT.md').read_text(encoding='utf-8')
    cases: set[str] = set()
    for entry in entries:
        if entry.get('pn') != 'PN-078' or entry.get('fd') != owner.get(78) or owner.get(78) != 'FD-12':
            raise ValueError('Assurance must resolve to PN-078 / primary FD-12')
        sub = entry.get('subitem')
        if type(sub) is not int or not 1 <= sub <= len(parts[78]):
            raise ValueError('Missing Assurance subitem')
        if sub != ordered_values.index((entry['kind'], entry['value'])) + 1:
            raise ValueError('Wrong per-value subitem index')
        if entry.get('positive') != f'AT-078-P{sub:02d}' or entry.get('negative') != f'AT-078-N{sub:02d}':
            raise ValueError('Wrong per-value oracle identity')
        if entry['value'] not in parts[78][sub - 1]:
            raise ValueError(f"PN-078.{sub:02d}: source value absent")
        expected_clause = 'ASSURANCE-MODE' if entry['kind'] == 'mode' else 'ASSURANCE-STATUS'
        if entry.get('source_clause') != expected_clause:
            raise ValueError('Wrong per-value source clause')
        for key in ('design', 'positive', 'negative', 'sit', 'uat'):
            nonempty(entry.get(key), f'{entry["value"]}/{key}')
        if entry['sit'] != 'SIT-15' or entry['uat'] not in by_id['FD-12']['uat']:
            raise ValueError('Assurance SIT/UAT unresolved')
        if entry['design'] != f'ASSURANCE_CONTRACT.md#{"modes" if entry["kind"] == "mode" else "statuses"}':
            raise ValueError('Assurance design anchor mismatch')
    # Concrete test definitions are declared plans, never claimed executed.
    tests = trace.get('tests', [])
    for case in tests:
        ident = case.get('id')
        if not isinstance(ident, str) or ident in cases:
            raise ValueError('Duplicate/missing concrete case ID')
        cases.add(ident)
        for key in ('input', 'expected', 'forbidden_effect'):
            nonempty(case.get(key), f'{ident}/{key}')
    for entry in entries:
        if entry['positive'] not in cases or entry['negative'] not in cases:
            raise ValueError('Assurance concrete oracle unresolved')
    for n in range(1, len(parts[78]) + 1):
        if not {f'AT-078-P{n:02d}', f'AT-078-N{n:02d}'}.issubset(cases):
            raise ValueError('Assurance subitem lacks concrete P/N definition')
    metric = trace.get('metric', {})
    if metric.get('pn') != 'PN-038' or metric.get('fd') != 'FD-19' or owner.get(38) != 'FD-19':
        raise ValueError('Metric owner unresolved')
    if metric.get('legacy_name') != 'human override' or metric.get('canonical_key') != 'human_ai_recommendation_disagreement_count':
        raise ValueError('Metric name resolution missing')
    if metric.get('can_authorize_acceptance') is not False or metric.get('can_create_acceptance_event') is not False:
        raise ValueError('Metric cannot create/authorize Human acceptance')
    metric_cases = {'AT-038-MP01', 'AT-038-MP02', 'AT-038-MN01', 'AT-038-MN02'}
    if set(metric.get('cases', [])) != metric_cases or not metric_cases.issubset(cases) or len(metric['cases']) != len(metric_cases):
        raise ValueError('Metric oracles missing')
    if metric['canonical_key'] not in contract or 'Override Accept' not in contract:
        raise ValueError('Metric contract resolution missing')
    # Cross-file links must exist and explicitly bind the repair, not a bare AT number.
    required_links = {'REQUIREMENTS.md', 'FEATURE_WORK_PACKAGES.md', 'PRD.md', 'SA.md', 'SD.md',
                      'DATA_AND_API.md', 'UX_SPEC.md', 'TEST_PLAN.md', 'OPERATIONS.md', 'UAT_AND_RELEASE.md'}
    links = trace.get('required_design_links', [])
    if len(links) != len(required_links) or set(links) != required_links:
        raise ValueError('Missing/invalid cross-file traceability set')
    for name in links:
        text = (root / name).read_text(encoding='utf-8')
        if 'ASSURANCE_CONTRACT.md' not in text or not ('PN-078' in text or 'PN-038' in text):
            raise ValueError(f'{name}: missing explicit repair contract link')
    if not trace.get('required_design_links'):
        raise ValueError('Missing cross-file traceability checks')
    return {'packages': len(packages), 'requirement_rows': len(owner),
            'functional_subitems': sum(len(v) for v in parts.values()),
            'planned_positive_negative_ut_case_groups': len(owner) * 2,
            'case_group_basis': 'PN count times P/N naming rule, NOT implemented/executed tests',
            'assurance_source_values': len(wanted), 'declared_repair_test_cases': len(cases),
            'unique_primary_assignment': True, 'package_dependency_dag': True,
            'topological_order': order, 'requirements_file_id_check': 'PASS',
            'pinned_assurance_mapping_check': 'PASS_LIMITED_EXPLICIT_MAPPING_ONLY',
            'full_semantic_source_coverage': 'INDEPENDENT_REVIEW_REQUIRED',
            'product_test_execution': 'NOT_RUN', 'independent_design_review': 'NOT_RUN'}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--matrix', type=Path, default=root / 'FEATURE_SCOPE_MATRIX.json')
    p.add_argument('--requirements', type=Path, default=root / 'REQUIREMENTS.md')
    p.add_argument('--trace', type=Path, default=root / 'ASSURANCE_TRACEABILITY.json')
    args = p.parse_args()
    try:
        raw = args.matrix.read_bytes()
        result = validate(json.loads(raw.decode('utf-8')), args.requirements.read_text(encoding='utf-8'),
                          json.loads(args.trace.read_text(encoding='utf-8')), root)
        result.update(result='PASS_PLANNING_STRUCTURE_ONLY', matrix_sha256=hashlib.sha256(raw).hexdigest(),
                      matrix_git_blob_sha=blob_sha(raw))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError, RecursionError) as exc:
        print(json.dumps({'result': 'FAIL', 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
