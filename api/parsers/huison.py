"""回森解析器"""
import re
import requests
from urllib.parse import urlparse, parse_qs, unquote
from .base import BaseParser


class HuisonParser(BaseParser):
    name = "回森"
    domains = ["viviv.com", "getkwai.com", "h5.getkwai.com"]

    def parse(self, url: str) -> dict:
        redirect_url = self.follow_redirect(url)
        params = self._extract_params(redirect_url)
        page_data = self._fetch_page_data(redirect_url, params)

        result = {
            "title": page_data.get("title", f"回森_{params.get('itemId', 'unknown')}"),
            "video_url": page_data.get("video_url"),
            "audio_url": params.get("audioUrl"),
            "cover_url": page_data.get("cover_url"),
            "platform": "回森",
            "author": page_data.get("author", ""),
        }

        if not result["video_url"] and params.get("itemId"):
            api_data = self._query_api(params["itemId"])
            if api_data:
                result["video_url"] = api_data.get("video_url", result["video_url"])
                result["title"] = api_data.get("title", result["title"])
                result["cover_url"] = api_data.get("cover_url", result["cover_url"])
                result["author"] = api_data.get("author", result["author"])
                if api_data.get("audio_url"):
                    result["audio_url"] = api_data["audio_url"]

        if not result["video_url"] and not result["audio_url"]:
            raise ValueError("回森解析失败，未找到可下载的媒体")

        return result

    def _extract_params(self, redirect_url: str) -> dict:
        parsed = urlparse(redirect_url)
        qs = parse_qs(parsed.query)
        result = {}
        for key in ["itemId", "audioUrl", "fromId", "cid"]:
            if key in qs:
                result[key] = unquote(qs[key][0]) if key == "audioUrl" else qs[key][0]
        return result

    def _fetch_page_data(self, url: str, params: dict) -> dict:
        try:
            headers = {**self.HEADERS, "Referer": "https://h5.getkwai.com/"}
            resp = requests.get(url, headers=headers, timeout=15)
            resp.encoding = resp.apparent_encoding or 'utf-8'
            html = resp.text

            data = {}
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.S)
            if title_match:
                t = title_match.group(1).strip()
                if t and "安全提示" not in t and len(t) > 4:
                    t = t.replace('作品分享 - 回森', '').replace('- 回森', '').strip(' -')
                    if t:
                        data["title"] = t

            for pattern in [
                r'"playUrl"\s*:\s*"(https?://[^"]+\.mp4[^"]*)"',
                r'"videoUrl"\s*:\s*"(https?://[^"]+)"',
                r'"url"\s*:\s*"(https?://[^"]+\.mp4[^"]*)"',
            ]:
                m = re.search(pattern, html)
                if m:
                    data["video_url"] = m.group(1).replace('\\u002F', '/').replace('\\/', '/')
                    break

            cover_m = re.search(r'"coverUrl"\s*:\s*"(https?://[^"]+)"', html)
            if cover_m:
                data["cover_url"] = cover_m.group(1)

            return data
        except Exception:
            return {}

    def _query_api(self, item_id: str) -> dict:
        api_url = "https://h5.getkwai.com/rest/wd/photo/info?kpn=KUAISHOU&captchaToken="
        headers = {
            **self.HEADERS,
            "Content-Type": "application/json",
            "Referer": f"https://h5.getkwai.com/html/mulight-web/share/video/index.html?itemId={item_id}",
        }
        try:
            resp = requests.post(api_url, json={"photoId": item_id}, headers=headers, timeout=10)
            if resp.status_code == 200:
                return self._parse_api_response(resp.json())
        except Exception:
            pass
        return None

    def _parse_api_response(self, data: dict) -> dict:
        result = {}
        try:
            photo = data.get("photo") or data.get("data") or data
            if isinstance(photo, dict):
                result["title"] = photo.get("caption", "")
                result["author"] = photo.get("userName", "")
                for key in ["playUrl", "videoUrl", "url", "mainMvUrl"]:
                    val = photo.get(key)
                    if val and isinstance(val, str) and val.startswith("http"):
                        result["video_url"] = val
                        break
                for key in ["coverUrl", "cover", "thumbnailUrl"]:
                    val = photo.get(key)
                    if val and isinstance(val, str) and val.startswith("http"):
                        result["cover_url"] = val
                        break
                for key in ["audioUrl", "musicUrl"]:
                    val = photo.get(key)
                    if val and isinstance(val, str) and val.startswith("http"):
                        result["audio_url"] = val
                        break
        except Exception:
            pass
        return result
