import os
import sys
import subprocess
from pathlib import Path


# ------------------------------------------------------------------------
# 一次性目录权限配置（需要管理员/root，仅需运行一次）
# ------------------------------------------------------------------------

def setup_directory_shared_permissions(dir_path):
    """
    一次性配置目录权限，使所有用户在该目录下新建的文件自动获得共享读写权限。
    需要以管理员 (Windows) 或 root (Linux) 身份运行，仅需执行一次。

    Windows: 设置 Everyone 完全控制 + 权限继承
    Linux:   设置默认 ACL (优先) 或 777
    """
    if not os.path.exists(dir_path):
        print(f"[权限配置] 路径不存在: {dir_path}")
        return False
    if not os.path.isdir(dir_path):
        print(f"[权限配置] 不是目录: {dir_path}")
        return False

    if sys.platform.startswith('win32'):
        return _setup_windows_directory(dir_path)
    elif sys.platform.startswith('linux'):
        return _setup_linux_directory(dir_path)
    else:
        print(f"[权限配置] 不支持的系统: {sys.platform}")
        return False


def _setup_windows_directory(dir_path):
    quoted = f'"{dir_path}"'
    cmd = f'icacls {quoted} /grant Everyone:(F) /t /inheritance:e /c'

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[权限配置] 成功: {dir_path} 已配置为共享目录")
            return True
        else:
            print(f"[权限配置] 失败，请以管理员身份运行以下命令:")
            print(f"    icacls {quoted} /grant Everyone:(F) /t /inheritance:e")
            return False
    except Exception as e:
        print(f"[权限配置] 错误: {e}")
        return False


def _setup_linux_directory(dir_path):
    # 优先使用 setfacl 设置默认权限（新文件自动继承）
    try:
        subprocess.run(
            f"setfacl -R -m d:o::rwx,o::rwx {dir_path}",
            shell=True, check=True, capture_output=True, text=True
        )
        print(f"[权限配置] 成功 (ACL): {dir_path} 已配置为共享目录")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # fallback: chmod 777
    try:
        subprocess.run(
            f"chmod -R 777 {dir_path}",
            shell=True, check=True, capture_output=True, text=True
        )
        print(f"[权限配置] 成功 (chmod): {dir_path} 已配置为共享目录")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[权限配置] 失败，请以 root 身份运行以下命令:")
        print(f"    sudo chmod -R 777 {dir_path}")
        return False


# ------------------------------------------------------------------------
# 单文件权限设置（轻量级，不阻塞导出流程）
# ------------------------------------------------------------------------

def set_file_permissions(file_path):
    """
    尝试为单个文件设置共享读写权限。
    仅在用户拥有该文件所有权时有效，失败不阻塞调用方。

    Windows: 用 icacls 授予 Everyone 完全控制（文件所有者可执行，无需管理员）
    Linux:   用 os.chmod 设为 666
    """
    if not os.path.exists(file_path):
        return False

    try:
        if sys.platform.startswith('linux'):
            os.chmod(file_path, 0o666)
            return True

        elif sys.platform.startswith('win32'):
            quoted = f'"{file_path}"'
            cmd = f'icacls {quoted} /grant Everyone:(F)'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return True
            else:
                print(f"[权限提示] 无法为文件设置共享权限，建议管理员运行一次目录权限配置")
                return False

        return False
    except Exception:
        return False


# ------------------------------------------------------------------------
# 向后兼容的封装
# ------------------------------------------------------------------------

def set_json_permissions(json_path):
    """向后兼容，同 set_file_permissions"""
    return set_file_permissions(json_path)


def seteveryone_fullct(path):
    """向后兼容，同 set_file_permissions"""
    return set_file_permissions(path)


def set_recursive_777(folder_path):
    """
    向后兼容，现在改为调用 setup_directory_shared_permissions。
    仅在 Linux 下有效（Windows 请用 setup_directory_shared_permissions）。
    """
    if not sys.platform.startswith('linux'):
        print("[权限配置] set_recursive_777 仅支持 Linux，Windows 请用 setup_directory_shared_permissions")
        return False
    return _setup_linux_directory(folder_path)


def find_all_json_files(root_dir):
    """遍历 root_dir 及其子目录，返回所有 .json 文件的路径列表"""
    root_path = Path(root_dir)
    return [str(file) for file in root_path.rglob("*.json")]
