#!/usr/bin/env python3

#
# Created by wsnzg6 on 2026/11/24.
# Copyright(c) 2026 ZGTeam233.
#

from pathlib import Path
from util import rvc_api_call
from config import VOCAL, OUTPUT, INDEX_DIR
import shutil


# ==================== RVC 初始化 ====================

def get_models(client):
    result = rvc_api_call(
        client,
        api_name="/infer_refresh"
    )

    return result.get("choices", [])


def load_rvc_model(client, args):
    print("正在刷新 RVC 模型列表...")

    models = get_models(client)

    if not models:
        print("ERROR: 没有获取到 RVC 模型列表")
        return False

    print("\n可用模型：")

    for model in models:
        print(f"  - {model}")

    model = args.model

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

def rvc_convert(client, args):
    print("开始 RVC 音频转换...")

    index_path = INDEX_DIR / f"{args.index}.index"

    if not index_path.is_file():
        print(f"ERROR: 索引文件不存在：{index_path}")
        return False

    result = rvc_api_call(
        client,
        args.speaker_id,
        str(VOCAL),
        args.pitch,
        args.f0_method,
        str(index_path),
        args.index_rate,
        0,
        args.rms,
        args.protect,
        api_name="/infer_convert"
    )

    if not isinstance(result, (tuple, list)) or len(result) < 2:
        print("ERROR: RVC 返回结果格式异常：", result)
        return False

    audio_result = result[1]

    if not audio_result:
        print("ERROR: RVC 没有返回转换后的音频")
        return False

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