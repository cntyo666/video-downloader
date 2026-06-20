"""基础解析器接口"""
import re
import time
import requests


class BaseParser:
    """视频解析器基类"""
    name = "base"
    domains: list[str] = []

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
    }

    MOBILE_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.0 Mobile/15E148 Safari/604.1"
        ),
    }

    def match(self, url: str) -> bool:
        return any(d in url for d in self.domains)

    def parse(self, url: str) -> dict:
        """
        解析链接，返回:
        {
            "title": str,
            "video_url": str | None,
            "audio_url": str | None,
            "cover_url": str | None,
            "platform": str,
            "author": str,
        }
        """
        raise NotImplementedError

    def follow_redirect(self, url: str) -> str:
        """跟踪重定向获取真实 URL"""
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

    @staticmethod
    def safe_filename(name: str, max_len: int = 80) -> str:
        name = re.sub(r'[\\/:*?"<>|\n\r\t]', '_', name)
        name = re.sub(r'_+', '_', name).strip('_. ')
        return name[:max_len] if name else f"video_{int(time.time())}"
