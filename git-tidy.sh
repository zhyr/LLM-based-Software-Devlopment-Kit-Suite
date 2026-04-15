#!/bin/bash

# --- 配置区 ---
SEARCH_PATH="${1:-.}"  # 默认搜索当前目录
MAX_DEPTH=3            # 查找 Git 仓库的最大深度
LOG_FILE="/tmp/git-tidy.log"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Git Tidy: 通用仓库清理工具 ===${NC}"
echo -e "搜索路径: ${YELLOW}$(realpath "$SEARCH_PATH")${NC}"

# 1. 查找所有 Git 仓库
REPOS=$(find "$SEARCH_PATH" -maxdepth "$MAX_DEPTH" -name ".git" -type d)
REPO_COUNT=$(echo "$REPOS" | grep -c ".git")

if [ "$REPO_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}未发现 Git 仓库，退出。${NC}"
    exit 0
fi

echo -e "发现项目: ${GREEN}${REPO_COUNT}${NC} 个"
echo "-----------------------------------"

# 2. 统计清理前体积
echo -n "正在计算初始体积... "
BEFORE_KB=$(du -sk $REPOS 2>/dev/null | awk '{sum += $1} END {print sum}')
echo -e "${YELLOW}$((BEFORE_KB / 1024)) MB${NC}"

# 3. 循环清理
CURRENT=0
rm -f "$LOG_FILE"

echo -e "开始批量清理 (git gc --aggressive)..."
for repo in $REPOS; do
    CURRENT=$((CURRENT + 1))
    REPO_DIR=$(dirname "$repo")
    REPO_NAME=$(basename "$REPO_DIR")
    
    # 显示进度
    printf "\r[%-20s] %d/%d 正在处理: %-20s" "$(printf '#%.0s' $(seq 1 $((CURRENT * 20 / REPO_COUNT))))" "$CURRENT" "$REPO_COUNT" "$REPO_NAME"
    
    # 执行清理 (后台运行，静默输出到日志)
    (cd "$REPO_DIR" && git gc --prune=now --aggressive >> "$LOG_FILE" 2>&1)
done

echo -e "\n-----------------------------------"

# 4. 统计清理后体积
AFTER_KB=$(du -sk $REPOS 2>/dev/null | awk '{sum += $1} END {print sum}')
SAVED_KB=$((BEFORE_KB - AFTER_KB))

# 5. 输出总结报告
echo -e "${GREEN}清理完成！${NC}"
echo -e "清理后体积: ${YELLOW}$((AFTER_KB / 1024)) MB${NC}"

if [ "$SAVED_KB" -gt 0 ]; then
    echo -e "本次共节省: ${GREEN}$((SAVED_KB / 1024)) MB${NC} ✨"
else
    echo -e "所有项目已是最佳状态，未发现可压缩空间。"
fi

if [ -f "$LOG_FILE" ]; then
    echo -e "${BLUE}详细日志已保存至: $LOG_FILE${NC}"
fi