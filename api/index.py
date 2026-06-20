"""视频下载器 v2 - Vercel 部署版"""
import os
import sys
import re
import time
import json
from flask import Flask, render_template, request, jsonify, Response, stream_with_context

from parsers import PARSERS

app = Flask(__name__)


def get_parser(url: str):
    for p in PARSERS:
        if p.match(url):
            return p
    return PARSERS[-1]  # GenericParser


def extract_urls(text: str) -> list:
    pattern = r'https?://[^\s<>"\')\]]+'
    urls = re.findall(pattern, text)
    return list(dict.fromkeys(urls))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/parse", methods=["POST"])
def parse_url():
    """解析单个链接"""
    data = request.get_json()
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "请输入链接"}), 400

    try:
        parser = get_parser(url)
        result = parser.parse(url)
        result["parser"] = parser.name
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/batch_parse", methods=["POST"])
def batch_parse():
    """批量解析"""
    data = request.get_json()
    text = data.get("text", "")
    urls = extract_urls(text)

    if not urls:
        return jsonify({"error": "未找到有效链接"}), 400

    results = []
    for url in urls:
        try:
            parser = get_parser(url)
            result = parser.parse(url)
            result["parser"] = parser.name
            result["url"] = url
            results.append(result)
        except Exception as e:
            results.append({"url": url, "error": str(e), "parser": "未知"})

    return jsonify({"results": results, "total": len(results)})


@app.route("/api/download", methods=["POST"])
def download_proxy():
    """流式代理下载 — 快手 CDN 直连返回，其他平台走代理"""
    data = request.get_json()
    media_url = data.get("url", "")
    title = data.get("title", f"video_{int(time.time())}")
    media_type = data.get("type", "video")

    if not media_url:
        return jsonify({"error": "无下载地址"}), 400

    # 快手 CDN 直连 — 返回 URL 让浏览器直接下载
    # djvod.ndcimgs.com 域名不需要鉴权，浏览器可直连
    cdn_domains = ["djvod.ndcimgs.com", "kwaicdn.com", "oskwai.com", "wsukwai.com"]
    is_cdn = any(d in media_url for d in cdn_domains)
    if is_cdn:
        return jsonify({"direct_url": media_url, "title": title, "type": media_type})

    # 通用代理下载
    safe_name = re.sub(r'[\\/:*?"<>|\n\r\t]', '_', title)[:80]
    safe_name = re.sub(r'_+', '_', safe_name).strip('_. ')
    if not safe_name:
        safe_name = f"download_{int(time.time())}"

    ext = ".mp4" if media_type == "video" else ".m4a"
    filename = f"{safe_name}{ext}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
    }

    if "bilivideo.com" in media_url or "bilibili.com" in media_url:
        headers["Referer"] = "https://www.bilibili.com/"

    try:
        import requests as req
        resp = req.get(media_url, headers=headers, stream=True, timeout=120)
        resp.raise_for_status()

        content_length = resp.headers.get('Content-Length')
        content_type = resp.headers.get('Content-Type', 'application/octet-stream')

        def generate():
            for chunk in resp.iter_content(8192):
                if chunk:
                    yield chunk

        response = Response(
            stream_with_context(generate()),
            content_type=content_type,
        )
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        if content_length:
            response.headers['Content-Length'] = content_length

        return response

    except Exception as e:
        return jsonify({"error": f"下载失败: {str(e)}"}), 500


if __name__ == "__main__":
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    port = int(os.environ.get("PORT", 5000))
    print(f"[START] Video Downloader v2 | http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
