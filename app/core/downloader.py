"""下载编排模块 —— 参数收集、配置覆写、调用 jmcomic 下载"""

import os

import jmcomic

from app.core.config import load_option, get_post_download_behaviors
from app.core.history import add as history_add
from app.core.pdf import delete_album_images, merge_album_to_pdf as pdf_merge
from app.ui.prompts import get_album_id, prompt_image_format, prompt_download_path, prompt_confirm


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

    # 下载后处理：按设置决定 每次询问(ask)/静默执行(yes)/静默跳过(no)
    merge_behavior, delete_behavior = get_post_download_behaviors()

    # 可选：将本次下载的图片整合为 PDF（失败仅告警，不影响主流程）
    pdf_path = None
    if merge_behavior == 'yes' or (
            merge_behavior == 'ask' and prompt_confirm('是否将本次下载的图片整合为 PDF？')):
        pdf_path = pdf_merge(option, result.detail)
        if pdf_path:
            print(f'PDF 已生成：{pdf_path}')

    # 可选：删除原漫画图片。仅在 PDF 生成成功后触发，避免没有 PDF 还删图
    if pdf_path and (delete_behavior == 'yes' or (
            delete_behavior == 'ask' and prompt_confirm('是否删除原漫画图片？（PDF 已生成，图片删除后不可恢复）'))):
        if delete_album_images(option, result.detail):
            print('原漫画图片已删除。')
