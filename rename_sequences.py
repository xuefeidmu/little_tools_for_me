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
            # 清理字符串：移除特殊字符，只保留字母、数字、下划线和连字符
            # 并替换空格为下划线，以确保文件名有效
            cleaned_name = "".join(
                c if c.isalnum() or c in ('_', '-') else '_' for c in str(sequence_name)
            ).strip().replace(' ', '_').replace('__', '_')  # 替换双下划线
            # 确保名称不为空
            return cleaned_name if cleaned_name else None

    except Exception as e:
        # 无法读取 DICOM 文件或缺少标签时返回 None
        # print(f"错误：无法读取 DICOM 文件 {os.path.basename(dicom_file_path)}。错误信息：{e}")
        pass

    return None


def find_first_dicom(folder_path):
    """
    在给定文件夹中查找并返回第一个 .dcm 或类似 DICOM 文件路径。
    """
    # 只需要检查当前文件夹，不深入子文件夹
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            # DICOM 文件通常没有扩展名或使用 .dcm/.dicom
            if '.' not in file or file.lower().endswith(('.dcm', '.dicom',)):
                return file_path
    return None


def rename_mr_sequence_folders(root_dir):
    """
    遍历总文件夹，重命名 MR 序列文件夹。
    """
    print(f"✅ 开始处理总文件夹：{root_dir}\n")

    rename_count = 0

    # 遍历总文件夹下的所有**病人文件夹**
    patient_folders = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]

    if not patient_folders:
        print("❌ 错误：在总文件夹中没有找到任何病人子文件夹。")
        return

    for patient_folder in patient_folders:
        patient_path = os.path.join(root_dir, patient_folder)

        print(f"\n👉 正在处理病人文件夹：{patient_folder}")

        # 遍历**病人文件夹**下的所有**MR序列文件夹** (现在是通用的，不再限制数字)
        mr_sequence_folders = [d for d in os.listdir(patient_path)
                               if os.path.isdir(os.path.join(patient_path, d))]

        if not mr_sequence_folders:
            print(f"   ⚠️  '{patient_folder}' 中没有找到任何子文件夹。跳过。")
            continue

        # 使用 tqdm 增加进度条
        for seq_folder_name in tqdm(mr_sequence_folders, desc=f"   - 序列文件夹"):
            seq_folder_path = os.path.join(patient_path, seq_folder_name)

            # 1. 查找第一个 DICOM 文件
            dicom_file = find_first_dicom(seq_folder_path)

            if dicom_file:
                # 2. 读取序列名称
                new_name = get_sequence_name(dicom_file)

                if new_name:
                    # 3. 构建新的文件夹路径
                    # 新格式：旧名称_新序列名称，防止重名
                    new_folder_name = f"{seq_folder_name}_{new_name}"
                    new_folder_path = os.path.join(patient_path, new_folder_name)

                    # 检查是否需要重命名 (防止重复运行或目标已存在)
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

                # else:
                #     print(f"      - 跳过：未在序列 '{seq_folder_name}' 中找到有效的序列名称。")
            # else:
            #     print(f"      - 跳过：未在文件夹 '{seq_folder_name}' 中找到 DICOM 文件。")

        print("-" * 30)  # 分隔线

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
