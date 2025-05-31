import os
import subprocess
from tkinter import filedialog
import tkinter as tk
import tkinter.simpledialog as simpledialog

def ask_fps(filename):
    root = tk.Tk()
    root.withdraw()
    fps = simpledialog.askinteger(
        "缺少 FPS 信息",
        f"文件 '{filename}' 缺少帧率标识。\n请输入此文件的帧率（fps）:",
        minvalue=1, maxvalue=100
    )
    root.destroy()
    return fps

def process_videos(input_folder, output_folder):
    for filename in os.listdir(input_folder):
        filepath = os.path.join(input_folder, filename)
        lower_name = filename.lower()
        
        # 1. 处理 .czi 文件：重命名
        if lower_name.endswith(".czi"):
            if "_fps-" not in filename:
                fps = ask_fps(filename)
                if fps is None:
                    print(f"跳过文件（未输入fps）: {filename}")
                    continue
                base, ext = os.path.splitext(filename)
                new_name = f"{base}_fps-{fps}{ext}"
                new_path = os.path.join(input_folder, new_name)
                os.rename(filepath, new_path)
                print(f"重命名 .czi 文件: {filename} -> {new_name}")
            else:
                print(f".czi 文件已规范命名: {filename}")
        
        # 2. 处理 .mov / .mp4 文件：格式转换
        elif lower_name.endswith((".mov", ".mp4")):
            fps = 2
            base_name = os.path.splitext(filename)[0]
            output_path = os.path.join(output_folder, f"{base_name}_fps-{fps}.avi")

            print(f"正在转换视频: {filename} -> {output_path}")
            try:
                subprocess.run([
                    "ffmpeg", "-i", filepath, "-r", str(fps),
                    "-c:v", "mjpeg", "-qscale:v", "2", "-pix_fmt", "yuvj420p", output_path
                ], check=True)
                print(f"转换成功: {output_path}")
            except subprocess.CalledProcessError as e:
                print(f"转换失败: {filename}，错误信息：{e}")
        
        else:
            print(f"跳过文件: {filename}")

# 主程序入口
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    input_folder = filedialog.askdirectory(title="请选择视频文件夹")
    if not input_folder:
        print("未选择文件夹，程序结束。")
        exit()

    print("\n文件夹路径:", input_folder)
    print("\n=== 开始处理视频文件 ===\n")

    os.makedirs(input_folder, exist_ok=True)
    process_videos(input_folder, input_folder)

    print("\n=== 所有视频处理完成 ===")
