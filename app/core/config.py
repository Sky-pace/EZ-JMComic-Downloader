"""配置解析模块 —— 负责定位和加载 option.yml"""

import os
import shutil
import sys

import jmcomic

from app.core.env import get_executable_dir


def _seed_external_config(src: str, dest: str) -> bool:
    """将内置配置复制到 exe 同目录，方便用户直接修改默认配置。失败时静默返回 False"""
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(src, dest)
        return True
    except OSError:
        return False


def resolve_option_path() -> str:
    """
    解析 option.yml 的路径，优先级:
    1. .exe 同目录下的 config/option.yml（用户可自行修改）
    2. PyInstaller 内置的 config/option.yml（只读 fallback；
       首次运行会复制一份到 exe 同目录，方便用户后续修改）
    3. 源码运行：项目根目录 config/option.yml
    """
    frozen = getattr(sys, 'frozen', False)

    if frozen:
        exe_dir = get_executable_dir()
        external_path = os.path.join(exe_dir, 'config', 'option.yml')
        if os.path.isfile(external_path):
            return external_path
        # 回退到 PyInstaller 内置资源
        fallback_path = os.path.join(sys._MEIPASS, 'config', 'option.yml')
        if os.path.isfile(fallback_path):
            # 配置自举：复制到 exe 同目录后优先使用外部副本
            if _seed_external_config(fallback_path, external_path):
                return external_path
            return fallback_path
        raise FileNotFoundError(
            f'找不到 option.yml，已尝试：\n  {external_path}\n  {fallback_path}'
        )

    # 源码运行：项目根目录
    return os.path.join(get_executable_dir(), 'config', 'option.yml')


def load_option(option_path: str = None):
    """加载 option.yml 并返回配置对象"""
    path = option_path or resolve_option_path()
    return jmcomic.create_option_by_file(path)