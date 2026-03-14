import os, sys, json
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

import requests

pexels_key = os.environ.get('PEXELS_API_KEY', '')
pixabay_key = os.environ.get('PIXABAY_API_KEY', '')

print("=" * 60)
print("TARSIER PIPELINE DIAGNOSTIC TEST")
print("=" * 60)

# Check API keys
print("\n--- API KEY STATUS ---")
if pexels_key:
    print(f"PEXELS_API_KEY: {pexels_key[:8]}... (set)")
else:
    print("PEXELS_API_KEY: *** MISSING! ***")
    
if pixabay_key:
    print(f"PIXABAY_API_KEY: {pixabay_key[:8]}... (set)")
else:
    print("PIXABAY_API_KEY: *** MISSING! ***")

# Check HF keys
for i in range(1, 7):
    k = os.environ.get(f"HF_API_KEY_{i}", "")
    status = f"{k[:8]}... (set)" if k else "*** MISSING! ***"
    print(f"HF_API_KEY_{i}: {status}")

# Test Pexels Videos for "tarsier"
print("\n--- PEXELS VIDEO SEARCH: 'tarsier' ---")
if pexels_key:
    h = {"Authorization": pexels_key}
    r = requests.get("https://api.pexels.com/videos/search", headers=h,
                     params={"query": "tarsier", "per_page": 15}, timeout=15)
    data = r.json()
    total = data.get("total_results", 0)
    print(f"Status: {r.status_code}, Total results: {total}")
    for v in data.get("videos", [])[:5]:
        print(f"  Video ID:{v['id']} duration:{v['duration']}s")
else:
    print("SKIPPED - no key")

# Test Pexels Photos for "tarsier"
print("\n--- PEXELS PHOTO SEARCH: 'tarsier' ---")
if pexels_key:
    r = requests.get("https://api.pexels.com/v1/search", headers=h,
                     params={"query": "tarsier", "per_page": 15, "orientation": "landscape"}, timeout=15)
    data = r.json()
    total = data.get("total_results", 0)
    print(f"Status: {r.status_code}, Total results: {total}")
    for p in data.get("photos", [])[:5]:
        alt = p.get("alt", "no alt")
        print(f"  Photo ID:{p['id']} alt: {alt[:60]}")
else:
    print("SKIPPED - no key")

# Test Pixabay Videos for "tarsier"
print("\n--- PIXABAY VIDEO SEARCH: 'tarsier' ---")
if pixabay_key:
    r = requests.get("https://pixabay.com/api/videos/",
                     params={"key": pixabay_key, "q": "tarsier", "per_page": 15}, timeout=15)
    data = r.json()
    total = data.get("total", 0)
    print(f"Status: {r.status_code}, Total results: {total}")
    for v in data.get("hits", [])[:5]:
        tags = v.get("tags", "")
        print(f"  Video ID:{v['id']} tags: {tags[:60]}")
else:
    print("SKIPPED - no key")

# Test Pixabay Photos for "tarsier"
print("\n--- PIXABAY PHOTO SEARCH: 'tarsier' ---")
if pixabay_key:
    r = requests.get("https://pixabay.com/api/",
                     params={"key": pixabay_key, "q": "tarsier", "per_page": 15, "image_type": "photo"}, timeout=15)
    data = r.json()
    total = data.get("total", 0)
    print(f"Status: {r.status_code}, Total results: {total}")
    for p in data.get("hits", [])[:5]:
        tags = p.get("tags", "")
        print(f"  Photo ID:{p['id']} tags: {tags[:60]}")
else:
    print("SKIPPED - no key")

# Check used_footage.json
print("\n--- USED FOOTAGE LOG ---")
try:
    with open("data/used_footage.json", "r") as f:
        used = json.load(f)
    print(f"Items already used: {len(used)}")
except:
    print("File missing or empty")

# Check topics for fb_fanspage
print("\n--- TOPICS STATUS (fb_fanspage) ---")
try:
    with open("data/topics.json", "r") as f:
        topics = json.load(f)
    for t in topics:
        if t.get("akun") == "fb_fanspage":
            print(f"  [{t['status']}] {t['topik']} ({t['tanggal']})")
except:
    print("File missing")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
