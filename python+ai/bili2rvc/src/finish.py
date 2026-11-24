#!/usr/bin/env python3

#
# Created by wsnzg6 on 2026/11/24.
# Copyright(c) 2026 ZGTeam233.
#

from config import OUTPUT, NOVOCALS, FINAL_OUTPUT, VIDEO, AUDIO, SEPARATED
from util import run_command, clean_directory


# ====================== 音频混合 ======================

def mix_audio(args):
    print("开始混合人声与伴奏...")

    if not OUTPUT.is_file() or not NOVOCALS.is_file():
        print("ERROR: 缺少人声或伴奏文件")
        return False

    if not run_command(
        [
            "ffmpeg",
            "-y",
            "-i", str(OUTPUT),
            "-i", str(NOVOCALS),
            "-filter_complex",
            f"[0:a]volume={args.vocal_volume}[v];"
            f"[1:a]volume={args.bgm_volume}[b];"
            "[v][b]amix=inputs=2:duration=longest:normalize=0[a]",
            "-map", "[a]",
            "-c:a", "pcm_s16le",
            str(FINAL_OUTPUT)
        ],
        "音频混合失败"
    ):
        return False

    print("混音完成")
    return True


# ================== 临时文件清理 ==================

def cleanup():
    print("开始清理临时文件...")

    files = [
        VIDEO,
        AUDIO,
        OUTPUT
    ]

    for file in files:
        if file.is_file():
            file.unlink()
            print(f"删除文件：{file.name}")

    clean_directory(SEPARATED)

    print("临时文件清理完成")