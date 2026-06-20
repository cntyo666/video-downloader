"""通用解析器 - yt-dlp 兜底"""
import shutil
import subprocess
import json
import re
from .base import BaseParser


class GenericParser(BaseParser):
    name = "通用"
    domains = []  # 兜底，匹配所有

    def match(self, url: str) -> bool:
        return True  # 兜底

    def parse(self, url: str) -> dict:
        ytdlp = shutil.which("yt-dlp")
        if not ytdlp:
            raise ValueError(
                "该平台暂无专用解析器，且 yt-dlp 未安装。\n"
                "支持的平台: 回森/抖音/快手/B站/小红书/微博"
            )

        try:
            # 获取视频信息
            cmd = [ytdlp, "--dump-json", "--no-download", "--no-warnings", url]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                encoding="utf-8", errors="replace"
            )

            if result.returncode != 0:
                raise ValueError(f"yt-dlp 解析失败: {result.stderr[:200]}")

            info = json.loads(result.stdout)

            video_url = None
            audio_url = None

            # 选择最佳格式
            formats = info.get("formats", [])
            if formats:
                # 最佳视频
                video_formats = [f for f in formats if f.get("vcodec") != "none"]
                if video_formats:
                    best = max(video_formats, key=lambda f: f.get("height", 0) or 0)
                    video_url = best.get("url")

                # 最佳音频
                audio_formats = [f for f in formats if f.get("acodec") != "none" and f.get("vcodec") == "none"]
                if audio_formats:
                    best_audio = max(audio_formats, key=lambda f: f.get("abr", 0) or 0)
                    audio_url = best_audio.get("url")

            if not video_url:
                video_url = info.get("url")

            return {
                "title": info.get("title", ""),
                "video_url": video_url,
                "audio_url": audio_url,
                "cover_url": info.get("thumbnail"),
                "platform": info.get("extractor", "通用"),
                "author": info.get("uploader", "") or info.get("channel", ""),
            }

        except subprocess.TimeoutExpired:
            raise ValueError("yt-dlp 解析超时（30秒）")
        except json.JSONDecodeError:
            raise ValueError("yt-dlp 返回数据格式错误")
        except Exception as e:
            raise ValueError(f"yt-dlp 错误: {str(e)}")
