import os, sys, time, json
sys.path.insert(0, '.')
# Fix encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv
load_dotenv()
import requests

token = os.environ.get('GITHUB_TOKEN', '')
headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json'
}

# Get latest runs
r = requests.get('https://api.github.com/repos/Bakpau535/Tarsier/actions/runs?per_page=5', headers=headers)
runs = r.json().get('workflow_runs', [])
for run in runs:
    num = run['run_number']
    name = run['name']
    status = run['status']
    conclusion = run.get('conclusion') or 'running'
    sha = run['head_sha'][:7]
    event = run['event']
    print(f"Run #{num} ({name}): status={status} conclusion={conclusion} sha={sha} trigger={event}")

# Get the latest completed run's logs
target_run = None
for run in runs:
    if run['status'] == 'completed' and run['name'] == 'FB Fanspage Schedule':
        target_run = run
        break

if not target_run:
    # Try in-progress run
    for run in runs:
        if run['name'] == 'FB Fanspage Schedule':
            target_run = run
            break

if target_run:
    run_id = target_run['id']
    print(f"\n--- Downloading logs for Run #{target_run['run_number']} (sha={target_run['head_sha'][:7]}) ---")
    
    log_r = requests.get(f'https://api.github.com/repos/Bakpau535/Tarsier/actions/runs/{run_id}/logs', 
                         headers=headers, allow_redirects=True)
    if log_r.status_code == 200:
        log_file = 'run_logs.zip'
        with open(log_file, 'wb') as f:
            f.write(log_r.content)
        print(f"Logs downloaded ({len(log_r.content)} bytes)")
        
        import zipfile
        with zipfile.ZipFile(log_file) as z:
            for name in z.namelist():
                if 'Run Pipeline' in name or 'pipeline' in name.lower():
                    print(f"\n{'='*80}")
                    print(f"=== {name} ===")
                    print(f"{'='*80}")
                    content = z.read(name).decode('utf-8', errors='replace')
                    # Print ALL lines from Run Pipeline step
                    for line in content.split('\n'):
                        print(f"  {line.rstrip()}")
    else:
        print(f"Cannot download logs: HTTP {log_r.status_code}")
        
        # Try getting live logs via steps API
        print("\n--- Trying job steps API ---")
        jr = requests.get(f'https://api.github.com/repos/Bakpau535/Tarsier/actions/runs/{run_id}/jobs', headers=headers)
        jobs = jr.json().get('jobs', [])
        for job in jobs:
            print(f"Job: {job['name']} status={job['status']}")
            for step in job.get('steps', []):
                print(f"  Step: {step['name']} status={step['status']} conclusion={step.get('conclusion','')}")
