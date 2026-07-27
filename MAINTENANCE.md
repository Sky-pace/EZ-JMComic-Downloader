# 维护方案

> 本文档面向维护者（人）。AI 协作规范见本地 `AGENT.md`（不入库）。
>
> **重要：任何涉及架构、模块、流程、规范的代码变更，必须同步更新本文档。**

## 1. 项目架构概览

```
jmcomic/
├── app/
│   ├── __init__.py                # 包声明 + __version__（自更新以此判断当前版本）
│   ├── main.py                    # 入口（极简，仅组装调用）
│   ├── core/                      # 核心业务层
│   │   ├── __init__.py
│   │   ├── env.py                 # 运行环境检测（frozen/exe路径）
│   │   ├── config.py              # option.yml 路径解析与加载
│   │   ├── downloader.py          # 下载编排器（参数收集 + 下载）
│   │   ├── history.py             # 历史记录管理（.jm_history.json）
│   │   ├── updater.py             # 自更新（检查 / 更新 / 回滚，用户决定）
│   │   └── menu.py                # 主菜单编排（下载 / 历史 / 更新 / 回滚）
│   └── ui/                        # 用户交互层
│       ├── __init__.py
│       └── prompts.py             # 命令行交互（输入/输出）
├── config/
│   └── option.yml                 # 配置参数
├── tests/
│   ├── __init__.py
│   └── test_main.py               # 冒烟测试
├── release/                       # 版本发布归档（exe 不入库，见 .gitignore）
│   ├── v1.0.0/
│   └── v1.1.0/
├── _to_delete/                    # 安全回收站（不入库）
├── jmdownload.spec                # PyInstaller 打包配置
├── requirements.txt               # 依赖声明
├── README.md                      # 项目说明
├── MAINTENANCE.md                 # 本文件
└── .gitignore
```

**分层原则：**

| 层 | 路径 | 职责 | 依赖方向 |
|----|------|------|----------|
| 入口 | `app/main.py` | 组装启动 | → core + ui |
| 核心 | `app/core/` | 业务逻辑、配置、下载、更新 | → ui, 第三方库 |
| 交互 | `app/ui/` | 用户输入/输出 | 无外部依赖 |

**禁止反向依赖：** `ui/` 不得依赖 `core/`。

---

## 2. 各模块职责

### 2.1 `app/main.py`
- 仅包含 `main()` 函数
- 调用 `setup_working_directory()` 设置工作目录
- 处理 `--history` 参数（直接进入历史记录，供脚本/冒烟测试非交互使用）
- 否则调用 `menu.run_menu()` 进入主菜单
- 捕获 `EOFError` / `KeyboardInterrupt` 优雅退出
- **不允许**包含任何业务逻辑或用户交互代码

### 2.2 `app/core/env.py`
- `is_frozen()` — 判断是否为 PyInstaller 打包运行
- `get_executable_dir()` — 获取运行根目录
- `setup_working_directory()` — 设置运行时 CWD

### 2.3 `app/core/config.py`
- `resolve_option_path()` — 按优先级定位 `option.yml`：
  1. `.exe` 同目录 `config/option.yml`
  2. PyInstaller 内置资源（带存在性检查）
  3. 项目根目录
- `load_option()` — 加载并返回 `jmcomic` 配置对象

### 2.4 `app/core/downloader.py`
- `run()` — 完整的下载编排器：
  1. 加载配置
  2. 收集相册 ID
  3. 询问图片格式（从 yml 读默认值）
  4. 询问下载路径（从 yml 读默认值）
  5. 调用 `jmcomic.download_album()`（异常捕获，失败友好提示）
  6. 下载成功后写入历史记录

### 2.5 `app/core/history.py`
- `add(album_id)` — 追加历史记录（去重，保留最新）
- `show()` — 打印历史记录及文件路径
- 存储文件为 `.jm_history.json`，位于 `get_executable_dir()`（与 cwd 无关）
- 写入失败仅告警，不中断主流程

### 2.6 `app/core/updater.py`
仅打包环境生效，提供三个独立能力（均由用户在主菜单中决定何时执行）：
- `check_for_update()` — 请求 GitHub Releases API 比对 `app.__version__`，有新版本返回 Release 信息，否则 `None`；任何失败静默降级
- `apply_update(release)` — 下载新 exe → sha256 校验 → 当前 exe 重命名为 `.old`（备份）→ 新 exe 上位 → 重启
- `has_rollback()` / `rollback()` — 检测 `.old` 备份；回滚 = 当前 exe 与 `.old` 互换（可再次回滚）→ 重启

### 2.7 `app/core/menu.py`
- `run_menu()` — 主菜单编排：启动时检查更新，动态显示可选项（下载 / 历史 / 更新 / 回滚 / 退出），更新与回滚执行前均需用户确认

### 2.8 `app/ui/prompts.py`
- `get_album_id()` — 获取相册 ID（循环验证：非空 + 纯数字）
- `prompt_image_format()` — 获取图片格式
- `prompt_download_path()` — 获取下载路径
- `prompt_menu_choice()` — 显示菜单并校验选择
- `prompt_confirm()` — y/N 确认

---

## 3. 自更新机制

### 3.1 工作原理

exe 启动时请求 `https://api.github.com/repos/Sky-pace/EZ-JMComic-Downloader/releases/latest`，
比对 `tag_name` 与内置 `__version__`。发现新版本时**仅在主菜单中给出更新选项**，
由用户确认后才下载、校验、热替换并重启；存在 `.old` 备份时菜单同时提供回滚选项。

### 3.2 不可变更的约定（**存量用户依赖**）

老版本 exe 写死了以下格式，**改动会导致所有存量用户更新失败**：

- Release tag 格式：`vX.Y.Z`
- 资源命名：`jmdownload-vX.Y.Z.exe` + `jmdownload-vX.Y.Z.exe.sha256`
  （updater 按"以 `.exe` / `.exe.sha256` 结尾"匹配，前缀可随项目名调整，后缀不能变）
- `.sha256` 文件内容：exe 的 sha256 十六进制摘要（首个空白前的部分）

### 3.3 数据安全

自更新只替换 exe 文件本身。用户数据（`.jm_history.json`、`config/option.yml`、`downloads/`）
均为 exe 旁的独立文件，不受更新影响。旧版本保留为 `.old` 备份，可手动回滚。

---

## 4. 依赖升级策略

### 4.1 `jmcomic` 库升级
每次升级 `jmcomic` 后需检查：

1. **`option.download.image` 类型** — 当前为 `dict`，若未来变更为对象则需同步修改 `downloader.py`
2. **`option.dir_rule` 类型** — 当前为对象，访问 `base_dir` 用 `getattr`
3. **API 签名变更** — 检查 `jmcomic.download_album()` 参数
4. **新增配置项** — 按需在 `config/option.yml` 中添加

**检查命令：**
```bash
pip show jmcomic          # 查看当前版本
python -c "import jmcomic; help(jmcomic.download_album)"  # 查看 API
```

### 4.2 `pyinstaller` 升级
- 检查 `.spec` 文件格式是否兼容
- 确认 `hiddenimports` 列表是否需要更新

---

## 5. 日常维护清单

### 每月
- [ ] 检查 `jmcomic` 是否有新版本
- [ ] 运行冒烟测试：`python tests/test_main.py`
- [ ] 确认 `.gitignore` 未遗漏新增产物类型

### 每次代码变更后
- [ ] 确保所有 import 路径与模块拆分对应
- [ ] 运行 `python -m app.main` 验证主流程
- [ ] **同步更新本文档与本地 `AGENT.md`**（结构图、模块职责、流程、规范）
- [ ] 及时提交 git（一个独立变更一次提交）

### 版本发布前
- [ ] 更新 `app/__init__.py` 的 `__version__` 和 `jmdownload.spec` 的 `name`（两处版本号一致）
- [ ] 打包测试：`pyinstaller jmdownload.spec`
- [ ] 在干净环境中测试 `.exe` 运行
- [ ] 归档到 `release/vX.Y.Z/`（exe 不入库）
- [ ] 提交、打 tag、推送
- [ ] 创建 GitHub Release，上传 exe + `.sha256`（格式见 §3.2，**自更新依赖**）
- [ ] 验证自更新：用旧版本 exe 运行，确认能检测到新版本

---

## 6. 扩展指南

### 6.1 添加新的用户交互（如多选菜单）
1. 在 `app/ui/prompts.py` 中添加函数
2. 在 `app/core/downloader.py` 中调用

### 6.2 支持新的配置项
1. 在 `config/option.yml` 中添加键值
2. 在 `app/core/downloader.py` 的 `run()` 中读取并应用

### 6.3 支持多平台路径（Linux/macOS）
- `app/core/env.py` 已使用 `os.path` 和 `sys.executable`，天然跨平台
- 新增平台特定逻辑仅在 `env.py` 中修改
- 注意：`updater.py` 的热替换依赖"Windows 允许重命名运行中的 exe"，其他平台需验证

### 6.4 添加日志
建议在 `app/core/` 下新建 `logging.py`：
```python
import logging
logger = logging.getLogger('jmdownload')
```
在 `downloader.py` 中用 `logger.info()` 替代 `print()`。

---

## 7. 故障排查

| 现象 | 可能原因 | 排查路径 |
|------|----------|----------|
| `找不到 option.yml` | 路径解析有误 | 检查 `app/core/config.py` 的 `resolve_option_path()` |
| `下载失败（API 错误）` | jmcomic 版本不兼容 | 对比 `jmcomic` changelog，修改 `downloader.py` |
| `打包后 .exe 闪退` | CWD 变化 | 确认 `env.py` 的 `setup_working_directory()` 被执行 |
| `ImportError` | 模块拆分后路径错 | 对照项目结构图检查 import 语句 |
| 自动更新一直失败 | 网络无法访问 GitHub / Release 资源缺失 | 检查 Release 是否有 exe + .sha256 两个资源；手动下载覆盖 |
| 更新后无法启动 | 新版 exe 损坏 | 删除新版，将 `.old` 备份改回原文件名回滚 |
| exe 旁出现 `.new` 残留 | 上次更新在校验阶段失败 | 可直接删除 `.new` 文件 |

---

## 8. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.1.0 | - | 模块化重构，分离 core/ui 层；新增历史记录、自更新 |
| v1.0.0 | - | 初始版本 |
