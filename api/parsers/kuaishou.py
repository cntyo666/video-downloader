"""快手解析器 - Playwright + stealth 绕过反爬，拦截 GraphQL 获取视频 URL"""
import re
import asyncio
import requests
from .base import BaseParser


class KuaishouParser(BaseParser):
    name = "快手"
    domains = ["kuaishou.com", "gifshow.com", "v.kuaishou.com"]

    def parse(self, url: str) -> dict:
        real_url = self._follow_redirect(url)
        photo_id = self._extract_id(real_url)
        
        # 用桌面版 URL（移动端页面没有 GraphQL API）
        desktop_url = f"https://www.kuaishou.com/short-video/{photo_id}" if photo_id else real_url
        
        # 用 Playwright + stealth 拦截 GraphQL API
        video_url, title, cover_url, author = self._extract_with_playwright(desktop_url)
        
        data = {"platform": "快手"}
        
        if title:
            data["title"] = title.strip()
        else:
            try:
                headers = {**self.HEADERS, "Referer": "https://www.kuaishou.com/"}
                resp = requests.get(real_url, headers=headers, timeout=15)
                title_m = re.search(r'<title[^>]*>(.*?)</title>', resp.text, re.S)
                if title_m:
                    t = title_m.group(1).strip().replace(' - 快手', '').strip()
                    if t:
                        data["title"] = t
            except:
                pass
        
        if video_url:
            data["video_url"] = video_url
        if cover_url:
            data["cover_url"] = cover_url
        if author:
            data["author"] = author
        
        return data

    def _extract_with_playwright(self, url: str) -> tuple:
        try:
            # 直接用 asyncio.run()
            result = asyncio.run(self._async_extract(url))
            print(f"Playwright result: video={result[0] is not None}, title={result[1]}")
            return result
        except Exception as e:
            import traceback
            print(f"Playwright extraction error: {e}")
            traceback.print_exc()
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
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
            )
            
            page = await context.new_page()
            stealth = Stealth()
            await stealth.apply_stealth_async(page)
            
            target_photo_id = self._extract_id(url)
            
            async def on_response(response):
                nonlocal video_url, title, cover_url, author
                resp_url = response.url
                ct = response.headers.get("content-type", "")
                
                if "graphql" in resp_url and "json" in ct:
                    try:
                        body = await response.json()
                        self._find_target(body, target_photo_id,
                            lambda v, t, c, a: self._set_result(v, t, c, a,
                                lambda: setattr(type(self), '_v', None)))
                        # 直接查找
                        found_v, found_t, found_c, found_a = self._find_in_data(body, target_photo_id)
                        if found_v and not video_url:
                            video_url = found_v
                            title = found_t
                            cover_url = found_c
                            author = found_a
                    except:
                        pass
            
            page.on("response", on_response)
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            except:
                pass
            
            await asyncio.sleep(8)
            
            # 从 Apollo state 提取
            if not video_url:
                try:
                    apollo = await page.evaluate("() => window.__APOLLO_STATE__ || null")
                    if apollo:
                        found_v, found_t, found_c, found_a = self._find_in_data(apollo, target_photo_id)
                        if found_v:
                            video_url = found_v
                            title = found_t
                            cover_url = found_c
                            author = found_a
                except:
                    pass
            
            # 提取标题
            if not title:
                try:
                    t = await page.title()
                    if t and "风控" not in t and "验证" not in t and len(t) > 3:
                        title = t
                except:
                    pass
            
            await browser.close()
        
        return video_url, title, cover_url, author

    def _find_in_data(self, data, target_photo_id=None, depth=0):
        """递归查找目标视频的 URL"""
        if depth > 15:
            return None, None, None, None
        
        first_match = None
        best_match = None  # 优先 djvod 域名（不需要鉴权）
        
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
                    # 精确匹配目标
                    if target_photo_id and photo_id and target_photo_id == photo_id:
                        return result
                    if not first_match:
                        first_match = result
                    # 优先 djvod 域名（不需要 pkey 鉴权）
                    if "djvod" in photo_url and not best_match:
                        best_match = result
            
            for v in data.values():
                found = self._find_in_data(v, target_photo_id, depth + 1)
                if found[0]:
                    return found
        
        elif isinstance(data, list):
            for item in data:
                found = self._find_in_data(item, target_photo_id, depth + 1)
                if found[0]:
                    return found
        
        # 优先返回 djvod 域名的 URL，其次返回第一个可用的
        return best_match or first_match or (None, None, None, None)

    def _find_target(self, data, photo_id, callback):
        pass  # 已合并到 _find_in_data

    def _set_result(self, v, t, c, a, cb):
        pass  # 已合并到 _find_in_data

    def _follow_redirect(self, url: str) -> str:
        try:
            resp = requests.head(url, headers=self.HEADERS, allow_redirects=False, timeout=10)
            loc = resp.headers.get("Location", "")
            if loc:
                return loc
        except:
            pass
        try:
            resp = requests.get(url, headers=self.HEADERS, allow_redirects=True, timeout=10)
            return resp.url
        except:
            return url

    def _extract_id(self, url: str) -> str:
        m = re.search(r'/short-video/(\w+)', url) or re.search(r'/photo/(\w+)', url)
        return m.group(1) if m else ""
