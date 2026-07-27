# AGENT.md — AI 协作规范

本项目 `jmcomic` 是一个基于 [jmcomic](https://github.com/hect0x7/JMComic-Crawler-Python) 库的禁漫命令行下载工具。

---

## 1. 目录结构约定

```
jmcomic/
├── AGENT.md                    # 本文件：AI 协作规范
├── app/                        # 源码
│   ├── main.py                 # 入口
│   ├── core/                   # 核心逻辑
│   │   ├── config.py           # 配置加载
│   │   ├── downloader.py       # 下载编排
│   │   ├── env.py              # 打包/运行环境检测
│   │   └── history.py          # 历史记录管理
│   └── ui/                     # 用户交互
│       └── prompts.py          # 命令行提示
├── config/
│   └── option.yml              # 默认下载参数
├── release/
│   └── vX.Y.Z/                 # 每次发版三个文件：exe + option.yml + README
├── tests/
│   └── test_main.py            # 冒烟测试
├── jmdownload.spec             # PyInstaller 打包配置
├── requirements.txt
├── README.MD
└── .gitignore
```

---

## 2. 开发与运行

### 源码运行
```bash
pip install -r requirements.txt
python -m app.main
```

### 打包
```bash
pyinstaller jmdownload.spec
```
打包输出为 `dist/jmdownload-vX.Y.Z.exe`（版本号与 spec 中的 `name` 一致）。

### 发版（Release）步骤

1. 修改 `jmdownload.spec` 中的 `name` 版本号
2. 运行 PyInstaller 打包
3. 将 `dist/jmdownload-vX.Y.Z.exe` + `config/option.yml` + `README.MD` 复制到 `release/vX.Y.Z/`
4. 清理构建产物：将 `build/` 和 `dist/` 移到 `_to_delete/`（**禁止直接 rm/delete**）
5. 提交所有变更，tag 为版本号
6. 若配置了远程仓库，推送 commits + tags

---

## 3. 关键约束（**必须遵守**）

### 3.1 删除操作禁令
**永远不要直接删除任何文件或目录。** 本项目使用 `_to_delete/` 目录作为安全回收站。

- 需要移除文件/目录时，统一使用 `mv`（Linux）或 `move`（Windows）命令移至 `_to_delete/`
- 示例：`move build _to_delete\build`
- 禁止使用：`rm`、`del`、`rmdir`、`os.remove()`、`shutil.rmtree()` 等任何实质性删除命令

### 3.2 路径问题
- 工作目录固定为 `e:\MyProject\jmcomic`，所有操作基于此目录
- `config/option.yml` 在打包时会通过 `.spec` 的 `datas` 参数打包进 exe 同目录
- `env.py` 中的 `get_executable_dir()` 负责处理打包前后路径差异

### 3.3 版本号一致
以下位置中的版本号必须保持同步：
- `jmdownload.spec` → `name = 'jmdownload-vX.Y.Z'`
- `tests/test_main.py` → exe 路径
- `release/vX.Y.Z/` 目录名及内容
- `RELEASE_INFO.md`（如有）

### 3.4 Python 兼容性
- 项目基于 Python 3.13，使用 `pyinstaller` 6.19
- 禁漫核心库为 `jmcomic`，通过 pip 安装

### 3.5 代码规范
- 使用空格缩进（4 格）
- 函数/模块均添加中文 docstring 说明
- 模块职责清晰：`core/` 业务逻辑，`ui/` 用户交互，`main.py` 入口
- `history` 模块中函数名与内置名冲突时，使用 `from x import y as z` 方式重命名（如 `add as history_add`）

### 3.6 历史记录
- 历史记录文件为 `.jm_history.json`，存储于程序运行目录（`get_executable_dir()`：打包后为 .exe 目录，源码运行为项目根目录，与 cwd 无关）
- 已加入 `.gitignore`，不应被提交
- 包含 `album_id` 和 `time` 字段，自动去重

---

## 4. Git 工作流

- 有意义的 commit message，格式：`type: brief description`
  - 类型：`feat` / `fix` / `chore` / `docs` / `refactor`
- 发版时打 tag：`vX.Y.Z`
- 提交前检查 `.gitignore` 确保无敏感/冗余文件

---

## 5. 测试

```bash
# 冒烟测试
python tests/test_main.py
# 单元测试
python -m pytest tests/
# 历史记录查看
python -m app.main --history