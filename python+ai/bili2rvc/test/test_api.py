#!/usr/bin/env python3

#
# Created by wsnzg6 on 2026/11/23.
# Copyright(c) 2026 ZGTeam233.
#

from gradio_client import Client

client = Client("http://127.0.0.1:7897")

print("正在刷新 RVC 模型列表...")

try:
    job = client.predict(api_name="/infer_refresh")

    print("任务对象：", job)
    print("等待任务完成...")

    result = job.result()

    print("模型刷新完成！")
    print("返回结果：", result)

except Exception as e:
    print("模型刷新失败：", repr(e))
    raise
