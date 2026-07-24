"""下载编排模块 —— 参数收集、配置覆写、调用 jmcomic 下载"""

import jmcomic

from app.core.config import load_option
from app.ui.prompts import get_album_id, prompt_image_format, prompt_download_path


def run() -> None:
    """执行完整的下载流程"""
    option = load_option()

    # 1. 相册 ID
    album_id = get_album_id()

    # 2. 图片格式 — 从 yml 读取默认值，用户输入非空时才覆盖
    yml_fmt = option.download.image.get('suffix', '.jpg')
    fmt = prompt_image_format(yml_fmt)
    if fmt != yml_fmt:
        option.download.image['suffix'] = fmt

    # 3. 下载路径 — 从 yml 读取默认值，用户输入非空时才覆盖
    yml_path = getattr(option.dir_rule, 'base_dir', './downloads')
    download_path = prompt_download_path(yml_path)
    if download_path != yml_path:
        option.dir_rule.base_dir = download_path

    jmcomic.download_album(album_id, option)