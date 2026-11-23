# -*- coding: utf-8 -*-
"""
NVIDIA H.265 批量转换工具
依赖：Python 3.9+、FFmpeg/FFprobe（需支持 hevc_nvenc）、NVIDIA 显卡及驱动
输出：原视频旁边的 文件名_H265.mkv
"""

import json
import os
import queue
import shutil
import subprocess
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".webm",
    ".m4v", ".ts", ".mts", ".m2ts", ".mpg", ".mpeg", ".3gp",
    ".ogv", ".vob", ".asf"
}

# 均衡质量：NVENC P5 + HQ + VBR CQ 26
NVENC_ARGS = [
    "-c:v", "hevc_nvenc",
    "-preset", "p5",
    "-tune", "hq",
    "-rc", "vbr",
    "-cq", "26",
    "-b:v", "0",
]


def find_binary(name: str) -> str | None:
    """优先查找脚本目录、bin 子目录，其次查找 PATH。"""
    exe = name + (".exe" if os.name == "nt" else "")
    here = Path(__file__).resolve().parent
    candidates = [here / exe, here / "bin" / exe]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return shutil.which(exe) or shutil.which(name)


def run_capture(args):
    return subprocess.run(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
    )


class H265ConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NVIDIA H.265 批量转换工具")
        self.root.geometry("820x590")
        self.root.minsize(700, 480)

        self.ffmpeg = find_binary("ffmpeg")
        self.ffprobe = find_binary("ffprobe")
        self.jobs = []
        self.worker = None
        self.events = queue.Queue()
        self.running = False
        self.cancel_requested = False
        self.current_process = None
        self.total = 0
        self.completed = 0
        self.success = 0
        self.skipped = 0
        self.failed = 0

        self._build_ui()
        self._check_tools()
        self.root.after(100, self._poll_events)

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)

        title = ttk.Label(
            outer, text="NVIDIA H.265（HEVC）批量转换",
            font=("Microsoft YaHei UI", 16, "bold")
        )
        title.pack(anchor="w")

        self.status_var = tk.StringVar(value="正在检查 FFmpeg 环境…")
        ttk.Label(outer, textvariable=self.status_var).pack(anchor="w", pady=(4, 10))

        toolbar = ttk.Frame(outer)
        toolbar.pack(fill="x", pady=(0, 8))
        self.add_files_btn = ttk.Button(toolbar, text="添加视频文件", command=self.add_files)
        self.add_files_btn.pack(side="left", padx=(0, 6))
        self.add_folder_btn = ttk.Button(toolbar, text="添加文件夹（递归）", command=self.add_folder)
        self.add_folder_btn.pack(side="left", padx=6)
        self.remove_btn = ttk.Button(toolbar, text="移除选中", command=self.remove_selected)
        self.remove_btn.pack(side="left", padx=6)
        self.clear_btn = ttk.Button(toolbar, text="清空列表", command=self.clear_list)
        self.clear_btn.pack(side="left", padx=6)

        list_frame = ttk.LabelFrame(outer, text="待处理视频", padding=6)
        list_frame.pack(fill="both", expand=True)
        columns = ("file", "state")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("file", text="文件路径")
        self.tree.heading("state", text="状态")
        self.tree.column("file", width=620, anchor="w")
        self.tree.column("state", width=110, anchor="center")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        progress_frame = ttk.Frame(outer)
        progress_frame.pack(fill="x", pady=(10, 4))
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x")
        self.progress_text = tk.StringVar(value="等待开始")
        ttk.Label(outer, textvariable=self.progress_text).pack(anchor="w")

        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(10, 0))
        self.start_btn = ttk.Button(bottom, text="开始转换", command=self.start)
        self.start_btn.pack(side="left")
        self.cancel_btn = ttk.Button(bottom, text="停止任务", command=self.cancel, state="disabled")
        self.cancel_btn.pack(side="left", padx=8)
        ttk.Label(
            bottom, text="输出：原文件目录 / 文件名_H265.mkv",
            foreground="#555"
        ).pack(side="right")

        log_frame = ttk.LabelFrame(outer, text="运行日志", padding=5)
        log_frame.pack(fill="x", pady=(10, 0))
        self.log = tk.Text(log_frame, height=7, wrap="word", state="disabled")
        self.log.pack(fill="x")

    def _log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _check_tools(self):
        if not self.ffmpeg or not self.ffprobe:
            missing = []
            if not self.ffmpeg:
                missing.append("ffmpeg.exe")
            if not self.ffprobe:
                missing.append("ffprobe.exe")
            self.status_var.set("未找到：" + "、".join(missing))
            self._log("请安装包含 FFmpeg 和 FFprobe 的完整版本。")
            self._log("可将两个 exe 放在本程序同目录或 bin 子目录，或加入 PATH。")
            self.start_btn.configure(state="disabled")
            return

        result = run_capture([self.ffmpeg, "-hide_banner", "-encoders"])
        if result.returncode != 0 or "hevc_nvenc" not in result.stdout:
            self.status_var.set("当前 FFmpeg 不包含 hevc_nvenc，无法进行 NVIDIA 硬件编码")
            self._log("错误：FFmpeg 编码器列表中没有 hevc_nvenc。")
            self.start_btn.configure(state="disabled")
            return

        self.status_var.set("环境检查通过：已找到 FFmpeg、FFprobe 和 hevc_nvenc")
        self._log(f"FFmpeg：{self.ffmpeg}")
        self._log(f"FFprobe：{self.ffprobe}")
        self._log("检测到 hevc_nvenc。开始转换时还会实际调用编码器；驱动/GPU 不兼容会报告失败。")

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="选择视频文件",
            filetypes=[("视频文件", "*.mp4 *.mkv *.mov *.avi *.wmv *.flv *.webm *.m4v *.ts *.mts *.m2ts *.mpg *.mpeg *.3gp"), ("所有文件", "*.*")]
        )
        self._add_paths(paths)

    def add_folder(self):
        folder = filedialog.askdirectory(title="选择要递归扫描的文件夹")
        if not folder:
            return
        found = []
        for path in Path(folder).rglob("*"):
            if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
                found.append(str(path))
        self._add_paths(found)
        self._log(f"文件夹扫描完成：找到 {len(found)} 个视频文件。")

    def _add_paths(self, paths):
        existing = {str(Path(p).resolve()).lower() for p in self.jobs}
        added = 0
        for item in paths:
            p = Path(item)
            if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS:
                key = str(p.resolve()).lower()
                if key not in existing:
                    self.jobs.append(str(p.resolve()))
                    self.tree.insert("", "end", iid=str(len(self.jobs) - 1), values=(str(p), "待处理"))
                    existing.add(key)
                    added += 1
        self._log(f"已添加 {added} 个视频。")

    def _rebuild_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, p in enumerate(self.jobs):
            self.tree.insert("", "end", iid=str(i), values=(p, "待处理"))

    def remove_selected(self):
        if self.running:
            return
        selected = sorted((int(x) for x in self.tree.selection()), reverse=True)
        for i in selected:
            if 0 <= i < len(self.jobs):
                self.jobs.pop(i)
        self._rebuild_tree()

    def clear_list(self):
        if self.running:
            return
        self.jobs.clear()
        self._rebuild_tree()
        self.progress_var.set(0)
        self.progress_text.set("等待开始")

    def start(self):
        if self.running or not self.jobs:
            if not self.jobs:
                messagebox.showinfo("提示", "请先添加视频文件或文件夹。")
            return
        if not self.ffmpeg or not self.ffprobe:
            messagebox.showerror("缺少组件", "请先配置 FFmpeg 和 FFprobe。")
            return

        self.running = True
        self.cancel_requested = False
        self.completed = self.success = self.skipped = self.failed = 0
        self.total = len(self.jobs)
        self.progress_var.set(0)
        self.start_btn.configure(state="disabled")
        self.add_files_btn.configure(state="disabled")
        self.add_folder_btn.configure(state="disabled")
        self.remove_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.worker = threading.Thread(target=self._worker, daemon=True)
        self.worker.start()

    def cancel(self):
        self.cancel_requested = True
        self._log("已请求停止：当前转码结束/中断后将停止后续任务。")
        proc = self.current_process
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass

    def _set_state(self, index, state):
        self.events.put(("state", index, state))

    def _worker(self):
        for index, source in enumerate(list(self.jobs)):
            if self.cancel_requested:
                break
            self.events.put(("log", f"[{index + 1}/{self.total}] 检测：{source}"))
            try:
                result = run_capture([
                    self.ffprobe, "-v", "error", "-select_streams", "v:0",
                    "-show_entries", "stream=codec_name",
                    "-of", "default=noprint_wrappers=1:nokey=1", source
                ])
                codec = result.stdout.strip().splitlines()[0].strip().lower() if result.stdout.strip() else ""
                if result.returncode != 0 or not codec:
                    self.skipped += 1
                    self._set_state(index, "检测失败")
                    self.events.put(("log", "[跳过] 无法读取视频编码信息或文件没有视频流。"))
                elif codec in ("hevc", "h265"):
                    self.skipped += 1
                    self._set_state(index, "已是 H.265")
                    self.events.put(("log", "[跳过] 已经是 H.265/HEVC。"))
                else:
                    output = str(Path(source).with_name(Path(source).stem + "_H265.mkv"))
                    if os.path.exists(output):
                        self.skipped += 1
                        self._set_state(index, "输出已存在")
                        self.events.put(("log", f"[跳过] 输出文件已存在：{output}"))
                    else:
                        ok = self._transcode(source, output)
                        if ok:
                            self.success += 1
                            self._set_state(index, "转换成功")
                            self.events.put(("log", f"[成功] {output}"))
                        else:
                            self.failed += 1
                            self._set_state(index, "转换失败")
            except Exception as exc:
                self.failed += 1
                self._set_state(index, "处理异常")
                self.events.put(("log", f"[异常] {exc}"))
            self.completed += 1
            self.events.put(("progress", self.completed, self.total))

        self.events.put(("finished", self.success, self.skipped, self.failed, self.cancel_requested))

    def _transcode(self, source, output):
        # -map 0:v:0：转换第一个视频流；音频/字幕流可选并直接复制。
        # MKV 容器兼容性较好，避免强制转换音频导致额外损失。
        command = [
            self.ffmpeg, "-hide_banner", "-y", "-i", source,
            "-map", "0:v:0", "-map", "0:a?", "-map", "0:s?",
            *NVENC_ARGS,
            "-c:a", "copy", "-c:s", "copy",
            "-max_muxing_queue_size", "2048",
            "-progress", "pipe:1", "-nostats",
            output
        ]
        self.events.put(("log", "[转码] NVIDIA NVENC / HEVC / P5 / CQ 26"))
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
            creationflags=creationflags
        )
        self.current_process = proc
        last_log = time.time()
        try:
            for line in proc.stdout:
                line = line.strip()
                if line.startswith("out_time="):
                    self.events.put(("file_progress", Path(source).name, line.split("=", 1)[1]))
                elif line and ("Error" in line or "error" in line or "failed" in line.lower()):
                    self.events.put(("log", line))
                if self.cancel_requested and proc.poll() is None:
                    proc.terminate()
            code = proc.wait()
        finally:
            self.current_process = None

        if self.cancel_requested:
            try:
                if os.path.exists(output):
                    os.remove(output)
            except OSError:
                pass
            return False

        if code != 0:
            self.events.put(("log", f"[失败] FFmpeg 退出代码：{code}。请检查 NVIDIA 驱动、显卡及编码器支持。"))
            try:
                if os.path.exists(output):
                    os.remove(output)
            except OSError:
                pass
            return False
        return True

    def _poll_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "log":
                    self._log(event[1])
                elif kind == "state":
                    idx, state = event[1], event[2]
                    item = str(idx)
                    if self.tree.exists(item):
                        vals = self.tree.item(item, "values")
                        self.tree.item(item, values=(vals[0], state))
                elif kind == "progress":
                    done, total = event[1], event[2]
                    self.progress_var.set(done / total * 100 if total else 0)
                    self.progress_text.set(f"文件进度：{done}/{total}")
                elif kind == "file_progress":
                    self.progress_text.set(f"正在转换：{event[1]}    FFmpeg 时间：{event[2]}")
                elif kind == "finished":
                    success, skipped, failed, cancelled = event[1:]
                    self.running = False
                    self.start_btn.configure(state="normal")
                    self.add_files_btn.configure(state="normal")
                    self.add_folder_btn.configure(state="normal")
                    self.remove_btn.configure(state="normal")
                    self.clear_btn.configure(state="normal")
                    self.cancel_btn.configure(state="disabled")
                    summary = f"成功：{success}    跳过：{skipped}    失败：{failed}"
                    self.progress_text.set(("已停止。 " if cancelled else "全部处理完成。 ") + summary)
                    self._log(("任务已停止。 " if cancelled else "任务完成。 ") + summary)
                    messagebox.showinfo("处理结果", ("任务已停止。\n" if cancelled else "处理完成。\n") + summary)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except tk.TclError:
        pass
    H265ConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
