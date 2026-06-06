"""
测试 jmdownload 程序是否能正常运行。

用法:
    python -m pytest tests/test_main.py
    python tests/test_main.py
"""

import subprocess
import os
import sys


def main():
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_module = os.path.join(script_dir, 'app', 'main.py')

    test_input = "12345\njpg\n" + os.path.join(script_dir, "downloads") + "\n"

    # 优先测试打包后的 .exe，不存在则运行 Python 脚本
    exe_path = os.path.join(script_dir, 'dist', 'jmdownload.exe')
    if os.path.exists(exe_path):
        cmd = [exe_path]
    else:
        cmd = [sys.executable, app_module]

    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        stdout, stderr = process.communicate(input=test_input, timeout=10)

        print("===== STDOUT =====")
        print(stdout)
        print("\n===== STDERR =====")
        print(stderr)
        print(f"\n返回码: {process.returncode}")

        if process.returncode != 0:
            print("⚠ 程序以非零状态退出，请检查日志")
        else:
            print("✓ 程序正常运行")

    except subprocess.TimeoutExpired:
        print("超时：脚本运行时间过长（可能正在下载尝试）")
        process.kill()
    except FileNotFoundError:
        print(f"文件未找到: {cmd}")
    except Exception as e:
        print(f"运行出错: {e}")


if __name__ == '__main__':
    main()