"""
JM Comic Downloader — 主程序入口

用法:
    python -m app.main                # 主菜单（下载 / 历史 / 更新 / 回滚）
    python -m app.main --history      # 直接查看历史记录
    pyinstaller jmdownload.spec       # 打包为 .exe
"""

import sys

from app.core.env import setup_working_directory
from app.core.history import show as history_show
from app.core.menu import run_menu


def main() -> None:
    setup_working_directory()

    if '--history' in sys.argv:
        history_show()
        return

    try:
        run_menu()
    except (EOFError, KeyboardInterrupt):
        # 输入流被关闭（管道/重定向）或用户按下 Ctrl+C
        print('\n已取消。')


if __name__ == '__main__':
    main()
