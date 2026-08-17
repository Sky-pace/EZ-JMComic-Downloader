#!/usr/bin/env bash
# EZ-JMComic-Downloader 安装 / 更新脚本（Linux/macOS）
#
# 用法:
#   ./install.sh           从 GitHub Releases 下载最新发行版并安装；
#                           若 Release 暂未提供 Linux 预编译二进制，会自动回退为源码构建
#   ./install.sh --source  强制拉取源码本地构建并安装（需 git、Python 3.13+ 与 pip）
#   ./install.sh --help    显示帮助
#
# 设计:
#   - 二进制与数据统一放 ~/.jmcomic（bin/、config/、历史、下载），免 sudo；
#   - 脚本不自动修改 PATH，安装完成后按当前 shell 打印加入 PATH 的命令；
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

# 下载函数：优先 curl，回退 wget；下载失败时返回非零（不直接退出，交由调用方决定）
download() {
    local url="$1" dest="$2"
    if have curl; then
        curl -fsSL --retry 3 -o "$dest" "$url"
    elif have wget; then
        wget -qO "$dest" "$url"
    else
        die "需要 curl 或 wget 才能下载，请先安装其一"
    fi
}

# 源码构建：clone 仓库 + 安装依赖 + PyInstaller 打包
build_from_source() {
    info "源码构建模式：拉取仓库并本地打包（需 git、Python 3.13+）..."
    for cmd in git python3; do
        have "$cmd" || die "源码构建需要 $cmd，请先安装"
    done
    python3 -m pip --version >/dev/null 2>&1 || die "源码构建需要 pip（python3 -m pip）"
    BUILD_DIR="$(mktemp -d)"
    git clone --depth 1 "https://github.com/${REPO}.git" "$BUILD_DIR"
    ( cd "$BUILD_DIR" \
        && python3 -m pip install -r requirements.txt pyinstaller \
        && python3 -m PyInstaller jmdownload.spec --noconfirm )
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
        echo "  ./install.sh --source  强制源码本地构建并安装（需 git、Python 3.13+ 与 pip）"
        echo "  ./install.sh --help    显示帮助"
        exit 0
        ;;
    "") ;;
    *) die "未知参数: $1（可用 --source 或 --help）" ;;
esac

# ---------- 准备目录 ----------
mkdir -p "$BIN_DIR" "$CONFIG_DIR"

# ---------- 获取二进制 ----------
TMP_FILE="$(mktemp)"
BUILD_DIR=""
cleanup() {
    rm -f "$TMP_FILE" "$TMP_FILE.sha256"
    [ -n "$BUILD_DIR" ] && rm -rf "$BUILD_DIR"
}
trap cleanup EXIT

if [ "$MODE" = "source" ]; then
    build_from_source
else
    info "从 GitHub Releases 下载最新版..."
    if ! download "${DOWNLOAD_BASE}/${BIN_NAME}" "$TMP_FILE"; then
        warn "Release 暂未提供 Linux 预编译二进制，自动切换为源码构建..."
        build_from_source
    else
        # 校验 sha256（Release 提供校验文件时）
        if download "${DOWNLOAD_BASE}/${BIN_NAME}.sha256" "$TMP_FILE.sha256" 2>/dev/null; then
            expected="$(awk '{print $1}' "$TMP_FILE.sha256")"
            actual="$(sha256_of "$TMP_FILE")"
            [ "$expected" = "$actual" ] || die "sha256 校验失败，已中止安装"
            ok "sha256 校验通过"
        else
            warn "未找到校验文件，跳过 sha256 校验"
        fi
    fi
fi

# ---------- 安装 ----------
chmod +x "$TMP_FILE"
mv -f "$TMP_FILE" "$BIN_PATH"
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