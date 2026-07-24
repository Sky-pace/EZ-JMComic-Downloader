"""
JM Comic Downloader — 主程序入口

用法:
    python -m app.main
    pyinstaller jmdownload.spec  # 打包为 .exe
"""

from app.core.env import setup_working_directory
from app.core.downloader import run


def main() -> None:
    setup_working_directory()
    run()


if __name__ == '__main__':
    main()