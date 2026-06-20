"""用 Playwright 渲染快手页面 - 带截图和详细日志"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
        )
        page = await context.new_page()
        
        # 记录所有请求
        request_count = 0
        async def handle_request(request):
            nonlocal request_count
            request_count += 1
            url = request.url
            if "video" in url or "wsukwai" in url or ".mp4" in url:
                print(f"  [REQ] {url[:200]}")
        
        page.on("request", handle_request)
        
        print("Loading kuaishou page...")
        try:
            resp = await page.goto("https://www.kuaishou.com/short-video/3x9n9s6azwdx36w", 
                          wait_until="domcontentloaded", timeout=30000)
            print(f"Response status: {resp.status}")
        except Exception as e:
            print(f"Navigation error: {e}")
        
        print(f"Page title: {await page.title()}")
        print(f"Page URL: {page.url}")
        
        # 等待
        await asyncio.sleep(3)
        
        # 截图
        await page.screenshot(path="C:/Users/Administrator/.qclaw/workspace/video-downloader/screenshot.png")
        print("Screenshot saved to screenshot.png")
        
        # 获取页面文本内容
        text = await page.inner_text("body")
        print(f"\nPage text ({len(text)} chars):")
        print(text[:500])
        
        # 检查是否有验证码
        if "captcha" in text.lower() or "验证" in text:
            print("\n[!] CAPTCHA detected!")
        
        # 检查是否有登录提示
        if "登录" in text or "login" in text.lower():
            print("\n[!] Login required!")
        
        print(f"\nTotal requests: {request_count}")
        
        await browser.close()

asyncio.run(main())
