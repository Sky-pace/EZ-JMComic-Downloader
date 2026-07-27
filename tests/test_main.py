"""
冒烟测试：验证 jmdownload 程序能正常启动并完成 --history 流程。

使用 --history 而非完整下载流程，避免触发真实网络下载。

用法:
    python -m pytest tests/test_main.py
    python tests/test_main.py
"""

import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE_PATH = os.path.join(PROJECT_ROOT, 'dist', 'jmdownload.exe')
TIMEOUT = 30


def _build_cmd() -> list[str]:
    """优先测试打包后的 .exe，不存在则以模块方式运行源码"""
    if os.path.exists(EXE_PATH):
        return [EXE_PATH, '--history']
    return [sys.executable, '-m', 'app.main', '--history']


def test_main_runs():
    """程序应能以退出码 0 完成 --history 流程"""
    cmd = _build_cmd()
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )

    print("===== STDOUT =====")
    print(result.stdout)
    print("===== STDERR =====")
    print(result.stderr)

    assert result.returncode == 0, (
        f'程序以非零状态退出（{result.returncode}），请检查日志'
    )


def main() -> int:
    """脚本方式运行冒烟测试，返回进程退出码"""
    try:
        test_main_runs()
    except (AssertionError, subprocess.TimeoutExpired) as e:
        print(f'[FAIL] {e}')
        return 1
    print('[OK] 程序正常运行')
    return 0


if __name__ == '__main__':
    sys.exit(main())
