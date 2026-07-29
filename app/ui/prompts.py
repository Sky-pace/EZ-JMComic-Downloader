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


def prompt_history_action(count: int) -> tuple:
    """
    历史记录管理输入（count 为当前记录数，序号 1-based）：
      回车      → ('back',)
      c         → ('clear',)
      序号 n    → ('delete', n)
      r+序号 n  → ('download', n)
    """
    while True:
        raw = input('操作 [序号=删除, r+序号=重新下载, c=清空, 回车=返回]: ').strip().lower()
        if raw == '':
            return ('back',)
        if raw == 'c':
            return ('clear',)
        action, num = 'delete', raw
        if raw.startswith('r'):
            action, num = 'download', raw[1:]
        if num.isdigit() and 1 <= int(num) <= count:
            return (action, int(num))
        print('无效的输入，请重新输入。')


def prompt_config_defaults(current_fmt: str, current_path: str) -> tuple:
    """
    询问新的默认配置，回车保持不变。
    返回 (图片格式, 下载路径)，未修改的项为 None；图片格式自动补前导点。
    """
    fmt = input(f'默认图片格式（当前 {current_fmt.lstrip(".")}，回车保持不变）: ').strip()
    path = input(
        f'默认下载路径（当前 {current_path}，建议使用相对路径（基于程序所在目录），回车保持不变）: '
    ).strip()
    if fmt and not fmt.startswith('.'):
        fmt = '.' + fmt
    return (fmt or None, path or None)