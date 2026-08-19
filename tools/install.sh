#!/usr/bin/env bash
# EZ-JMComic-Downloader 安装 / 更新脚本（Linux/macOS）
#
# 用法:
#   ./install.sh           从 GitHub Releases 下载最新发行版并安装；
#                           若 Release 暂未提供 Linux 预编译二进制，会自动回退为源码构建
#   ./install.sh --source  强制拉取源码本地构建并安装（需 git 与 Python 3.10+；
#                           构建在临时 venv 中进行，不污染系统 Python）
#   ./install.sh --help    显示帮助
#
# 设计:
#   - 二进制与数据统一放 ~/.jmcomic（bin/、config/、历史、下载），免 sudo；
#   - 脚本不自动修改 PATH，安装完成后按当前 shell 打印加入 PATH 的命令；
#   - 下载带单行进度条与断点续传（中断后重跑接着下），404 与网络错误区分提示；
#   - 幂等可重复执行，重跑即更新到最新版（"一条命令自更新"）。

set -euo pipefail

REPO="Sky-pace/EZ-JMComic-Downloader"
DATA_DIR="${HOME}/.jmcomic"
BIN_DIR="${DATA_DIR}/bin"
CONFIG_DIR="${DATA_DIR}/config"
BIN_NAME="jmdownload"
BIN_PATH="${BIN_DIR}/${BIN_NAME}"
DOWNLOAD_BASE="https://github.com/${REPO}/releases/latest/download"

# ---------- 工具函数 ----------
info() { printf '\033[1;34m[INFO]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[ OK ]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[WARN]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[FAIL]\033[0m %s\n' "$*" >&2; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

# 下载函数：优先 curl，回退 wget；单行进度条 + 断点续传（网络中断时重试接着下）
# 返回码约定：0=成功；22(curl) / 8(wget) = HTTP 错误（如 404 资源不存在）；33(curl) = 续传偏移无效；其他 = 网络错误
download() {
    local url="$1" dest="$2"
    if have curl; then
        # -f 让 HTTP 错误返回 22；-C - 断点续传；--retry-all-errors 网络错误也重试
        curl -fL --progress-bar -C - --retry 3 --retry-all-errors --connect-timeout 15 -o "$dest" "$url"
    elif have wget; then
        wget --show-progress -q -c --tries=3 -O "$dest" "$url"
    else
        die "需要 curl 或 wget 才能下载，请先安装其一"
    fi
}

# 源码构建：clone 仓库 + 临时 venv 安装依赖 + PyInstaller 打包
build_from_source() {
    info "源码构建模式：拉取仓库并本地打包（需 git、Python 3.10+）..."
    for cmd in git python3; do
        have "$cmd" || die "源码构建需要 $cmd，请先安装"
    done
    # 代码使用了 3.10+ 语法（X | None 类型注解），低版本 python3 会在 import 时直接报错
    python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
        || die "源码构建需要 Python 3.10+（当前：$(python3 --version 2>&1)）"
    BUILD_DIR="$(mktemp -d)"
    git clone --depth 1 "https://github.com/${REPO}.git" "$BUILD_DIR"
    # 在临时 venv 中构建：规避新版发行版的 PEP 668 限制（externally-managed-environment），
    # 且不污染系统 Python；构建产物拷出后随临时目录一并清理
    python3 -m venv "$BUILD_DIR/.venv" \
        || die "创建虚拟环境失败（Debian/Ubuntu 需先安装 python3-venv）"
    ( cd "$BUILD_DIR" \
        && ./.venv/bin/python -m pip install -q -r requirements.txt \
        && ./.venv/bin/python -m PyInstaller jmdownload.spec --noconfirm )
    cp "$BUILD_DIR/dist/${BIN_NAME}" "$TMP_FILE"
    ok "源码构建完成"
}

# 计算文件 sha256
sha256_of() {
    if have sha256sum; then
        sha256sum "$1" | awk '{print $1}'
    elif have shasum; then
        shasum -a 256 "$1" | awk '{print $1}'
    else
        die "需要 sha256sum 或 shasum 进行校验"
    fi
}

# ---------- 参数解析 ----------
MODE="release"
case "${1:-}" in
    --source) MODE="source" ;;
    --help|-h)
        echo "用法:"
        echo "  ./install.sh           从 GitHub Releases 下载最新发行版并安装；若无预编译二进制则自动源码构建"
        echo "  ./install.sh --source  强制源码本地构建并安装（需 git 与 Python 3.10+，构建在临时 venv 中进行）"
        echo "  ./install.sh --help    显示帮助"
        exit 0
        ;;
    "") ;;
    *) die "未知参数: $1（可用 --source 或 --help）" ;;
esac

# ---------- 准备目录 ----------
mkdir -p "$BIN_DIR" "$CONFIG_DIR"

# ---------- 获取二进制 ----------
# 下载临时文件用固定路径：网络中断后重跑本脚本可断点续传（安装成功后才清理）
TMP_FILE="${BIN_DIR}/.${BIN_NAME}.part"
BUILD_DIR=""
SUCCESS=0
cleanup() {
    [ "$SUCCESS" = 1 ] && rm -f "$TMP_FILE" "$TMP_FILE.sha256"
    [ -n "$BUILD_DIR" ] && rm -rf "$BUILD_DIR"
    return 0
}
trap cleanup EXIT

if [ "$MODE" = "source" ]; then
    build_from_source
else
    info "从 GitHub Releases 下载最新版..."
    if [ -s "$TMP_FILE" ]; then
        info "检测到上次未完成的下载，将断点续传"
    fi
    rc=0
    download "${DOWNLOAD_BASE}/${BIN_NAME}" "$TMP_FILE" || rc=$?
    if [ "$rc" -eq 33 ]; then
        # 续传偏移无效：本地残留比新版本还大（旧版本残留），删除后完整重下
        warn "续传偏移无效（疑似旧版本残留），已删除残留并重新完整下载..."
        rm -f "$TMP_FILE"
        rc=0
        download "${DOWNLOAD_BASE}/${BIN_NAME}" "$TMP_FILE" || rc=$?
    fi
    if [ "$rc" -eq 22 ] || [ "$rc" -eq 8 ]; then
        # HTTP 错误（404）：Release 确实没有 Linux 预编译二进制，走源码构建
        rm -f "$TMP_FILE"
        warn "Release 暂未提供 Linux 预编译二进制，自动切换为源码构建..."
        build_from_source
    elif [ "$rc" -ne 0 ]; then
        die "下载中断（网络错误，退出码 $rc）：无法稳定访问 GitHub 或其 CDN（release-assets.githubusercontent.com）。
  - 已下载部分已保留，网络恢复后重跑本脚本可断点续传
  - 也可检查网络/代理后重试，或改用源码构建：bash install.sh --source"
    else
        ok "下载完成"
        # 校验 sha256（Release 提供校验文件时）
        rm -f "$TMP_FILE.sha256"
        if download "${DOWNLOAD_BASE}/${BIN_NAME}.sha256" "$TMP_FILE.sha256" 2>/dev/null; then
            expected="$(awk '{print $1}' "$TMP_FILE.sha256")"
            actual="$(sha256_of "$TMP_FILE")"
            if [ "$expected" != "$actual" ]; then
                rm -f "$TMP_FILE"
                die "sha256 校验失败（可能是续传拼接了旧版本残留）。残留已删除，请重跑本脚本完整下载"
            fi
            ok "sha256 校验通过"
        else
            warn "未找到校验文件，跳过 sha256 校验"
        fi
    fi
fi

# ---------- 安装 ----------
chmod +x "$TMP_FILE"
mv -f "$TMP_FILE" "$BIN_PATH"
SUCCESS=1
ok "已安装到 ${BIN_PATH}"

# ---------- PATH 提示（不自动修改） ----------
echo
info "安装完成。请将程序加入 PATH 以便在终端直接使用："
case "${SHELL:-}" in
    */fish)
        echo '  fish_add_path "$HOME/.jmcomic/bin"'
        echo '  （或写入 ~/.config/fish/config.fish：）'
        echo '  if not contains "$HOME/.jmcomic/bin" "$PATH"; set -p PATH "$HOME/.jmcomic/bin"; end'
        ;;
    */zsh)
        echo '  echo '\''export PATH="$HOME/.jmcomic/bin:$PATH"'\'' >> ~/.zshrc'
        echo '  source ~/.zshrc'
        ;;
    *)
        echo '  echo '\''export PATH="$HOME/.jmcomic/bin:$PATH"'\'' >> ~/.bashrc'
        echo '  source ~/.bashrc'
        ;;
esac
echo
info "数据目录：${DATA_DIR}（历史、配置、默认下载均在此）"
info "更新到最新版：重新运行本脚本即可（一条命令自更新）"