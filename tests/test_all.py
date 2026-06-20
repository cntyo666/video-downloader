"""端到端测试脚本 - 验证所有解析器"""
import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.parsers import PARSERS

# 测试用例
TEST_CASES = [
    {
        "name": "回森",
        "urls": [
            "https://s.viviv.com/rJYldkDi",
        ],
    },
    {
        "name": "B站",
        "urls": [
            "https://www.bilibili.com/video/BV1GJ411x7h7",
        ],
    },
    {
        "name": "快手",
        "urls": [
            "https://v.kuaishou.com/abc123",
        ],
    },
]


def test_parser(parser, url, name):
    """测试单个解析器"""
    print(f"\n{'='*60}")
    print(f"🧪 测试: {name}")
    print(f"📎 URL: {url}")
    print(f"🔧 解析器: {parser.name}")
    print(f"{'='*60}")

    start = time.time()
    try:
        result = parser.parse(url)
        elapsed = time.time() - start

        print(f"✅ 解析成功 ({elapsed:.1f}s)")
        print(f"   标题: {result.get('title', 'N/A')}")
        print(f"   作者: {result.get('author', 'N/A')}")
        print(f"   平台: {result.get('platform', 'N/A')}")
        print(f"   视频: {'✓ ' + result['video_url'][:80] + '...' if result.get('video_url') else '✗ 无'}")
        print(f"   音频: {'✓' if result.get('audio_url') else '✗'}")
        print(f"   封面: {'✓' if result.get('cover_url') else '✗'}")

        # 验证下载
        if result.get("video_url"):
            test_download(result["video_url"], result.get("title", "test"))

        return True
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ 解析失败 ({elapsed:.1f}s): {e}")
        return False


def test_download(url, title):
    """测试下载"""
    import requests
    print(f"\n   📥 测试下载...")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0"}
        resp = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        size = resp.headers.get('Content-Length', '?')
        ct = resp.headers.get('Content-Type', '?')
        print(f"   状态: {resp.status_code}")
        print(f"   大小: {size} bytes")
        print(f"   类型: {ct}")

        if resp.status_code == 200:
            print(f"   ✅ 下载链接可用")
        else:
            print(f"   ⚠️ 状态码: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ 下载测试失败: {e}")


def main():
    print("🎬 视频下载器 v2 - 端到端测试")
    print("=" * 60)

    total = 0
    passed = 0

    for case in TEST_CASES:
        for url in case["urls"]:
            total += 1
            # 找到匹配的解析器
            parser = None
            for p in PARSERS:
                if p.match(url) and p.name != "通用":
                    parser = p
                    break
            if not parser:
                parser = PARSERS[-1]

            if test_parser(parser, url, case["name"]):
                passed += 1

    print(f"\n{'='*60}")
    print(f"📊 测试结果: {passed}/{total} 通过")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
