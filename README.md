# 🎬 视频下载器 v2

无水印视频下载工具，支持多平台。

## 支持平台

| 平台 | 解析 | 下载 | 备注 |
|------|------|------|------|
| 回森 | ✅ | ✅ | API 直连 |
| 抖音 | ✅ | ✅ | 分享页 + Web API |
| 快手 | ⚠️ | ⚠️ | 反爬较强，Vercel 可能受限 |
| B站 | ✅ | ✅ | API + DASH 流 |
| 小红书 | ✅ | ✅ | 页面提取 |
| 微博 | ✅ | ✅ | 移动端 API |
| 通用 | ✅ | ✅ | 需要 yt-dlp |

## 部署

### Vercel
```bash
# 安装 Vercel CLI
npm i -g vercel

# 部署
vercel --prod
```

### 本地开发
```bash
# 安装依赖
pip install -r requirements.txt

# 启动
python app.py

# 访问 http://localhost:5000
```

### 本地增强版（快手 Playwright）
```bash
# 额外安装
pip install playwright playwright-stealth
playwright install chromium

# 使用增强版解析器
python -c "from parsers.kuaishou_playwright import KuaishouPlaywrightParser; ..."
```

## 项目结构

```
video-downloader-v2/
├── api/
│   ├── index.py              # Flask 主应用
│   ├── requirements.txt      # Vercel 依赖
│   ├── parsers/
│   │   ├── __init__.py       # 解析器注册
│   │   ├── base.py           # 基类
│   │   ├── kuaishou.py       # 快手（多策略）
│   │   ├── douyin.py         # 抖音
│   │   ├── bilibili.py       # B站
│   │   ├── xiaohongshu.py    # 小红书
│   │   ├── huison.py         # 回森
│   │   ├── weibo.py          # 微博
│   │   └── generic.py        # yt-dlp 兜底
│   └── templates/
│       └── index.html        # 前端页面
├── parsers/
│   └── kuaishou_playwright.py # 本地 Playwright 增强版
├── tests/
│   └── test_all.py           # 端到端测试
├── app.py                    # 本地启动
├── vercel.json               # Vercel 配置
└── requirements.txt          # 本地依赖
```

## 技术方案

### 快手 403 问题
- **根因**: 快手 CDN 对服务器 IP 返回 403
- **Vercel 方案**: 移动端 API + 页面 SSR 提取，优先 `djvod.ndcimgs.com` 域名（无需鉴权）
- **本地方案**: Playwright + stealth 拦截 GraphQL，浏览器直连 CDN 下载
- **CDN 域名分析**:
  - `djvod.ndcimgs.com` — tag 参数，可直接下载 ✅
  - `kwaicdn.com` — pkey 参数，403 ❌
  - `oskwai.com` — pkey 参数，403 ❌

### 下载模式
- **通用代理**: Flask 服务端流式转发（回森/抖音/B站/小红书/微博）
- **CDN 直连**: 返回 JSON `{direct_url}` 让浏览器直接下载（快手）
