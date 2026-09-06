import json, subprocess

# 1) Live terminal output (real run)
r = subprocess.run(['python3', 'flowsentry_cli.py', 'scan', 'examples/real'],
                   capture_output=True, text=True)
out = r.stdout.strip().splitlines()
print('LIVE OUTPUT (tail 25):')
for line in out[-25:]:
    print(line)
print('exit:', r.returncode)

# 2) scan_report.json summary
d = json.load(open('examples/scan_report.json'))
print('\nREPORT KEYS:', list(d.keys())[:10] if isinstance(d, dict) else 'list')
for k in ('summary', 'totals', 'stats'):
    if isinstance(d, dict) and k in d:
        print(k, '=>', json.dumps(d[k])[:400])
if isinstance(d, dict) and 'files' in d:
    print('files count:', len(d['files']))