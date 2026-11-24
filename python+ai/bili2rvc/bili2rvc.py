
#!/usr/bin/env python3

#
# Created by wsnzg6 on 2026/11/23.
# Copyright(c) 2026 ZGTeam233.
#

import subprocess
import shutil
from pathlib import Path
from gradio_client import Client


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

# ==================== 通用函数 ====================

def input_with_default(param, default_value):
    value = input(param).strip()
    return value if value else default_value


def run_command(command, error_message):
    """执行外部命令并检查返回值"""

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode != 0:
        print(f"ERROR: {error_message}")
        print(result.stderr)
        return False

    return True


def rename_by_suffix(directory, suffix, new_name):
    """重命名目录下唯一一个指定后缀的文件"""

    directory = Path(directory)
    files = list(directory.glob(f"*{suffix}"))

    if len(files) != 1:
        print(f"文件数量异常：找到 {len(files)} 个 {suffix} 文件")
        return False

    target = directory / new_name

    if target.exists():
        if not target.is_file():
            print("ERROR: 目标路径不是文件")
            return False

        target.unlink()

    files[0].rename(target)
    return True


def clean_directory(directory):
    """清理指定目录"""

    directory = Path(directory)

    if directory.is_dir():
        shutil.rmtree(directory)

def rvc_api_call(client, *args, api_name):
    """调用 RVC API，并等待异步任务完成"""
    job = client.predict(
        *args,
        api_name=api_name
    )

    if hasattr(job, "result") and callable(job.result):
        return job.result()

    return job


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

    if not VOCAL.is_file():
        print(f"ERROR: 找不到人声文件：{VOCAL}")
        return False

    print("人声分离完成")
    return True


# ==================== RVC 初始化 ====================

def load_rvc_model(client):
    print("正在刷新 RVC 模型列表...")

    refresh_result = rvc_api_call(
        client,
        api_name="/infer_refresh"
    )

    models = refresh_result.get("choices", [])

    if not models:
        print("ERROR: 没有获取到 RVC 模型列表")
        return False

    print("\n可用模型：")
    for model in models:
        print(f"  - {model}")

    model = input_with_default(
        "选取模型:",
        DEFAULT_MODEL
    )

    if not model.endswith(".pth"):
        model += ".pth"

    if model not in models:
        print(f"ERROR: 模型不存在：{model}")
        return False

    print(f"正在加载模型：{model}")

    rvc_api_call(
        client,
        model,
        0.33,
        0.33,
        api_name="/infer_change_voice"
    )

    print("RVC 模型加载完成")
    return True


# ==================== RVC 音频转换 ====================

def rvc_convert(client):
    print("开始 RVC 音频转换...")

    pitch = int(input_with_default("变调:", "-12"))

    index = input_with_default(
        "选取索引:",
        DEFAULT_INDEX
    )

    index_path = f"assets/indices/{index}.index"

    result = rvc_api_call(
        client,
        0,                          # speaker ID
        str(VOCAL),    # 输入音频
        pitch,                      # 变调
        "rmvpe",                    # 音高提取算法
        index_path,                 # index 文件
        0.75,                       # index rate
        0,                          # 重采样率
        0.25,                       # RMS 混合比例
        0.25,                       # protect
        api_name="/infer_convert"
    )

    if not isinstance(result, (tuple, list)) or len(result) < 2:
        print("ERROR: RVC 返回结果格式异常：", result)
        return False

    audio_result = result[1]

    if not audio_result:
        print("ERROR: RVC 没有返回转换后的音频")
        return False

    # 兼容字符串路径和文件信息字典
    if isinstance(audio_result, dict):
        output_file = audio_result.get("path") or audio_result.get("name")
    else:
        output_file = audio_result

    if not output_file:
        print("ERROR: 无法获取 RVC 输出文件路径")
        return False

    output_path = Path(output_file)

    if not output_path.is_file():
        print(f"ERROR: RVC 输出文件不存在：{output_path}")
        return False

    shutil.copy2(output_path, OUTPUT)

    print("RVC 转换完成")
    return True


# ====================== 音频混合 ======================
def mix_audio():
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
            "[0:a]volume=1.0[v];"
            "[1:a]volume=0.8[b];"
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

# ================== 临时文件清理 =================

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


# ==================== 主流程 ====================

def bili2rvc():

    url = input_with_default(
        f"请输入 B 站视频链接（直接回车使用默认: {DEFAULT_URL}）",
        DEFAULT_URL
    )

    if not url.startswith(("http://", "https://")):
        print("ERROR: 无效的视频链接")
        return

    print("\n========== Bili2RVC ==========\n")

    try:
        # 1. 下载视频
        if not download_video(url):
            return

        # 2. 提取音频
        if not extract_audio():
            return

        # 3. Demucs 分离人声
        if not separate_vocals():
            return

        # 4. 连接 RVC
        print("正在连接 RVC API...")

        client = Client(RVC_API)

        # 5. 加载模型
        if not load_rvc_model(client):
            return

        # 6. RVC 转换
        if not rvc_convert(client):
            return

        # 7. 混合人声与伴奏
        if not mix_audio():
            return

        # 8. 清理临时文件
        cleanup()

        print("\n========== 处理完成 ==========")
        print(f"最终输出：{FINAL_OUTPUT}")

    except KeyboardInterrupt:
        print("\n用户取消操作")

    except Exception as e:
        print(f"\nERROR: 程序异常：{e}")


if __name__ == "__main__":
    bili2rvc()
