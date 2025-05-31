import os
import shutil
from ij import IJ, WindowManager
from ij.plugin.frame import RoiManager
from ij.plugin import ZProjector
import os
import Time_Series_Analyzer_V3
import time
import subprocess
import sys
from java.lang import Runtime  # 用于在 Jython 中执行系统命令
from javax.swing import JOptionPane
import csv
import re


# 定义 ijm 内容为字符串
ijm_script = """
// 1.0 Get input folders .
indir = getArgument();("Choose an input folder.");
avidir = indir + "converted_data\\\\"
roidir = indir + "results\\\\roi\\\\"
list = getFileList(avidir);
listroi = getFileList(roidir);
// 2.0 Get filelist of input folder
list = getFileList(avidir);
listroi = getFileList(roidir);
for (i = 0; i < list.length; i++) {
    if (endsWith(list[i], ".avi") || endsWith(list[i], ".czi")) {
        // Check whether run before
        norun = true;
        if (endsWith(list[i], ".avi") || endsWith(list[i], ".czi")) {
            // Initialize control variables
            for (j = 0; j < listroi.length; j++) {
                if (endsWith(list[i], ".avi")) {
                    ext = ".avi";
                } else {
                    ext = ".czi";
                }
                roiVideoName = listroi[j].substring(0, listroi[j].lastIndexOf(ext) + lengthOf(ext));
                if (list[i]==roiVideoName) {
                    norun = false;
                    break;
                }
            }
        }
        if (norun) {
            open(avidir + list[i]);
            setTool("rectangle"); // Select Rectangle
            roiManager("reset"); // clear ROI Manager
            
            keepRunning = true;
            roiIndex = 0; // Number initialized as 0
    
            while (keepRunning) {
                // Prompt the user to select the signal area
                waitForUser("Draw the **Signal Area** ROI first, then click **OK**.\\n \\nDraw the **Background Area** ROI next, then click **OK**.\\n   - Please draw them in pairs: Signal first, then Background.\\n \\n**The first ROI must be drawn during the activation frame** before clicking **OK**.\\n \\nTo stop:\\n   - Draw a rectangle with width or height **less than 10 pixels** starting from the top-left corner (less than (100, 100)) and click **OK**.");
    
                // Obtain the rectangular coordinates of the signal area
                getSelectionBounds(x, y, width, height);
    
                // Check if the user has drawn a too small rectangle
                if ((width < 10 || height < 10) && x <= 100 && y <= 100) {
                    print("The SIGNAL rectangle is too small. Stopping...");
                    keepRunning = false;
                    break; // Exit the while loop
                }
    
                // If the user clicks Cancel, the entire loop will be stopped
                if (width == 0 && height == 0) {
                    print("User canceled the process. Stopping...");
                    keepRunning = false;
                    break; // Exit the while loop
                }
    
                // Save the rectangular information of the signal area to the variable
                signalX = x;
                signalY = y;
                signalWidth = width;
                signalHeight = height;
    
                // Add signal area to ROI Manager
                roiManager("Add");
                
                currentIndex = roiManager("count") - 1; // Get the ROI index just added
                if (currentIndex < 0) {
                    print("Error: Failed to add SIGNAL ROI.");
                    keepRunning = false;
                    break;
                }
                roiManager("select", currentIndex);
                if (currentIndex == 0) {
                    stimuliName = Roi.getName;
                    stimuliFrame = substring(stimuliName, 0, 4);
                    stimuliFrame = parseInt(stimuliFrame);
                }
                roiManager("rename", "Signal_" + roiIndex); // Manually control the numbering, named Signal-X
    
                // **Lock the ROI of the signal area to prevent it from being dragged**
                makeRectangle(signalX, signalY, signalWidth, signalHeight); // Restore signal area
                run("Add Selection..."); // Save signal area as static selection
                run("Duplicate...", "title=Fixed_Signal_ROI"); // Create a fixed copy
    
                // Prompt the user to select the background area
                waitForUser("Drag the rectangle to the BASE (background) area, and confirm.");
                getSelectionBounds(baseX, baseY, baseWidth, baseHeight);
    
                // Check if the user has drawn a background rectangle that is too small
                if ((baseWidth < 10 || baseHeight < 10) && baseX <= 100 && baseY <= 100) {
                    print("The BASE rectangle is too small. Stopping...");
                    keepRunning = false;
                    break;
                }
    
                // If the user does not select the background area (clicks Cancel), stop the entire loop
                if (baseWidth == 0 && baseHeight == 0) {
                    print("User canceled the process. Stopping...");
                    keepRunning = false;
                    break;
                }
    
                // Add background area to ROI Manager and mark it
                roiManager("Add");
                currentIndex = roiManager("count") - 1; // Retrieve the index of the background area
                if (currentIndex < 0) {
                    print("Error: Failed to add BASE ROI.");
                    keepRunning = false;
                    break;
                }
                roiManager("select", currentIndex);
                roiManager("rename", "Base_" + roiIndex); // Manually control the numbering, named Base_X
                
                roiManager("save", roidir + list[i] + "_SF-" + stimuliFrame + ".all_ROIs.zip");
                print("Signal and Base ROIs saved successfully.");
    
                // Number increment to ensure signal and background correspondence
                roiIndex++;
            }
            selectImage(list[i]); // Select current image
            run("Close All"); //Close all images
        }
    }
}
"""

def create_ijm_file(output_dir):
    # 自动生成 .ijm 文件
    ijm_path = os.path.join(output_dir, "temp_script.ijm")
    with open(ijm_path, "w") as f:
        f.write(ijm_script)
    return ijm_path

def reformat_table(input_file, output_file):
    """
    将原始表格转换为指定格式，并保存为新文件。

    参数：
    - input_file: str，原始表格文件路径
    - output_file: str，转换后的文件保存路径

    输出：
    - 无返回值，转换后的文件将保存到指定路径
    """
    # 从文件名中提取信息
    filename = os.path.basename(input_file)
    # video_name, fps, stimuli_frame = (
    #     filename.split("_")[0],
    #     filename.split("_")[1].split("-")[1],
    #     filename.split("_")[-1].split("-")[-1].replace(".csv", ""),
    # )

    video_name = filename.split("_fps-")[0]
    fps_match = re.search(r"_fps-(\d+)", filename)
    stimuli_match = re.search(r"_SF-(\d+)", filename)

    fps = fps_match.group(1) if fps_match else 1
    stimuli_frame = stimuli_match.group(1) if stimuli_match else "NA"

    # 读取原始表格数据
    with open(input_file, 'r') as infile:
        reader = csv.reader(infile)
        headers = next(reader)  # 读取第一行（表头）
        data = list(reader)     # 读取剩余内容

    # 筛选 Signal 和 Base 列
    signal_base_pairs = []
    for col in headers:
        if col.startswith("Signal"):
            signal_base_pairs.append((col, col.replace("Signal", "Base")))

    # 创建新的表格数据
    formatted_data = [["Timepoint"]]  # 新表头起始列
    for i, (signal_col, base_col) in enumerate(signal_base_pairs):
        formatted_data[0].extend(["Sample{}_fluorescence".format(i + 1),
                                  "Sample{}_base".format(i + 1)])

    # 将每一对 Signal 和 Base 的值合并到新表格
    for row_index, row in enumerate(data):
        new_row = [row_index + 1]  # Timepoint 列从 1 开始
        for signal_col, base_col in signal_base_pairs:
            # 获取 Signal 和 Base 列的值
            signal_index = headers.index(signal_col)
            base_index = headers.index(base_col)
            new_row.extend([row[signal_index], row[base_index]])
        formatted_data.append(new_row)

    # 写入新文件（添加表头信息）
    with open(output_file, 'wb') as outfile:
        outfile.write("# Video_name: {}\n".format(video_name))
        outfile.write("# Stimuli_frame: {}\n".format(stimuli_frame))
        outfile.write("# fps: {}\n".format(fps))

        writer = csv.writer(outfile)
        writer.writerows(formatted_data)

def gcamp_time_analyzer(folder_path_project):
    avidir = folder_path_project + "converted_data\\"
    roidir = folder_path_project + "results\\roi\\"
    resultdir = folder_path_project + "results\\gcamp_analysis\\"

    # 遍历文件夹，获取 .avi 和 .zip 文件
    avi_files = [f for f in os.listdir(avidir) if f.endswith('.avi') or f.endswith('.czi')]
    zip_files = [f for f in os.listdir(roidir) if f.endswith('.zip') or f.endswith('.zip')]
    csv_files = [f for f in os.listdir(resultdir) if f.endswith('.csv')]

    # 遍历 .avi 文件
    for avi_file in avi_files:
        # 获取 .avi 文件的基本名（去掉后缀）
        avi_base_name = os.path.splitext(avi_file)[0]

        # 查找匹配的 .zip 文件
        matching_zip = None
        for zip_file in zip_files:
            # 检查 .zip 文件名是否以 .avi 文件的基本名为前缀
            if zip_file.startswith(avi_base_name):
                matching_zip = zip_file
                stimuli_frame = re.search(r'SF-(\d+)\.all_ROIs\.zip', zip_file)
                stimuli_frame = stimuli_frame.group(1)
                break
        # 检查是否已经跑过这个文档了
        for csv_file in csv_files:
            # 检查 .csv 文件名是否以 .avi 文件的基本名为前缀
            if csv_file.startswith(avi_base_name):
                matching_zip = None
                break

        # 如果找到匹配的 .zip 文件
        if matching_zip:
            # 导入 ROI
            IJ.run("ROI Manager...")
            rm = RoiManager.getInstance()
            rm.reset()  # 重置 ROI 管理器
            rm.open(os.path.join(roidir, matching_zip))

            # 打开 .avi 文件
            imp = IJ.openImage(os.path.join(avidir, avi_file))
            imp.show()
            
            # 等待图像窗口加载完成
            time.sleep(2)  # 确保图像已打开（视情况调整时间）

            # 执行分析操作（根据你的需求调整）
            analyzer = Time_Series_Analyzer_V3()
            analyzer.getAverage()
            # 等待 "Time Trace(s)" 窗口弹出
            target_window_title = "Time Trace Average"
            wait_time = 0
            max_wait_time = 180  # 设置最大等待时间（秒）
            # 检查目标窗口是否打开
            while True:
                open_windows = WindowManager.getImageTitles()
                if target_window_title in open_windows:
                    break  # 如果找到目标窗口，退出循环
                    time.sleep(1)  # 等待 1 秒
                    wait_time += 1
                if wait_time > max_wait_time:
                    break

            # 保存结果
            IJ.selectWindow("Time Trace(s)")
            output_csv = os.path.join(resultdir, avi_base_name + "_Time_Table_SF-" + stimuli_frame +".csv")
            IJ.saveAs("Results", output_csv)
            print "Results saved to: {output_csv}"  
            time.sleep(2)  # 确保图像已打开（视情况调整时间）
            # 关闭所有打开的窗口
            imp.close()
            IJ.run("Close All")
            IJ.selectWindow("Time Series V3_0");
            IJ.run("Close");
        else:
            # 如果没有找到匹配的 .zip 文件
            print "Skipping: {}, No ROI files found or Has run before".format(avi_file)

def integrate_gcamp_data(main_folder, output_file):
    # 初始化一个空的字典来存储整合数据（按时间点）
    timepoint_data = {}
    header = ['Timepoint']
    n_col = 0
    # 遍历每个条件文件夹
    for condition_folder in os.listdir(main_folder):
        condition_path = os.path.join(main_folder, condition_folder)
        if os.path.isdir(condition_path):
            # 获取文件夹中的所有文件
            for file_name in os.listdir(condition_path):
                if file_name.endswith(".csv") and file_name.startswith("formatted_"):
                    file_path = os.path.join(condition_path, file_name)
                    # 读取 CSV 文件，跳过前三行注释
                    with open(file_path, 'r') as f:
                        # 读取前几行（假设注释在前3行）
                        header_lines = [f.readline().strip() for _ in range(3)]

                    # 获取Stimuli_frame（假设它在第二行并且格式为 '# Stimuli_frame: 471'）
                    Video_name, stim_frame, fps = None, None, None
                    for line in header_lines:
                        if line.startswith('# Video_name'):
                            # 使用正则表达式提取 Video_name
                            match = re.search(r'#\s*Video_name:\s*([\d\-]+\s*[\d\:]+)', line)
                            if match:
                                Video_name = str(match.group(1))  # 提取并转换为整数
                            else:
                                print("Warning: Video_name in {} could not be parsed.".format(file_name))
                        elif line.startswith('# Stimuli_frame'):
                            # 使用正则表达式提取 Stimuli_frame
                            match = re.search(r'#\s*Stimuli_frame:\s*(\d+)', line)
                            if match:
                                stim_frame = int(match.group(1))  # 提取并转换为整数
                            else:
                                print("Warning: Stimuli frame in {} could not be parsed.".format(file_name))
                        elif line.startswith('# fps'):
                            # 使用正则表达式提取 fps
                            match = re.search(r'#\s*fps:\s*(\d+)', line)
                            if match:
                                fps = int(match.group(1))  # 提取并转换为整数
                            else:
                                print("Warning: fps in {} could not be parsed.".format(file_name))

                    # 读取 CSV 文件的实际数据，跳过前三行注释
                    with open(file_path, 'r') as f:
                        reader = csv.reader(f)
                        rows = list(reader)[3:]  # 跳过前三行注释

                        # 创建一个新的数据列表
                        data = []

                        for row in rows:
                            # 从第二列开始处理（row[1:]），并尝试将每个值转换为浮动数字
                            processed_row = []
                            for i, value in enumerate(row[1:]):  # 从第二列开始
                                try:
                                    # 尝试将每个值转换为浮动类型
                                    float_value = float(value)
                                    processed_row.append(float_value)
                                except ValueError:
                                    # 如果不能转换为浮动类型，则保留原始值或采取其他处理
                                    processed_row.append(value)

                            # 添加到最终数据列表
                            data.append(processed_row)

                    # 获取时间点（Timepoint）
                    timepoints = [(float(t) - float(stim_frame)) / float(fps) for t in range(1, len(data) + 1)]

                    # 从第二列开始处理数据，偶数列为荧光，奇数列为背景
                    fluorescence_base = []
                    for i in range(0, len(data[0]), 2):
                        n_col = n_col + 1
                        # 偶数列是荧光数据，奇数列是背景数据
                        fluorescence_col = [float(row[i]) if isinstance(row[i], (int, float)) else 0.0 for row in data]  # 确保转换为 float 类型
                        background_col = [float(row[i + 1]) if isinstance(row[i + 1], (int, float)) else 0.0 for row in data]  # 确保转换为 float 类型
                        
                        # 计算荧光信号 - 背景信号
                        fluorescence_base = [fluorescence - background for fluorescence, background in zip(fluorescence_col, background_col)]
                        header.append("{}".format(condition_folder) + "_{}_fluorescence-base_".format(file_name) + str(i/2))

                        # 将数据按 Timepoint 存入字典
                        for idx, timepoint in enumerate(timepoints):
                            if timepoint not in timepoint_data:
                                timepoint_data[timepoint] = []
                                for j in range(n_col-1):
                                    timepoint_data[timepoint].append(None)
                            
                            while len(timepoint_data[timepoint]) < n_col-1:
                                timepoint_data[timepoint].append(None)
                            # 添加每个条件的荧光基准数据
                            timepoint_data[timepoint].append(fluorescence_base[idx])

    with open(output_file, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        # 按 Timepoint 排序并写入数据行
        for timepoint in sorted(timepoint_data.keys()):
            row = [timepoint] + timepoint_data[timepoint]
            writer.writerow(row)
    
    print("Data has been successfully integrated and saved to {}".format(output_file))

def setup_project_structure(folder_path2):
    """
    Create the directory structure for Project_Folder and organize necessary files into corresponding folders.
    """
    # Define required file types for each category
    required_files = {
        "raw_data": [".mov", ".mp4"],  # At least one .mov or .mp4 file is required
        "converted_data": [".avi", ".czi"]
    }

    # Define the root project folder
    project_folder = os.path.join(folder_path2, "Project_Folder")

    # Define the directory structure
    folders = {
        "raw_data": os.path.join(project_folder, "raw_data"),                   # Original video files
        "converted_data": os.path.join(project_folder, "converted_data"),       # Converted AVI files
        "results": os.path.join(project_folder, "results"),                     # Output analysis results
        "results_roi": os.path.join(project_folder, "results", "roi"),          # ROI-related files
        "results_gcamp": os.path.join(project_folder, "results", "gcamp_analysis"),  # GCaMP analysis results
        "results_figures": os.path.join(project_folder, "results", "figures")  # Figures generated from data analysis
    }

    # Create the directory structure
    for folder_name, folder_path in folders.items():
        if not os.path.exists(folder_path):  # Check if folder exists
            os.makedirs(folder_path)        # Create folder if it doesn't exist
        print("Folder has been created or confirmed to exist: %s -> %s" % (folder_name, folder_path))

    # # Function to check if required video files exist (including in subfolders)
    # def has_required_files(folder_path, required_files):
    #     """
    #     Check if the folder or its subfolders contain the necessary video files.
    #     """
    #     for root, _, files in os.walk(folder_path):  # Traverse the folder and subfolders
    #         for file in files:
    #             if file.endswith(tuple(required_files["raw_data"])):  # Check for .mov or .mp4
    #                 return True
    #     return False

    # # Check if required video files exist
    # if not has_required_files(folder_path2, required_files):
    #     print("No valid .mov or .mp4 files found in the folder or its subfolders. The program has terminated.")
    #     exit()

    # 新增所有支持的原始格式
    all_supported_raw_extensions = required_files["raw_data"] + required_files["converted_data"]

    # 检查是否存在任何受支持的视频文件（包括 .mov, .mp4, .czi）
    def has_any_supported_files(folder_path, extensions):
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(tuple(extensions)):
                    return True
        return False

    # 替代原始的 has_required_files 检查
    if not has_any_supported_files(folder_path2, all_supported_raw_extensions):
        print("No valid .mov, .mp4, or .czi files found in the folder or its subfolders. The program has terminated.")
        exit()

    # Move files into corresponding folders
    def move_files_to_folders(folder_path, folders, current_script="workflow.py"):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            # Skip directories
            if os.path.isdir(file_path):
                continue

            # Skip the current script file
            if filename == current_script:
                continue

            # Get file extension
            file_ext = os.path.splitext(filename)[-1].lower()
            file_base = os.path.splitext(filename)[0]
            moved = False

            for folder, extensions_or_files in required_files.items():
                if folder in ["raw_data", "converted_data"] and file_ext in extensions_or_files:
                    dest_folder = folders[folder]

                    # 针对 .czi 文件进行重命名处理
                    if file_ext == ".czi" and "_fps-" not in file_base:
                        new_filename = file_base + "_fps-1" + file_ext
                        new_file_path = os.path.join(dest_folder, new_filename)
                        shutil.move(file_path, new_file_path)
                        print("Moved and renamed .czi file: %s -> %s" % (filename, new_file_path))
                    else:
                        shutil.move(file_path, os.path.join(dest_folder, filename))
                        print("Moved file: %s -> %s" % (filename, dest_folder))

                    moved = True
                    break

            if not moved:
                print("Unclassified file: %s, please handle manually." % filename)

    # Start moving files
    move_files_to_folders(folder_path2, folders)

    print("\nThe directory structure has been created and the file classification is complete.")

def normalize_csv(input_file, output_file, time_column="Timepoint", time_range=(-5, 0)):
    """
    对指定 CSV 文件中的数据列进行归一化处理，并输出到新的文件。
    
    参数：
        input_file (str): 输入的 CSV 文件路径。
        output_file (str): 输出的 CSV 文件路径。
        time_column (str): 时间列的名称（默认是 "Timepoint"）。
        time_range (tuple): 时间范围，默认为 (-5, 0)。
    """
    # 读取 CSV 文件
    rows = []
    with open(input_file, "r") as file:
        reader = csv.reader(file)
        rows = list(reader)

    # 提取表头和数据
    header = rows[0]
    data = rows[1:]
    
    for row in data:
        while len(row) < len(header):
            row.append('')  # 添加None或空字符串('')

    # 定义时间列和其他数据列
    if time_column not in header:
        raise ValueError("Time column '{}' not found in the file.".format(time_column))
    
    time_index = header.index(time_column)
    value_indices = [i for i in range(len(header)) if i != time_index]

    # 将数据转换为 float，并处理空值为 None
    data = [[float(cell) if cell != "" and cell != "NA" else None for cell in row] for row in data]

    # 筛选时间范围内的数据
    filtered_data = [row for row in data if row[time_index] is not None and time_range[0] <= row[time_index] <= time_range[1]]

    # 计算每列的 baseline_mean
    baseline_means = []
    for col_index in value_indices:
        valid_values = [row[col_index] for row in filtered_data if row[col_index] is not None]
        if valid_values:
            mean_value = sum(valid_values) / len(valid_values)
        else:
            mean_value = None
        baseline_means.append(mean_value)

    # 按公式 (x - baseline_mean) / baseline_mean 变换数据
    for row in data:
        for i, col_index in enumerate(value_indices):
            if row[col_index] is not None and baseline_means[i] is not None:
                baseline_mean = baseline_means[i]
                row[col_index] = (row[col_index] - baseline_mean) / baseline_mean

    # 写入处理后的数据到新的 CSV 文件
    with open(output_file, "wb") as file:
        writer = csv.writer(file)
        writer.writerow(header)  # 写入表头
        for row in data:
            # 转换 None 值回空字符串
            writer.writerow([cell if cell is not None else "" for cell in row])

    print("The data has been standardized and saved to {}".format(output_file))

# Main workflow
if __name__ == "__main__":
    # ======= 1. Select Input Folder =======
    folder_path2 = IJ.getDirectory("Choose an input folder.")
    folder_path_project = os.path.join(folder_path2, "Project_Folder\\")
    scripts_path = os.path.join(folder_path_project, 'scripts\\')

    print("=== Setting up project structure ===\n")
    setup_project_structure(folder_path2)  # Create directories and organize files
    print("\n=== Project structure setup complete ===\n")

    # ======= 2. ROI Selection Step =======
    print("=== Selecting ROI ===\n")
    output_dir = ".\\temp"  # Temporary directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # Create the directory if it doesn't exist
    ijm_file = create_ijm_file(output_dir)  # Generate the IJM file
    IJ.runMacroFile(ijm_file, folder_path_project)  # Run the IJM script
    print("\n=== ROI Selection Complete ===\n")

    # ======= 3. GCaMP Time Analysis =======
    print("\n=== GCaMP Time Analysis ===\n")
    gcamp_time_analyzer(folder_path_project)  # Perform GCaMP time analysis
    print("\n=== GCaMP Time Analysis Complete ===\n")

    # ======= 4. CSV Formatting =======
    print("\n=== CSV Formatting ===\n")
    # Get the full path of the gcamp_analysis folder
    gcamp_analysis_path = os.path.join(folder_path_project, 'results', 'gcamp_analysis')
    if os.path.exists(gcamp_analysis_path):
        # Iterate through all files in the gcamp_analysis folder
        for file_name in os.listdir(gcamp_analysis_path):
            if file_name.startswith('formatted_'):  # Skip already formatted files
                continue
            if file_name.endswith('.csv'):  # Process only CSV files
                input_file = os.path.join(gcamp_analysis_path, file_name)
                output_file = os.path.join(gcamp_analysis_path, 'formatted_' + file_name)
                reformat_table(input_file, output_file)  # Format the table
                print("File reformatted: {}".format(file_name))
    print("\n=== CSV Formatting Complete ===\n")

    # ======= 5. Manual Classification =======
    print("\n=== Manual Classification Step ===\n")
    Runtime.getRuntime().exec('explorer "{}"'.format(gcamp_analysis_path))  # Open folder for user to classify files
    time.sleep(2)  
    JOptionPane.showMessageDialog(None, "Please complete the file classification in the folder and press OK to continue...")
    print("\n=== Manual Classification Complete ===\n")

    # ======= 6. File Integration =======
    print("\n=== Starting File Integration ===\n")
    output_path = os.path.join(gcamp_analysis_path, 'formatted_consolidated_data.csv')
    integrate_gcamp_data(gcamp_analysis_path, output_path)  # Integrate data
    print("\n=== File Integration Complete ===\n")

    # ======= 7. File Integration =======
    print("\n=== Starting File Integration ===\n")
    input_file = os.path.join(gcamp_analysis_path, "formatted_consolidated_data.csv")
    output_file = os.path.join(folder_path_project, 'results', "figures", "normalized_data.csv")
    # 调用 normalize_csv 函数
    normalize_csv(input_file, output_file)
    print("\n=== File Integration Complete ===\n")

    # ======= 8. Workflow Completed =======
    print("\n=== Workflow Complete ===")
