"""小红书解析器"""
import re
import requests
from .base import BaseParser


class XiaohongshuParser(BaseParser):
    name = "小红书"
    domains = ["xiaohongshu.com", "xhslink.com"]

    def parse(self, url: str) -> dict:
        real_url = self.follow_redirect(url)
        headers = {**self.HEADERS, "Referer": "https://www.xiaohongshu.com/"}
        resp = requests.get(real_url, headers=headers, timeout=15)
        html = resp.text

        data = {"platform": "小红书"}

        title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.S)
        if title_m:
            t = title_m.group(1).strip().replace(' - 小红书', '').strip()
            if t:
                data["title"] = t

        for pattern in [
            r'"originVideoKey"\s*:\s*"(https?://[^"]+)"',
            r'"video"\s*:\s*\{[^}]*"url"\s*:\s*"(https?://[^"]+)"',
            r'"url"\s*:\s*"(https?://[^"]*\.mp4[^"]*)"',
            r'"media"\s*:\s*\{[^}]*"stream"\s*:\s*\{[^}]*"h264"\s*:\s*\[?\{[^}]*"url"\s*:\s*"(https?://[^"]+)"',
        ]:
            m = re.search(pattern, html)
            if m:
                data["video_url"] = m.group(1).replace('\\u002F', '/').replace('\\/', '/')
                break

        cover_m = re.search(r'"imageList"\s*:\s*\[.*?"url"\s*:\s*"(https?://[^"]+)"', html)
        if cover_m:
            data["cover_url"] = cover_m.group(1)

        author_m = re.search(r'"nickname"\s*:\s*"(.*?)"', html)
        if author_m:
            data["author"] = author_m.group(1)

        if not data.get("video_url"):
            raise ValueError("小红书解析失败，可能是图文笔记或需要登录")

        return data
