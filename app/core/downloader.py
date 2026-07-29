"""下载编排模块 —— 参数收集、配置覆写、调用 jmcomic 下载"""

import os

import jmcomic

from app.core.config import load_option
from app.core.history import add as history_add
from app.ui.prompts import get_album_id, prompt_image_format, prompt_download_path


def run(album_id: str = None, default_path: str = None) -> None:
    """执行完整的下载流程。传入 album_id/default_path 时跳过对应提问（供历史记录重新下载）"""
    option = load_option()

    # 1. 相册 ID
    if album_id is None:
        album_id = get_album_id()

    # 2. 图片格式 — 从 yml 读取默认值，用户输入非空时才覆盖
    yml_fmt = option.download.image.get('suffix', '.jpg')
    fmt = prompt_image_format(yml_fmt)
    if fmt != yml_fmt:
        option.download.image['suffix'] = fmt

    # 3. 下载路径 — 优先用传入的默认路径，否则从 yml 读取默认值
    yml_path = default_path or getattr(option.dir_rule, 'base_dir', './downloads')
    download_path = prompt_download_path(yml_path)
    if download_path != yml_path:
        option.dir_rule.base_dir = download_path

    try:
        result = jmcomic.download_album(album_id, option)
    except Exception as e:
        print(f'\n下载失败：{e}')
        print('可能是相册 ID 不存在，或 jmcomic 库与目标站点不兼容——请留意新版本发布。')
        print('问题持续存在可到仓库反馈：https://github.com/Sky-pace/EZ-JMComic-Downloader/issues')
        return

    # 记录历史：相册名取不到时退化为空字符串，路径记录为绝对路径
    name = getattr(getattr(result, 'detail', None), 'name', '') or ''
    history_add(album_id, name, os.path.abspath(download_path))
