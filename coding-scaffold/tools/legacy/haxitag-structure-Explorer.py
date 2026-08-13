#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
目录结构扫描工具 (Directory Structure Explorer)

功能说明：
1. 生成指定目录的树形结构图
2. 支持排除特定后缀名文件
3. 支持排除二进制文件
4. 提供文件和目录的统计信息
5. 可配置扫描深度和单目录文件数限制

使用方法：
1. 基本使用（扫描当前目录）：
   python script.py

2. 指定目录扫描：
   python script.py -d /path/to/directory
   或
   python script.py /path/to/directory

3. 排除特定后缀文件：
   python script.py -d /path/to/directory --exclude-ext exe dll pdf

4. 排除二进制文件：
   python script.py -d /path/to/directory --exclude-binary

5. 设置最大深度和单目录文件数限制：
   python script.py -d /path/to/directory --max-depth 5 --max-files 50

输出说明：
1. 在指定目录生成 "{目录名}-目录.txt" 文件
2. 包含完整的目录树形结构
3. 统计信息（总文件数、排除文件数等）
4. 标记超深目录和超大目录
"""

import os
import sys
import fnmatch
import mimetypes

class DirectoryExplorer:
    def __init__(self, root_path, max_depth=10, max_files=100, exclude_extensions=None, exclude_binary=False):
        """
        初始化目录扫描器
        
        参数说明：
        root_path: 起始扫描目录
        max_depth: 最大扫描深度
        max_files: 单个目录最大文件数限制
        exclude_extensions: 要排除的文件后缀列表
        exclude_binary: 是否排除二进制文件
        """
        self.root_path = root_path
        self.max_depth = max_depth
        self.max_files = max_files
        self.exclude_extensions = exclude_extensions or []
        self.exclude_binary = exclude_binary
        self.output = []
        self.deep_directories = set()  # 存储超过最大深度的目录
        self.large_directories = set()  # 存储超过文件数限制的目录
        
        # 统计信息
        self.stats = {
            'total_files': 0,      # 扫描的总文件数
            'excluded_files': 0,   # 被排除的文件数
            'total_dirs': 0,       # 扫描的总目录数
            'excluded_dirs': 0     # 被排除的目录数
        }
        
        # 默认忽略的文件和目录列表
        self.IGNORE_LIST = [
            'node_modules',
            'readme.md',
            '.next',
            '.git',
            '.gitignore',
            '.vscode',
            '.idea',
            '.contentlayer',
            'LICENSE*',
            'file_merger.py',
            'SECURITY.md',
            'CODE_OF_CONDUCT.md',
            '需求说明.md',
            '*-目录.txt',
            'README.md.txt',
            '*/.DS_Store',
            '*.DS_Store',
            '*.log',
            'findIncorrectLinks.js',
            'check-env-permissions.js',
            'posts/*',
            'briefs/*',
            '*/images/*',
            '*/logo/*',
            '.dockerignore',
            'Dockerfile',
            'HaxiTAG- AI-CMS-deployment-guide.md',
            'checkPostsJson.js',
            'scan-link-error.js',
            'check-links.js',
            'feishu-token-generator.js',
            'scan-link-error.js',
            'privacy-policy.md',
            'uploads/*',
            'HaxiTAG-AICMS-173093038046*.txt',
            'AICMS-structure-Explorer.py',
            '.drafts-cache.json',
            '*/node_modules/*',
        ]

    def is_binary_file(self, file_path):
        """
        判断文件是否为二进制文件
        
        判断方法：
        1. 首先通过文件扩展名判断
        2. 如果无法判断，则读取文件内容进行判断
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            return not mime_type.startswith('text/')
        
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' in chunk
        except (IOError, OSError):
            return True

    def should_ignore(self, file_path):
        """
        判断文件或目录是否应该被忽略
        
        判断依据：
        1. 是否在默认忽略列表中
        2. 是否为要排除的扩展名
        3. 是否为二进制文件（当启用二进制排除时）
        """
        # 检查是否在忽略列表中
        for pattern in self.IGNORE_LIST:
            if fnmatch.fnmatch(file_path.lower(), pattern.lower()):
                return True
                
        # 检查文件扩展名
        if self.exclude_extensions:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in self.exclude_extensions:
                self.stats['excluded_files'] += 1
                return True
                
        # 检查是否为二进制文件
        if self.exclude_binary and os.path.isfile(os.path.join(self.root_path, file_path)):
            if self.is_binary_file(os.path.join(self.root_path, file_path)):
                self.stats['excluded_files'] += 1
                return True
                
        return False

    def explore(self):
        """
        开始目录扫描
        生成目录结构并保存到文件
        """
        self.output = [f"/{os.path.basename(self.root_path)}"]
        self._explore_recursive(self.root_path, 0)
        
        dir_name = os.path.basename(self.root_path)
        output_filename = f"{dir_name}-目录.txt"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            # 写入目录结构
            f.write('\n'.join(self.output))
            
            # 写入深度超限目录信息
            if self.deep_directories:
                f.write('\n\n以下目录深度超过限制：\n')
                for dir_path in self.deep_directories:
                    f.write(f"- {dir_path}\n")
            
            # 写入文件数超限目录信息
            if self.large_directories:
                f.write('\n\n以下目录文件数超过限制：\n')
                for dir_path in self.large_directories:
                    f.write(f"- {dir_path}\n")
                    
            # 写入统计信息
            f.write('\n\n扫描统计：\n')
            f.write(f"总文件数: {self.stats['total_files']}\n")
            f.write(f"被排除的文件数: {self.stats['excluded_files']}\n")
            f.write(f"总目录数: {self.stats['total_dirs']}\n")
            f.write(f"被排除的目录数: {self.stats['excluded_dirs']}\n")
        
        # 在控制台显示统计信息
        print(f"目录列表已保存到 {output_filename}")
        print("\n扫描统计：")
        print(f"总文件数: {self.stats['total_files']}")
        print(f"被排除的文件数: {self.stats['excluded_files']}")
        print(f"总目录数: {self.stats['total_dirs']}")
        print(f"被排除的目录数: {self.stats['excluded_dirs']}")

    def _explore_recursive(self, current_path, depth):
        """
        递归扫描目录
        
        参数：
        current_path: 当前扫描的路径
        depth: 当前深度
        """
        if depth > self.max_depth:
            self.deep_directories.add(current_path)
            return

        try:
            items = sorted(os.listdir(current_path))
        except PermissionError:
            return

        if len(items) > self.max_files:
            self.large_directories.add(current_path)

        prefix = '│   ' * depth
        for i, item in enumerate(items):
            item_path = os.path.join(current_path, item)
            relative_item_path = os.path.relpath(item_path, self.root_path)
            
            is_dir = os.path.isdir(item_path)
            if is_dir:
                self.stats['total_dirs'] += 1
            else:
                self.stats['total_files'] += 1
            
            if self.should_ignore(relative_item_path):
                if is_dir:
                    self.stats['excluded_dirs'] += 1
                continue

            is_last = (i == len(items) - 1)
            branch = '└── ' if is_last else '├── '

            if is_dir:
                self.output.append(f"{prefix}{branch}{item}/")
                self._explore_recursive(item_path, depth + 1)
            else:
                self.output.append(f"{prefix}{branch}{item}")

            if is_last and depth > 0:
                self.output.append(f"{prefix}")

def main():
    """
    主函数：处理命令行参数并启动扫描
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='目录结构扫描工具')
    # 支持 -d 和位置参数两种方式指定目录
    parser.add_argument('-d', '--directory', dest='path', 
                      help='起始目录路径')
    parser.add_argument('default_path', nargs='?', default=None,
                      help='起始目录路径（位置参数方式）')
    parser.add_argument('--exclude-ext', nargs='*', 
                      help='要排除的文件扩展名 (例如: .exe .dll)')
    parser.add_argument('--exclude-binary', action='store_true',
                      help='排除二进制文件')
    parser.add_argument('--max-depth', type=int, default=10,
                      help='最大目录深度 (默认: 10)')
    parser.add_argument('--max-files', type=int, default=100,
                      help='单个目录最大文件数 (默认: 100)')
    
    args = parser.parse_args()
    
    # 确定实际使用的路径
    path = args.path or args.default_path or os.getcwd()
    
    # 处理扩展名列表
    exclude_extensions = args.exclude_ext if args.exclude_ext else []
    exclude_extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in exclude_extensions]
    
    # 创建扫描器并执行扫描
    explorer = DirectoryExplorer(
        path,
        max_depth=args.max_depth,
        max_files=args.max_files,
        exclude_extensions=exclude_extensions,
        exclude_binary=args.exclude_binary
    )
    explorer.explore()

if __name__ == "__main__":
    main()