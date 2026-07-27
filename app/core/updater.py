"""自更新模块 —— 启动时检查 GitHub Releases 新版本，自动下载并替换自身

仅对 PyInstaller 打包的 .exe 生效；源码运行直接跳过。
任何更新失败都不影响程序正常使用。
"""

import hashlib
import json
import os
import subprocess
import sys
import urllib.request

from app import __version__
from app.core.env import get_executable_dir, is_frozen

GITHUB_REPO = 'Sky-pace/EZ-JMComic-Downloader'
API_URL = f'https://api.github.com/repos/{GITHUB_REPO}/releases/latest'
CHECK_TIMEOUT = 3      # 检查更新超时（秒）
DOWNLOAD_TIMEOUT = 30  # 下载 socket 超时（秒）

_USER_AGENT = 'EZ-JMComic-Downloader'


def _version_key(tag: str) -> tuple:
    """将 'v1.2.3' 形式的版本号解析为可比较的元组"""
    parts = []
    for piece in tag.lstrip('vV').split('.'):
        try:
            parts.append(int(piece))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _http_get(url: str, timeout: int):
    """发起带 User-Agent 的 GET 请求（GitHub API 强制要求 UA 头）"""
    req = urllib.request.Request(url, headers={'User-Agent': _USER_AGENT})
    return urllib.request.urlopen(req, timeout=timeout)


def _download(url: str, dest: str) -> None:
    """流式下载文件到指定路径"""
    with _http_get(url, DOWNLOAD_TIMEOUT) as resp, open(dest, 'wb') as f:
        while True:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)


def _sha256(path: str) -> str:
    """计算文件的 sha256 摘要"""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()


def _find_assets(release: dict) -> tuple[dict, dict]:
    """从 Release 资源中找到 .exe 及其 .sha256 校验文件"""
    exe_asset = sha_asset = None
    for asset in release.get('assets', []):
        name = asset.get('name', '')
        if name.endswith('.exe'):
            exe_asset = asset
        elif name.endswith('.exe.sha256'):
            sha_asset = asset
    if not exe_asset or not sha_asset:
        raise RuntimeError('Release 中缺少 .exe 或 .sha256 文件')
    return exe_asset, sha_asset


def _apply_update(exe_asset: dict, sha_asset: dict) -> None:
    """下载新 exe，校验 sha256 后替换当前运行的 exe（旧版本保留为 .old 备份）"""
    current = sys.executable
    new_path = current + '.new'
    old_path = current + '.old'

    _download(exe_asset['browser_download_url'], new_path)

    with _http_get(sha_asset['browser_download_url'], CHECK_TIMEOUT) as resp:
        expected = resp.read().decode('utf-8').split()[0].strip().lower()
    if _sha256(new_path) != expected:
        os.remove(new_path)
        raise RuntimeError('新版本文件校验失败，已放弃更新')

    # Windows 允许重命名正在运行的 exe，但不能直接覆盖
    if os.path.exists(old_path):
        os.remove(old_path)
    os.rename(current, old_path)
    os.rename(new_path, current)


def _restart() -> None:
    """启动新版本并退出当前进程"""
    subprocess.Popen([sys.executable], cwd=get_executable_dir())
    sys.exit(0)


def check_and_update() -> None:
    """检查并应用更新（仅打包环境生效；失败时打印提示后继续使用旧版本）"""
    if not is_frozen():
        return
    try:
        release = json.loads(_http_get(API_URL, CHECK_TIMEOUT).read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code != 404:  # 404 = 仓库还没有任何 Release，属正常情况
            print(f'检查更新失败（不影响使用）：{e}')
        return
    try:
        latest = release.get('tag_name', '')
        if not latest or _version_key(latest) <= _version_key(__version__):
            return

        print(f'发现新版本 {latest}（当前 v{__version__}），正在自动更新...')
        exe_asset, sha_asset = _find_assets(release)
        _apply_update(exe_asset, sha_asset)
        print('更新完成，正在重启...')
        _restart()
    except Exception as e:
        print(f'自动更新失败（不影响使用）：{e}')
