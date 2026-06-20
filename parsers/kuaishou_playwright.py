# 快手 Playwright 本地增强版解析器
# 仅在本地运行（需要 playwright + playwright-stealth）
# Vercel 环境使用 api/parsers/kuaishou.py 的多策略方案
import re
import json
import asyncio
import requests
from api.parsers.base import BaseParser


class KuaishouPlaywrightParser(BaseParser):
    name = "快手(Playwright)"
    domains = ["kuaishou.com", "gifshow.com", "v.kuaishou.com"]

    def parse(self, url: str) -> dict:
        real_url = self.follow_redirect(url)
        photo_id = self._extract_id(real_url)
        desktop_url = f"https://www.kuaishou.com/short-video/{photo_id}" if photo_id else real_url

        video_url, title, cover_url, author = self._extract_with_playwright(desktop_url)

        data = {"platform": "快手"}
        if title:
            data["title"] = title.strip()
        if video_url:
            data["video_url"] = video_url
        if cover_url:
            data["cover_url"] = cover_url
        if author:
            data["author"] = author

        if not data.get("video_url"):
            raise ValueError("Playwright 也未能获取视频，可能被反爬拦截")

        return data

    def _extract_id(self, url: str) -> str:
        m = re.search(r'/short-video/(\w+)', url) or re.search(r'/photo/(\w+)', url)
        return m.group(1) if m else ""

    def _extract_with_playwright(self, url: str) -> tuple:
        try:
            return asyncio.run(self._async_extract(url))
        except Exception as e:
            print(f"Playwright error: {e}")
            return None, None, None, None

    async def _async_extract(self, url: str) -> tuple:
        from playwright.async_api import async_playwright
        from playwright_stealth import Stealth

        video_url = None
        title = None
        cover_url = None
        author = None

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
            )
            page = await context.new_page()
            stealth = Stealth()
            await stealth.apply_stealth_async(page)

            target_photo_id = self._extract_id(url)

            async def on_response(response):
                nonlocal video_url, title, cover_url, author
                if video_url:
                    return
                ct = response.headers.get("content-type", "")
                if "graphql" in response.url and "json" in ct:
                    try:
                        body = await response.json()
                        found = self._find_video(body, target_photo_id)
                        if found:
                            video_url, title, cover_url, author = found
                    except:
                        pass

            page.on("response", on_response)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            except:
                pass

            await asyncio.sleep(8)

            if not video_url:
                try:
                    apollo = await page.evaluate("() => window.__APOLLO_STATE__ || null")
                    if apollo:
                        found = self._find_video(apollo, target_photo_id)
                        if found:
                            video_url, title, cover_url, author = found
                except:
                    pass

            if not title:
                try:
                    t = await page.title()
                    if t and "风控" not in t and "验证" not in t and len(t) > 3:
                        title = t
                except:
                    pass

            await browser.close()

        return video_url, title, cover_url, author

    def _find_video(self, data, target_photo_id=None, depth=0):
        if depth > 15:
            return None
        if isinstance(data, dict):
            photo = data.get("photo")
            if isinstance(photo, dict):
                photo_url = photo.get("photoUrl", "")
                photo_id = photo.get("id", "")
                if photo_url and any(x in photo_url for x in ["djvod", "kwaicdn", "oskwai", "wsukwai"]):
                    result = (
                        photo_url,
                        photo.get("caption", "") or photo.get("title", ""),
                        photo.get("coverUrl", ""),
                        photo.get("userName", ""),
                    )
                    if target_photo_id and photo_id and target_photo_id == photo_id:
                        return result
                    if "djvod" in photo_url:
                        return result
            for v in data.values():
                found = self._find_video(v, target_photo_id, depth + 1)
                if found:
                    return found
        elif isinstance(data, list):
            for item in data:
                found = self._find_video(item, target_photo_id, depth + 1)
                if found:
                    return found
        return None
