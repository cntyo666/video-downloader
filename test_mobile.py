"""测试快手移动端 API"""
import requests
import re
import json

# 方法: 使用移动端 API
# 快手短视频的移动端 API 格式
photo_id = "3x9n9s6azwdx36w"

# 移动端 User-Agent
mobile_headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 方法1: 移动端页面
mobile_url = f"https://m.kuaishou.com/short-video/{photo_id}"
print(f"=== 方法1: 移动端页面 {mobile_url} ===")
try:
    resp = requests.get(mobile_url, headers=mobile_headers, timeout=15, allow_redirects=True)
    print(f"Status: {resp.status_code}, Length: {len(resp.text)}")
    
    # 提取视频 URL
    patterns = [
        r'"playUrl"\s*:\s*"(https?://[^"]+)"',
        r'"photoUrl"\s*:\s*"(https?://[^"]+)"',
        r'"videoUrl"\s*:\s*"(https?://[^"]+)"',
        r'"src"\s*:\s*"(https?://[^"]*wsukwai[^"]*)"',
        r'"src"\s*:\s*"(https?://[^"]*kuaishou[^"]*\.mp4[^"]*)"',
    ]
    for p in patterns:
        m = re.search(p, resp.text)
        if m:
            url = m.group(1).replace("\\u002F", "/").replace("\\/", "/")
            print(f"Found: {url[:150]}")
            break
    else:
        # 查找所有可能的视频 URL
        all_urls = re.findall(r'https?://[^\s"\'<>]+', resp.text)
        video_urls = [u for u in all_urls if any(x in u for x in ["wsukwai", "v4-imv", "v3-imv", ".mp4", "video"])]
        if video_urls:
            for u in video_urls[:5]:
                print(f"  Candidate: {u[:150]}")
        else:
            print("No video URLs found")
            # 检查是否有 JS 渲染
            if "__APOLLO_STATE__" in resp.text:
                print("Has Apollo state (JS rendered)")
            if "window.__data" in resp.text:
                print("Has window.__data")
except Exception as e:
    print(f"Error: {e}")

# 方法2: gifshow API
print(f"\n=== 方法2: gifshow API ===")
gifshow_url = f"https://www.gifshow.com/short-video/{photo_id}"
try:
    resp = requests.get(gifshow_url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }, timeout=15, allow_redirects=True)
    print(f"Status: {resp.status_code}, Length: {len(resp.text)}")
    
    for p in patterns:
        m = re.search(p, resp.text)
        if m:
            url = m.group(1).replace("\\u002F", "/").replace("\\/", "/")
            print(f"Found: {url[:150]}")
            break
    else:
        print("No video URLs found")
except Exception as e:
    print(f"Error: {e}")

# 方法3: 直接访问 CDN URL 测试
print(f"\n=== 方法3: 测试已知 CDN URL 模式 ===")
# 从之前的错误信息中提取的 CDN URL 格式
# v4-imv-fdl.wsukwai.com 是快手视频 CDN
print("快手 CDN 域名: v4-imv-fdl.wsukwai.com, v3-imv-fdl.wsukwai.com")
print("需要从页面获取带 pkey 的完整 URL")
