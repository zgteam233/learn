#!/usr/bin/env python3

#
# Created by wsnzg6 on 2026/11/24.
# Copyright(c) 2026 ZGTeam233.
#

from preproc import download_video, extract_audio, separate_vocals
from gradio_client import Client
from config import RVC_API, FINAL_OUTPUT
from rvcapi import get_models, load_rvc_model, rvc_convert
from finish import mix_audio, cleanup


# ==================== 主流程 ====================

def bili2rvc(args):

    if not args.url.startswith(("http://", "https://")):
        print("ERROR: 无效的视频链接")
        return False

    print("\n========== Bili2RVC ==========\n")

    try:
        # 1. 下载视频
        if not download_video(args.url):
            return False

        # 2. 提取音频
        if not extract_audio():
            return False

        # 3. Demucs 分离人声
        if not separate_vocals():
            return False

        # 4. 连接 RVC
        print("正在连接 RVC API...")
        client = Client(RVC_API)

        # 5. 列出模型
        if args.list_models:
            models = get_models(client)

            print("\n可用模型：")
            for model in models:
                print(f"  - {model}")

            return True

        # 6. 加载模型
        if not load_rvc_model(client, args):
            return False

        # 7. RVC 转换
        if not rvc_convert(client, args):
            return False

        # 8. 混合人声与伴奏
        if not mix_audio(args):
            return False

        # 9. 清理临时文件
        if not args.no_cleanup:
            cleanup()

        print("\n========== 处理完成 ==========")
        print(f"最终输出：{FINAL_OUTPUT}")

        return True

    except KeyboardInterrupt:
        print("\n用户取消操作")
        return False

    except Exception as e:
        print(f"\nERROR: 程序异常：{e}")
        return False