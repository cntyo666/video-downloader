"""方案：在本地 Flask 服务中，用浏览器打开快手页面，拦截视频请求"""
import asyncio
import json
from playwright.async_api import async_playwright

async def extract_video_url(share_url: str) -> dict:
    """用 Playwright 打开快手分享链接，拦截视频请求"""
    video_urls = []
    page_title = ""
    
    async with async_playwright() as p:
        # 连接到用户已打开的 Edge 浏览器（需要启动时加 --remote-debugging-port）
        # 或者用 stealth 模式
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )
        
        # 注入反检测脚本
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
            window.chrome = {runtime: {}};
        """)
        
        page = await context.new_page()
        
        # 拦截视频请求
        async def on_response(response):
            url = response.url
            ct = response.headers.get("content-type", "")
            if "video" in ct or "wsukwai" in url:
                video_urls.append(url)
                print(f"  [VIDEO] {url[:200]}")
        
        page.on("response", on_response)
        
        print(f"Loading: {share_url}")
        try:
            await page.goto(share_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(8)  # 等待视频加载
        except Exception as e:
            print(f"Error: {e}")
        
        page_title = await page.title()
        print(f"Title: {page_title}")
        
        # 尝试点击播放按钮
        try:
            play_btn = await page.query_selector("[class*='play'], [class*='video'], video")
            if play_btn:
                await play_btn.click()
                await asyncio.sleep(3)
        except:
            pass
        
        # 检查 video 元素
        video_elements = await page.query_selector_all("video, source")
        for v in video_elements:
            src = await v.get_attribute("src")
            if src:
                video_urls.append(src)
                print(f"  [ELEMENT] {src[:200]}")
        
        await browser.close()
    
    return {
        "title": page_title,
        "video_urls": list(set(video_urls)),
    }

# 测试
result = asyncio.run(extract_video_url("https://v.kuaishou.com/3QZ7t1"))
print(f"\n=== Result ===")
print(f"Title: {result['title']}")
print(f"Video URLs: {len(result['video_urls'])}")
for u in result['video_urls']:
    print(f"  {u[:200]}")
