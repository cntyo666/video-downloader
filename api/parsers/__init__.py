"""解析器注册"""
from .huison import HuisonParser
from .douyin import DouyinParser
from .kuaishou import KuaishouParser
from .bilibili import BilibiliParser
from .xiaohongshu import XiaohongshuParser
from .weibo import WeiboParser
from .generic import GenericParser

PARSERS = [
    HuisonParser(),
    DouyinParser(),
    KuaishouParser(),
    BilibiliParser(),
    XiaohongshuParser(),
    WeiboParser(),
    GenericParser(),
]

__all__ = ["PARSERS"]
