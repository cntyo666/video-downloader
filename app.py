"""本地开发启动"""
import sys
import os
import io

# 修复 Windows 控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 将 api 目录加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from api.index import app

if __name__ == "__main__":
    print("=" * 50)
    print("Video Downloader v2 - Local Dev")
    print("http://127.0.0.1:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)
