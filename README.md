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
│   │   ├── downloader.py   # 下载编排
│   │   ├── history.py      # 历史记录管理
│   │   ├── updater.py      # 自更新（检查 / 更新 / 回滚）
│   │   └── menu.py         # 主菜单编排
│   └── ui/                 # 用户交互层
│       ├── __init__.py
│       └── prompts.py      # 命令行交互
├── config/                 # 配置文件
│   └── option.yml          # 下载参数（图片格式、路径等）
├── release/                # 历史版本归档（exe 通过 Releases 分发）
├── tests/                  # 测试
│   ├── __init__.py
│   └── test_main.py        # 功能/冒烟测试
├── jmdownload.spec         # PyInstaller 打包配置
├── requirements.txt        # Python 依赖
├── .gitignore
└── README.md
```

## 🚀 快速开始

### 方式一：下载 exe（推荐）

从 [Releases](https://github.com/Sky-pace/EZ-JMComic-Downloader/releases/latest) 下载最新的 `jmdownload-vX.Y.Z.exe`，双击即可运行。

exe 启动时会**自动检查更新**：发现新版本时主菜单会出现更新选项，由你确认后才会下载、校验并升级。升级后旧版本保留为备份，可通过菜单随时回滚。下载路径、历史记录、配置文件均不受影响。

### 方式二：源码运行

```bash
pip install -r requirements.txt
python -m app.main
```

### 方式三：打包为 .exe

```bash
pip install pyinstaller
pyinstaller jmdownload.spec
```
构建产物位于 `dist/jmdownload-v1.2.1.exe`，双击即可运行。

### 使用

程序启动后显示主菜单，输入数字选择：

```
===== JM 漫画下载器 v1.2.1 =====
  1. 下载漫画
  2. 查看历史记录
  0. 退出
```

完成一项操作后会自动回到主菜单，可继续选择其他操作；输入 `0` 退出程序。
检测到新版本或存在旧版本备份时，菜单会额外出现「更新」「回滚」选项（仅打包的 exe）。

#### 下载漫画

主菜单选择 `1`，然后按提示依次输入：

1. **相册 ID** — 漫画 ID（数字）
2. **图片格式** — `jpg`、`png`、`webp` 等（默认 `jpg`）
3. **下载路径** — 保存目录（默认 `./downloads`）

#### 查看历史记录

主菜单选择 `2`，或使用命令行参数：

```bash
python -m app.main --history
```

下载过的漫画 ID 会自动记录，可通过此命令查看历史及存储文件路径。
历史记录文件为 `.jm_history.json`，存放于程序运行目录。

## ⚙️ 配置

编辑 `config/option.yml`：

```yml
download:
  image:
    suffix: .jpg          # 默认图片格式
dir_rule:
  base_dir: ./downloads   # 默认保存路径
```

使用 exe 时无需手动创建：首次运行会自动在 exe 同目录生成 `config/option.yml`，编辑后下次启动生效。

## ❓ 常见问题

| 问题 | 解决 |
|------|------|
| 下载很慢 | 与网络和服务器有关，属正常情况 |
| 找不到 option.yml | 确保 `config/option.yml` 存在 |
| 能在 Mac / Linux 运行吗 | 使用 `python -m app.main` 即可 |
| 打包后 option.yml 找不到 | 已通过 `.spec` 的 `datas` 配置处理，无需额外操作 |
| exe 如何升级 | 启动时自动检查，有新版本时主菜单会出现「更新」选项，确认即可；也可到 Releases 页手动下载覆盖 |
| 更新失败/想回滚 | 主菜单选择「回滚」；或手动将 exe 旁的 `.old` 备份改回原名 |

## 🐛 问题反馈

下载异常或有功能建议，请到 [Issues](https://github.com/Sky-pace/EZ-JMComic-Downloader/issues) 反馈。

## 📄 许可

仅用于学习交流，请勿用于商业用途。