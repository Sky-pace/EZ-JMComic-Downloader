"""配置解析模块 —— 负责定位和加载 option.yml、读写下载后行为设置"""

import json
import os
import re
import shutil
import sys

import jmcomic

from app.core.env import get_data_dir, get_executable_dir


def _seed_external_config(src: str, dest: str) -> bool:
    """将配置种子复制到数据目录，方便用户直接修改默认配置。失败时静默返回 False"""
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(src, dest)
        return True
    except OSError:
        return False


def resolve_option_path() -> str:
    """
    解析 option.yml 的路径，优先级:
    1. 数据目录下的 config/option.yml（用户可自行修改；
       Windows 为 exe 同目录，Linux 为 ~/.jmcomic）
    2. PyInstaller 内置的 config/option.yml（只读 fallback；
       首次运行会复制一份到数据目录，方便用户后续修改）
    3. 源码运行：优先数据目录（Windows 下即项目根目录），
       缺失时从项目根目录自举一份，保证 Linux 数据统一落 ~/.jmcomic
    """
    frozen = getattr(sys, 'frozen', False)
    data_path = os.path.join(get_data_dir(), 'config', 'option.yml')

    if frozen:
        if os.path.isfile(data_path):
            return data_path
        # 回退到 PyInstaller 内置资源
        fallback_path = os.path.join(sys._MEIPASS, 'config', 'option.yml')
        if os.path.isfile(fallback_path):
            # 配置自举：复制到数据目录后优先使用外部副本
            if _seed_external_config(fallback_path, data_path):
                return data_path
            return fallback_path
        raise FileNotFoundError(
            f'找不到 option.yml，已尝试：\n  {data_path}\n  {fallback_path}'
        )

    # 源码运行：数据目录优先，缺失时从项目根目录自举
    project_path = os.path.join(get_executable_dir(), 'config', 'option.yml')
    if os.path.isfile(data_path):
        return data_path
    if os.path.isfile(project_path):
        if _seed_external_config(project_path, data_path):
            return data_path
        return project_path
    raise FileNotFoundError(
        f'找不到 option.yml，已尝试：\n  {data_path}\n  {project_path}'
    )


def load_option(option_path: str = None):
    """加载 option.yml 并返回配置对象"""
    path = option_path or resolve_option_path()
    return jmcomic.create_option_by_file(path)


def update_option_defaults(suffix: str = None, base_dir: str = None) -> None:
    """
    修改 option.yml 中的默认配置项（为 None 的项不修改）。
    按行替换目标键的值，保留文件中的注释和用户自行添加的其他配置。
    键不存在时抛出 KeyError。
    """
    path = resolve_option_path()
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    for key, value in (('suffix', suffix), ('base_dir', base_dir)):
        if value is None:
            continue
        # 值写到行尾或行内注释前，保留注释与其余内容
        pattern = rf'(?m)^(\s*{key}\s*:\s*)[^#]*?(\s*#.*)?$'
        if not re.search(pattern, text):
            raise KeyError(f'配置文件中找不到 {key} 键：{path}')
        # 用 lambda 避免路径中的反斜杠被当作正则转义
        text = re.sub(
            pattern,
            lambda m, v=value: m.group(1) + v + (m.group(2) or ''),
            text,
        )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


# 下载后行为的合法取值：ask=每次询问，yes=静默执行，no=静默跳过
BEHAVIOR_VALUES = ('ask', 'yes', 'no')


def _default_settings_path() -> str:
    """设置文件路径：.jm_settings.json，位于数据目录（与历史记录同位置）

    Windows：exe 同目录；Linux：~/.jmcomic。
    """
    return os.path.join(get_data_dir(), '.jm_settings.json')


def get_post_download_behaviors(settings_path: str = None) -> tuple:
    """
    读取下载后行为设置，返回 (merge_pdf, delete_images)。
    文件缺失/损坏或取值非法时对应项回退为 'ask'（每次询问）。
    """
    path = settings_path or _default_settings_path()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError):
        data = {}
    merge = data.get('merge_pdf')
    delete = data.get('delete_images')
    return (
        merge if merge in BEHAVIOR_VALUES else 'ask',
        delete if delete in BEHAVIOR_VALUES else 'ask',
    )


def update_post_download_behaviors(merge_pdf: str = None, delete_images: str = None,
                                   settings_path: str = None) -> None:
    """
    写回下载后行为设置（为 None 的项不修改），文件中的其他键保持不变。
    取值必须为 ask/yes/no，否则抛 ValueError。
    """
    for value in (merge_pdf, delete_images):
        if value is not None and value not in BEHAVIOR_VALUES:
            raise ValueError(f'非法行为取值：{value}（应为 ask/yes/no）')
    path = settings_path or _default_settings_path()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError):
        data = {}
    if merge_pdf is not None:
        data['merge_pdf'] = merge_pdf
    if delete_images is not None:
        data['delete_images'] = delete_images
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)