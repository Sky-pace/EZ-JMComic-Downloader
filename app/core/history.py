"""历史记录模块 —— 记录使用过的漫画 ID，支持查询及存储位置查看"""

import json
import os
import unicodedata
from datetime import datetime

from app.core.env import get_data_dir

HISTORY_FILENAME = '.jm_history.json'


def _get_history_path() -> str:
    """获取历史记录文件的完整路径（存放于程序数据目录，与 cwd 无关）

    Windows：exe 同目录；Linux：~/.jmcomic。
    """
    return os.path.join(get_data_dir(), HISTORY_FILENAME)


def _load() -> list[dict]:
    """加载历史记录列表（按时间倒序）"""
    path = _get_history_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save(records: list[dict]) -> None:
    """保存历史记录到文件（写入失败时仅告警，不中断主流程）"""
    path = _get_history_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f'警告：历史记录写入失败（{e}）')


def add(album_id: str, name: str = '', path: str = '', pdf_path: str = '') -> None:
    """
    追加一条历史记录（去重，保留最新）。
    name 为漫画名称，path 为图片保存目录（绝对路径），pdf_path 为 PDF 路径（无则空串）。
    """
    records = _load()
    # 移除旧记录中相同 ID 的条目
    records = [r for r in records if r.get('album_id') != album_id]
    records.insert(0, {
        'album_id': album_id,
        'name': name,
        'path': path,
        'pdf_path': pdf_path,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    })
    _save(records)


def delete(album_id: str) -> None:
    """删除指定 ID 的历史记录"""
    records = _load()
    _save([r for r in records if r.get('album_id') != album_id])


def clear() -> None:
    """清空所有历史记录"""
    _save([])


def _disp_width(s: str) -> int:
    """字符串的终端显示宽度（中文等全角字符按 2 计）"""
    return sum(2 if unicodedata.east_asian_width(ch) in 'WF' else 1 for ch in s)


def _pad(s: str, width: int) -> str:
    """按显示宽度右补空格，用于表格对齐"""
    return s + ' ' * max(0, width - _disp_width(s))


def show() -> list[dict]:
    """以表格形式打印历史记录（带序号）及存储文件路径，返回记录列表"""
    path = _get_history_path()
    print(f'\n历史记录文件: {path}')
    records = _load()
    if not records:
        print('(暂无历史记录)')
        return []

    def fmt_path(p: str) -> str:
        """源目录路径：不存在时标注（已删除），实时检测而非存死值"""
        if not p:
            return '-'
        return p if os.path.isdir(p) else p + '（已删除）'

    headers = ('序号', '漫画ID', '漫画名称', '下载时间', '保存路径', 'PDF')
    rows = [
        (
            str(i),
            str(r.get('album_id', '-')),
            r.get('name') or '-',   # 老版本记录无此字段
            r.get('time', '-'),
            fmt_path(r.get('path', '')),
            r.get('pdf_path') or '-',   # 老版本记录无此字段
        )
        for i, r in enumerate(records, 1)
    ]
    # 前 N-1 列按内容计算对齐宽度，最后一列（路径）不补齐
    widths = [
        max(_disp_width(headers[i]), *(_disp_width(row[i]) for row in rows))
        for i in range(len(headers) - 1)
    ]

    def render(cols: tuple) -> str:
        padded = [_pad(c, w) for c, w in zip(cols[:-1], widths)]
        return '  ' + '  '.join(padded + [cols[-1]])

    print(f'共 {len(records)} 条记录:\n')
    print(render(headers))
    print(render(tuple('-' * w for w in widths) + ('-' * 8,)))
    for row in rows:
        print(render(row))
    print()
    return records