"""Read-only single-ZIP mechanical gate. Semantic evidence review remains required."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile

REQUIRED = {
    'START_HERE.md', 'REVIEW_PACKET.md', 'HUMAN_REQUEST.txt',
    'GIT_REVIEW_CANDIDATE.txt', 'CHANGED_FILE_ALLOWLIST.txt',
    'THIS_ROUND_DIFF.patch', 'VALIDATION_RESULTS.md',
    'ENVIRONMENT_FINGERPRINT.md', 'MANIFEST_SHA256.txt',
}
ROLES = {'CREATED', 'MODIFIED', 'REFERENCE', 'EVIDENCE', 'CONTROL', 'GIT_BUNDLE'}
FORBIDDEN_PARTS = {'.git', '.venv', 'node_modules', '__pycache__', 'dist', 'cache',
                   'browser-profile', 'browser_profiles', 'cookies', 'login data'}
SECRET_PATTERNS = [rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                   rb'\bsk-[A-Za-z0-9_-]{24,}', rb'\bghp_[A-Za-z0-9]{30,}']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def control(data):
    text = data.decode('utf-8')
    match = re.search(r'```json\s*\n(.*?)\n```', text, re.S)
    return json.loads(match.group(1) if match else text)


def git(repo, *args):
    result = subprocess.run(['git', '-c', 'safe.directory=' + repo.as_posix(),
                             '-C', str(repo), *args], capture_output=True)
    if result.returncode:
        raise ValueError('Git command failed: ' + ' '.join(args))
    return result.stdout


def validate(archive, repo, candidate, predecessor, expected_zip_sha=None):
    failures = []

    def require(ok, name):
        if not ok:
            failures.append(name)

    require(bool(re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', candidate)), 'exact C')
    require(bool(re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', predecessor)), 'exact P')
    if expected_zip_sha:
        require(sha(archive.read_bytes()) == expected_zip_sha, 'external ZIP hash')
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        require(len(names) == len(set(names)), 'duplicate archive paths')
        require(len(names) == len({n.casefold() for n in names}), 'case collision')
        for name in names:
            parts = PurePosixPath(name).parts
            require(bool(parts) and not name.startswith('/') and '\\' not in name
                    and ':' not in name and '..' not in parts, 'unsafe path: ' + name)
            require(not any(p.casefold() in FORBIDDEN_PARTS for p in parts),
                    'excluded path: ' + name)
            info = z.getinfo(name)
            require((info.external_attr >> 16) & 0o170000 != 0o120000,
                    'ZIP symlink: ' + name)
        require(z.testzip() is None, 'ZIP CRC')
        require(REQUIRED.issubset(names), 'standard content missing')
        if not REQUIRED.issubset(names):
            return failures
        data = {n: z.read(n) for n in names}

    manifest = json.loads(data['MANIFEST_SHA256.txt'])
    require(manifest['REVIEW_CANDIDATE_SHA'] == candidate, 'manifest C mismatch')
    require(manifest['PREDECESSOR_SHA'] == predecessor, 'manifest P mismatch')
    entries = manifest['FILES']
    indexed = {r['PATH']: r for r in entries}
    require(len(entries) == len(indexed), 'duplicate manifest path')
    require(set(indexed) == set(data) - {'MANIFEST_SHA256.txt'}, 'manifest file set')
    for name, row in indexed.items():
        require(row['ROLE'] in ROLES, 'unknown manifest role: ' + name)
        require(name in data, 'missing payload: ' + name)
        if name not in data:
            continue
        require(len(data[name]) == row['SIZE'] and sha(data[name]) == row['SHA256'],
                'payload size/hash: ' + name)
        # Signature scan is intentionally bounded; bundle blobs need separate inspection.
        if row['ROLE'] != 'GIT_BUNDLE':
            require(not any(re.search(p, data[name]) for p in SECRET_PATTERNS),
                    'secret signature: ' + name)
        if row['ROLE'] in {'CREATED', 'MODIFIED', 'REFERENCE'} and 'REPO_PATH' in row:
            require(data[name] == git(repo, 'show', row.get('SOURCE_SHA', candidate)
                                     + ':' + row['REPO_PATH']), 'Git bytes: ' + name)

    schema = json.loads((Path(__file__).parents[1] / 'references/package-fields.json')
                        .read_text(encoding='utf-8'))
    start = control(data['START_HERE.md'])
    packet = control(data['REVIEW_PACKET.md'])
    environment = control(data['ENVIRONMENT_FINGERPRINT.md'])
    for label, obj in [('START_HERE', start), ('REVIEW_PACKET', packet),
                       ('ENVIRONMENT', environment)]:
        require(set(schema[label]).issubset(obj), 'fields: ' + label)
    for obj in [start, packet]:
        require(obj['REVIEW_CANDIDATE_SHA'] == candidate and
                obj['PREDECESSOR_SHA'] == predecessor, 'control identity')
    require(start['REVIEWER_FIRST_ACTION'] == 'READ START_HERE.md', 'first action')
    require(start['PUSH_STATUS'] == 'NOT_PUSHED', 'push status')
    require(start['ALL_REQUIRED_PARTS'] == 'ONE_ZIP',
            'split package requires separate completeness gate; unsupported here')
    require(packet['GOAL_STATUS'] == 'REVIEW_READY', 'packet delivery state')
    require(packet['REVIEW_LEVEL'] in {'L1', 'L2', 'L3'}, 'review level')
    require(not packet['UNEXPECTED_CHANGED_FILES'], 'unexpected changed files')
    require(packet['GOAL_ID'] == start['GOAL_ID'] == manifest['GOAL_ID'], 'Goal ID')
    require(packet['BRANCH'] == start['BRANCH'] == manifest['BRANCH'], 'branch metadata')
    bundle = packet['GIT_BUNDLE_REF']
    require(bundle in data or (packet['REVIEW_LEVEL'] != 'L3' and
                              str(bundle).startswith(('NOT_REQUIRED:',
                                                      'NOT_AVAILABLE_WITH_REASON:'))),
            'bundle requirement / missing reason')
    if bundle in data:
        with tempfile.TemporaryDirectory(prefix='pn-review-bundle-') as temp:
            bundle_file = Path(temp) / 'candidate.bundle'
            bundle_file.write_bytes(data[bundle])
            git(repo, 'bundle', 'verify', str(bundle_file))
            heads = git(repo, 'bundle', 'list-heads', str(bundle_file)).decode('utf-8')
            require(candidate in heads.split(), 'bundle candidate ref')
    allow = control(data['CHANGED_FILE_ALLOWLIST.txt'])
    require(allow['MATCH'] == 'YES', 'allowlist match')
    actual = git(repo, 'diff', '--no-renames', '--name-status', predecessor,
                 candidate).decode('utf-8').splitlines()
    mapping = {'A': 'CREATED', 'M': 'MODIFIED', 'D': 'DELETED', 'T': 'MODIFIED'}
    changes = [{'PATH': line.split('\t', 1)[1], 'CHANGE': mapping[line[0]]}
               for line in actual]
    # --no-renames represents a rename as deletion/addition without losing either path.
    require(allow['ACTUAL'] == changes, 'allowlist actual versus Git')
    require({x['PATH'] for x in changes}.issubset(set(allow['AUTHORIZED'])),
            'unauthorized path')
    require(packet['CHANGED_FILES'] == [x['PATH'] for x in changes], 'packet changes')
    for change in changes:
        p, kind = change['PATH'], change['CHANGE']
        require(p in packet[kind + '_FILES'], 'packet change category: ' + p)
        if kind != 'DELETED':
            require(sum(1 for r in entries if r.get('REPO_PATH') == p and
                        r['ROLE'] == kind) == 1, 'changed bytes missing/duplicate: ' + p)
    require(manifest.get('DELETED_FILES', []) == packet['DELETED_FILES'], 'deletions')
    require(data['THIS_ROUND_DIFF.patch'] == git(repo, 'diff', '--full-index',
            '--binary', predecessor + '..' + candidate), 'exact patch')
    evidence = control(data['VALIDATION_RESULTS.md'])['CHECKS']
    require(bool(evidence), 'no checks')
    for e in evidence:
        require(set(schema['VALIDATION_RESULT']).issubset(e), 'check fields')
        require(e['OUTPUT_REF'] in data, 'missing output ref: ' + e['TEST_ID'])
        if e['MANDATORY']:
            require(not e['SKIPPED'] and not e['BLOCKING'], 'mandatory skip/block')
            require(e['ACTUAL_EXIT_CODE'] == 0, 'mandatory harness exit')
        if e['NEGATIVE_TEST']:
            require(all(k in e for k in ['HARNESS_EXIT_CODE', 'TARGET_COMMAND_EXIT_CODE',
                    'EXPECTED_NEGATIVE_RESULT', 'ACTUAL_NEGATIVE_RESULT']),
                    'negative exit separation')
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zip', type=Path)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--predecessor', required=True)
    parser.add_argument('--expected-zip-sha')
    args = parser.parse_args()
    try:
        failures = validate(args.zip, args.repo.resolve(), args.candidate,
                            args.predecessor, args.expected_zip_sha)
    except (KeyError, ValueError, OSError, zipfile.BadZipFile) as error:
        failures = ['invalid package structure: ' + str(error)]
    print(json.dumps({'PACKAGE_MECHANICAL_VALIDATION': 'FAIL' if failures else 'PASS',
                      'failures': failures, 'scope': 'single ZIP; semantic freshness, '
                      'Human attribution and bundle blob safety require recorded checks'},
                     ensure_ascii=False))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
