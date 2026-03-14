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

# Get last 5 completed FB runs
r = requests.get('https://api.github.com/repos/Bakpau535/Tarsier/actions/runs?per_page=10', headers=headers)
runs = r.json().get('workflow_runs', [])

fb_runs = [run for run in runs if run['name'] == 'FB Fanspage Schedule' and run['status'] == 'completed']
print(f"Found {len(fb_runs)} completed FB runs\n")

for target in fb_runs[:3]:  # Last 3 runs
    print(f"{'='*80}")
    print(f"Run #{target['run_number']} | sha={target['head_sha'][:7]} | {target['conclusion']} | {target['created_at']}")
    print(f"{'='*80}")
    
    log_r = requests.get(f'https://api.github.com/repos/Bakpau535/Tarsier/actions/runs/{target["id"]}/logs', 
                         headers=headers, allow_redirects=True)
    if log_r.status_code != 200:
        print(f"Cannot download: HTTP {log_r.status_code}")
        continue

    with open('run_logs.zip', 'wb') as f:
        f.write(log_r.content)

    with zipfile.ZipFile('run_logs.zip') as z:
        for name in z.namelist():
            if 'Run Pipeline' in name:
                content = z.read(name).decode('utf-8', errors='replace')
                lines = content.split('\n')
                for line in lines:
                    stripped = line.strip()
                    if 'Z ' in stripped:
                        stripped = stripped.split('Z ', 1)[1] if 'Z ' in stripped else stripped
                    # Show key diagnostic lines
                    if any(k in stripped for k in [
                        'Selected Topic', 'Processing topic',
                        'Script generated', 'FALLBACK SCRIPT',
                        'Metadata generated', 'Voiceover',
                        'Freesound', 'CDN music', 'Music processed',
                        'Tarsier strategy', 'Tarsier total', 'Tarsier PHOTOS',
                        'Final:', 'QC Score', 'PREVIEW',
                        'already completed',
                    ]):
                        print(f"  {stripped}")
    print()
