"""运行环境检测模块 —— 判断是否以 PyInstaller 打包方式运行，提供基础路径。"""

import os
import sys


def is_frozen() -> bool:
    """是否由 PyInstaller 打包为 .exe 运行"""
    return getattr(sys, 'frozen', False)


def get_executable_dir() -> str:
    """获取可执行文件所在目录（打包后为 .exe 目录，开发时为项目根目录）"""
    if is_frozen():
        return os.path.dirname(sys.executable)
    # app/core/env.py → app/core/ → app/ → 项目根目录
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def setup_working_directory() -> None:
    """PyInstaller 打包后，将 cwd 设为 .exe 所在目录，确保相对路径正确"""
    if is_frozen():
        os.chdir(get_executable_dir())