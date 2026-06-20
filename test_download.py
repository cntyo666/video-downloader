"""本地测试：快手视频解析 + 下载"""
import requests
import re
import json
import subprocess
import os

url = "https://v.kuaishou.com/3QZ7t1"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.kuaishou.com/",
}

print("=== Step 1: 跟踪重定向 ===")
resp = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
print(f"Final URL: {resp.url[:120]}")
print(f"Status: {resp.status_code}")
print(f"Content length: {len(resp.text)}")

print("\n=== Step 2: 提取视频 URL ===")
html = resp.text
video_url = None

patterns = [
    r'"playUrl"\s*:\s*"(https?://[^"]+)"',
    r'"photoUrl"\s*:\s*"(https?://[^"]+)"',
    r'"webp_video_url"\s*:\s*"(https?://[^"]+)"',
    r'"videoUrl"\s*:\s*"(https?://[^"]+)"',
    r'src="(https?://[^"]*\.mp4[^"]*)"',
]

for p in patterns:
    m = re.search(p, html)
    if m:
        video_url = m.group(1).replace("\\u002F", "/").replace("\\/", "/")
        print(f"Found video URL: {video_url[:150]}")
        break

if not video_url:
    # 尝试从 __APOLLO_STATE__ 提取
    apollo_m = re.search(r'window\.__APOLLO_STATE__\s*=\s*({.*?})\s*;?\s*</script>', html, re.S)
    if apollo_m:
        print("Found Apollo state, parsing...")
        try:
            data = json.loads(apollo_m.group(1))
            # 递归查找 URL
            def find_urls(obj, depth=0):
                if depth > 10:
                    return
                if isinstance(obj, str) and ("wsukwai.com" in obj or "kuaishou.com" in obj) and ("mp4" in obj or "video" in obj):
                    print(f"  Found URL in state: {obj[:150]}")
                elif isinstance(obj, dict):
                    for v in obj.values():
                        find_urls(v, depth+1)
                elif isinstance(obj, list):
                    for v in obj:
                        find_urls(v, depth+1)
            find_urls(data)
        except Exception as e:
            print(f"Parse error: {e}")
    else:
        print("No Apollo state found")

    # 尝试其他模式
    all_urls = re.findall(r'https?://[^\s"\'<>]+', html)
    video_urls = [u for u in all_urls if "wsukwai.com" in u or ("kuaishou.com" in u and ".mp4" in u)]
    if video_urls:
        video_url = video_urls[0]
        print(f"Found via URL scan: {video_url[:150]}")
    else:
        print("No video URL found")
        # 打印一些有用的调试信息
        title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.S)
        if title_m:
            print(f"Page title: {title_m.group(1).strip()[:100]}")

if video_url:
    print(f"\n=== Step 3: 测试下载 ===")
    dl_headers = {**headers, "Referer": "https://www.kuaishou.com/"}
    try:
        dl_resp = requests.head(video_url, headers=dl_headers, timeout=15, allow_redirects=True)
        print(f"HEAD status: {dl_resp.status_code}")
        print(f"Content-Type: {dl_resp.headers.get('Content-Type', 'N/A')}")
        print(f"Content-Length: {dl_resp.headers.get('Content-Length', 'N/A')}")
    except Exception as e:
        print(f"HEAD error: {e}")

    # 尝试 GET 下载前 1KB
    try:
        dl_resp = requests.get(video_url, headers=dl_headers, timeout=15, stream=True)
        print(f"GET status: {dl_resp.status_code}")
        chunk = next(dl_resp.iter_content(1024))
        print(f"Downloaded {len(chunk)} bytes successfully")
        dl_resp.close()
    except Exception as e:
        print(f"GET error: {e}")
