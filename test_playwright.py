"""用 Playwright 渲染快手页面，拦截视频请求"""
import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    video_urls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()
        
        # 拦截所有网络请求，捕获视频 URL
        async def handle_response(response):
            url = response.url
            if any(x in url for x in ["wsukwai.com", "v4-imv", "v3-imv", ".mp4", "video"]):
                ct = response.headers.get("content-type", "")
                if "video" in ct or "mp4" in ct or "wsukwai" in url:
                    video_urls.append(url)
                    print(f"  [VIDEO] {url[:150]}")
        
        page.on("response", handle_response)
        
        print("Loading kuaishou page...")
        try:
            await page.goto("https://www.kuaishou.com/short-video/3x9n9s6azwdx36w", 
                          wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"Navigation: {e}")
        
        # 等待视频加载
        await asyncio.sleep(5)
        
        # 尝试从页面提取视频元素
        print("\n--- Looking for video elements ---")
        videos = await page.query_selector_all("video")
        for v in videos:
            src = await v.get_attribute("src")
            if src:
                print(f"  video src: {src[:150]}")
                video_urls.append(src)
        
        sources = await page.query_selector_all("video source")
        for s in sources:
            src = await s.get_attribute("src")
            if src:
                print(f"  source src: {src[:150]}")
                video_urls.append(src)
        
        # 提取 Apollo state
        print("\n--- Apollo State ---")
        apollo = await page.evaluate("() => window.__APOLLO_STATE__ || null")
        if apollo:
            # 查找视频 URL
            def find_video_urls(obj, path=""):
                if isinstance(obj, str):
                    if "wsukwai" in obj or "v4-imv" in obj or ".mp4" in obj:
                        print(f"  [{path}] {obj[:150]}")
                        video_urls.append(obj)
                elif isinstance(obj, dict):
                    for k, v in obj.items():
                        find_video_urls(v, f"{path}.{k}")
                elif isinstance(obj, list):
                    for i, v in enumerate(obj):
                        find_video_urls(v, f"{path}[{i}]")
            find_video_urls(apollo)
        
        await browser.close()
    
    if video_urls:
        print(f"\n=== Found {len(video_urls)} video URLs ===")
        for u in video_urls:
            print(f"  {u[:200]}")
    else:
        print("\n=== No video URLs found ===")

asyncio.run(main())
