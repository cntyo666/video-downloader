"""回森 (viviv.com / getkwai.com) 解析器"""
import re
import requests
from urllib.parse import urlparse, parse_qs, unquote
from .base import BaseParser


class HuisonParser(BaseParser):
    name = "回森"
    domains = ["viviv.com", "getkwai.com", "h5.getkwai.com"]

    def parse(self, url: str) -> dict:
        # 1. 获取重定向 URL
        redirect_url = self._follow_redirect(url)

        # 2. 解析参数
        params = self._extract_params(redirect_url)

        # 3. 尝试获取页面数据（可能有视频 URL）
        page_data = self._fetch_page_data(redirect_url, params)

        result = {
            "title": page_data.get("title", f"回森_{params.get('itemId', 'unknown')}"),
            "video_url": page_data.get("video_url"),
            "audio_url": params.get("audioUrl"),
            "cover_url": page_data.get("cover_url"),
            "platform": "回森",
            "author": page_data.get("author", ""),
        }

        # 如果从页面没拿到视频 URL，尝试 API
        if not result["video_url"] and params.get("itemId"):
            api_data = self._query_api(params["itemId"])
            if api_data:
                result["video_url"] = api_data.get("video_url", result["video_url"])
                result["title"] = api_data.get("title", result["title"])
                result["cover_url"] = api_data.get("cover_url", result["cover_url"])
                result["author"] = api_data.get("author", result["author"])
                # API 可能有更高质量的音频
                if api_data.get("audio_url"):
                    result["audio_url"] = api_data["audio_url"]

        return result

    def _follow_redirect(self, url: str) -> str:
        """跟踪短链接重定向"""
        try:
            resp = requests.head(url, headers=self.HEADERS, allow_redirects=False, timeout=10)
            location = resp.headers.get("Location", "")
            if location:
                return location
        except Exception:
            pass
        # fallback: 用 GET
        try:
            resp = requests.get(url, headers=self.HEADERS, allow_redirects=True, timeout=10)
            return resp.url
        except Exception:
            return url

    def _extract_params(self, redirect_url: str) -> dict:
        """从重定向 URL 提取参数"""
        parsed = urlparse(redirect_url)
        qs = parse_qs(parsed.query)

        result = {}
        if "itemId" in qs:
            result["itemId"] = qs["itemId"][0]
        if "audioUrl" in qs:
            result["audioUrl"] = unquote(qs["audioUrl"][0])
        if "fromId" in qs:
            result["fromId"] = qs["fromId"][0]
        if "cid" in qs:
            result["cid"] = qs["cid"][0]

        return result

    def _fetch_page_data(self, url: str, params: dict) -> dict:
        """尝试从页面 HTML 提取更多数据"""
        try:
            headers = {**self.HEADERS, "Referer": "https://h5.getkwai.com/"}
            resp = requests.get(url, headers=headers, timeout=15)
            resp.encoding = resp.apparent_encoding or 'utf-8'
            html = resp.text

            data = {}

            # 尝试提取标题
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.S)
            if title_match:
                t = title_match.group(1).strip()
                if t and "安全提示" not in t and len(t) > 4:
                    # 去掉平台后缀
                    t = t.replace('作品分享 - 回森', '').replace('- 回森', '').strip(' -')
                    if t:
                        data["title"] = t

            # 尝试提取视频 URL（页面可能内嵌 JSON 数据）
            video_patterns = [
                r'"playUrl"\s*:\s*"(https?://[^"]+\.mp4[^"]*)"',
                r'"videoUrl"\s*:\s*"(https?://[^"]+)"',
                r'"url"\s*:\s*"(https?://[^"]+\.mp4[^"]*)"',
                r'"src"\s*:\s*"(https?://[^"]+\.mp4[^"]*)"',
                r'"coverUrl"\s*:\s*"(https?://[^"]+)"',
                r'"cover"\s*:\s*\{[^}]*"url"\s*:\s*"(https?://[^"]+)"',
            ]
            for pattern in video_patterns:
                m = re.search(pattern, html)
                if m:
                    val = m.group(1).replace('\\u002F', '/').replace('\\/', '/')
                    if 'playUrl' in pattern or 'videoUrl' in pattern or '.mp4' in val.lower():
                        data.setdefault("video_url", val)
                    elif 'cover' in pattern.lower():
                        data.setdefault("cover_url", val)

            return data
        except Exception:
            return {}

    def _query_api(self, item_id: str) -> dict:
        """尝试调用回森/快手 API 获取作品详情"""
        apis = [
            # 快手通用作品详情 API
            {
                "url": "https://h5.getkwai.com/rest/wd/photo/info?kpn=KUAISHOU&captchaToken=",
                "method": "POST",
                "json": {"photoId": item_id, "isLongVideo": False},
            },
        ]

        for api in apis:
            try:
                headers = {
                    **self.HEADERS,
                    "Content-Type": "application/json",
                    "Referer": f"https://h5.getkwai.com/html/mulight-web/share/video/index.html?itemId={item_id}",
                }
                if api["method"] == "POST":
                    resp = requests.post(api["url"], json=api["json"], headers=headers, timeout=10)
                else:
                    resp = requests.get(api["url"], headers=headers, timeout=10)

                if resp.status_code == 200:
                    data = resp.json()
                    return self._parse_api_response(data)
            except Exception:
                continue

        return None

    def _parse_api_response(self, data: dict) -> dict:
        """解析 API 返回数据"""
        result = {}
        try:
            # 快手 API 通用结构
            photo = data.get("photo") or data.get("data") or data
            if isinstance(photo, dict):
                result["title"] = photo.get("caption", "")
                result["author"] = photo.get("userName", "")

                # 视频 URL
                for key in ["playUrl", "videoUrl", "url", "mainMvUrl"]:
                    val = photo.get(key)
                    if val and isinstance(val, str) and val.startswith("http"):
                        result["video_url"] = val
                        break

                # 封面
                for key in ["coverUrl", "cover", "thumbnailUrl"]:
                    val = photo.get(key)
                    if val and isinstance(val, str) and val.startswith("http"):
                        result["cover_url"] = val
                        break

                # 音频
                for key in ["audioUrl", "musicUrl"]:
                    val = photo.get(key)
                    if val and isinstance(val, str) and val.startswith("http"):
                        result["audio_url"] = val
                        break
        except Exception:
            pass
        return result
