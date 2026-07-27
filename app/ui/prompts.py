"""用户交互模块 —— 负责所有用户输入/输出"""


def get_album_id() -> str:
    """获取漫画相册 ID，确保为纯数字"""
    while True:
        album_id = input('请输入相册 ID: ').strip()
        if not album_id:
            print('相册 ID 不能为空，请重新输入。')
            continue
        if not album_id.isdigit():
            print('相册 ID 必须是数字，请重新输入。')
            continue
        return album_id


def prompt_image_format(default_fmt: str = '.jpg') -> str:
    """获取图片格式，默认使用传入值"""
    hint = f'请输入图片格式（如 jpg、png）[默认 {default_fmt.lstrip(".")}]: '
    fmt = input(hint).strip() or default_fmt
    if not fmt.startswith('.'):
        fmt = '.' + fmt
    return fmt


def prompt_download_path(default_path: str = './downloads') -> str:
    """获取下载路径，默认使用传入值"""
    return input(f'请输入下载路径 [默认 {default_path}]: ').strip() or default_path


def prompt_menu_choice(items: list[tuple[str, str]]) -> str:
    """显示菜单并获取用户选择，items 为 (选项键, 显示文本) 列表，返回所选键"""
    for key, label in items:
        print(f'  {key}. {label}')
    valid = {key for key, _ in items}
    while True:
        choice = input('请选择: ').strip().lower()
        if choice in valid:
            return choice
        print('无效的选择，请重新输入。')


def prompt_confirm(message: str) -> bool:
    """询问用户确认，输入 y 确认，其余视为取消"""
    return input(f'{message} [y/N]: ').strip().lower() == 'y'