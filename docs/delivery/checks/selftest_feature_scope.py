"""Exercise the planning validator with one valid input and four forbidden mutations."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
validator = root / 'checks' / 'validate_feature_scope.py'
original = json.loads((root / 'FEATURE_SCOPE_MATRIX.json').read_text(encoding='utf-8'))
cases = [('valid-matrix', original, 0)]
x = copy.deepcopy(original)
x['packages'][0]['items'][0][0] = 1
cases.append(('duplicate-and-missing-PN', x, 1))
x = copy.deepcopy(original)
x['packages'][0]['deps'] = ['FD-04']
cases.append(('dependency-cycle', x, 1))
x = copy.deepcopy(original)
x['packages'][0]['forbidden'] = []
cases.append(('missing-limits', x, 1))
x = copy.deepcopy(original)
x['product_implementation'] = 'AUTHORIZED'
cases.append(('silent-start-authorization', x, 1))
results = []
with tempfile.TemporaryDirectory(prefix='polynexus-plan-selftest-') as temporary:
    for name, data, expected in cases:
        path = Path(temporary) / (name + '.json')
        path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        process = subprocess.run([sys.executable, str(validator), '--matrix', str(path)],
                                 capture_output=True, text=True, encoding='utf-8', timeout=15)
        results.append({'case': name, 'expected_exit': expected,
                        'actual_exit': process.returncode, 'matched': process.returncode == expected})
passed = all(result['matched'] for result in results)
print(json.dumps({'result': 'PASS' if passed else 'FAIL', 'scope': 'PLANNING_VALIDATOR_SELFTEST_ONLY',
                  'cases': results, 'product_tests': 'NOT_RUN',
                  'independent_design_review': 'NOT_RUN'}, ensure_ascii=False, indent=2))
raise SystemExit(0 if passed else 1)
