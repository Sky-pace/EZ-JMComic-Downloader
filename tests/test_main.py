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

# 直接运行本脚本时 sys.path 不含项目根目录，需手动加入才能 import app
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


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


def test_pdf_merge():
    """PDF 整合：图片按自然序合并，生成的 PDF 页数正确"""
    import re
    import tempfile

    from PIL import Image

    from app.core.pdf import _natural_key, merge_images_to_pdf

    # 自然排序：1 < 2 < 10（而非字典序 1 < 10 < 2）
    names = ['10.jpg', '2.jpg', '1.jpg']
    assert sorted(names, key=_natural_key) == ['1.jpg', '2.jpg', '10.jpg']

    # 合并 3 张图片，校验 PDF 文件头与页数（临时目录由系统自动清理，非项目文件）
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for i, color in enumerate(('red', 'green', 'blue')):
            p = os.path.join(tmp, f'{i + 1}.jpg')
            Image.new('RGB', (100, 200), color).save(p)
            paths.append(p)
        pdf_path = os.path.join(tmp, 'out.pdf')
        merge_images_to_pdf(paths, pdf_path)

        with open(pdf_path, 'rb') as f:
            data = f.read()
        assert data.startswith(b'%PDF-'), '生成的文件不是有效 PDF'
        pages = len(re.findall(rb'/Type\s*/Page[^s]', data))
        assert pages == 3, f'PDF 页数应为 3，实际 {pages}'


def test_settings_behaviors():
    """下载后行为设置：缺省 ask/ask，可写回单项，非法取值回退 ask"""
    import tempfile

    from app.core.config import get_post_download_behaviors, update_post_download_behaviors

    with tempfile.TemporaryDirectory() as tmp:
        settings = os.path.join(tmp, '.jm_settings.json')

        # 文件不存在 → 默认 ask/ask
        assert get_post_download_behaviors(settings) == ('ask', 'ask')

        # 只写 merge_pdf，delete_images 保持默认
        update_post_download_behaviors(merge_pdf='yes', settings_path=settings)
        assert get_post_download_behaviors(settings) == ('yes', 'ask')

        # 再写 delete_images，merge_pdf 保持已设值
        update_post_download_behaviors(delete_images='no', settings_path=settings)
        assert get_post_download_behaviors(settings) == ('yes', 'no')

        # 文件内容损坏 → 回退 ask/ask
        with open(settings, 'w', encoding='utf-8') as f:
            f.write('not json')
        assert get_post_download_behaviors(settings) == ('ask', 'ask')

        # 非法取值抛 ValueError
        try:
            update_post_download_behaviors(merge_pdf='bad', settings_path=settings)
        except ValueError:
            pass
        else:
            raise AssertionError('非法行为取值未抛 ValueError')


def test_delete_album_images():
    """删除原图：本子目录被整体删除，旁边的 PDF 不受影响"""
    import tempfile
    from types import SimpleNamespace

    from app.core.pdf import delete_album_images

    with tempfile.TemporaryDirectory() as tmp:
        album_dir = os.path.join(tmp, '本子名')
        os.makedirs(os.path.join(album_dir, '第1话'))
        with open(os.path.join(album_dir, '第1话', '1.jpg'), 'wb') as f:
            f.write(b'fake')
        pdf_path = album_dir + '.pdf'
        with open(pdf_path, 'wb') as f:
            f.write(b'%PDF-fake')

        option = SimpleNamespace(
            dir_rule=SimpleNamespace(decide_album_root_dir=lambda album: album_dir))
        assert delete_album_images(option, album=None) is True
        assert not os.path.exists(album_dir), '本子目录应被删除'
        assert os.path.isfile(pdf_path), 'PDF 应保留'


def main() -> int:
    """脚本方式运行测试，返回进程退出码"""
    try:
        test_main_runs()
        test_pdf_merge()
        test_settings_behaviors()
        test_delete_album_images()
    except (AssertionError, subprocess.TimeoutExpired) as e:
        print(f'[FAIL] {e}')
        return 1
    print('[OK] 程序正常运行')
    return 0


if __name__ == '__main__':
    sys.exit(main())
