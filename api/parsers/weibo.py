"""微博解析器"""
import re
import requests
from .base import BaseParser


class WeiboParser(BaseParser):
    name = "微博"
    domains = ["weibo.com", "m.weibo.cn", "weibo.cn"]

    def parse(self, url: str) -> dict:
        real_url = self.follow_redirect(url)

        # 移动端 API
        mid = self._extract_mid(real_url)
        if mid:
            result = self._try_mobile_api(mid)
            if result and result.get("video_url"):
                return result

        # 页面提取
        headers = {**self.HEADERS, "Referer": "https://weibo.com/"}
        resp = requests.get(real_url, headers=headers, timeout=15)
        html = resp.text

        data = {"platform": "微博"}

        title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.S)
        if title_m:
            data["title"] = title_m.group(1).strip().replace(' - 微博', '').strip()

        for pattern in [
            r'"stream_url"\s*:\s*"(https?://[^"]+)"',
            r'"stream_url_hd"\s*:\s*"(https?://[^"]+)"',
            r'"url"\s*:\s*"(https?://[^"]*\.mp4[^"]*)"',
        ]:
            m = re.search(pattern, html)
            if m:
                data["video_url"] = m.group(1).replace('\\/', '/')
                break

        author_m = re.search(r'"screen_name"\s*:\s*"(.*?)"', html)
        if author_m:
            data["author"] = author_m.group(1)

        if not data.get("video_url"):
            raise ValueError("微博解析失败，可能是纯文本微博或需要登录")

        return data

    def _extract_mid(self, url: str) -> str:
        m = re.search(r'/(\d{10,})', url)
        return m.group(1) if m else ""

    def _try_mobile_api(self, mid: str) -> dict:
        api_url = f"https://m.weibo.cn/statuses/show?id={mid}"
        headers = {**self.MOBILE_HEADERS, "Referer": "https://m.weibo.cn/"}
        try:
            resp = requests.get(api_url, headers=headers, timeout=15)
            if resp.status_code != 200:
                return None
            data = resp.json().get("data", {})
            if not data:
                return None

            result = {
                "platform": "微博",
                "title": data.get("status_title", ""),
                "author": data.get("user", {}).get("screen_name", ""),
            }

            page_info = data.get("page_info", {})
            if page_info.get("type") == "video":
                urls = page_info.get("urls", {}) or page_info.get("media_info", {})
                result["video_url"] = (
                    urls.get("mp4_720p_mp4") or
                    urls.get("mp4_hd_mp4") or
                    urls.get("mp4_ld_mp4") or
                    urls.get("stream_url") or
                    urls.get("stream_url_hd")
                )

            if not result.get("video_url"):
                pics = data.get("pics", [])
                if pics:
                    result["cover_url"] = pics[0].get("large", {}).get("url", "")

            return result
        except Exception:
            return None
