

import os
import sys
import subprocess

from pathlib import Path

import Pathsetup


def set_recursive_777(folder_path):
    """
    为Linux系统中的指定文件夹及其所有内容（包括子文件夹和文件）
    统一设置777权限（所有用户可读写执行）
    """
    # 检查系统是否为Linux
    if not sys.platform.startswith('linux'):
        print("错误：此功能仅适用于Linux系统")
        return False
    
    # 检查路径是否存在且为文件夹
    if not os.path.exists(folder_path):
        print(f"错误：路径 '{folder_path}' 不存在")
        return False
    if not os.path.isdir(folder_path):
        print(f"错误：'{folder_path}' 不是一个文件夹")
        return False
    
    try:
        # 使用chmod -R递归设置所有内容为777权限
        subprocess.run(
            f"chmod -R 777 {folder_path}",
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        
        print(f"成功为 '{folder_path}' 及其所有内容设置777权限")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"权限设置失败：{e.stderr}")
        return False
    except Exception as e:
        print(f"发生错误：{str(e)}")
        return False

# ------------------------------------------------------------------------


def seteveryone_fullct(path):
    # windows
    # 处理路径中的空格，确保命令正确识别
    quoted_path = f'"{path}"'
    # 构建icacls命令，授予Everyone完全控制权限，/t表示递归处理子目录
    cmd = f'icacls {quoted_path} /grant Everyone:(F) /t'
    
    try:
        # 执行命令
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True  # 当命令返回非0状态码时抛出异常
        )
        print(f'成功设置权限: {path}')
        return True
    except subprocess.CalledProcessError as e:
        print(f'设置权限失败: {path}')
        print(f'错误信息: {e.stderr}')
        return False
    except Exception as e:
        print(f'发生意外错误: {str(e)}')
        return False
# ------------------------------------------------------------------------

def set_json_permissions(json_path):
    """专门为JSON文件设置跨平台权限，确保用户可编辑"""
    if sys.platform.startswith('linux'):
        # Linux：开放读写权限
        os.chmod(json_path, 0o666)
    elif sys.platform.startswith('win32'):
        seteveryone_fullct(json_path)

            
            
            
# 遍历所有json文件，尝试修改json文件的权限
def find_all_json_files(root_dir):
    """
    遍历 root_dir 及其子目录，返回所有 .json 文件的路径列表（pathlib 版本）
    """
    root_path = Path(root_dir)
    # 递归查找所有 .json 文件（case-insensitive）
    json_files = list(root_path.rglob("*.json"))  # rglob 递归匹配
    # 转换为字符串路径（可选，根据需要保留 Path 对象）
    return [str(file) for file in json_files]


def quanxianseting():
    # 导出文件时候设置单个文件的权限
    target_dir = Pathsetup.ToolboxSettings_path()
    json_files = find_all_json_files(target_dir)
    for i in json_files:
        try:
            set_json_permissions(i)
        except:
            print(f"修改权限失败{i}")


def quanxianallchanged():
    # 尝试修改全部的文件权限
    root_path = Pathsetup.ToolboxSettings_path()
    
    # 使用os.walk遍历目录
    for dirpath, dirnames, filenames in os.walk(root_path):
        if "#" not in dirpath:
            if sys.platform.startswith('linux'):
                try:
                    set_recursive_777(dirpath)
                except:
                    pass
            else:
                try:
                    set_json_permissions(dirpath)
                except:
                    pass
