"""抖音/TikTok 解析器"""
import re
import requests
from .base import BaseParser


class DouyinParser(BaseParser):
    name = "抖音"
    domains = ["douyin.com", "iesdouyin.com", "tiktok.com", "vm.tiktok.com", "v.douyin.com"]

    def parse(self, url: str) -> dict:
        real_url = self.follow_redirect(url)
        video_id = self._extract_id(real_url)
        if not video_id:
            raise ValueError(f"无法从 URL 提取视频 ID: {real_url}")

        # 方法 1: 分享页
        result = self._method_share_page(video_id)
        if result and result.get("video_url"):
            return result

        # 方法 2: Web API
        result = self._method_web_api(video_id)
        if result and result.get("video_url"):
            return result

        raise ValueError("抖音解析失败，可能需要登录或视频已删除")

    def _extract_id(self, url: str) -> str:
        for pattern in [r'/video/(\d+)', r'/note/(\d+)', r'itemId=(\d+)']:
            m = re.search(pattern, url)
            if m:
                return m.group(1)
        return ""

    def _method_share_page(self, video_id: str) -> dict:
        share_url = f"https://www.iesdouyin.com/share/video/{video_id}/"
        headers = {**self.HEADERS, "Referer": "https://www.douyin.com/"}
        try:
            resp = requests.get(share_url, headers=headers, timeout=15)
            html = resp.text

            data = {"platform": "抖音"}

            title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.S)
            if title_m:
                data["title"] = title_m.group(1).strip().replace(' - 抖音', '').strip()

            for pattern in [
                r'"playApi"\s*:\s*"(https?://[^"]+)"',
                r'"play_addr"\s*:\s*\{[^}]*"url_list"\s*:\s*\["(https?://[^"]+)"',
                r'"download_addr"\s*:\s*\{[^}]*"url_list"\s*:\s*\["(https?://[^"]+)"',
                r'src="(https?://[^"]*\.mp4[^"]*)"',
            ]:
                m = re.search(pattern, html)
                if m:
                    data["video_url"] = m.group(1).replace('\\u002F', '/').replace('\\/', '/')
                    break

            cover_m = re.search(r'"cover"\s*:\s*\{[^}]*"url_list"\s*:\s*\["(https?://[^"]+)"', html)
            if cover_m:
                data["cover_url"] = cover_m.group(1).replace('\\u002F', '/').replace('\\/', '/')

            return data
        except Exception:
            return {}

    def _method_web_api(self, video_id: str) -> dict:
        api_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}"
        headers = {
            **self.HEADERS,
            "Referer": "https://www.douyin.com/",
            "Cookie": "msToken=xxx",
        }
        try:
            resp = requests.get(api_url, headers=headers, timeout=15)
            if resp.status_code != 200:
                return {}

            data = resp.json()
            detail = data.get("aweme_detail", {})
            if not detail:
                return {}

            result = {
                "title": detail.get("desc", ""),
                "platform": "抖音",
                "author": detail.get("author", {}).get("nickname", ""),
            }

            video = detail.get("video", {})
            play_addr = video.get("play_addr", {})
            url_list = play_addr.get("url_list", [])
            if url_list:
                result["video_url"] = url_list[0]

            cover = video.get("cover", {})
            cover_list = cover.get("url_list", [])
            if cover_list:
                result["cover_url"] = cover_list[0]

            return result
        except Exception:
            return {}
