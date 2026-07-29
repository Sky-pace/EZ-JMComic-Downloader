"""自更新模块 —— 检查 GitHub Releases 新版本，由用户决定更新或回滚

仅对 PyInstaller 打包的 .exe 生效；源码运行所有函数均安全降级。
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


_BAR_WIDTH = 30  # 进度条宽度（字符数）


def _render_bar(downloaded: int, total: int) -> str:
    """渲染单行进度条（仅用 GBK 安全字符，避免 Windows 控制台编码错误）"""
    pct = downloaded * 100 // total
    filled = downloaded * _BAR_WIDTH // total
    bar = '#' * filled + '-' * (_BAR_WIDTH - filled)
    return f'  [{bar}] {pct:3d}%  {downloaded / 2 ** 20:.1f}/{total / 2 ** 20:.1f} MB'


def _download(url: str, dest: str) -> None:
    """流式下载文件到指定路径（单行刷新进度条；服务器未返回大小时按量汇报）"""
    with _http_get(url, DOWNLOAD_TIMEOUT) as resp, open(dest, 'wb') as f:
        total = int(resp.headers.get('Content-Length') or 0)
        downloaded = 0
        while True:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                print('\r' + _render_bar(downloaded, total), end='', flush=True)
            elif downloaded % (4 << 20) < (1 << 16):
                print(f'\r  已下载 {downloaded / 2 ** 20:.1f} MB', end='', flush=True)
    print()  # 进度条结束后换行


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


def _restart() -> None:
    """启动新版本并退出当前进程

    Windows 下新进程使用独立控制台（CREATE_NEW_CONSOLE）：
    父进程退出后系统会销毁为其创建的控制台窗口，若子进程共享该控制台
    且尚未完成挂接，会被一并销毁（双击启动时表现为"更新后没有重启"）。
    """
    kwargs = {}
    if os.name == 'nt':
        kwargs['creationflags'] = subprocess.CREATE_NEW_CONSOLE
    subprocess.Popen([sys.executable], cwd=get_executable_dir(), **kwargs)
    sys.exit(0)


def check_for_update() -> dict | None:
    """检查是否有新版本（仅打包环境）。有则返回 Release 信息，否则返回 None"""
    if not is_frozen():
        return None
    try:
        release = json.loads(_http_get(API_URL, CHECK_TIMEOUT).read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code != 404:  # 404 = 仓库还没有任何 Release，属正常情况
            print(f'检查更新失败（不影响使用）：{e}')
        return None
    except Exception as e:
        print(f'检查更新失败（不影响使用）：{e}')
        return None

    latest = release.get('tag_name', '')
    if not latest or _version_key(latest) <= _version_key(__version__):
        return None
    return release


def apply_update(release: dict) -> None:
    """下载 Release 中的新 exe，校验 sha256 后替换当前 exe（旧版本保留为 .old），随后重启"""
    current = sys.executable
    new_path = current + '.new'
    old_path = current + '.old'

    tag = release.get('tag_name', '')
    print(f'\n正在更新到 {tag}')

    exe_asset, sha_asset = _find_assets(release)

    print('[1/3] 正在从 GitHub 下载新版本...')
    _download(exe_asset['browser_download_url'], new_path)
    print('[1/3] 下载完成 [OK]')

    print('[2/3] 校验文件完整性...')
    with _http_get(sha_asset['browser_download_url'], CHECK_TIMEOUT) as resp:
        expected = resp.read().decode('utf-8').split()[0].strip().lower()
    if _sha256(new_path) != expected:
        os.remove(new_path)
        raise RuntimeError('新版本文件校验失败，已放弃更新')
    print('[2/3] 校验通过 [OK]')

    # Windows 允许重命名正在运行的 exe，但不能直接覆盖
    print('[3/3] 替换旧版本...')
    if os.path.exists(old_path):
        os.remove(old_path)
    os.rename(current, old_path)
    os.rename(new_path, current)
    print('[3/3] 替换完成 [OK]')

    print('更新完成，正在重启...')
    print('（若新程序未能正常启动，请手动双击 exe；或将 .old 备份改回原名即可回滚）')
    _restart()


def has_rollback() -> bool:
    """是否存在可回滚的旧版本备份（.old 文件）"""
    return is_frozen() and os.path.exists(sys.executable + '.old')


def rollback() -> None:
    """回滚：当前 exe 与 .old 备份互换（可再次回滚），随后重启"""
    current = sys.executable
    old_path = current + '.old'
    tmp_path = current + '.swap'

    os.rename(current, tmp_path)
    os.rename(old_path, current)
    os.rename(tmp_path, old_path)

    print('已回滚到上一版本，正在重启...')
    _restart()
