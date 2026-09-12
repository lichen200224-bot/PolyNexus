"""Fault-inject only temporary planning data; no product tests or independent verdict."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = json.loads((ROOT / 'FEATURE_SCOPE_MATRIX.json').read_text(encoding='utf-8'))
TRACE = json.loads((ROOT / 'ASSURANCE_TRACEABILITY.json').read_text(encoding='utf-8'))
cases = [('valid', MATRIX, TRACE, 0, 'PASS_PLANNING_STRUCTURE_ONLY')]

def mutation(name, matrix_fn=None, trace_fn=None, reason=''):
    m, t = copy.deepcopy(MATRIX), copy.deepcopy(TRACE)
    if matrix_fn:
        matrix_fn(m)
    if trace_fn:
        trace_fn(t)
    cases.append((name, m, t, 1, reason))

mutation('duplicate-PN', lambda m: m['packages'][0]['items'][0].__setitem__(0, 1), reason='duplicate PN')
mutation('cycle', lambda m: m['packages'][0].__setitem__('deps', ['FD-04']), reason='Dependency cycle')
mutation('missing-limits', lambda m: m['packages'][0].__setitem__('forbidden', []), reason='missing forbidden')
mutation('silent-start', lambda m: m.__setitem__('product_implementation', 'AUTHORIZED'), reason='must not authorize')
mutation('missing-PN078', lambda m: next(p for p in m['packages'] if p['id']=='FD-12')['items'].pop(), reason='PN sets differ')
for i, entry in enumerate(TRACE['values']):
    name = entry['kind'] + '-' + entry['value']
    mutation('remove-mapping-' + name, trace_fn=lambda t, i=i: t['values'].pop(i), reason='source-value coverage gap')
    def strip_value(m, index=entry['subitem']-1, value=entry['value']):
        row = next(r for p in m['packages'] for r in p['items'] if r[0]==78)
        parts = row[1].split('；')
        parts[index] = parts[index].replace(value, 'REMOVED')
        row[1] = '；'.join(parts)
    mutation('remove-subitem-value-' + name, strip_value, reason='source value absent')
mutation('missing-source', trace_fn=lambda t: t['sources'].pop('scope'), reason='source mapping differs')
mutation('missing-clause', trace_fn=lambda t: t['clauses'].pop(0), reason='source-clause mapping')
mutation('missing-oracle', trace_fn=lambda t: t['tests'].pop(0), reason='oracle unresolved')
mutation('wrong-owner', trace_fn=lambda t: t['values'][0].__setitem__('fd','FD-19'), reason='primary FD-12')
mutation('metric-authority', trace_fn=lambda t: t['metric'].__setitem__('can_authorize_acceptance',True), reason='cannot create/authorize')
mutation('metric-event', trace_fn=lambda t: t['metric'].__setitem__('can_create_acceptance_event',True), reason='cannot create/authorize')
mutation('metric-missing-case', trace_fn=lambda t: t['metric']['cases'].pop(), reason='Metric oracles missing')
results=[]
with tempfile.TemporaryDirectory(prefix='polynexus-docs-repair-selftest-') as folder:
    for name, matrix, trace, expected, reason in cases:
        mp, tp = Path(folder)/'matrix.json', Path(folder)/'trace.json'
        mp.write_text(json.dumps(matrix,ensure_ascii=False),encoding='utf-8')
        tp.write_text(json.dumps(trace,ensure_ascii=False),encoding='utf-8')
        command=[sys.executable,'-B',str(ROOT/'checks/validate_feature_scope.py'),
                 '--matrix',str(mp),'--trace',str(tp),'--requirements',str(ROOT/'REQUIREMENTS.md')]
        run=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',timeout=15)
        text=run.stdout+run.stderr
        matched=run.returncode==expected and reason in text
        results.append({'case':name,'expected_exit':expected,'actual_exit':run.returncode,
                        'expected_reason_observed':reason in text,'matched':matched})
        if not matched:
            results[-1]['diagnostic']=text[:1500]
passed=all(r['matched'] for r in results)
print(json.dumps({'result':'PASS' if passed else 'FAIL','scope':'PLANNING_VALIDATOR_SELFTEST_ONLY',
                  'cases':results,'case_count':len(results),'product_tests':'NOT_RUN',
                  'independent_review':'NOT_RUN'},ensure_ascii=False,indent=2))
raise SystemExit(0 if passed else 1)
