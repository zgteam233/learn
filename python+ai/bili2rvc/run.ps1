./.venv/Scripts/python.exe ./src/bili2rvc.py `
        --url "https://www.bilibili.com/video/BV1Ze4y1V7bZ/?"

# usage: bili2rvc.py [-h] [--url URL] [--model MODEL] [--index INDEX] [--pitch PITCH] [--index-rate INDEX_RATE] [--rms RMS]
#                    [--protect PROTECT] [--vocal-volume VOCAL_VOLUME] [--bgm-volume BGM_VOLUME] [--f0-method F0_METHOD]
#                    [--speaker-id SPEAKER_ID] [--no-cleanup] [--list-models]
#
# Bili2RVC - B站视频下载、人声分离、RVC转换与混音
#
# options:
#   -h, --help            show this help message and exit
#   --url URL             B站视频链接
#   --model MODEL         RVC 模型名称
#   --index INDEX         RVC 索引名称
#   --pitch PITCH         变调，默认 -12
#   --index-rate INDEX_RATE
#                         索引混合比例，默认 0.75
#   --rms RMS             RMS 混合比例，默认 0.25
#   --protect PROTECT     Protect，默认 0.25
#   --vocal-volume VOCAL_VOLUME
#                         人声音量，默认 1.2
#   --bgm-volume BGM_VOLUME
#                         伴奏音量，默认 0.8
#   --f0-method F0_METHOD
#                         音高提取算法，默认 rmvpe
#   --speaker-id SPEAKER_ID
#                        说话人 ID，默认 0
#   --no-cleanup          不清理中间文件
#   --list-models         列出 RVC 可用模型并退出
