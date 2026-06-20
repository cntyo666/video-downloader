"""测试快手 GraphQL API 获取视频信息"""
import requests
import re
import json

# 先获取 cookies
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.kuaishou.com/",
})

# 访问分享链接获取重定向后的 URL 和 cookies
share_url = "https://v.kuaishou.com/3QZ7t1"
resp = session.get(share_url, allow_redirects=True, timeout=15)
print(f"Redirect URL: {resp.url[:120]}")

# 提取 photoId
photo_m = re.search(r'/short-video/(\w+)', resp.url) or re.search(r'photoId=(\w+)', resp.url)
if not photo_m:
    print("Cannot extract photoId")
    exit(1)

photo_id = photo_m.group(1)
print(f"Photo ID: {photo_id}")

# 尝试 GraphQL API
api_url = "https://www.kuaishou.com/graphql"
session.headers.update({
    "Content-Type": "application/json",
    "Referer": f"https://www.kuaishou.com/short-video/{photo_id}",
})

# 方法1: visionVideoDetailPhoto
payload = {
    "operationName": "visionVideoDetailPhoto",
    "variables": {"photoId": photo_id, "page": "detail"},
    "query": "query visionVideoDetailPhoto($photoId: String, $type: String, $page: String) { visionVideoDetail(photoId: $photoId, type: $type, page: $page) { photo { id duration caption likeCount realLikeCount coverUrl photoUrl liked } } }"
}

try:
    api_resp = session.post(api_url, json=payload, timeout=15)
    print(f"\nAPI Status: {api_resp.status_code}")
    data = api_resp.json()
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
except Exception as e:
    print(f"API error: {e}")

# 方法2: visionVideoDetail
payload2 = {
    "operationName": "visionVideoDetail",
    "variables": {"photoId": photo_id, "page": "detail"},
    "query": "query visionVideoDetail($photoId: String, $type: String, $page: String) { visionVideoDetail(photoId: $photoId, type: $type, page: $page) { photo { id duration caption likeCount realLikeCount coverUrl photoUrl liked } } }"
}

try:
    api_resp2 = session.post(api_url, json=payload2, timeout=15)
    print(f"\nAPI2 Status: {api_resp2.status_code}")
    data2 = api_resp2.json()
    print(json.dumps(data2, indent=2, ensure_ascii=False)[:1000])
except Exception as e:
    print(f"API2 error: {e}")

# 打印 cookies
print(f"\nCookies: {dict(session.cookies)}")
