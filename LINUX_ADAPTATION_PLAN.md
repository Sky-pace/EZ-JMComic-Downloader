# Linux 适配路线

> 本文档记录 Linux 适配的完整方案，关键设计已经过需求确认。
> 本文档仅记录适配方案，**不构成任何代码修改**；代码改动将另行排期实施，本文档作为路线与验收依据。
> 适配目标不限于 Ubuntu/Debian/Fedora，需同时覆盖 Arch / openSUSE / WSL 等发行版，以及 bash / zsh / fish 等多终端。

---

## 目标形态

- 支持两种获取方式：
  1. 从 GitHub Releases 下载 Linux 发行版二进制
  2. 自行拉取源码编译（`pip install -r requirements.txt` + `pyinstaller jmdownload.spec`）
- 下载完成后 **一条命令即可自更新**
- 可在终端直接使用（**加入 PATH** 作为官方安装流程的最后一步）

---

## 现状

项目基于 `jmcomic` 库，核心功能（下载、PDF 合并、历史记录）跨平台。当前以 **Windows .exe 打包** 为中心，存在两个层面的平台硬编码：

1. **updater 硬编码 `.exe` 命名**、替换后未恢复可执行权限位；
2. **用户数据文件紧跟可执行文件目录**（`get_executable_dir()`）——Linux 下若数据放在 `~/.jmcomic/bin` 会污染 bin 目录，且若沿用「装进系统目录」的思路会遭遇 root 只读。

---

## 总体设计决策（已确认）

### 1. 目录布局：全塞 `~/.jmcomic`，免 sudo

二进制与用户数据统一放入用户主目录下的 `~/.jmcomic`，该目录**天然为当前用户可写**，由此：

- 在线自更新全程**不需要 sudo / pkexec** 提权，`updater.py` 不引入任何提权复杂度；
- 历史、设置、配置、默认下载目录全部可写；
- 安装 / 更新 / 卸载均不触碰系统目录，**发行版无关**。

```
~/.jmcomic/
├── bin/
│   └── jmdownload          # 二进制本体（自更新替换对象）
├── config/
│   └── option.yml          # 用户可改的外部配置
├── .jm_history.json        # 历史记录
├── .jm_settings.json       # 下载后行为设置
└── downloads/              # 默认下载目录（相对路径 ./downloads 的落点）
```

> 注：原「系统级 `/usr/local/bin` + sudo」的方向已整体删除，不纳入本路线。

### 2. PATH：install.sh 只提示、不自动改

`install.sh` 完成安装后**不写 rc、不建软链**，只按当前 `$SHELL` 检测并打印对应命令，把 PATH 掌控权交给用户。

```bash
case "$SHELL" in
  */fish)
    # fish 官方推荐 fish_add_path，自动持久化、幂等去重（fish 3.2+）
    echo '请将以下命令粘贴到当前 fish 会话（会自动持久化）：'
    echo '  fish_add_path "$HOME/.jmcomic/bin"'
    echo '（或写入 ~/.config/fish/config.fish：）'
    echo '  if not contains "$HOME/.jmcomic/bin" "$PATH"; set -p PATH "$HOME/.jmcomic/bin"; end'
    ;;
  */zsh)
    echo '请将以下行加入 ~/.zshrc：'
    echo '  export PATH="$HOME/.jmcomic/bin:$PATH"'
    echo '然后执行: source ~/.zshrc'
    ;;
  *)
    # bash 及其他 POSIX shell
    echo '请将以下行加入 ~/.bashrc：'
    echo '  export PATH="$HOME/.jmcomic/bin:$PATH"'
    echo '然后执行: source ~/.bashrc'
    ;;
esac
```

可选附加提示（跨 shell/发行版通用的软链方式，但 Arch+fish 未必继承 `~/.profile`，故 shell 专属命令仍是可靠兜底）：

```bash
ln -sf ~/.jmcomic/bin/jmdownload ~/.local/bin/jmdownload
```

`README.md` 的「方式四：Linux 安装」将**「加入 PATH」作为该方式的最后一步**，并分 bash / zsh / fish 三栏给出命令。

---

## 需要适配的点

### 1. `app/core/env.py` — 数据目录与二进制目录分离（🔴 阻断）

当前 `get_executable_dir()` 同时承担「定位二进制」与「定位用户数据」两个职责。Linux 下数据应统一放 `~/.jmcomic`，与二进制所在层（`~/.jmcomic/bin`）分开。

**新增 `get_data_dir()`：**

```python
def get_data_dir() -> str:
    """用户数据目录。Windows 保持现状（可执行文件目录），Linux 统一放 ~/.jmcomic"""
    if os.name == 'nt':
        return get_executable_dir()
    return os.path.join(os.path.expanduser('~'), '.jmcomic')
```

**配套改动：**
- `setup_working_directory()`：打包后 Linux 下 `chdir(get_data_dir())`，使相对路径 `./downloads` 自动落到 `~/.jmcomic/downloads`（Windows 行为不变）；
- `history.py` 的 `.jm_history.json` 改用 `get_data_dir()`；
- `config.py` 的外部 `config/option.yml` 与 `.jm_settings.json` 改用 `get_data_dir()`（源码运行与打包运行统一）；
- `get_executable_dir()` 保留，供 updater 定位二进制自身。

> **对原计划的更正**：原计划把 `env.py` 列入「无需改动」，这是错误结论——数据目录分离是本路线最关键的改动之一。

### 2. `app/core/updater.py` — 自更新模块（🔴 阻断）

#### 2.1 `_find_assets()`：弃用后缀匹配，改精确匹配二进制名

**原方案有 bug**：`_binary_suffix()` 在 Linux 返回 `('', '.sha256')`，而 `name.endswith('')` 恒为 True，无法可靠区分可执行文件与校验文件（原计划虽加 `and name` 兜底，仍不可靠）。

改为**精确匹配**：

```python
import os as _os

def _binary_names() -> tuple[str, str]:
    """返回 (可执行文件名, 校验文件名)。精确匹配，天然支持多架构命名"""
    bin_name = _os.path.basename(sys.executable)   # Windows: jmdownload.exe / Linux: jmdownload
    return bin_name, bin_name + '.sha256'
```

`_find_assets()` 使用该函数精确匹配 `asset['name']`。Windows 下 `sys.executable` 自然带 `.exe`，无需平台判断；Release 命名与二进制同名同前缀即可。

（可选增强：未来如需单文件多架构分发，可额外支持从环境变量/参数传入平台标识，如 `jmdownload-linux-x86_64`；默认精确匹配已可工作。）

#### 2.2 替换后补 `chmod +x`（原方案遗漏的 Linux 阻断项）

onefile 更新下载的 `.new` 文件由 `open(dest, 'wb')` 创建，默认权限 0644；`os.rename` 替换后**新二进制不可执行**。必须恢复执行权限，建议在 rename 前处理：

```python
os.chmod(new_path, 0o755)   # 先对新文件加执行位，再替换
```

#### 2.3 `os.rename` 跨文件系统 → `_safe_replace()`

`~/.jmcomic` 与系统 `/tmp` 可能位于不同文件系统，`os.rename()` 会抛 `OSError: [Errno 18] Invalid cross-device link`。保留原方案：

```python
import shutil

def _safe_replace(src: str, dst: str) -> None:
    """原子重命名，跨文件系统时回退到 shutil.move（复制+删除）"""
    try:
        os.rename(src, dst)
    except OSError:
        shutil.move(src, dst)
```

`apply_update()` / `rollback()` 中的 `os.rename()` 全部替换为 `_safe_replace()`。

#### 2.4 `_restart()` 补 `start_new_session`

原计划判断正确：`subprocess.CREATE_NEW_CONSOLE` 已有 `os.name == 'nt'` 守卫，POSIX 下不会引用，原代码在 Linux 已可运行。仍建议显式补 else 分支，让子进程脱离终端会话：

```python
kwargs = {}
if os.name == 'nt':
    kwargs['creationflags'] = subprocess.CREATE_NEW_CONSOLE
else:
    kwargs['start_new_session'] = True   # 终端关闭不会杀掉新进程
subprocess.Popen([sys.executable], cwd=get_executable_dir(), **kwargs)
sys.exit(0)
```

#### 2.5 更新 / 回滚提示文案跨平台

- 「手动双击 exe」→ Linux 下改为「重新运行 `jmdownload`」；
- 「将 .old 备份改回原名」→ Linux 下改为「重新运行 `install.sh` 即可恢复」；
- 提示文案按 `os.name` 分支输出。

#### 2.6 明确不需要提权逻辑

因 `~/.jmcomic` 恒为当前用户可写，`apply_update()` 全程**无需 sudo / pkexec / 可写性检测降级**。任何提权相关逻辑均不引入。

### 3. `install.sh` — 安装 / 更新脚本（新增，🟡 补充）

实现「一条命令」安装与更新（脚本幂等、可重复执行）：

- **默认**：从 GitHub Releases 下载当前 Linux 发行版二进制 → `~/.jmcomic/bin/`，下载后校验 sha256（Release 提供时）并 `chmod +x`；
- **`--source`**：源码构建（`pip install -r requirements.txt` + `pyinstaller jmdownload.spec`），产物复制到 `~/.jmcomic/bin/`；
- 首次运行创建 `~/.jmcomic/config/`（放入 `option.yml` 种子）；
- 完成后**不自动改 PATH**，按 `$SHELL` 检测并打印 bash / zsh / fish 对应提示（见「总体设计决策 2」）；
- 该脚本同时即**「一条命令自更新」**的入口。

### 4. `jmdownload.spec` — `upx` 按平台条件化（🟡 体验）

Linux onefile 下建议关闭 UPX：UPX 压缩的 ELF 在部分发行版（启用 seccomp / 加固策略的环境）可能被内核拒绝执行。

**注意**：`jmdownload.spec` 是 Windows / Linux **共用**的同一份文件，直接改成 `upx=False` 会让 Windows 打包产物也失去 UPX 压缩（仅影响体积，不影响功能）。为做到 Windows 零变化，应**按平台条件化**：

```python
upx=(sys.platform != 'linux'),
```

即 Windows 保持 `upx=True` 压缩产物，Linux 关闭 UPX。

### 5. `.gitignore` — 补 Linux 自更新临时产物（🟡）

现有仅忽略 `*.exe.old` / `*.exe.new`，补充 Linux onefile 产生的临时文件：

```gitignore
jmdownload.old
jmdownload.new
jmdownload.swap
```

并按需调整 `tools/` 忽略规则，以纳入 `install.sh`。

### 6. `tests/test_main.py` — 跨平台二进制路径探测（🟡）

`EXE_PATH` 硬编码 `dist/jmdownload.exe`。改为按平台探测：

- `win32` → `dist/jmdownload.exe`
- 其他 → `dist/jmdownload`

（当前实现找不到时会优雅回退源码运行，但变量名与注释应跨平台正确。）

### 7. `README.md` — 文档（🟡）

- 新增「**方式四：Linux 安装**」：安装脚本、`--source` 源码构建、目录布局说明；**将「加入 PATH」作为该方式的最后一步**，分 bash / zsh / fish 三栏给出命令；
- 说明「一条命令自更新」= 重跑 `install.sh` 或 app 内在线自更新（免 sudo）；
- FAQ 更新：Linux 自更新与数据存储位置（`~/.jmcomic`）说明；
- 修正滞后的版本号示例（当前为 v1.4.1）；
- 部分 Windows 专属描述标注「（仅 Windows）」。

### 8. Release 资源命名约定

| 平台 | 可执行文件 | 校验文件 |
|------|-----------|----------|
| Windows | `jmdownload.exe` | `jmdownload.exe.sha256` |
| Linux | `jmdownload` | `jmdownload.sha256` |

未来若分架构发布：`jmdownload-linux-x86_64` / `jmdownload-linux-aarch64`，校验文件同名前缀 + `.sha256`；`_find_assets()` 精确匹配天然支持。

---

## 改动量

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `app/core/env.py` | 新增 `get_data_dir()`；调整 `setup_working_directory()` | 数据目录与二进制目录分离 |
| `app/core/config.py` | 改用 `get_data_dir()` | 外部 config 与 settings 落 `~/.jmcomic` |
| `app/core/history.py` | 改用 `get_data_dir()` | 历史落 `~/.jmcomic` |
| `app/core/updater.py` | 精确匹配二进制名、`chmod +x`、`_safe_replace`、`start_new_session`、跨平台文案 | 自更新全链路 |
| `install.sh`（新增） | 下载/源码构建、sha256 校验、PATH 提示 | 一条命令安装 / 更新 |
| `jmdownload.spec` | `upx` 按平台条件化 | Linux onefile 稳健性，Windows 压缩产物不变 |
| `.gitignore` | 补 Linux 临时产物；调整 `tools/` 忽略 | 防误入库 |
| `tests/test_main.py` | 跨平台二进制路径探测 | 测试正确性 |
| `README.md` | 方式四（含 bash/zsh/fish 三栏 PATH）、FAQ、版本号修正 | 文档 |

---

## 无需改动

- `app/core/downloader.py` / `app/core/menu.py` / `app/core/pdf.py` / `app/ui/prompts.py` — 纯业务逻辑，无平台依赖
- `app/main.py` — 入口无平台差异
- `config/option.yml` — 内容跨平台通用

> 注：原计划的「无需改动」列表包含 `app/core/env.py`，现更正为**需要改动**（见上文第 1 节）。