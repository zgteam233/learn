#!/usr/bin/env python3

#
# Created by wsnzg6 on 2026/11/24.
# Copyright(c) 2026 ZGTeam233.
#

import argparse
from config import DEFAULT_URL, DEFAULT_MODEL, DEFAULT_INDEX


# ==================== 参数解析 ====================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Bili2RVC - B站视频下载、人声分离、RVC转换与混音"
    )

    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="B站视频链接"
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="RVC 模型名称"
    )

    parser.add_argument(
        "--index",
        default=DEFAULT_INDEX,
        help="RVC 索引名称"
    )

    parser.add_argument(
        "--pitch",
        type=int,
        default=-12,
        help="变调，默认 -12"
    )

    parser.add_argument(
        "--index-rate",
        type=float,
        default=0.75,
        help="索引混合比例，默认 0.75"
    )

    parser.add_argument(
        "--rms",
        type=float,
        default=0.25,
        help="RMS 混合比例，默认 0.25"
    )

    parser.add_argument(
        "--protect",
        type=float,
        default=0.25,
        help="Protect，默认 0.25"
    )

    parser.add_argument(
        "--vocal-volume",
        type=float,
        default=1.2,
        help="人声音量，默认 1.2"
    )

    parser.add_argument(
        "--bgm-volume",
        type=float,
        default=0.8,
        help="伴奏音量，默认 0.8"
    )

    parser.add_argument(
        "--f0-method",
        default="rmvpe",
        help="音高提取算法，默认 rmvpe"
    )

    parser.add_argument(
        "--speaker-id",
        type=int,
        default=0,
        help="说话人 ID，默认 0"
    )

    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="不清理中间文件"
    )

    parser.add_argument(
        "--list-models",
        action="store_true",
        help="列出 RVC 可用模型并退出"
    )

    return parser.parse_args()