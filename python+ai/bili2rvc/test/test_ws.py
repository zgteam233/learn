#!/usr/bin/env python3

#
# Created by wsnzg6 on 2026/11/23.
# Copyright(c) 2026 ZGTeam233.
#

from importlib.metadata import version
from gradio_client import Client

print("gradio_client:", version("gradio_client"))

try:
    print("gradio:", version("gradio"))
except Exception:
    print("gradio: 未安装在当前 Python 环境")

client = Client("http://127.0.0.1:7897")

print("服务端 Gradio 版本:", client.config.get("version"))
print("通信协议:", client.config.get("protocol"))
print("API 前缀:", client.config.get("api_prefix"))