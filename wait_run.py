import os, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv
load_dotenv()
import requests

token = os.environ.get('GITHUB_TOKEN', '')
headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}

print("Waiting for Run #37 to complete...")
for i in range(20):
    time.sleep(30)
    r = requests.get('https://api.github.com/repos/Bakpau535/Tarsier/actions/runs?per_page=1', headers=headers)
    runs = r.json().get('workflow_runs', [])
    if runs:
        status = runs[0].get('status')
        conclusion = runs[0].get('conclusion', 'n/a')
        num = runs[0].get('run_number')
        print(f"  Check {i+1}: Run #{num} status={status} conclusion={conclusion}")
        if status == 'completed':
            print("RUN COMPLETED!")
            break
    else:
        print(f"  Check {i+1}: no runs found")
else:
    print("TIMEOUT after 10 minutes")
