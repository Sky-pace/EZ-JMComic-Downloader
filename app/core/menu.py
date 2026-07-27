"""主菜单编排模块 —— 启动后询问用户要执行的任务（下载 / 历史 / 更新 / 回滚）"""

from app import __version__
from app.core.downloader import run as download_run
from app.core.history import show as history_show
from app.core.updater import apply_update, check_for_update, has_rollback, rollback
from app.ui.prompts import prompt_confirm, prompt_menu_choice


def _confirm_and_update(release: dict) -> None:
    """用户确认后执行更新"""
    tag = release.get('tag_name', '')
    if not prompt_confirm(f'确认下载并更新到 {tag}？更新后程序将自动重启'):
        print('已取消更新。')
        return
    try:
        apply_update(release)
    except Exception as e:
        print(f'更新失败（当前版本不受影响）：{e}')


def _confirm_and_rollback() -> None:
    """用户确认后执行回滚"""
    if not prompt_confirm('确认回滚到上一版本？回滚后程序将自动重启'):
        print('已取消回滚。')
        return
    try:
        rollback()
    except Exception as e:
        print(f'回滚失败：{e}')


def run_menu() -> None:
    """显示主菜单并执行用户选择的任务；任务完成后返回菜单，输入 0 才退出"""
    # 仅打包环境会返回非 None；每次启动只检查一次，检查失败静默降级为"无更新可选"
    release = check_for_update()

    while True:
        items = [
            ('1', '下载漫画'),
            ('2', '查看历史记录'),
        ]
        if release:
            items.append(('3', f"更新到 {release.get('tag_name', '')}（当前 v{__version__}）"))
        if has_rollback():
            items.append(('4', '回滚到上一版本'))
        items.append(('0', '退出'))

        print(f'\n===== JM 漫画下载器 v{__version__} =====')
        choice = prompt_menu_choice(items)

        if choice == '0':
            return
        if choice == '1':
            download_run()
        elif choice == '2':
            history_show()
        elif choice == '3' and release:
            _confirm_and_update(release)
        elif choice == '4' and has_rollback():
            _confirm_and_rollback()
