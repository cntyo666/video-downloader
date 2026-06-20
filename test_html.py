"""分析快手页面 HTML 结构"""
import requests
import re

url = "https://v.kuaishou.com/3QZ7t1"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.kuaishou.com/",
}

resp = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
html = resp.text

print(f"HTML length: {len(html)}")
print(f"URL: {resp.url[:120]}")

# 查找所有 script 标签中的数据
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.S)
print(f"\nFound {len(scripts)} script tags")

for i, s in enumerate(scripts):
    if len(s.strip()) > 50:
        print(f"\n--- Script {i} (len={len(s)}) ---")
        # 查找 window.__data 或类似的数据注入
        if "window." in s or "var " in s or "__NEXT_DATA__" in s or "__APOLLO" in s:
            print(s[:500])
            print("...")
        
        # 查找视频相关关键词
        if any(kw in s for kw in ["playUrl", "photoUrl", "videoUrl", "wsukwai", "mp4", "video_url"]):
            print(f"  [CONTAINS VIDEO DATA]")
            print(s[:500])

# 查找 window.__data
data_m = re.search(r'window\.__data\s*=\s*({.*?})\s*;?\s*</script>', html, re.S)
if data_m:
    print(f"\n=== Found window.__data ===")
    print(data_m.group(1)[:500])

# 查找任何 JSON 数据块
json_blocks = re.findall(r'(?:window\.\w+|var \w+)\s*=\s*(\{[^}]{100,})', html)
print(f"\nFound {len(json_blocks)} large JSON blocks")
for i, block in enumerate(json_blocks[:3]):
    print(f"\n--- JSON Block {i} ---")
    print(block[:300])

# 查找所有包含 URL 的行
print("\n=== Lines with video-related content ===")
for line in html.split("\n"):
    if any(kw in line.lower() for kw in ["playurl", "videourl", "photourl", "wsukwai", "mp4"]):
        print(line.strip()[:200])
