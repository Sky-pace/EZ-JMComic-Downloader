"""用户交互模块 —— 负责所有用户输入/输出"""


def get_album_ids() -> list[str]:
    """获取漫画相册 ID（支持空格分隔批量输入），确保均为纯数字；去重并保持输入顺序"""
    while True:
        raw = input('请输入相册 ID（批量下载可用空格分隔多个 ID）: ').strip()
        if not raw:
            print('相册 ID 不能为空，请重新输入。')
            continue
        ids = raw.split()
        bad = [i for i in ids if not i.isdigit()]
        if bad:
            print(f'相册 ID 必须是数字，请检查：{" ".join(bad)}')
            continue
        return list(dict.fromkeys(ids))


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


def parse_selection(text: str, album_ids: list[str]) -> list[int]:
    """
    解析编号选择表达式，返回选中的 0-based 序号列表（升序去重）。

    支持：`1 2 3`（序号）、`1-4`（区间）、`^4`（排除）、直接写 album ID（优先于序号匹配）；
    空串为全选。全部为排除项时基于全选扣除，与正选混用时从正选结果中剔除。
    非法输入抛 ValueError。
    """
    count = len(album_ids)
    if count == 0:
        return []
    text = text.strip()
    if not text:
        return list(range(count))

    def to_index(token: str) -> int:
        if token in album_ids:  # 优先按 album ID 精确匹配，匹配不上再当序号
            return album_ids.index(token)
        if token.isdigit() and 1 <= int(token) <= count:
            return int(token) - 1
        raise ValueError(f'无效的序号或 ID：{token}')

    include, exclude = set(), set()
    for token in text.split():
        neg = token.startswith('^')
        body = token[1:] if neg else token
        target = exclude if neg else include
        if '-' in body:
            lo, _, hi = body.partition('-')
            if not (lo.isdigit() and hi.isdigit()) or not 1 <= int(lo) <= int(hi) <= count:
                raise ValueError(f'无效的区间：{body}')
            target.update(range(int(lo) - 1, int(hi)))
        else:
            target.add(to_index(body))
    base = include if include else set(range(count))
    return sorted(base - exclude)


def prompt_selection(action: str, items: list[tuple[str, str, str]]) -> list[int]:
    """
    编号选择界面：items 为 (album_id, 名称, 作者) 列表，按 1-based 编号展示。
    选择语法见 parse_selection；回车默认全选，输入 n 全不选；非法输入提示后重问。
    返回选中的 0-based 序号列表。
    """
    for i, (aid, name, author) in enumerate(items, 1):
        print(f'  {i} {name}  {author}  {aid}')
    ids = [aid for aid, _, _ in items]
    while True:
        raw = input(f'==> 要{action}的漫画: （示例: "1 2 3"、"1-3"、"^4" 或漫画ID；回车全选，n 全不选）').strip()
        if raw.lower() == 'n':
            return []
        try:
            return parse_selection(raw, ids)
        except ValueError as e:
            print(f'{e}，请重新输入。')


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


def _prompt_behavior(label: str, current: str):
    """询问某项下载后行为：ask=每次询问 / yes=自动执行 / no=不执行，回车保持不变"""
    hint = f'{label}（ask=每次询问 / yes=自动执行 / no=不执行，当前 {current}，回车保持不变）: '
    while True:
        value = input(hint).strip().lower()
        if value == '':
            return None
        if value in ('ask', 'yes', 'no'):
            return value
        print('无效的输入，请输入 ask、yes 或 no。')


def prompt_config_defaults(current_fmt: str, current_path: str,
                           current_merge: str, current_delete: str) -> tuple:
    """
    询问新的默认配置，回车保持不变。
    返回 (图片格式, 下载路径, 整合PDF行为, 删除原图行为)，未修改的项为 None；
    图片格式自动补前导点；行为取值为 ask/yes/no。
    """
    fmt = input(f'默认图片格式（当前 {current_fmt.lstrip(".")}，回车保持不变）: ').strip()
    path = input(
        f'默认下载路径（当前 {current_path}，建议使用相对路径（基于程序所在目录），回车保持不变）: '
    ).strip()
    merge = _prompt_behavior('下载后整合 PDF', current_merge)
    delete = _prompt_behavior('整合后删除原图', current_delete)
    if fmt and not fmt.startswith('.'):
        fmt = '.' + fmt
    return (fmt or None, path or None, merge, delete)