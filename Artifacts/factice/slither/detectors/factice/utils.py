import os
import shutil

"""
文件读写相关函数
"""


def copy_paste_contract_file(source_file_path, destination_folder_path):
    try:
        shutil.copy(source_file_path, destination_folder_path)
        print(f"文件已成功复制到 {destination_folder_path}")
    except Exception as e:
        print(f"复制文件时出错：{e}")


def get_home_folder_path(folder_name) -> str:
    home_directory = os.environ['HOME']
    home_folder_path = os.path.join(home_directory, folder_name)
    os.makedirs(home_folder_path, exist_ok=True)
    return home_folder_path


def save_source_code(file_name, source_code, destination_folder_path):
    # 构建完整的文件路径
    if file_name and source_code:
        file_path = os.path.join(destination_folder_path, file_name)
        # 将源代码写入文件
        with open(file_path, 'w') as file:
            file.write(source_code)
            print(f"合约源代码已保存为 {file_path}")
    else:
        print("file_name或source_code为空")
