#!/usr/bin/env python3

#
# Created by wsnzg6 on 2026/11/24.
# Copyright(c) 2026 ZGTeam233.
#

from config import WORKDIR, VIDEO, AUDIO, SEPARATED, VOCAL, NOVOCALS
from util import rename_by_suffix, run_command, clean_directory


# ==================== 下载视频 ====================

def download_video(url):
    print("开始下载视频...")

    if not run_command(
        ["bbdownn", "-p", "1", url],
        "B站视频下载失败"
    ):
        return False

    if not rename_by_suffix(WORKDIR, ".mp4", VIDEO.name):
        print("ERROR: 无法确定下载的视频文件")
        return False

    print("视频下载完成")
    return True


# ==================== 提取音频 ====================

def extract_audio():
    print("开始提取音频...")

    if not run_command(
        [
            "ffmpeg",
            "-y",
            "-i", str(VIDEO),
            "-vn",
            "-c:a", "aac",
            str(AUDIO)
        ],
        "FFmpeg 音频提取失败"
    ):
        return False

    print("音频提取完成")
    return True


# ==================== Demucs 人声分离 ====================

def separate_vocals():
    print("开始 Demucs 人声分离...")

    clean_directory(SEPARATED)

    if not run_command(
        [
            "docker", "run",
            "--rm",
            "--gpus", "all",
            "-e", "HF_ENDPOINT=https://hf-mirror.com",
            "-v", f"{WORKDIR}:/app",
            "-w", "/app",
            "demucs",
            "--two-stems", "vocals",
            "-d", "cuda",
            "/app/output.aac"
        ],
        "Demucs 分离失败"
    ):
        return False

    if not VOCAL.is_file() or not NOVOCALS.is_file():
        print("ERROR: 找不到人声或伴奏文件")
        return False

    print("人声分离完成")
    return True