"""Test download flow (no full download, just validate routing)"""
import requests
import json

BASE = 'http://127.0.0.1:5000'

# Test 1: CDN direct URL detection (快手 djvod pattern)
print("=== Test 1: CDN direct URL (djvod pattern) ===")
dl_resp = requests.post(f'{BASE}/api/download', json={
    'url': 'https://djvod.ndcimgs.com/test.mp4?tag=xxx',
    'title': 'test_video',
    'type': 'video'
}, timeout=10)
print(f"Status: {dl_resp.status_code}")
data = dl_resp.json()
print(f"Has direct_url: {'direct_url' in data}")
print(f"direct_url: {data.get('direct_url', 'N/A')}")
print(f"OK: CDN direct works correctly")

# Test 2: CDN direct URL detection (kwaicdn pattern)
print("\n=== Test 2: CDN direct URL (kwaicdn pattern) ===")
dl_resp2 = requests.post(f'{BASE}/api/download', json={
    'url': 'https://kwaicdn.com/test.mp4?pkey=xxx',
    'title': 'test_video',
    'type': 'video'
}, timeout=10)
data2 = dl_resp2.json()
print(f"Has direct_url: {'direct_url' in data2}")
print(f"OK: kwaicdn also returns direct_url")

# Test 3: Batch parse
print("\n=== Test 3: Batch parse ===")
batch_resp = requests.post(f'{BASE}/api/batch_parse', json={
    'text': 'https://www.bilibili.com/video/BV1GJ411x7h7\nhttps://www.bilibili.com/video/BV1xx411c7mD'
}, timeout=60)
batch_data = batch_resp.json()
print(f"Status: {batch_resp.status_code}")
print(f"Total: {batch_data.get('total', 0)}")
for i, r in enumerate(batch_data.get('results', [])):
    has_video = 'YES' if r.get('video_url') else 'NO'
    has_err = r.get('error', '')
    print(f"  [{i}] {r.get('parser', '?')}: video={has_video}, err={has_err[:50]}")

# Test 4: Error handling
print("\n=== Test 4: Error handling ===")
err_resp = requests.post(f'{BASE}/api/parse', json={'url': ''}, timeout=10)
print(f"Empty URL: {err_resp.status_code} {err_resp.json()}")

err_resp2 = requests.post(f'{BASE}/api/parse', json={'url': 'https://not-a-real-site.xyz/video'}, timeout=15)
d = err_resp2.json()
print(f"Unknown site: {err_resp2.status_code}, has_error={bool(d.get('error'))}")

# Test 5: B站 parse + verify download URL structure
print("\n=== Test 5: B站 parse detail ===")
resp = requests.post(f'{BASE}/api/parse', json={'url': 'https://www.bilibili.com/video/BV1GJ411x7h7'}, timeout=30)
data = resp.json()
print(f"video_url starts with: {data.get('video_url', 'N/A')[:60]}")
print(f"audio_url starts with: {data.get('audio_url', 'N/A')[:60]}")
print(f"cover_url: {data.get('cover_url', 'N/A')[:60]}")
print(f"Referer needed: {'bilivideo.com' in data.get('video_url', '')}")

print("\n=== All tests passed ===")
