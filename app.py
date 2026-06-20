"""
视频下载器 - 云端版
支持: 回森/抖音/快手/B站/小红书/微博 + yt-dlp 通用兜底
部署: Render / Railway / 本地均可
"""
import os
import sys
import time
import json
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from parsers.huison import HuisonParser
from parsers.douyin import DouyinParser
from parsers.kuaishou import KuaishouParser
from parsers.bilibili import BilibiliParser
from parsers.xiaohongshu import XiaohongshuParser
from parsers.weibo import WeiboParser
from parsers.generic import GenericParser

app = Flask(__name__)

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
    """根据 URL 选择解析器"""
    for p in PARSERS:
        if p.match(url):
            return p
    return GenericParser()


def extract_urls(text: str) -> list:
    """从文本中提取所有 URL"""
    pattern = r'https?://[^\s<>"\')\]]+'
    urls = re.findall(pattern, text)
    return list(dict.fromkeys(urls))  # 去重保序


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/parse", methods=["POST"])
def parse_url():
    """解析单个链接"""
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
    """流式代理下载 — 直接转发给用户，不在服务器存文件"""
    data = request.get_json()
    media_url = data.get("url", "")
    title = data.get("title", f"video_{int(time.time())}")
    media_type = data.get("type", "video")

    if not media_url:
        return jsonify({"error": "无下载地址"}), 400

    # 生成安全文件名
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

    # B站视频需要特殊 Referer
    if "bilivideo.com" in media_url or "bilibili.com" in media_url:
        headers["Referer"] = "https://www.bilibili.com/"

    try:
        import requests as req
        resp = req.get(media_url, headers=headers, stream=True, timeout=120)
        resp.raise_for_status()

        # 获取内容长度（如果有）
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


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    port = int(os.environ.get("PORT", 5000))
    print(f"[启动] 视频下载器 (云端版)")
    print(f"[地址] http://0.0.0.0:{port}")
    print(f"[平台] 回森 / 抖音 / 快手 / B站 / 小红书 / 微博 + 通用")
    app.run(host="0.0.0.0", port=port, debug=False)
