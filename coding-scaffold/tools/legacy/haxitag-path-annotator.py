#!/usr/bin/env python3
"""
File Path Annotator (haxitag-path-annotator.py)
=============================================

This script adds or updates path annotations at the beginning of source code files.
It helps maintain clear file location information within a project's structure.

Supported file types:
    - Python (.py)   - Uses "# " prefix
    - TypeScript (.ts, .tsx) - Uses "// " prefix

Usage:
------
1. Process current directory (uses script directory as root):
    python haxitag-path-annotator.py

2. Process specific directory:
    python haxitag-path-annotator.py -d /path/to/target/directory

3. Set project root directory:
    python haxitag-path-annotator.py --root /path/to/project/root

4. Process specific directory with custom project root:
    python haxitag-path-annotator.py -d /path/to/target/directory --root /path/to/project/root

5. Show help:
    python haxitag-path-annotator.py --help

Arguments:
    -d, --directory : str, optional
        Directory to start scanning and processing (default: script directory)
    --root : str, optional
        Project root directory for calculating relative paths (default: script directory)
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Set, List
from fnmatch import fnmatch

# ====================
# 配置区域
# ====================

# 配置支持的文件类型
SUPPORTED_EXTENSIONS = {'.py', '.tsx', '.ts'}

# 忽略的目录模式（目录名，支持通配符）
IGNORE_DIRECTORIES = {
    # 构建和依赖目录
    'node_modules',
    'dist',
    'build',
    '.git',
    '__pycache__',
    '.pytest_cache',
    'venv',
    '.env',
    'target',
    
    # IDE和编辑器目录
    '.idea',
    '.vscode',
    
    # 测试目录
    '__tests__',
    'test',
    'tests',
    'coverage',
    
    # 临时目录
    'temp',
    'tmp',
    
    # 其他
    'logs',
    'backups',
    'bak',
}

# 忽略的文件模式（支持通配符）
IGNORE_FILES = {
    # 测试文件
    '*.test.ts',
    '*.test.tsx',
    '*.test.py',
    '*.spec.ts',
    '*.spec.tsx',
    '*.spec.py',
    'test_*.py',
    
    # 临时文件
    '*.tmp',
    '*.temp',
    '*.bak',
    '*~',
    
    # 编译和压缩文件
    '*.min.js',
    '*.min.css',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    
    # 日志文件
    '*.log',
    
    # 系统文件
    '.DS_Store',
    'Thumbs.db',
    
    # 其他
    '*.d.ts',
    '*.map'
}

# 二进制文件后缀名集合
BINARY_EXTENSIONS = {
    # 可执行文件
    '.exe', '.dll', '.so', '.dylib', '.bin',
    # 图片文件
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.webp', '.svg',
    # 音视频文件
    '.mp3', '.mp4', '.avi', '.mov', '.wav',
    # 压缩文件
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
    # 数据库文件
    '.db', '.sqlite', '.sqlite3',
    # 文档二进制格式
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    # 其他二进制格式
    '.pyc', '.pyo', '.pyd',  # Python编译文件
    '.class',  # Java编译文件
    '.o',  # C/C++目标文件
}

class PathMatcher:
    def __init__(self):
        """初始化路径匹配器，使用内置的忽略规则"""
        self.ignore_dirs = IGNORE_DIRECTORIES
        self.ignore_files = IGNORE_FILES

    def should_ignore(self, path: str) -> bool:
        """
        检查路径是否应该被忽略
        
        Args:
            path: 相对于项目根目录的路径
            
        Returns:
            bool: 如果路径应该被忽略则返回True
        """
        path_obj = Path(path)
        
        # 检查是否在忽略目录中
        for part in path_obj.parts:
            if any(fnmatch(part, pattern) for pattern in self.ignore_dirs):
                return True
        
        # 检查文件名是否匹配忽略模式
        return any(fnmatch(path_obj.name, pattern) for pattern in self.ignore_files)

class FileStats:
    def __init__(self):
        self.total_files = 0
        self.supported_files = 0
        self.correct_annotation = 0
        self.added_annotation = 0
        self.updated_annotation = 0
        self.binary_files = 0
        self.unsupported_files = 0
        self.unsupported_extensions: Set[str] = set()
        self.unsupported_files_list: List[str] = []  # 存储不支持的文件路径
        self.error_files: Dict[str, str] = {}  # 存储处理失败的文件及错误信息

class PathAnnotator:
    def __init__(self, target_dir: str = None, project_root: str = None):
        # 获取脚本所在目录作为默认根目录
        script_dir = Path(__file__).parent.resolve()
        
        # 设置目标目录和项目根目录
        self.target_dir = Path(target_dir).resolve() if target_dir else script_dir
        self.project_root = Path(project_root).resolve() if project_root else script_dir
        
        # 初始化统计信息和路径匹配器
        self.stats = FileStats()
        self.path_matcher = PathMatcher()
        
        # 验证目录
        if not self.target_dir.exists():
            raise ValueError(f"Target directory does not exist: {self.target_dir}")
        if not self.target_dir.is_dir():
            raise ValueError(f"Target path is not a directory: {self.target_dir}")
        if not self.project_root.exists():
            raise ValueError(f"Project root directory does not exist: {self.project_root}")
        if not self.project_root.is_dir():
            raise ValueError(f"Project root path is not a directory: {self.project_root}")

    def get_comment_prefix(self, file_ext: str) -> str:
        return '# ' if file_ext == '.py' else '// '

    def get_relative_path(self, file_path: Path) -> str:
        try:
            return str(file_path.relative_to(self.project_root))
        except ValueError:
            # 如果文件不在项目根目录下，使用相对于目标目录的路径
            return str(file_path.relative_to(self.target_dir))

    def process_file(self, file_path: Path) -> None:
        # 检查文件是否应该被忽略
        relative_to_root = str(file_path.relative_to(self.project_root))
        if self.path_matcher.should_ignore(relative_to_root):
            return

        self.stats.total_files += 1
        file_ext = file_path.suffix.lower()

        # 检查是否为二进制文件
        if file_ext in BINARY_EXTENSIONS:
            self.stats.binary_files += 1
            return

        # 检查是否为支持的文件类型
        if file_ext not in SUPPORTED_EXTENSIONS:
            self.stats.unsupported_files += 1
            self.stats.unsupported_extensions.add(file_ext)
            self.stats.unsupported_files_list.append(str(file_path))
            return

        self.stats.supported_files += 1
        relative_path = self.get_relative_path(file_path)
        comment_prefix = self.get_comment_prefix(file_ext)
        expected_annotation = f"{comment_prefix}{relative_path}"

        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            self.stats.error_files[str(file_path)] = error_msg
            print(error_msg)
            return

        # 确保文件至少有一行内容
        if not lines:
            lines = ['\n']

        # 检查第一行是否为路径注释
        has_path_annotation = False
        is_correct_annotation = False
        
        if lines:  # 如果文件不为空
            first_line_normalized = ' '.join(lines[0].strip().split())
            expected_annotation_normalized = ' '.join(expected_annotation.strip().split())
            
            has_path_annotation = (
                lines[0].strip().startswith(comment_prefix.strip()) and 
                (relative_path in lines[0] or str(file_path) in lines[0])
            )
            is_correct_annotation = (first_line_normalized == expected_annotation_normalized)

        if is_correct_annotation:
            # 注释正确，不需要修改
            self.stats.correct_annotation += 1
            print(f"Correct annotation exists in: {file_path}")
            print(f"  Current annotation: {lines[0].strip()}")
        elif has_path_annotation:
            # 有注释但不正确，需要更新
            lines[0] = expected_annotation + '\n'
            self.stats.updated_annotation += 1
            print(f"Updated annotation in: {file_path}")
            print(f"  New annotation: {expected_annotation}")
        else:
            # 没有注释，需要添加
            lines.insert(0, expected_annotation + '\n')
            self.stats.added_annotation += 1
            print(f"Added annotation to: {file_path}")
            print(f"  New annotation: {expected_annotation}")

        # 写入更新后的内容
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        except Exception as e:
            error_msg = f"Error writing file: {str(e)}"
            self.stats.error_files[str(file_path)] = error_msg
            print(error_msg)

    def process_directory(self) -> None:
        """处理目录及其子目录中的文件"""
        for root, dirs, files in os.walk(self.target_dir):
            # 修改dirs列表以跳过应该忽略的目录
            dirs[:] = [d for d in dirs if not self.path_matcher.should_ignore(d)]
            
            for file in files:
                file_path = Path(root) / file
                try:
                    relative_path = file_path.relative_to(self.project_root)
                    if not self.path_matcher.should_ignore(str(relative_path)):
                        self.process_file(file_path)
                except ValueError:
                    # 如果文件不在项目根目录下，使用相对于目标目录的路径
                    relative_path = file_path.relative_to(self.target_dir)
                    if not self.path_matcher.should_ignore(str(relative_path)):
                        self.process_file(file_path)

    def print_stats(self) -> None:
        print("\n=== Path Annotation Statistics ===")
        print(f"Target directory: {self.target_dir}")
        print(f"Project root: {self.project_root}")
        print(f"Total files scanned: {self.stats.total_files}")
        print(f"Supported files found: {self.stats.supported_files}")
        print(f"Files with correct annotations: {self.stats.correct_annotation}")
        print(f"Files where annotations were added: {self.stats.added_annotation}")
        print(f"Files where annotations were updated: {self.stats.updated_annotation}")
        print(f"Binary files ignored: {self.stats.binary_files}")
        print(f"Unsupported files: {self.stats.unsupported_files}")
        
        if self.stats.unsupported_extensions:
            print("\nUnsupported file extensions found:")
            for ext in sorted(self.stats.unsupported_extensions):
                print(f"  - {ext}")
            
        if self.stats.unsupported_files_list:
            print("\nUnsupported files list:")
            for file_path in sorted(self.stats.unsupported_files_list):
                print(f"  - {file_path}")
        
        if self.stats.error_files:
            print("\nFiles with errors:")
            for file_path, error in self.stats.error_files.items():
                print(f"  - {file_path}: {error}")

def parse_args():
    parser = argparse.ArgumentParser(
        description='Add or update path annotations in source code files.'
    )
    parser.add_argument(
        '-d', '--directory',
        help='Directory to start scanning and processing (default: script directory)'
    )
    parser.add_argument(
        '--root',
        help='Project root directory for calculating relative paths (default: script directory)'
    )
    return parser.parse_args()

def main():
    args = parse_args()
    try:
        annotator = PathAnnotator(args.directory, args.root)
        annotator.process_directory()
        annotator.print_stats()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()