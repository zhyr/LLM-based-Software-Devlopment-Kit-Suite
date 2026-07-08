# 预览（推荐先跑）
~/Documents/disk_maintenance.sh --dry-run --yes

# 默认：全局 + work
~/Documents/disk_maintenance.sh --yes

# 仅工作区
~/Documents/disk_maintenance.sh --work-only --yes

# 多工作区根目录
WORK_ROOTS="$HOME/work $HOME/projects" ~/Documents/disk_maintenance.sh --work-only --yes

# 额外选项
~/Documents/disk_maintenance.sh --docker --vacuum-cursor --yes

# 日常使用和清理
~/Documents/disk_maintenance.sh --dry-run --yes   # 先预览
~/Documents/disk_maintenance.sh --yes             # 再正式清理