import os
import pydicom
from tkinter import Tk, filedialog
from tqdm import tqdm

def get_sequence_name(dicom_file_path):
    """
    读取第一个 DICOM 文件的 'SequenceName' (0x0018, 0x0024) 标签。
    """
    try:
        # pydicom 默认惰性加载像素数据，以提高速度
        ds = pydicom.dcmread(dicom_file_path, stop_before_pixels=True)
        # 获取序列名称 (Sequence Name) 标签
        # DICOM Tag: (0018, 0024)
        sequence_name = ds.get("SequenceName")
        
        if sequence_name:
            # 清理字符串，移除特殊字符，只保留字母、数字和下划线
            # 并替换空格为下划线，以确保文件名有效
            cleaned_name = "".join(
                c if c.isalnum() or c in (' ', '_', '-') else '_' for c in str(sequence_name)
            ).strip().replace(' ', '_')
            return cleaned_name
        
    except Exception as e:
        # print(f"错误：无法读取 DICOM 文件 {os.path.basename(dicom_file_path)}。错误信息：{e}")
        pass
    
    return None

def find_first_dicom(folder_path):
    """
    在给定文件夹中查找并返回第一个 .dcm 或 .dicom 文件路径。
    """
    for root, _, files in os.walk(folder_path):
        for file in files:
            # DICOM 文件通常没有扩展名或使用 .dcm/.dicom
            if '.' not in file or file.lower().endswith(('.dcm', '.dicom')):
                return os.path.join(root, file)
    return None

def rename_mr_sequence_folders(root_dir):
    """
    遍历总文件夹，重命名 MR 序列文件夹。
    """
    print(f"✅ 开始处理总文件夹：{root_dir}\n")
    
    # 统计重命名的数量
    rename_count = 0
    
    # 遍历总文件夹下的所有**病人文件夹**
    # os.walk 会返回 (当前路径, 子文件夹列表, 文件列表)
    for patient_folder in os.listdir(root_dir):
        patient_path = os.path.join(root_dir, patient_folder)
        
        # 确保是文件夹
        if not os.path.isdir(patient_path):
            continue
            
        print(f"👉 正在处理病人文件夹：{patient_folder}")
        
        # 遍历**病人文件夹**下的所有**MR序列文件夹** (这些是数字命名的)
        # 使用 tqdm 增加进度条，提升用户体验
        mr_sequence_folders = [d for d in os.listdir(patient_path) 
                               if os.path.isdir(os.path.join(patient_path, d)) and d.isdigit()]

        if not mr_sequence_folders:
             print(f"   ⚠️  '{patient_folder}' 中没有找到数字命名的子文件夹。")
             continue

        for seq_folder_name in tqdm(mr_sequence_folders, desc=f"   - 序列文件夹"):
            seq_folder_path = os.path.join(patient_path, seq_folder_name)
            
            # 1. 查找第一个 DICOM 文件
            dicom_file = find_first_dicom(seq_folder_path)
            
            if dicom_file:
                # 2. 读取序列名称
                new_name = get_sequence_name(dicom_file)
                
                if new_name:
                    # 3. 构建新的文件夹路径
                    # 格式：旧名称_新序列名称，防止重名
                    new_folder_name = f"{seq_folder_name}_{new_name}"
                    new_folder_path = os.path.join(patient_path, new_folder_name)
                    
                    # 检查是否需要重命名 (防止重复运行)
                    if seq_folder_name != new_folder_name and not os.path.exists(new_folder_path):
                        try:
                            os.rename(seq_folder_path, new_folder_path)
                            # print(f"      - 重命名：'{seq_folder_name}' -> '{new_folder_name}'")
                            rename_count += 1
                        except OSError as e:
                            print(f"      ❌ 错误：无法重命名文件夹 '{seq_folder_name}'。错误信息：{e}")
                    elif os.path.exists(new_folder_path):
                         # print(f"      - 跳过：目标名称 '{new_folder_name}' 已存在。")
                         pass
                    
                else:
                    # print(f"      - 跳过：未在序列 '{seq_folder_name}' 中找到有效的序列名称。")
                    pass
            else:
                # print(f"      - 跳过：未在文件夹 '{seq_folder_name}' 中找到 DICOM 文件。")
                pass
        
        print("-" * 20) # 分隔线
        
    print(f"\n✨ 完成！总共重命名了 {rename_count} 个 MR 序列文件夹。")

# --- 主程序入口 ---
if __name__ == "__main__":
    # 隐藏 Tkinter 主窗口
    root = Tk()
    root.withdraw()
    
    # 弹出文件夹选择对话框
    print("请选择包含所有**病人文件夹**的**总文件夹**...")
    root_directory = filedialog.askdirectory(
        title="选择 DICOM 总文件夹 (包含所有病人文件夹)"
    )
    
    if root_directory:
        rename_mr_sequence_folders(root_directory)
    else:
        print("操作已取消，未选择任何文件夹。")
