"""下载编排模块 —— 参数收集、配置覆写、调用 jmcomic 下载（支持批量）"""

import os

import jmcomic

from app.core.config import load_option, get_post_download_behaviors
from app.core.history import add as history_add
from app.core.pdf import delete_album_images, merge_album_to_pdf as pdf_merge
from app.ui.prompts import (
    get_album_ids,
    prompt_download_path,
    prompt_image_format,
    prompt_selection,
)


def _album_name(detail) -> str:
    """取本子名称，取不到时退化为空字符串"""
    return getattr(detail, 'name', '') or ''


def _album_author(detail) -> str:
    """取本子作者（jmcomic 返回的可能是字符串或列表），取不到时为空字符串"""
    author = getattr(detail, 'author', '') or ''
    if isinstance(author, (list, tuple)):
        return ', '.join(str(a) for a in author)
    return str(author)


def _download_all(ids: list[str], option) -> list[tuple[str, object]]:
    """逐本下载，单本失败不影响其他本子。返回成功列表 [(album_id, detail)]（保持输入顺序）"""
    succeeded, failed = [], []
    for aid in ids:
        try:
            result = jmcomic.download_album(aid, option)
            succeeded.append((aid, result.detail))
        except Exception as e:
            failed.append(aid)
            print(f'\n下载失败：{aid}（{e}）')
    if failed:
        print(f'\n下载完成：成功 {len(succeeded)} 本，失败 {len(failed)} 本，失败 ID：{" ".join(failed)}')
        print('失败可能是相册 ID 不存在，或 jmcomic 库与目标站点不兼容——请留意新版本发布。')
        print('问题持续存在可到仓库反馈：https://github.com/Sky-pace/EZ-JMComic-Downloader/issues')
    return succeeded


def _album_items(albums: list[tuple[str, object]]) -> list[tuple[str, str, str]]:
    """构造编号选择界面所需的 (album_id, 名称, 作者) 列表"""
    return [(aid, _album_name(d), _album_author(d)) for aid, d in albums]


def run(album_id: str = None, default_path: str = None) -> None:
    """
    执行完整的下载流程，支持批量（多个 ID）。

    传入 album_id 时跳过 ID 提问（供历史记录重新下载，单本）；
    图片格式与下载路径整批只问一次、全部本子共用。
    """
    option = load_option()

    # 1. 相册 ID（支持空格分隔批量输入；传入 album_id 时跳过提问）
    ids = [album_id] if album_id is not None else get_album_ids()

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

    # 4. 逐本下载，单本失败不中断整批
    succeeded = _download_all(ids, option)
    if not succeeded:
        return

    # 下载后处理：按设置决定 每次询问(ask)/静默执行(yes)/静默跳过(no)
    merge_behavior, delete_behavior = get_post_download_behaviors()

    # 5. 整合 PDF（失败仅告警，不影响其他本子）
    #    yes=全部整合；ask=编号选择（回车全选）；no=跳过
    pdf_paths = {}  # album_id -> pdf_path（仅记录生成成功的）
    if merge_behavior != 'no':
        picked = list(range(len(succeeded))) if merge_behavior == 'yes' \
            else prompt_selection('整合为 PDF', _album_items(succeeded))
        for i in picked:
            aid, detail = succeeded[i]
            pdf_path = pdf_merge(option, detail)
            if pdf_path:
                pdf_paths[aid] = pdf_path
                print(f'PDF 已生成：{pdf_path}')

    # 6. 删除原图：仅对 PDF 生成成功的本子开放，避免没有 PDF 还删图
    pdf_ok = [(aid, d) for aid, d in succeeded if aid in pdf_paths]
    if pdf_ok and delete_behavior != 'no':
        picked = list(range(len(pdf_ok))) if delete_behavior == 'yes' \
            else prompt_selection('删除原图', _album_items(pdf_ok))
        for i in picked:
            aid, detail = pdf_ok[i]
            if delete_album_images(option, detail):
                print(f'原漫画图片已删除：{aid}')

    # 7. 写入历史（每本一条，含 PDF 路径；源目录是否存在在展示时实时检测）
    abs_path = os.path.abspath(download_path)
    for aid, detail in succeeded:
        history_add(aid, _album_name(detail), abs_path, pdf_paths.get(aid, ''))
