"""用户交互模块 —— 负责所有用户输入/输出"""


def get_album_id() -> str:
    """获取漫画相册 ID，确保非空"""
    album_id = input('Enter album ID: ').strip()
    if not album_id:
        print('Album ID cannot be empty, please try again.')
        return get_album_id()
    return album_id


def prompt_image_format(default_fmt: str = '.jpg') -> str:
    """获取图片格式，默认使用传入值"""
    hint = f'Enter image format (e.g., jpg, png) [{default_fmt}]: '
    fmt = input(hint).strip() or default_fmt
    if not fmt.startswith('.'):
        fmt = '.' + fmt
    return fmt


def prompt_download_path(default_path: str = './downloads') -> str:
    """获取下载路径，默认使用传入值"""
    return input(f'Enter download path [{default_path}]: ').strip() or default_path