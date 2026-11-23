#!/usr/bin/env python3

#
# Created by wsnzg6 on 2026/11/23.
# Copyright(c) 2026 ZGTeam233.
#

from gradio_client import Client

client = Client("http://127.0.0.1:7897")

print("客户端协议:", client.protocol)
print("服务端协议字段:", client.config.get("protocol", "<缺失>"))
print("服务端版本:", client.config.get("version"))

print("\nEndpoint 协议:")
for key, endpoint in client.endpoints.items():
    print(
        f"ID={key}, "
        f"API={endpoint.api_name}, "
        f"Protocol={endpoint.protocol}"
    )

print("\nAPI 信息:")
client.view_api()