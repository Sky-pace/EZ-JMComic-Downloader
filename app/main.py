"""
JM Comic Downloader — 主程序入口

用法:
    python -m app.main
    pyinstaller jmdownload.spec  # 打包为 .exe
"""

import os
import sys

import jmcomic


def get_album_id() -> str:
    """获取漫画相册 ID，确保非空"""
    album_id = input('Enter album ID: ').strip()
    if not album_id:
        print('Album ID cannot be empty, please try again.')
        return get_album_id()
    return album_id


def resolve_option_path() -> str:
    """
    解析 option.yml 的路径，优先级:
    1. .exe 同目录下的 config/option.yml（用户可自行修改）
    2. PyInstaller 内置的 config/option.yml（只读 fallback）
    3. 源码运行：项目根目录 config/option.yml
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后运行
        exe_dir = os.path.dirname(sys.executable)
        external_path = os.path.join(exe_dir, 'config', 'option.yml')
        if os.path.isfile(external_path):
            return external_path
        # 外部没有则回退到内置的
        return os.path.join(sys._MEIPASS, 'config', 'option.yml')
    else:
        # 正常 Python 下运行：app/main.py → 项目根目录
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, 'config', 'option.yml')


def setup_working_directory() -> None:
    """PyInstaller 打包后，将 cwd 设为 .exe 所在目录"""
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))


def prompt_image_format() -> str:
    fmt = input('Enter image format (e.g., jpg, png): ').strip() or 'jpg'
    if not fmt.startswith('.'):
        fmt = '.' + fmt
    return fmt


def prompt_download_path() -> str:
    return input('Enter download path: ').strip() or './downloads'


def main() -> None:
    setup_working_directory()

    option_path = resolve_option_path()
    option = jmcomic.create_option_by_file(option_path)

    # 1. 相册 ID
    album_id = get_album_id()

    # 2. 图片格式
    fmt = prompt_image_format()
    option.download.image.suffix = fmt

    # 3. 下载路径
    download_path = prompt_download_path()
    option.dir_rule.base_dir = download_path

    jmcomic.download_album(album_id, option)


if __name__ == '__main__':
    main()