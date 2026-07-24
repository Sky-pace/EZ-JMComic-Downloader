# 维护方案

## 1. 项目架构概览

```
jmcomic/
├── app/
│   ├── __init__.py                # 包声明
│   ├── main.py                    # 入口（极简，仅组装调用）
│   ├── core/                      # 核心业务层
│   │   ├── __init__.py
│   │   ├── env.py                 # 运行环境检测（frozen/exe路径）
│   │   ├── config.py              # option.yml 路径解析与加载
│   │   └── downloader.py          # 下载编排器（参数收集 + 下载）
│   └── ui/                        # 用户交互层
│       ├── __init__.py
│       └── prompts.py             # 命令行交互（输入/输出）
├── config/
│   └── option.yml                 # 配置参数
├── tests/
│   ├── __init__.py
│   └── test_main.py               # 冒烟测试
├── release/                       # 版本发布归档
│   └── v1.0.0/
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
| 核心 | `app/core/` | 业务逻辑、配置、下载 | → ui, 第三方库 |
| 交互 | `app/ui/` | 用户输入/输出 | 无外部依赖 |

**禁止反向依赖：** `ui/` 不得依赖 `core/`。

---

## 2. 各模块职责

### 2.1 `app/main.py`
- 仅包含 `main()` 函数
- 调用 `setup_working_directory()` 设置工作目录
- 调用 `downloader.run()` 启动流程
- **不允许**包含任何业务逻辑或用户交互代码

### 2.2 `app/core/env.py`
- `is_frozen()` — 判断是否为 PyInstaller 打包运行
- `get_executable_dir()` — 获取运行根目录
- `setup_working_directory()` — 设置运行时 CWD

### 2.3 `app/core/config.py`
- `resolve_option_path()` — 按优先级定位 `option.yml`：
  1. `.exe` 同目录 `config/option.yml`
  2. PyInstaller 内置资源
  3. 项目根目录
- `load_option()` — 加载并返回 `jmcomic` 配置对象

### 2.4 `app/core/downloader.py`
- `run()` — 完整的下载编排器：
  1. 加载配置
  2. 收集相册 ID
  3. 询问图片格式（从 yml 读默认值）
  4. 询问下载路径（从 yml 读默认值）
  5. 调用 `jmcomic.download_album()`

### 2.5 `app/ui/prompts.py`
- `get_album_id()` — 获取相册 ID（递归验证非空）
- `prompt_image_format()` — 获取图片格式
- `prompt_download_path()` — 获取下载路径

---

## 3. 依赖升级策略

### 3.1 `jmcomic` 库升级
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

### 3.2 `pyinstaller` 升级
- 检查 `.spec` 文件格式是否兼容
- 确认 `hiddenimports` 列表是否需要更新

---

## 4. 日常维护清单

### 每月
- [ ] 检查 `jmcomic` 是否有新版本
- [ ] 运行冒烟测试：`python tests/test_main.py`
- [ ] 确认 `.gitignore` 未遗漏新增产物类型

### 每次代码变更后
- [ ] 确保所有 import 路径与模块拆分对应
- [ ] 运行 `python -m app.main` 验证主流程
- [ ] 更新 `README.md` 中的项目结构图（如有文件增删）
- [ ] 更新本文件中的模块职责说明

### 版本发布前
- [ ] 更新 `release/` 目录下的版本文件夹
- [ ] 更新 `jmdownload.spec` 中 `name` 字段（含版本号）
- [ ] 打包测试：`pyinstaller jmdownload.spec`
- [ ] 在干净环境中测试 `.exe` 运行

---

## 5. 扩展指南

### 5.1 添加新的用户交互（如多选菜单）
1. 在 `app/ui/prompts.py` 中添加函数
2. 在 `app/core/downloader.py` 中调用

### 5.2 支持新的配置项
1. 在 `config/option.yml` 中添加键值
2. 在 `app/core/downloader.py` 的 `run()` 中读取并应用

### 5.3 支持多平台路径（Linux/macOS）
- `app/core/env.py` 已使用 `os.path` 和 `sys.executable`，天然跨平台
- 新增平台特定逻辑仅在 `env.py` 中修改

### 5.4 添加日志
建议在 `app/core/` 下新建 `logging.py`：
```python
import logging
logger = logging.getLogger('jmdownload')
```
在 `downloader.py` 中用 `logger.info()` 替代 `print()`。

---

## 6. 故障排查

| 现象 | 可能原因 | 排查路径 |
|------|----------|----------|
| `找不到 option.yml` | 路径解析有误 | 检查 `app/core/config.py` 的 `resolve_option_path()` |
| `下载失败（API 错误）` | jmcomic 版本不兼容 | 对比 `jmcomic` changelog，修改 `downloader.py` |
| `打包后 .exe 闪退` | CWD 变化 | 确认 `env.py` 的 `setup_working_directory()` 被执行 |
| `ImportError` | 模块拆分后路径错 | 对照项目结构图检查 import 语句 |

---

## 7. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.1.0 | - | 模块化重构，分离 core/ui 层 |
| v1.0.0 | - | 初始版本 |