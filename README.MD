# JM 漫画下载器

> 基于 [jmcomic](https://github.com/hect0x7/JMComic-Crawler-Python) 库的禁漫命令行下载工具。

## 📁 项目结构

```
jmcomic/
├── app/                    # 主程序源码
│   ├── __init__.py
│   ├── main.py             # 入口脚本
│   ├── core/               # 核心业务层
│   │   ├── __init__.py
│   │   ├── env.py          # 运行环境检测
│   │   ├── config.py       # 配置加载
│   │   └── downloader.py   # 下载编排
│   └── ui/                 # 用户交互层
│       ├── __init__.py
│       └── prompts.py      # 命令行交互
├── config/                 # 配置文件
│   └── option.yml          # 下载参数（图片格式、路径等）
├── release/                # 发行版文件
│   └── v1.1.0/             # 当前版本
├── tests/                  # 测试
│   ├── __init__.py
│   └── test_main.py        # 功能/冒烟测试
├── jmdownload.spec         # PyInstaller 打包配置
├── requirements.txt        # Python 依赖
├── .gitignore
└── README.md
```

## 🚀 快速开始

### 方式一：源码运行

```bash
pip install -r requirements.txt
python -m app.main
```

### 方式二：打包为 .exe

```bash
pip install pyinstaller
pyinstaller jmdownload.spec
```
构建产物位于 `dist/jmdownload.exe`，双击即可运行。

### 使用

程序启动后按提示依次输入：

1. **相册 ID** — 漫画 ID（数字）
2. **图片格式** — `jpg`、`png`、`webp` 等（默认 `jpg`）
3. **下载路径** — 保存目录（默认 `./downloads`）

## ⚙️ 配置

编辑 `config/option.yml`：

```yml
download:
  image:
    suffix: .jpg          # 默认图片格式
dir_rule:
  base_dir: ./downloads   # 默认保存路径
```

## ❓ 常见问题

| 问题 | 解决 |
|------|------|
| 下载很慢 | 与网络和服务器有关，属正常情况 |
| 找不到 option.yml | 确保 `config/option.yml` 存在 |
| 能在 Mac / Linux 运行吗 | 使用 `python -m app.main` 即可 |
| 打包后 option.yml 找不到 | 已通过 `.spec` 的 `datas` 配置处理，无需额外操作 |

## 📄 许可

仅用于学习交流，请勿用于商业用途。