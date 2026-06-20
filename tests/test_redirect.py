import requests
url = 'https://v.kuaishou.com/7PbMWy'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0'}
try:
    resp = requests.head(url, headers=headers, allow_redirects=False, timeout=10)
    print(f'HEAD Status: {resp.status_code}')
    loc = resp.headers.get('Location', 'N/A')
    print(f'Location: {loc}')
except Exception as e:
    print(f'HEAD Error: {e}')
try:
    resp = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
    print(f'GET Final URL: {resp.url}')
    print(f'GET Status: {resp.status_code}')
    print(f'Content length: {len(resp.text)}')
    print(f'Title: ', end='')
    import re
    m = re.search(r'<title[^>]*>(.*?)</title>', resp.text, re.S)
    print(m.group(1).strip() if m else 'N/A')
except Exception as e:
    print(f'GET Error: {e}')
