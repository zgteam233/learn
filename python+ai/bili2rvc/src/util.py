#!/usr/bin/env python3

#
# Created by wsnzg6 on 2026/11/24.
# Copyright(c) 2026 ZGTeam233.
#

import subprocess
import shutil
from pathlib import Path


# ==================== 通用函数 ====================

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