import os, sys, json
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv
load_dotenv()
import requests, zipfile

token = os.environ.get('GITHUB_TOKEN', '')
headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json'
}

# Get Run #31 (latest FB run with diagnostics)
r = requests.get('https://api.github.com/repos/Bakpau535/Tarsier/actions/runs?per_page=5', headers=headers)
runs = r.json().get('workflow_runs', [])
target = None
for run in runs:
    if run['head_sha'].startswith('323df94') or (run['name'] == 'FB Fanspage Schedule' and run['run_number'] == 31):
        target = run
        break

if not target:
    target = runs[0]

print(f"Analyzing Run #{target['run_number']} sha={target['head_sha'][:7]}")

log_r = requests.get(f'https://api.github.com/repos/Bakpau535/Tarsier/actions/runs/{target["id"]}/logs', 
                     headers=headers, allow_redirects=True)
if log_r.status_code != 200:
    print(f"Cannot download: HTTP {log_r.status_code}")
    sys.exit(1)

with open('run_logs.zip', 'wb') as f:
    f.write(log_r.content)

with zipfile.ZipFile('run_logs.zip') as z:
    for name in z.namelist():
        if 'Run Pipeline' in name:
            print(f"\n{'='*100}")
            print(f"FILE: {name}")
            print(f"{'='*100}")
            content = z.read(name).decode('utf-8', errors='replace')
            lines = content.split('\n')
            for line in lines:
                # Strip ANSI and timestamp prefix for readability
                cleaned = line.rstrip()
                if cleaned:
                    print(cleaned)
