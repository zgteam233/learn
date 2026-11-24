# Bili2RVC

Bili2RVC 是一个命令行工具，可将 Bilibili 视频中的人声转换为指定的 RVC 音色，并与原视频伴奏混合输出。

处理流程：

1. 使用 `bbdownn` 下载视频。
2. 使用 FFmpeg 提取音频。
3. 使用 Docker 和 Demucs 分离人声与伴奏。
4. 通过 Gradio API 调用本机 RVC 服务进行人声转换。
5. 使用 FFmpeg 将转换后的人声与伴奏混合，生成 `final.wav`。

## 运行环境

- Windows 和 Python（项目当前使用 Python 3.12）。
- Python 依赖：`pip install -r requirements.txt`。
- 外部程序：`bbdownn`、`ffmpeg`、Docker。
- Demucs Docker 镜像和可用的 NVIDIA GPU（脚本通过 `--gpus all` 使用 GPU）。
- 已启动并可访问的 RVC Gradio 服务，默认地址为 `http://127.0.0.1:7897`。
- RVC 模型和索引文件。当前索引目录在 `src/config.py` 中配置为 `C:\RVC\assets\indices`。

运行命令时请从项目目录启动程序，因为输入、输出和中间文件目录基于当前工作目录确定。RVC 服务地址、RVC 根目录和默认模型等配置也可在 `src/config.py` 中修改。

## CLI 调用

在项目目录打开 PowerShell：

```powershell
.\.venv\Scripts\python.exe .\src\bili2rvc.py `
  --url "https://www.bilibili.com/video/BVxxxxxxxxxx/" `
  --model "danling_newV3" `
  --index "danling_newV3_added_IVF4158_Flat_nprobe_1_danling_newV3_v2"
```

也可以省略参数，使用 `src/config.py` 中的默认视频 URL、模型和索引：

```powershell
.\.venv\Scripts\python.exe .\src\bili2rvc.py
```

可用参数：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--url` | 配置中的默认 URL | Bilibili 视频链接 |
| `--model` | `danling_newV3` | RVC 模型名称，可省略 `.pth` 后缀 |
| `--index` | 配置中的默认索引 | RVC 索引名称，可省略 `.index` 后缀 |
| `--pitch` | `-12` | 变调 |
| `--index-rate` | `0.75` | 索引混合比例 |
| `--rms` | `0.25` | RMS 混合比例 |
| `--protect` | `0.25` | Protect 参数 |
| `--vocal-volume` | `1.2` | 混音时的人声音量 |
| `--bgm-volume` | `0.8` | 混音时的伴奏音量 |
| `--f0-method` | `rmvpe` | 音高提取算法 |
| `--speaker-id` | `0` | 说话人 ID |
| `--no-cleanup` | 关闭 | 保留视频、音频和分离结果等中间文件 |
| `--list-models` | 关闭 | 查询并打印 RVC 可用模型 |

例如，调整变调并保留处理中间文件：

```powershell
.\.venv\Scripts\python.exe .\src\bili2rvc.py `
  --url "https://www.bilibili.com/video/BVxxxxxxxxxx/" `
  --pitch -5 `
  --no-cleanup
```

运行成功后，最终音频写入当前工作目录下的 `final.wav`。默认情况下，处理完成后会清理下载视频、提取音频、转换音频和 Demucs 分离目录。

> 注意：当前 `--list-models` 选项是在下载和 Demucs 分离之后执行的，因此调用它仍需要满足前置处理依赖。

## Python 代码调用

主流程函数定义在 `src/mainapi.py`，函数签名为 `bili2rvc(args)`。`args` 需要提供与 CLI 参数相同名称的属性。下面的例子可放在项目根目录的 Python 脚本中运行：

```python
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from mainapi import bili2rvc

args = SimpleNamespace(
    url="https://www.bilibili.com/video/BVxxxxxxxxxx/",
    model="danling_newV3",
    index="danling_newV3_added_IVF4158_Flat_nprobe_1_danling_newV3_v2",
    pitch=-12,
    index_rate=0.75,
    rms=0.25,
    protect=0.25,
    vocal_volume=1.2,
    bgm_volume=0.8,
    f0_method="rmvpe",
    speaker_id=0,
    no_cleanup=False,
    list_models=False,
)

if not bili2rvc(args):
    raise SystemExit("Bili2RVC 处理失败")
```

`bili2rvc(args)` 在成功时返回 `True`，处理失败或用户中断时返回 `False`。若希望复用 CLI 参数解析器，可在自己的入口程序中调用 `parse.parse_args()` 获取参数对象，再传给 `bili2rvc()`。

## 输出与中间文件

- `final.wav`：最终混音结果。
- `input.mp4`：下载的视频。
- `output.aac`：从视频提取的音频。
- `output.wav`：RVC 转换后的人声。
- `separated/`：Demucs 分离的人声和伴奏。

除 `final.wav` 外，其余文件默认会在流程成功结束后清理；使用 `--no-cleanup` 可保留它们用于检查。
