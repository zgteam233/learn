#!/usr/bin/env python3

#
# Created by wsnzg6 on 2026/11/24.
# Copyright(c) 2026 ZGTeam233.
#

from pathlib import Path


# ==================== 配置 ====================

DEFAULT_URL = "https://www.bilibili.com/video/BV1kk4y1j7nZ/"
DEFAULT_MODEL = "danling_newV3"
DEFAULT_INDEX = "danling_newV3_added_IVF4158_Flat_nprobe_1_danling_newV3_v2"

RVC_API = "http://127.0.0.1:7897"

WORKDIR = Path.cwd().resolve()

VIDEO = WORKDIR / "input.mp4"
AUDIO = WORKDIR / "output.aac"
OUTPUT = WORKDIR / "output.wav"

SEPARATED = WORKDIR / "separated"
VOCAL = SEPARATED / "htdemucs" / "output" / "vocals.wav"
NOVOCALS = SEPARATED / "htdemucs" / "output" / "no_vocals.wav"

FINAL_OUTPUT = WORKDIR / "final.wav"

RVC_ROOT = Path(r"C:\RVC").resolve()
INDEX_DIR = RVC_ROOT / "assets" / "indices"