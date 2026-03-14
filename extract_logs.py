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

# Get latest completed FB run
r = requests.get('https://api.github.com/repos/Bakpau535/Tarsier/actions/runs?per_page=5', headers=headers)
runs = r.json().get('workflow_runs', [])

target = None
for run in runs:
    if run['name'] == 'FB Fanspage Schedule' and run['status'] == 'completed':
        target = run
        break

if not target:
    print("No completed FB run found")
    sys.exit(1)

print(f"Analyzing Run #{target['run_number']} sha={target['head_sha'][:7]} conclusion={target['conclusion']}")

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
            content = z.read(name).decode('utf-8', errors='replace')
            lines = content.split('\n')
            # Print only the important diagnostic lines
            for line in lines:
                if any(k in line for k in [
                    'MediaGen', 'PEXELS', 'PIXABAY', 'HF_API', 'Gemini', 'FALLBACK',
                    'Visual source', 'tarsier', 'Tarsier', 'support', 'Support',
                    'Final:', 'ratio', 'Script generated', 'Metadata generated',
                    'Freesound', 'music', 'Music', 'assembled', 'QC', 'PREVIEW',
                    'Selected Topic', 'Processing topic', 'voiceover', 'Voiceover'
                ]):
                    # Strip timestamp prefix
                    stripped = line.strip()
                    if 'Z ' in stripped:
                        stripped = stripped.split('Z ', 1)[1] if 'Z ' in stripped else stripped
                    print(stripped)
