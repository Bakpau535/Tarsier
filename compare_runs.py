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

# Get latest run
r = requests.get('https://api.github.com/repos/Bakpau535/Tarsier/actions/runs?per_page=3', headers=headers)
runs = r.json().get('workflow_runs', [])

for target in runs[:1]:
    print(f"Run #{target['run_number']} | {target['name']} | sha={target['head_sha'][:7]} | status={target['status']} | {target['conclusion']}")
    
    if target['status'] != 'completed':
        print("Still running, waiting...")
        import time
        for _ in range(10):
            time.sleep(15)
            r2 = requests.get(f"https://api.github.com/repos/Bakpau535/Tarsier/actions/runs/{target['id']}", headers=headers)
            s = r2.json().get('status')
            print(f"  ...{s}")
            if s == 'completed':
                break

    log_r = requests.get(f'https://api.github.com/repos/Bakpau535/Tarsier/actions/runs/{target["id"]}/logs', 
                         headers=headers, allow_redirects=True)
    if log_r.status_code != 200:
        print(f"Cannot download: HTTP {log_r.status_code}")
        continue

    with open('run_logs.zip', 'wb') as f:
        f.write(log_r.content)

    with zipfile.ZipFile('run_logs.zip') as z:
        for name in z.namelist():
            if 'Run Pipeline' in name or 'Install' in name:
                content = z.read(name).decode('utf-8', errors='replace')
                lines = content.split('\n')
                for line in lines:
                    stripped = line.strip()
                    if 'Z ' in stripped:
                        stripped = stripped.split('Z ', 1)[1] if 'Z ' in stripped else stripped
                    # Show KEY diagnostic and important lines
                    if any(k in stripped for k in [
                        'KEY', 'key-', 'Gemini keys',
                        'Selected Topic', 'Processing topic',
                        'Script generated', 'FALLBACK',
                        'Metadata generated', 'Voiceover',
                        'Freesound', 'Music',
                        'VO duration', 'Video assembled',
                        'QC Score', 'PREVIEW',
                        'Gemini error', 'EXHAUSTED',
                        'Music log',
                    ]):
                        print(f"  {stripped}")
    print()
