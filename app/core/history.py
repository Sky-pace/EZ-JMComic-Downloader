"""历史记录模块 —— 记录使用过的漫画 ID，支持查询及存储位置查看"""

import json
import os
from datetime import datetime

from app.core.env import get_executable_dir

HISTORY_FILENAME = '.jm_history.json'


def _get_history_path() -> str:
    """获取历史记录文件的完整路径（存放于程序运行目录，与 cwd 无关）"""
    return os.path.join(get_executable_dir(), HISTORY_FILENAME)


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


def add(album_id: str) -> None:
    """追加一条历史记录（去重，保留最新）"""
    records = _load()
    # 移除旧记录中相同 ID 的条目
    records = [r for r in records if r.get('album_id') != album_id]
    records.insert(0, {
        'album_id': album_id,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    })
    _save(records)


def show() -> None:
    """打印历史记录及存储文件路径"""
    path = _get_history_path()
    print(f'\n历史记录文件: {path}')
    records = _load()
    if not records:
        print('(暂无历史记录)')
        return
    print(f'共 {len(records)} 条记录:\n')
    print('  {"album_id": "xxxx", "time": "2026-07-27 09:00:00"}')
    print()
    for r in records:
        print(f'  {r["album_id"]}  —  {r["time"]}')
    print()