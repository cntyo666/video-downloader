"""快手解析器 - 多策略: 移动端 API + 页面 SSR 提取"""
import re
import json
import time
import requests
from .base import BaseParser


class KuaishouParser(BaseParser):
    name = "快手"
    domains = ["kuaishou.com", "gifshow.com", "v.kuaishou.com", "v.m.chenzhongtech.com"]

    def parse(self, url: str) -> dict:
        real_url = self.follow_redirect(url)
        photo_id = self._extract_id(real_url)

        # 策略 1: 移动端 API
        if photo_id:
            result = self._try_mobile_api(photo_id)
            if result and result.get("video_url"):
                return result

        # 策略 2: 移动端分享页 SSR 数据
        result = self._try_share_page(real_url, photo_id)
        if result and result.get("video_url"):
            return result

        # 策略 3: 桌面页面 meta 标签
        result = self._try_desktop_page(real_url, photo_id)
        if result and result.get("video_url"):
            return result

        raise ValueError(
            "快手解析失败: 反爬限制较强，服务端无法直接获取视频。\n"
            "建议: 使用本地版本（支持 Playwright 浏览器自动化）"
        )

    def _extract_id(self, url: str) -> str:
        """提取 photoId"""
        patterns = [
            r'/short-video/(\w+)',
            r'/photo/(\w+)',
            r'photoId=(\w+)',
            r'itemId=(\w+)',
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1)
        return ""

    def _try_mobile_api(self, photo_id: str) -> dict:
        """策略 1: 快手移动端作品详情 API"""
        api_url = "https://v.m.chenzhongtech.com/rest/wd/photo/info?kpn=KUAISHOU&captchaToken="
        headers = {
            **self.MOBILE_HEADERS,
            "Content-Type": "application/json",
            "Referer": f"https://v.m.chenzhongtech.com/photo/{photo_id}",
            "Origin": "https://v.m.chenzhongtech.com",
        }
        try:
            resp = requests.post(api_url, json={"photoId": photo_id}, headers=headers, timeout=15)
            if resp.status_code != 200:
                return None

            data = resp.json()
            result = self._parse_api_response(data, photo_id)
            if result and result.get("video_url"):
                result["platform"] = "快手"
                return result
        except Exception:
            pass
        return None

    def _try_share_page(self, url: str, photo_id: str) -> dict:
        """策略 2: 移动端分享页 HTML 提取"""
        share_urls = []
        if photo_id:
            share_urls.append(f"https://v.m.chenzhongtech.com/photo/{photo_id}")
            share_urls.append(f"https://v.m.chenzhongtech.com/short-video/{photo_id}")

        for share_url in share_urls:
            try:
                headers = {
                    **self.MOBILE_HEADERS,
                    "Referer": "https://v.m.chenzhongtech.com/",
                }
                resp = requests.get(share_url, headers=headers, timeout=15, allow_redirects=True)
                html = resp.text

                result = {"platform": "快手"}

                # 提取 SSR 数据
                ssr_patterns = [
                    r'window\.__INITIAL_STATE__\s*=\s*({.*?});?\s*</',
                    r'window\.__NEXT_DATA__\s*=\s*({.*?});?\s*</',
                    r'<script[^>]*>\s*self\.__next_f\.push\(\[.*?"({.*?photoUrl.*?})"\s*\]',
                ]
                for pattern in ssr_patterns:
                    m = re.search(pattern, html, re.S)
                    if m:
                        try:
                            raw = m.group(1)
                            if raw.startswith('"'):
                                raw = json.loads(raw)
                            data = json.loads(raw) if isinstance(raw, str) else raw
                            found = self._find_video_in_data(data, photo_id)
                            if found:
                                result.update(found)
                                return result
                        except (json.JSONDecodeError, TypeError):
                            continue

                # 提取 title
                title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.S)
                if title_m:
                    t = title_m.group(1).strip()
                    t = re.sub(r'\s*[-_|].*?(快手|Kuaishou).*?$', '', t, flags=re.I)
                    if t and len(t) > 1:
                        result["title"] = t

                # 提取 og:video
                og_video = re.search(r'<meta[^>]+property="og:video"[^>]+content="([^"]+)"', html)
                if og_video:
                    result["video_url"] = og_video.group(1)
                    return result

                # 提取视频 URL 直接匹配
                video_m = re.search(r'"(https?://[^"]*(?:djvod|kwaicdn|oskwai)[^"]*\.mp4[^"]*)"', html)
                if video_m:
                    result["video_url"] = video_m.group(1)
                    return result

            except Exception:
                continue
        return None

    def _try_desktop_page(self, url: str, photo_id: str) -> dict:
        """策略 3: 桌面页面提取"""
        desktop_url = f"https://www.kuaishou.com/short-video/{photo_id}" if photo_id else url
        try:
            headers = {
                **self.HEADERS,
                "Referer": "https://www.kuaishou.com/",
            }
            resp = requests.get(desktop_url, headers=headers, timeout=15)
            html = resp.text

            result = {"platform": "快手"}

            # Apollo state
            apollo_m = re.search(r'window\.__APOLLO_STATE__\s*=\s*({.*?});?\s*</', html, re.S)
            if apollo_m:
                try:
                    data = json.loads(apollo_m.group(1))
                    found = self._find_video_in_data(data, photo_id)
                    if found:
                        result.update(found)
                        return result
                except json.JSONDecodeError:
                    pass

            # SSR data
            for pattern in [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});?\s*</',
                r'window\.__NEXT_DATA__\s*=\s*({.*?});?\s*</',
            ]:
                m = re.search(pattern, html, re.S)
                if m:
                    try:
                        data = json.loads(m.group(1))
                        found = self._find_video_in_data(data, photo_id)
                        if found:
                            result.update(found)
                            return result
                    except json.JSONDecodeError:
                        continue

            # Title
            title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.S)
            if title_m:
                t = title_m.group(1).strip()
                t = re.sub(r'\s*[-_|].*?(快手|Kuaishou).*?$', '', t, flags=re.I)
                if t and len(t) > 1:
                    result["title"] = t

        except Exception:
            pass
        return None

    def _find_video_in_data(self, data, target_photo_id: str = None, depth: int = 0) -> dict:
        """递归查找视频 URL"""
        if depth > 20:
            return None

        if isinstance(data, dict):
            photo = data.get("photo")
            if isinstance(photo, dict):
                photo_url = photo.get("photoUrl", "")
                photo_id = photo.get("id", "")
                if photo_url and any(x in photo_url for x in ["djvod", "kwaicdn", "oskwai", "wsukwai"]):
                    result = {
                        "video_url": photo_url,
                        "title": photo.get("caption", "") or photo.get("title", ""),
                        "cover_url": photo.get("coverUrl", ""),
                        "author": photo.get("userName", ""),
                    }
                    if target_photo_id and photo_id and target_photo_id == photo_id:
                        return result
                    if not target_photo_id:
                        return result

            for v in data.values():
                found = self._find_video_in_data(v, target_photo_id, depth + 1)
                if found:
                    return found

        elif isinstance(data, list):
            for item in data:
                found = self._find_video_in_data(item, target_photo_id, depth + 1)
                if found:
                    return found

        return None

    def _parse_api_response(self, data: dict, photo_id: str = None) -> dict:
        """解析 API 响应"""
        result = {}
        try:
            photo = data.get("photo") or data.get("data") or data
            if not isinstance(photo, dict):
                return None

            result["title"] = photo.get("caption", "")
            result["author"] = photo.get("userName", "")
            result["cover_url"] = photo.get("coverUrl", "")

            # 视频 URL
            for key in ["photoUrl", "playUrl", "videoUrl", "url", "mainMvUrl"]:
                val = photo.get(key)
                if val and isinstance(val, str) and val.startswith("http"):
                    result["video_url"] = val
                    break

            # 优先 djvod 域名
            if result.get("video_url") and "djvod" not in result["video_url"]:
                for key in ["photoUrl", "playUrl", "videoUrl"]:
                    val = photo.get(key)
                    if val and isinstance(val, str) and "djvod" in val:
                        result["video_url"] = val
                        break

        except Exception:
            pass
        return result if result.get("video_url") else None
