"""
JM Comic Downloader — 主程序入口

用法:
    python -m app.main                # 正常下载
    python -m app.main --history      # 查看历史记录
    pyinstaller jmdownload.spec       # 打包为 .exe
"""

import sys

from app.core.env import setup_working_directory
from app.core.downloader import run
from app.core.history import show as history_show
from app.core.updater import check_and_update


def main() -> None:
    setup_working_directory()

    # 仅打包环境生效：发现新版本时会自动更新并重启，不再继续当前流程
    check_and_update()

    if '--history' in sys.argv:
        history_show()
        return

    try:
        run()
    except (EOFError, KeyboardInterrupt):
        # 输入流被关闭（管道/重定向）或用户按下 Ctrl+C
        print('\n已取消。')


if __name__ == '__main__':
    main()
