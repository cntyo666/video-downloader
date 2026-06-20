"""
视频下载器 - Vercel Serverless 版
支持: 回森/抖音/快手/B站/小红书/微博 + yt-dlp 通用兜底
"""
import os
import re
import time
import json
import sys
from pathlib import Path

# 确保 api 目录在 path 中
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from parsers.huison import HuisonParser
from parsers.douyin import DouyinParser
from parsers.kuaishou import KuaishouParser
from parsers.bilibili import BilibiliParser
from parsers.xiaohongshu import XiaohongshuParser
from parsers.weibo import WeiboParser
from parsers.generic import GenericParser

app = Flask(__name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

# 解析器列表（按优先级排序）
PARSERS = [
    HuisonParser(),
    DouyinParser(),
    KuaishouParser(),
    BilibiliParser(),
    XiaohongshuParser(),
    WeiboParser(),
    GenericParser(),  # 兜底
]


def get_parser(url: str):
    for p in PARSERS:
        if p.match(url):
            return p
    return GenericParser()


def extract_urls(text: str) -> list:
    pattern = r'https?://[^\s<>"\')\]]+'
    urls = re.findall(pattern, text)
    return list(dict.fromkeys(urls))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/parse", methods=["POST"])
def parse_url():
    data = request.get_json()
    url = data.get("url", "").strip()
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
    """流式代理下载"""
    data = request.get_json()
    media_url = data.get("url", "")
    title = data.get("title", f"video_{int(time.time())}")
    media_type = data.get("type", "video")

    if not media_url:
        return jsonify({"error": "无下载地址"}), 400

    safe_name = re.sub(r'[\\/:*?"<>|\n\r\t]', '_', title)[:80]
    safe_name = re.sub(r'_+', '_', safe_name).strip('_. ')
    if not safe_name:
        safe_name = f"download_{int(time.time())}"

    ext = ".mp4" if media_type == "video" else ".m4a"
    filename = f"{safe_name}{ext}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    if "bilivideo.com" in media_url or "bilibili.com" in media_url:
        headers["Referer"] = "https://www.bilibili.com/"
    elif "wsukwai.com" in media_url or "kuaishou.com" in media_url or "gifshow.com" in media_url:
        headers["Referer"] = "https://www.kuaishou.com/"
    elif "douyin" in media_url or "tiktok" in media_url:
        headers["Referer"] = "https://www.douyin.com/"
    elif "xiaohongshu" in media_url or "xhscdn" in media_url:
        headers["Referer"] = "https://www.xiaohongshu.com/"
    elif "weibo" in media_url or "sinaimg" in media_url:
        headers["Referer"] = "https://weibo.com/"

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


# Vercel handler
def handler(request, response):
    return app
