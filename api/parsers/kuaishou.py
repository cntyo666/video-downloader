"""快手解析器"""
import re
import requests
from .base import BaseParser


class KuaishouParser(BaseParser):
    name = "快手"
    domains = ["kuaishou.com", "gifshow.com", "v.kuaishou.com"]

    def parse(self, url: str) -> dict:
        real_url = self._follow_redirect(url)
        photo_id = self._extract_id(real_url)

        headers = {**self.HEADERS, "Referer": "https://www.kuaishou.com/"}
        resp = requests.get(real_url, headers=headers, timeout=15)
        html = resp.text

        # 提取 cookies 用于后续下载鉴权
        cookies = resp.cookies.get_dict()
        cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())

        data = {"platform": "快手", "_cookies": cookie_str}

        # 标题
        title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.S)
        if title_m:
            t = title_m.group(1).strip().replace(' - 快手', '').strip()
            if t:
                data["title"] = t

        # 视频 URL
        video_patterns = [
            r'"playUrl"\s*:\s*"(https?://[^"]+)"',
            r'"videoUrl"\s*:\s*"(https?://[^"]+)"',
            r'"webp_video_url"\s*:\s*"(https?://[^"]+)"',
            r'"photoUrl"\s*:\s*"(https?://[^"]+)"',
            r'src="(https?://[^"]*\.mp4[^"]*)"',
        ]
        for p in video_patterns:
            m = re.search(p, html)
            if m:
                data["video_url"] = m.group(1).replace('\\u002F', '/').replace('\\/', '/')
                break

        # 封面
        cover_m = re.search(r'"coverUrl"\s*:\s*"(https?://[^"]+)"', html)
        if cover_m:
            data["cover_url"] = cover_m.group(1).replace('\\u002F', '/').replace('\\/', '/')

        # 作者
        author_m = re.search(r'"userName"\s*:\s*"(.*?)"', html)
        if author_m:
            data["author"] = author_m.group(1)

        return data

    def _follow_redirect(self, url: str) -> str:
        try:
            resp = requests.head(url, headers=self.HEADERS, allow_redirects=False, timeout=10)
            loc = resp.headers.get("Location", "")
            if loc:
                return loc
        except Exception:
            pass
        try:
            resp = requests.get(url, headers=self.HEADERS, allow_redirects=True, timeout=10)
            return resp.url
        except Exception:
            return url

    def _extract_id(self, url: str) -> str:
        m = re.search(r'/short-video/(\w+)', url) or re.search(r'/photo/(\w+)', url)
        return m.group(1) if m else ""
