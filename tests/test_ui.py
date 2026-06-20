import requests

resp = requests.get('http://127.0.0.1:5000/')
print(f'Status: {resp.status_code}')
ct = resp.headers.get('Content-Type', '')
print(f'Content-Type: {ct}')
print(f'Size: {len(resp.text)} bytes')

html = resp.text
checks = [
    ('Title', '视频下载器' in html or 'v2' in html),
    ('Tab single', 'tab active' in html),
    ('Tab batch', '批量解析' in html),
    ('Parse button', 'btn-parse' in html),
    ('API endpoint', '/api/parse' in html),
    ('Download func', 'doDownload' in html),
    ('Dark theme', '--bg' in html),
    ('Toast system', 'toast' in html),
]
print('\nFrontend checks:')
for name, ok in checks:
    symbol = 'OK' if ok else 'FAIL'
    print(f'  [{symbol}] {name}')

# Test Bilibili parse
print('\n--- B站 parse test ---')
resp2 = requests.post('http://127.0.0.1:5000/api/parse', json={'url': 'https://www.bilibili.com/video/BV1GJ411x7h7'}, timeout=30)
print(f'Status: {resp2.status_code}')
data = resp2.json()
print(f'Parser: {data.get("parser", "N/A")}')
print(f'Title: {data.get("title", "N/A")}')
print(f'Video URL: {"YES" if data.get("video_url") else "NO"}')
print(f'Audio URL: {"YES" if data.get("audio_url") else "NO"}')
print(f'Cover URL: {"YES" if data.get("cover_url") else "NO"}')
print(f'Author: {data.get("author", "N/A")}')

# Test video URL is accessible
if data.get('video_url'):
    try:
        head = requests.head(data['video_url'], timeout=10, allow_redirects=True)
        print(f'Video HEAD status: {head.status_code}')
        print(f'Video size: {head.headers.get("Content-Length", "?")} bytes')
    except Exception as e:
        print(f'Video HEAD error: {e}')

print('\n--- Done ---')
