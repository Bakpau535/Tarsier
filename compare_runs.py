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

# Get ALL completed runs (both FB and YT)
r = requests.get('https://api.github.com/repos/Bakpau535/Tarsier/actions/runs?per_page=10', headers=headers)
runs = r.json().get('workflow_runs', [])

completed = [run for run in runs if run['status'] == 'completed']
print(f"Found {len(completed)} completed runs\n")

for target in completed[:2]:  # Last 2 runs
    print(f"{'='*80}")
    print(f"Run #{target['run_number']} | {target['name']} | sha={target['head_sha'][:7]} | {target['conclusion']} | {target['created_at']}")
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
                    # Show ALL important lines
                    if any(k in stripped for k in [
                        'Selected Topic', 'Processing topic',
                        'Script generated', 'FALLBACK SCRIPT', 'FALLBACK',
                        'Metadata generated', 'Voiceover',
                        'Freesound', 'CDN', 'Music',
                        'Tarsier strategy', 'Tarsier total', 'Tarsier PHOTOS',
                        'Final:', 'QC Score', 'PREVIEW',
                        'assembly', 'assembled', 'duration',
                        'total', 'Video', 'audio',
                        'Gemini error', 'Gemini (', 'Script generated',
                        'MAIN TOPIC', 'Music log',
                        'already completed', 'key-',
                    ]):
                        print(f"  {stripped}")
    print()
