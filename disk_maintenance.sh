#!/usr/bin/env bash
# =============================================================================
# disk_maintenance.sh — 开发者通用磁盘清理工具 (v4)
#
# 目标：安全清理开发/编译/测试产生的临时与冗余文件，不破坏环境与配置。
#
# 用法:
#   ./disk_maintenance.sh                  # 默认：全局轻量 + work 项目缓存
#   ./disk_maintenance.sh --dry-run        # 仅预览，不删除
#   ./disk_maintenance.sh --work-only      # 仅清理工作区
#   ./disk_maintenance.sh --global-only    # 仅清理全局工具缓存
#   ./disk_maintenance.sh --include-release # 同时清理 Rust target/release
#   ./disk_maintenance.sh --include-root-dist # 清理仓库根 dist（仍跳过含 .dmg/.pkg 的目录）
#   ./disk_maintenance.sh --docker         # 额外执行 docker/orbstack prune
#   ./disk_maintenance.sh --vacuum-cursor  # 压缩 Cursor state.vscdb（需退出 Cursor）
#   ./disk_maintenance.sh --yes            # 跳过确认
#
# 环境变量:
#   WORK_ROOTS   空格分隔的工作区根目录，默认: "$HOME/work"
#   DRY_RUN=1    等同 --dry-run
#
# 默认绝不删除:
#   node_modules, .git, .env*, venv/.venv, vendor, data/, 含 .dmg/.pkg/.app 的 dist
#   target/release（除非 --include-release）
# =============================================================================

set -euo pipefail

VERSION="4.0.0"
DRY_RUN="${DRY_RUN:-0}"
WORK_ONLY=0
GLOBAL_ONLY=0
INCLUDE_RELEASE=0
INCLUDE_ROOT_DIST=0
DOCKER_PRUNE=0
VACUUM_CURSOR=0
ASSUME_YES=0
FREED_KB=0

WORK_ROOTS="${WORK_ROOTS:-$HOME/work}"

# -----------------------------------------------------------------------------
# 日志与工具
# -----------------------------------------------------------------------------
log()  { printf '%s\n' "$*"; }
info() { log "ℹ️  $*"; }
ok()   { log "✅ $*"; }
warn() { log "⚠️  $*"; }
skip() { log "⏭  $*"; }

disk_report() {
  local label="${1:-磁盘}"
  if df -h /System/Volumes/Data &>/dev/null; then
    log "📊 ${label}: $(df -h /System/Volumes/Data | awk 'NR==2 {print $4 " 可用 / " $2 " 总计 (" $5 " 已用)"}')"
  elif df -h "$HOME" &>/dev/null; then
    log "📊 ${label}: $(df -h "$HOME" | awk 'NR==2 {print $4 " 可用 / " $2 " 总计 (" $5 " 已用)"}')"
  fi
}

kb_of() {
  du -sk "$1" 2>/dev/null | awk '{print $1}' || echo 0
}

safe_rm() {
  local path="$1"
  local reason="${2:-}"
  [[ -e "$path" ]] || return 0

  if should_skip_path "$path"; then
    skip "保护路径，跳过: $path"
    return 0
  fi

  local kb
  kb=$(kb_of "$path")
  if [[ "$DRY_RUN" == "1" ]]; then
    log "🔍 [dry-run] 将删除 (${kb}KB) ${reason:+$reason: }$path"
    FREED_KB=$((FREED_KB + kb))
    return 0
  fi

  rm -rf "$path" 2>/dev/null || {
    warn "删除失败: $path"
    return 0
  }
  FREED_KB=$((FREED_KB + kb))
  log "🗑  已删除 (${kb}KB) ${reason:+$reason: }$path"
}

# 路径是否应保护（任意祖先或自身命中即跳过）
should_skip_path() {
  local p="$1"
  # 规范化：去掉末尾 /
  p="${p%/}"

  case "$p" in
    *"/node_modules"*|*"/node_modules/"*|*"/.git"*|*"/.git/"*) return 0 ;;
    *"/.env"*|*"/.env."*|*"/venv"*|*"/.venv"*|*"/vendor"*|*"/vendor/"*) return 0 ;;
    *"/data"*|*"/data/"*) return 0 ;;
    *"/.cargo/bin"*|*"/.cargo/registry/src"*) return 0 ;;
  esac

  # 保护含发布制品的 dist
  if [[ "$p" == *"/dist" ]] || [[ "$p" == *"/dist/"* ]]; then
    if has_release_artifacts "$p"; then
      return 0
    fi
  fi

  return 1
}

has_release_artifacts() {
  local dir="$1"
  [[ -d "$dir" ]] || return 1
  find "$dir" -maxdepth 3 \( -name '*.dmg' -o -name '*.pkg' -o -name '*.app' -o -name '*.tar.gz' -o -name '*.zip' \) \
    -print -quit 2>/dev/null | grep -q .
}

build_find_prune() {
  : # 见 find_work — 使用内联 prune 表达式
}

# 在工作区内 find，自动跳过 node_modules / .git / data 等
find_work() {
  local root="$1"
  shift
  # shellcheck disable=SC2068
  find "$root" \( \
    -name node_modules -o -name .git -o -name venv -o -name .venv \
    -o -name vendor -o -name data -o -name .cargo \
  \) -prune -o $@ -print 2>/dev/null
}

# 避免管道子 shell 导致 FREED_KB 统计丢失
foreach_path() {
  local reason="$1"
  shift
  while IFS= read -r path; do
    [[ -n "$path" ]] && safe_rm "$path" "$reason"
  done < <( "$@" 2>/dev/null )
}

# -----------------------------------------------------------------------------
# 工作区：合并扫描，减少重复遍历
# -----------------------------------------------------------------------------
clean_work_tree() {
  local root="$1"
  [[ -d "$root" ]] || return 0

  # 1) 通用临时目录（单次 find；跳过 target/ 内条目，由 rust-target 步骤处理）
  foreach_path "cache-dir" find_work "$root" -type d ! -path '*/target/*' \( \
    -name .next -o -name out -o -name .turbo -o -name .parcel-cache -o -name .nuxt -o -name .output \
    -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache -o -name .tox \
    -o -name coverage -o -name htmlcov -o -name .nyc_output \
    -o -name test-results -o -name playwright-report -o -name playwright-browsers \
    -o -name .playwright-mcp -o -name .npm-cache -o -name .forge-e2e-works \
    -o -name .vite -o -name .swc -o -name __pycache__ \
  \)

  # 2) tsbuildinfo
  foreach_path "tsbuildinfo" find_work "$root" -type f \( -name 'tsconfig.tsbuildinfo' -o -name '*.tsbuildinfo' \)

  # 3) Rust target（默认仅 debug）
  while IFS= read -r target_dir; do
    [[ -n "$target_dir" ]] || continue
    safe_rm "$target_dir/debug" "rust-target-debug"
    safe_rm "$target_dir/tmp" "rust-target-tmp"
  done < <(find_work "$root" -type d -name target)
  if [[ "$INCLUDE_RELEASE" == "1" ]]; then
    while IFS= read -r target_dir; do
      safe_rm "$target_dir/release" "rust-target-release"
    done < <(find_work "$root" -type d -name target)
  fi

  # 4) Electron staging
  foreach_path "electron-staging" find_work "$root" -type d -name electron-staging

  while IFS= read -r build_dir; do
    [[ -n "$build_dir" ]] || continue
    if [[ -d "$build_dir/electron-staging" ]] || [[ -d "$build_dir/test-state" ]]; then
      safe_rm "$build_dir/electron-staging" "build-staging"
      safe_rm "$build_dir/test-state" "build-test-state"
    fi
  done < <(find_work "$root" -type d -name build)

  while IFS= read -r rel_dir; do
    [[ -n "$rel_dir" ]] || continue
    if find "$rel_dir" -maxdepth 3 \( -name '*.blockmap' -o -name 'builder-debug.yml' -o -name 'builder-effective-config.yaml' \) -print -quit 2>/dev/null | grep -q .; then
      safe_rm "$rel_dir" "electron-release-artifacts"
    fi
  done < <(find_work "$root" -type d -name release)

  # 5) 嵌套 dist（apps/*/dist 等）
  local nested dir
  for nested in \
    "$root"/*/apps/*/dist \
    "$root"/*/packages/*/dist \
    "$root"/*/frontend/dist \
    "$root"/*/web/dist \
    "$root"/*/client/dist \
    "$root"/*/*/apps/*/dist \
    "$root"/*/*/frontend/dist \
    ; do
    for dir in $nested; do
      [[ -d "$dir" ]] || continue
      should_skip_path "$dir" && continue
      safe_rm "$dir" "nested-dist"
    done
  done
  if [[ "$INCLUDE_ROOT_DIST" == "1" ]]; then
    while IFS= read -r dir; do
      should_skip_path "$dir" && continue
      safe_rm "$dir" "root-dist"
    done < <(find_work "$root" -type d -name dist)
  fi

  # 6) 项目 logs（仅 .log 文件）
  while IFS= read -r dir; do
    [[ -n "$dir" ]] || continue
    case "$dir" in */data/logs|*/data/logs/*) continue ;; esac
    while IFS= read -r f; do
      safe_rm "$f" "log-file"
    done < <(find "$dir" -type f \( -name '*.log' -o -name '*.log.*' \) 2>/dev/null)
  done < <(find_work "$root" -type d -name logs)

  # 7) server/outputs 与根目录测试截图
  while IFS= read -r dir; do
    [[ "$dir" == */server/outputs ]] && safe_rm "$dir" "server-outputs"
  done < <(find_work "$root" -type d -name outputs)

  foreach_path "test-screenshot" find "$root" -maxdepth 2 -type f -name 'test-result*.png'
}

clean_work_trees() {
  info "工作区项目缓存: $WORK_ROOTS"
  for root in $WORK_ROOTS; do
    [[ -d "$root" ]] || { warn "目录不存在，跳过: $root"; continue; }
    log "── 扫描: $root"
    clean_work_tree "$root"
  done
  ok "工作区清理完成"
}

# 以下旧函数已由 clean_work_tree 合并
clean_work_named_dirs() { clean_work_tree "$1"; }

# -----------------------------------------------------------------------------
# 参数解析
# -----------------------------------------------------------------------------
usage() {
  sed -n '3,22p' "$0" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)          DRY_RUN=1 ;;
    --work-only)        WORK_ONLY=1 ;;
    --global-only)      GLOBAL_ONLY=1 ;;
    --include-release)  INCLUDE_RELEASE=1 ;;
    --include-root-dist) INCLUDE_ROOT_DIST=1 ;;
    --docker)           DOCKER_PRUNE=1 ;;
    --vacuum-cursor)    VACUUM_CURSOR=1 ;;
    --yes|-y)           ASSUME_YES=1 ;;
    --help|-h)          usage; exit 0 ;;
    *)                  warn "未知参数: $1"; usage; exit 1 ;;
  esac
  shift
done

if [[ "$WORK_ONLY" == "1" && "$GLOBAL_ONLY" == "1" ]]; then
  warn "不能同时指定 --work-only 与 --global-only"
  exit 1
fi

RUN_GLOBAL=1
RUN_WORK=1
[[ "$WORK_ONLY" == "1" ]] && RUN_GLOBAL=0
[[ "$GLOBAL_ONLY" == "1" ]] && RUN_WORK=0

# -----------------------------------------------------------------------------
# 全局：Gradle / npm / Cargo 下载缓存
# -----------------------------------------------------------------------------
clean_global_gradle() {
  info "Gradle 缓存（保留 wrapper 与已安装发行版）..."
  if [[ ! -d "$HOME/.gradle" ]]; then skip "未找到 ~/.gradle"; return; fi
  pkill -f GradleDaemon 2>/dev/null || true
  for pattern in "caches/build-cache-*" "caches/*/files-*" "caches/journal-*" "caches/transforms-*"; do
    for p in "$HOME/.gradle"/$pattern; do
      [[ -e "$p" ]] || continue
      safe_rm "$p" "gradle"
    done
  done
  find "$HOME/.gradle/daemon" -name "*.log" -delete 2>/dev/null || true
  ok "Gradle 缓存处理完成"
}

clean_global_npm() {
  info "npm 全局缓存（不影响 node_modules，重装依赖时自动拉取）..."
  if command -v npm &>/dev/null; then
    if [[ "$DRY_RUN" == "1" ]]; then
      local kb; kb=$(kb_of "$HOME/.npm")
      log "🔍 [dry-run] npm cache clean --force (~${kb}KB ~/.npm)"
      FREED_KB=$((FREED_KB + kb))
    else
      npm cache clean --force 2>/dev/null || true
      safe_rm "$HOME/.npm/_logs" "npm-logs"
    fi
    ok "npm 缓存处理完成"
  else
    skip "未找到 npm"
  fi
}

clean_global_cargo() {
  info "Cargo registry 下载缓存（保留 ~/.cargo/registry/src 与 ~/.cargo/bin）..."
  safe_rm "$HOME/.cargo/registry/cache" "cargo-registry-cache"
  ok "Cargo 缓存处理完成"
}

clean_global_pip() {
  info "pip 缓存..."
  if command -v pip3 &>/dev/null; then
    if [[ "$DRY_RUN" == "1" ]]; then
      local cache_dir
      cache_dir=$(pip3 cache dir 2>/dev/null || echo "")
      if [[ -n "$cache_dir" && -d "$cache_dir" ]]; then
        local kb; kb=$(kb_of "$cache_dir")
        log "🔍 [dry-run] pip cache purge (~${kb}KB)"
        FREED_KB=$((FREED_KB + kb))
      fi
    else
      pip3 cache purge 2>/dev/null || true
    fi
    ok "pip 缓存处理完成"
  else
    skip "未找到 pip3"
  fi
}

clean_global_homebrew() {
  info "Homebrew 缓存..."
  if command -v brew &>/dev/null; then
    if [[ "$DRY_RUN" == "1" ]]; then
      log "🔍 [dry-run] brew cleanup -s"
    else
      brew cleanup -s 2>/dev/null || true
    fi
    ok "Homebrew 缓存处理完成"
  else
    skip "未找到 brew"
  fi
}

# -----------------------------------------------------------------------------
# 全局：IDE / 编辑器
# -----------------------------------------------------------------------------
clean_cursor() {
  info "Cursor 临时文件与历史备份..."
  local cursor_dir=""
  case "$(uname -s)" in
    Darwin) cursor_dir="$HOME/Library/Application Support/Cursor" ;;
    Linux)  cursor_dir="${XDG_CONFIG_HOME:-$HOME/.config}/Cursor" ;;
  esac
  [[ -n "$cursor_dir" && -d "$cursor_dir" ]] || { skip "未找到 Cursor 目录"; return; }

  while IFS= read -r dir; do
    safe_rm "$dir" "cursor-backup"
  done < <(find "$cursor_dir/User" -maxdepth 1 -type d -name 'globalStorage_backup_*' 2>/dev/null)

  for sub in logs CachedData Partitions; do
    if [[ -d "$cursor_dir/$sub" ]]; then
      while IFS= read -r item; do
        safe_rm "$item" "cursor-$sub"
      done < <(find "$cursor_dir/$sub" -mindepth 1 -maxdepth 1 2>/dev/null)
    fi
  done

  # Cursor Agent / 沙箱 cargo 缓存（常见位置）
  for sandbox in \
    "$TMPDIR/cursor-sandbox-cache" \
    /var/folders/*/*/T/cursor-sandbox-cache \
    "$HOME/.cursor/sandbox-cache" \
    ; do
    for p in $sandbox; do
      [[ -d "$p" ]] && safe_rm "$p" "cursor-sandbox"
    done
  done

  if [[ "$VACUUM_CURSOR" == "1" ]]; then
    local vscdb="$cursor_dir/User/globalStorage/state.vscdb"
    if [[ -f "$vscdb" ]]; then
      if pgrep -x "Cursor" >/dev/null 2>&1; then
        warn "Cursor 运行中，跳过 VACUUM（请先退出 Cursor）"
      elif [[ "$DRY_RUN" == "1" ]]; then
        log "🔍 [dry-run] sqlite3 VACUUM $vscdb"
      else
        sqlite3 "$vscdb" "VACUUM;" 2>/dev/null && safe_rm "${vscdb}.backup" "cursor-vscdb-backup"
        ok "state.vscdb 已压缩"
      fi
    fi
  fi

  ok "Cursor 清理完成"
}

clean_vscode() {
  info "VS Code 日志与 CachedData..."
  local code_dir=""
  case "$(uname -s)" in
    Darwin) code_dir="$HOME/Library/Application Support/Code" ;;
    Linux)  code_dir="${XDG_CONFIG_HOME:-$HOME/.config}/Code" ;;
  esac
  [[ -d "$code_dir" ]] || { skip "未找到 VS Code"; return; }
  for sub in logs CachedData; do
    [[ -d "$code_dir/$sub" ]] || continue
    while IFS= read -r item; do
      safe_rm "$item" "vscode-$sub"
    done < <(find "$code_dir/$sub" -mindepth 1 -maxdepth 1 2>/dev/null)
  done
  ok "VS Code 清理完成"
}

# -----------------------------------------------------------------------------
# 全局：Xcode / iOS 模拟器（仅 macOS）
# -----------------------------------------------------------------------------
clean_xcode() {
  [[ "$(uname -s)" == "Darwin" ]] || { skip "非 macOS，跳过 Xcode"; return; }
  info "Xcode DerivedData 与不可用模拟器..."
  if [[ -d "$HOME/Library/Developer/Xcode/DerivedData" ]]; then
    while IFS= read -r item; do
      safe_rm "$item" "xcode-deriveddata"
    done < <(find "$HOME/Library/Developer/Xcode/DerivedData" -mindepth 1 -maxdepth 1 2>/dev/null)
  fi
  if [[ "$DRY_RUN" != "1" ]]; then
    xcrun simctl delete unavailable 2>/dev/null || true
  else
    log "🔍 [dry-run] xcrun simctl delete unavailable"
  fi
  safe_rm "$HOME/Library/Logs/CoreSimulator" "simulator-logs"
  if [[ -d "$HOME/Library/Developer/CoreSimulator/Caches" ]]; then
    while IFS= read -r item; do
      safe_rm "$item" "simulator-cache"
    done < <(find "$HOME/Library/Developer/CoreSimulator/Caches" -mindepth 1 2>/dev/null)
  fi
  ok "Xcode / 模拟器缓存处理完成"
}

# -----------------------------------------------------------------------------
# 全局：Docker / OrbStack
# -----------------------------------------------------------------------------
clean_docker() {
  info "Docker / OrbStack 未使用镜像与构建缓存..."
  if [[ "$DRY_RUN" == "1" ]]; then
    log "🔍 [dry-run] docker system prune -f"
    command -v orb &>/dev/null && log "🔍 [dry-run] orb docker system prune -f"
    return
  fi
  docker system prune -f 2>/dev/null || true
  orb docker system prune -f 2>/dev/null || true
  ok "Docker 清理完成"
}

# -----------------------------------------------------------------------------
# 废纸篓（可选，默认关闭 — 易误删）
# -----------------------------------------------------------------------------
clean_trash() {
  [[ "${EMPTY_TRASH:-0}" == "1" ]] || return 0
  info "清空废纸篓..."
  if [[ "$(uname -s)" == "Darwin" && -d "$HOME/.Trash" ]]; then
    while IFS= read -r item; do
      safe_rm "$item" "trash-item"
    done < <(find "$HOME/.Trash" -mindepth 1 -maxdepth 1 2>/dev/null)
  fi
}

# -----------------------------------------------------------------------------
# 主流程
# -----------------------------------------------------------------------------
main() {
  log "=============================="
  log "🧹 开发者磁盘清理 v${VERSION}"
  [[ "$DRY_RUN" == "1" ]] && warn "DRY-RUN 模式：不会实际删除文件"
  log "=============================="
  disk_report "清理前"
  log ""

  if [[ "$ASSUME_YES" != "1" && "$DRY_RUN" != "1" ]]; then
  read -r -p "确认执行清理？[y/N] " ans
  case "$ans" in
    y|Y|yes|YES) ;;
    *) log "已取消"; exit 0 ;;
  esac
  fi

  if [[ "$RUN_GLOBAL" == "1" ]]; then
    log "── 全局工具缓存 ──"
    clean_global_gradle
    clean_global_npm
    clean_global_cargo
    clean_global_pip
    clean_global_homebrew
    clean_cursor
    clean_vscode
    clean_xcode
    [[ "$DOCKER_PRUNE" == "1" ]] && clean_docker
    log ""
  fi

  if [[ "$RUN_WORK" == "1" ]]; then
    log "── 工作区项目缓存 ──"
    clean_work_trees
    log ""
  fi

  clean_trash

  log ""
  disk_report "清理后"
  local freed_mb=$((FREED_KB / 1024))
  log "=============================="
  if [[ "$DRY_RUN" == "1" ]]; then
    log "🔍 预览完成，预计可释放约 ${freed_mb} MB（实际可能因嵌套略有偏差）"
  else
    ok "清理完成，约释放 ${freed_mb} MB"
  fi
  log "=============================="
  log ""
  log "保留项: node_modules, .env, data/, venv, target/release(默认), 含 .dmg 的 dist"
  log "可选: --include-release  --include-root-dist  --docker  --vacuum-cursor  --dry-run"
}

main "$@"
