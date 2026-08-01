"""PDF 整合模块 —— 将下载的漫画图片按顺序合并为 PDF、清理原图"""

import os
import re
import shutil

from PIL import Image

IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')


def _natural_key(name: str) -> list:
    """自然排序键：按数字切分文件名，保证 1.jpg < 2.jpg < 10.jpg"""
    return [int(part) if part.isdigit() else part.lower()
            for part in re.split(r'(\d+)', name)]


def merge_images_to_pdf(image_paths: list, pdf_path: str) -> None:
    """将图片列表按给定顺序合并为一个 PDF 文件"""
    images = []
    try:
        for path in image_paths:
            with Image.open(path) as im:
                images.append(im.convert('RGB'))
        images[0].save(pdf_path, 'PDF', save_all=True,
                       append_images=images[1:], quality=95)
    finally:
        for im in images:
            im.close()


def merge_album_to_pdf(option, album) -> str | None:
    """
    将本子所有已下载图片按章节顺序、页码顺序合并为 PDF。
    输出到本子文件夹同级的 <本子名>.pdf；失败仅告警并返回 None，不影响主流程。
    """
    try:
        image_paths = []
        for photo in album:
            save_dir = option.dir_rule.decide_image_save_dir(album, photo)
            if not os.path.isdir(save_dir):
                continue
            names = [f for f in os.listdir(save_dir)
                     if f.lower().endswith(IMAGE_EXTS)]
            names.sort(key=_natural_key)
            image_paths.extend(os.path.join(save_dir, f) for f in names)

        if not image_paths:
            print('未找到已下载的图片，跳过 PDF 生成。')
            return None

        pdf_path = option.dir_rule.decide_album_root_dir(album) + '.pdf'
        merge_images_to_pdf(image_paths, pdf_path)
        return pdf_path
    except Exception as e:
        print(f'PDF 生成失败：{e}（图片本身不受影响）')
        return None


def delete_album_images(option, album) -> bool:
    """
    删除本子的整个图片目录（仅在 PDF 生成成功后调用）。
    失败仅告警并返回 False。
    """
    try:
        root = option.dir_rule.decide_album_root_dir(album)
        if os.path.isdir(root):
            shutil.rmtree(root)
        return True
    except Exception as e:
        print(f'删除原漫画图片失败：{e}')
        return False
