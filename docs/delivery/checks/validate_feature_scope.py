"""Validate planning structure only; never certifies product or independent review."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


def validate(data: dict[str, Any]) -> dict[str, Any]:
    if data.get('product_implementation') != 'HOLD_PENDING_START_GATES':
        raise ValueError('Preparation must not silently authorize product implementation')
    packages = data.get('packages')
    if not isinstance(packages, list) or len(packages) != 22:
        raise ValueError('Expected 22 explicit feature work packages')
    by_id: dict[str, dict[str, Any]] = {}
    requirements: list[int] = []
    subitems = 0
    for package in packages:
        ident = package.get('id')
        if not isinstance(ident, str) or not re.fullmatch(r'FD-\d{2}', ident) or ident in by_id:
            raise ValueError(f'Duplicate or invalid package: {ident}')
        by_id[ident] = package
        for field in ('title', 'batch', 'areas', 'forbidden', 'inputs', 'outputs', 'sit_positive', 'sit_negative', 'items'):
            if not package.get(field):
                raise ValueError(f'{ident}: missing contract field {field}')
        if not isinstance(package.get('deps'), list) or not isinstance(package.get('uat'), list):
            raise ValueError(f'{ident}: deps/uat must be arrays')
        if ident != 'FD-22' and not package['uat']:
            raise ValueError(f'{ident}: product package lacks Human UAT mapping')
        for uat in package['uat']:
            if uat not in {f'HU-{n:02d}' for n in range(1, 13)}:
                raise ValueError(f'{ident}: unknown Human UAT {uat}')
        for row in package['items']:
            if not isinstance(row, list) or len(row) != 3:
                raise ValueError(f'{ident}: item must be [PN number, subitems, limits]')
            number, features, limits = row
            if type(number) is not int or not 1 <= number <= 77:
                raise ValueError(f'{ident}: invalid PN number {number}')
            if not isinstance(features, str) or not isinstance(limits, str) or not limits.strip():
                raise ValueError(f'{ident}/PN-{number:03d}: absent feature/negative oracle')
            parts = [s.strip() for s in features.split('；') if s.strip()]
            if len(parts) < 2:
                raise ValueError(f'{ident}/PN-{number:03d}: subitems not decomposed')
            requirements.append(number)
            subitems += len(parts)
    if len(requirements) != 77 or set(requirements) != set(range(1, 78)):
        raise ValueError('PN-001..077 must each have exactly one primary owner')
    done: set[str] = set()
    active: set[str] = set()
    order: list[str] = []

    def visit(ident: str) -> None:
        if ident not in by_id:
            raise ValueError(f'Unknown dependency: {ident}')
        if ident in active:
            raise ValueError(f'Dependency cycle: {ident}')
        if ident in done:
            return
        active.add(ident)
        for dependency in by_id[ident]['deps']:
            visit(dependency)
        active.remove(ident)
        done.add(ident)
        order.append(ident)

    for ident in by_id:
        visit(ident)
    return {'packages': len(packages), 'requirement_rows': len(requirements), 'functional_subitems': subitems,
            'planned_positive_negative_ut_case_groups': 154, 'unique_primary_assignment': True,
            'package_dependency_dag': True, 'topological_order': order,
            'product_test_execution': 'NOT_RUN', 'independent_design_review': 'NOT_RUN'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix', type=Path, default=Path(__file__).resolve().parents[1] / 'FEATURE_SCOPE_MATRIX.json')
    parser.add_argument('--requirements', type=Path, help='Optional actual REQUIREMENTS.md for cross-file ID checks')
    args = parser.parse_args()
    try:
        raw = args.matrix.read_bytes()
        summary = validate(json.loads(raw.decode('utf-8')))
        if args.requirements is not None:
            ids = re.findall(r'^\| PN-(\d{3}) \|', args.requirements.read_text(encoding='utf-8'), re.MULTILINE)
            if len(ids) != 77 or {int(s) for s in ids} != set(range(1, 78)):
                raise ValueError('REQUIREMENTS.md PN rows differ from scope matrix')
            summary['requirements_file_id_check'] = 'PASS'
        else:
            summary['requirements_file_id_check'] = 'NOT_RUN'
        summary['matrix_sha256'] = hashlib.sha256(raw).hexdigest()
        summary['matrix_git_blob_sha'] = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        summary['result'] = 'PASS_PLANNING_STRUCTURE_ONLY'
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
        print(json.dumps({'result': 'FAIL', 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
