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
│   │   ├── pdf.py          # 图片整合为 PDF
│   │   └── menu.py         # 主菜单编排
│   └── ui/                 # 用户交互层
│       ├── __init__.py
│       └── prompts.py      # 命令行交互
├── config/                 # 配置文件
│   └── option.yml          # 下载参数（图片格式、路径等）
├── tests/                  # 测试
│   ├── __init__.py
│   └── test_main.py        # 功能/冒烟测试
├── jmdownload.spec         # PyInstaller 打包配置
├── requirements.txt        # Python 依赖
├── .gitignore
└── README.md
```

## 🚀 快速开始

### Windows：下载 exe

从 [Releases](https://github.com/Sky-pace/EZ-JMComic-Downloader/releases/latest) 下载最新的 `jmdownload.exe`，双击即可运行。

exe 启动时会**自动检查更新**：发现新版本时主菜单会出现更新选项，由你确认后才会下载、校验并升级。升级后旧版本保留为备份，可通过菜单随时回滚。下载路径、历史记录、配置文件均不受影响。

### Linux / macOS：一键安装

一条命令从 GitHub Releases 下载并安装到 `~/.jmcomic`（免 sudo）：

```bash
curl -fsSL https://raw.githubusercontent.com/Sky-pace/EZ-JMComic-Downloader/main/tools/install.sh -o install.sh
bash install.sh
```

或直接拉取源码本地构建：

```bash
bash install.sh --source
```

安装完成后，**最后一步：将程序加入 PATH**，以便在终端直接使用 `jmdownload`：

| Shell | 命令 |
|-------|------|
| bash | `echo 'export PATH="$HOME/.jmcomic/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc` |
| zsh | `echo 'export PATH="$HOME/.jmcomic/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc` |
| fish | `fish_add_path "$HOME/.jmcomic/bin"` |

> 数据目录为 `~/.jmcomic`（`bin/` 存放程序、`config/` 存放配置，历史记录与默认下载均在此）。
> 更新到最新版：重新运行 `bash install.sh` 即可（一条命令自更新）；打包版启动时也会自动检查更新，全程免 sudo。
>
> **Linux 预编译二进制的运行要求**：基于 Ubuntu 24.04（glibc 2.39）构建，要求运行环境 glibc ≥ 2.39（约相当于 Ubuntu 24.04+ / Debian 13+ / Fedora 39+）。更老的发行版请用 `bash install.sh --source` 在本机从源码构建（需 git 与 Python 3.10+，构建在临时 venv 中进行，不污染系统环境）。

### 使用

程序启动后显示主菜单，输入数字选择：

```
===== JM 漫画下载器 v1.4.1 =====
  1. 下载漫画
  2. 查看历史记录
  0. 退出
```

完成一项操作后会自动回到主菜单，可继续选择其他操作；输入 `0` 退出程序。
检测到新版本或存在旧版本备份时，菜单会额外出现「更新」「回滚」选项（仅打包版）。

#### 下载漫画

主菜单选择 `1`，然后按提示依次输入：

1. **相册 ID** — 漫画 ID（数字）
2. **图片格式** — `jpg`、`png`、`webp` 等（默认 `jpg`）
3. **下载路径** — 保存目录（默认 `./downloads`）

下载完成后会询问「是否将本次下载的图片整合为 PDF」，输入 `y` 即按章节、页码顺序生成 `<下载目录>/pdf/<本子名>.pdf`；PDF 生成成功后还会询问「是否删除原漫画图片」，输入 `y` 删除各章节的图片目录（PDF 保留）。

这两项询问都可在「修改默认配置」中改为自动执行（`yes`）或自动跳过（`no`），见下文「配置」。

#### 历史记录管理

主菜单选择 `2`，以表格形式查看历史（ID、名称、保存路径、PDF 路径、时间）。源图片目录被删除后路径会标注「（已删除）」（实时检测）；PDF 列显示 PDF 保存位置，未生成显示 `-`。随后可输入：

- **序号** — 删除对应记录
- **r+序号** — 重新下载该漫画（自动沿用当时的保存路径，适合误删漫画后恢复）
- **c** — 清空所有记录（需确认）
- **回车** — 返回主菜单

历史记录文件为 `.jm_history.json`，存放于数据目录（Windows 为 exe 同目录，Linux 为 `~/.jmcomic`）。也可直接用命令行参数查看：

```bash
jmdownload --history
```

## ⚙️ 配置

主菜单选择 `5` 可直接修改默认配置，回车保持不变，修改后下次启动生效。可配置项：

- **图片格式 / 下载路径** — 写入 `config/option.yml`
- **下载后整合 PDF / 整合后删除原图** — 各可设 `ask`（每次询问，默认）、`yes`（自动执行）、`no`（自动跳过），写入程序目录下的 `.jm_settings.json`（因 jmcomic 不容忍 option.yml 中的未知键，此项独立存放）

例如把两项都设为 `yes`，下载完成后会自动生成 PDF 并删除原图，全程无需干预；「删除原图」仅在 PDF 成功生成后才会触发，PDF 未生成时不会删图。

也可以手动编辑 `config/option.yml`：

```yml
download:
  image:
    suffix: .jpg          # 默认图片格式
dir_rule:
  base_dir: ./downloads   # 默认保存路径（相对路径基于程序所在目录）
```

使用打包版时无需手动创建：首次运行会自动在数据目录生成 `config/option.yml`（Windows 为 exe 同目录，Linux 为 `~/.jmcomic`）。

## ❓ 常见问题

| 问题 | 解决 |
|------|------|
| 下载很慢 | 与网络和服务器有关，属正常情况 |
| 找不到 option.yml | 确保 `config/option.yml` 存在 |
| 能在 Mac / Linux 运行吗 | 支持。Linux / macOS 用 `install.sh` 一键安装（见快速开始） |
| 打包后 option.yml 找不到 | 已通过 `.spec` 的 `datas` 配置处理，无需额外操作 |
| 打包版如何升级 | 启动时自动检查，有新版本时主菜单会出现「更新」选项，确认即可；Linux 也可重跑 `install.sh` |
| 更新失败/想回滚 | 主菜单选择「回滚」；或手动将 `.old` 备份改回原名（Windows 为 exe 旁，Linux 为 `~/.jmcomic/bin` 旁） |
| Linux 数据存在哪里 | 统一在 `~/.jmcomic`（历史、配置、默认下载） |

## ⚠️ 已知问题

| 问题 | 状态 | 应对 |
|------|------|------|
| 更新后程序没有自动重启 | v1.3.2 已修复（旧版本更新时仍可能发生一次） | 更新本身已完成，手动双击 exe 即可 |
| 更新后首次启动报 `ModuleNotFoundError`（如 curl_cffi._wrapper） | 一次性瞬态问题，不可复现 | 重新运行 exe 即可；持续出现请到 Issues 反馈 |

## 🤝 参与贡献

欢迎 Issue 和 PR。

### 开发环境

- Python 3.13+
- 克隆仓库：`git clone https://github.com/Sky-pace/EZ-JMComic-Downloader.git`
- 建议使用虚拟环境：

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

### 常用命令

```bash
python tests/test_main.py   # 冒烟测试
pyinstaller jmdownload.spec # 打包（产物在 dist/：Windows 为 jmdownload.exe，Linux 为 jmdownload）
```

> 本地调试可用 `python -m app.main`，但**仅供开发调试**：数据会落在项目根目录（历史/配置/下载），且无自更新（自更新仅打包版可用）。正常使用请用上方「快速开始」的安装方式。

### 架构约定

- 分层：`app/core/`（业务逻辑）→ `app/ui/`（命令行交互），**ui 不得依赖 core**
- `main.py` 仅组装调用，不含业务逻辑
- 4 空格缩进，函数/模块写中文 docstring

### 提交规范

- commit message 格式：`type: brief description`，类型：`feat` / `fix` / `chore` / `docs` / `refactor`
- 一个独立变更一次提交

## 🐛 问题反馈

下载异常或有功能建议，请到 [Issues](https://github.com/Sky-pace/EZ-JMComic-Downloader/issues) 反馈。

## 📄 许可与免责声明

本项目仅供学习交流使用，请勿用于商业用途。使用者应遵守所在地区的法律法规及目标网站的使用条款，由此产生的一切后果由使用者自行承担，与项目作者无关。下载内容的版权归原作者所有。