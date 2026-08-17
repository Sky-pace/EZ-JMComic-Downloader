"""运行环境检测模块 —— 判断是否以 PyInstaller 打包方式运行，提供基础路径。"""

import os
import sys


def is_frozen() -> bool:
    """是否由 PyInstaller 打包为二进制运行"""
    return getattr(sys, 'frozen', False)


def get_executable_dir() -> str:
    """获取可执行文件所在目录（打包后为二进制目录，开发时为项目根目录）"""
    if is_frozen():
        return os.path.dirname(sys.executable)
    # app/core/env.py → app/core/ → app/ → 项目根目录
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def get_data_dir() -> str:
    """获取用户数据目录，并确保其存在。

    Windows：保持现状，跟随可执行文件目录（历史/配置与 exe 同目录）。
    Linux：统一放 ~/.jmcomic，与二进制（~/.jmcomic/bin）分离；
    目录恒为当前用户可写，历史/配置/默认下载均落于此，自更新全程免 sudo。
    首次调用自动创建目录，保证后续直接写文件不会失败。
    """
    path = get_executable_dir() if os.name == 'nt' \
        else os.path.join(os.path.expanduser('~'), '.jmcomic')
    os.makedirs(path, exist_ok=True)
    return path


def setup_working_directory() -> None:
    """PyInstaller 打包后，将 cwd 设为数据目录，确保相对路径正确。

    Windows：仍在 exe 所在目录（与旧版本行为一致）。
    Linux：切到 ~/.jmcomic，使相对路径 ./downloads 落到 ~/.jmcomic/downloads。
    """
    if is_frozen():
        os.chdir(get_data_dir())