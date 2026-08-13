# 放在项目的根目录下，python3 haxitag-context-builder.py-n custom-name.txt-d 目录或者文件地址 使用这个命令运行，
# -d后面为指定的合并代码目录或文件，需要忽略的文件以通配符、文件名或者后缀的形式放在对应的配置中。
# 不设置指定目录，则以当前脚本所在目录为起点，遍历其下所有目录。
# 可以使用 -n 或 --name 参数指定输出文件名
# 使用-d 或 --dir 指定集成合并的代码文件或者文件目录，会自动忽略二进制文件，但是最好提前声明

import os
import time
import re
import sys
import argparse
from datetime import datetime
import fnmatch

# Define common programming file extensions by category
PROGRAMMING_EXTENSIONS = {
    # JavaScript/TypeScript Ecosystem
    'javascript': ['.js', '.mjs', '.cjs', '.jsx'],
    'typescript': ['.ts', '.tsx', '.d.ts', '.cts', '.mts'],
    'nodejs': ['.node', '.njs'],
    'nextjs': ['.page.tsx', '.page.ts', '.page.jsx', '.page.js'],
    'vue': ['.vue', '.nvue'],
    'angular': ['.ng.html', '.ng.ts', '.component.ts', '.service.ts', '.pipe.ts', '.module.ts'],
    'svelte': ['.svelte'],
    
    # Python Ecosystem
    'python': ['.py', '.pyi', '.pyx', '.pxd', '.pyw', '.rpy', '.cpy', '.gyp'],
    'jupyter': ['.ipynb'],
    'django': ['.djt', '.jinja2'],
    
    # Mobile & Desktop Development
    'swift': ['.swift', '.xib', '.storyboard', '.swift-version'],
    'swiftui': ['.swift'],
    'kotlin': ['.kt', '.kts', '.ktm'],
    'dart': ['.dart'],
    'flutter': ['.dart'],
    
    # Systems Programming
    'rust': ['.rs', '.rlib'],
    'golang': ['.go', '.mod'],
    'c_cpp': ['.c', '.cpp', '.h', '.hpp', '.cc', '.hh', '.cxx', '.hxx'],
}

# Define directories to ignore
IGNORE_DIRS = {
    # Node.js 环境
    'node_modules',
    'npm-debug',
    'yarn-debug',
    'yarn-error',
    '.npm',
    '.yarn',
    '.pnpm',
    
    # 测试目录
    '__tests__',
    'test-results',
    'coverage',
    '__snapshots__',
    '.jest',
    'cypress',
    'e2e',
    
    # 构建输出
    'build',
    'dist',
    'out',
    'output',
    '.next',
    '.nuxt',
    '.vuepress/dist',
    
    # IDE和编辑器
    '.idea',
    '.vscode',
    '.vs',
    '.eclipse',
    '*/pdf-extract-run/*',
    
    # 其他开发工具
    '.git',
    '.svn',
    '.hg',
    '.github',
    '.gitlab',
    '.husky',
    
    # 日志目录
    'logs',
    'log',
    '.drafts-cache.*',
    
    # Python相关
    '__pycache__',
    '.pytest_cache',
    '.tox',
    '.venv',
    'venv',
    '.env',
    '.env.local',
    'env',
    'prisma',
}

# 忽略文件列表
IGNORE_LIST = [
    'config.css',
    'readme.md',
    'README.md',
    'file_merger.py',
    'ollama-api-readme.md',
    '.DS_Store',
    'styles.css',
    'icon*.png',
    'haxitag-structure-Explorer.py',
    '*-目录.txt',
    'haxitag-context-builder.py',
    '.gitignore',
    'package.json',
    'package-lock.json',
    'build/*',
    'test-results/*',
    'docker-compose.yml',
    'Dockerfile',
    'docker-entrypoint.sh',
    'logs/*',
    'node_modules/*',
    'tsconfig.json',
    'tsconfig.build.json',
    'tsconfig.json',
    '*.css',
    '*.md',
    '*.html',
    '*.htm',
    '.xml',
    '.csv',
    '.log',
    '.ini',
    '.yaml', 
    '.yml', 
    '.xml', 
    '.toml',
    'Makefile',
    'Dockerfile',
    'docker-compose.yml',
    'docker-compose.yaml',
    '.dockerignore',
    '.gitignore',
    '.npmignore',
    'package.json',
    'package-lock.json',
    'yarn.lock',
    'requirements.txt',
    'Pipfile',
    'poetry.lock',
    'Cargo.toml',
    'Cargo.lock',
    'go.mod',
    'go.sum',
    '*.lock',
    '.txt', '.log', '.pdf', '.doc', '.docx', '.rtf', '.xls', '.xlsx', '.ppt', '.pptx',
    '.sql', '.mysql', '.sqlite', '.pgsql', '.mongodb',
    '.html', '.htm', '.xhtml', '.css', '.scss', '.sass', '.less', '.styl',
    '.xml', '.json', '.yaml', '.yml', '.ini', '.env', '.sh', '.bash', '.zsh',
    '.bat', '.cmd', '.ps1', '.psm1', '.psd1',
    '*.txt',
    '*.json',
    '*.prisma',
    '*.sql',
    'test*',
    'generated/*',
    'prisma/*',
]

class ProcessingStats:
    """统计处理信息"""
    def __init__(self):
        self.processed_files = 0  # 处理的文件数
        self.ignored_files = 0    # 忽略的文件数
        self.total_chars = 0      # 总字符数
        self.scanned_files = 0    # 扫描的文件总数

    def calculate_tokens(self):
        """计算预估token数"""
        return int((self.total_chars / 5) * 0.75)

    def print_stats(self):
        """打印统计信息"""
        print("\n处理统计：")
        print(f"合并的文件数: {self.processed_files}")
        print(f"总字符数: {self.total_chars:,}")
        print(f"预估token数: {self.calculate_tokens():,}")
        print(f"忽略的文件数: {self.ignored_files}")
        print(f"扫描的文件总数: {self.scanned_files}")

# 创建全局统计对象
stats = ProcessingStats()

def preprocess_paths(paths):
    """预处理路径参数，分割错误连接的路径"""
    if not paths:
        return paths
        
    processed_paths = []
    for path in paths:
        # 检查并修复路径分隔
        if "'" in path[1:-1] if len(path) > 2 else False:  # 忽略开头和结尾的引号
            # 分割错误连接的路径
            sub_paths = path.replace("''", "' '").split("' '")
            # 清理每个子路径的引号和空格
            sub_paths = [p.strip().strip("'") for p in sub_paths]
            processed_paths.extend(sub_paths)
        else:
            # 清理单个路径的引号和空格
            cleaned_path = path.strip().strip("'").strip('"')
            if cleaned_path:  # 只添加非空路径
                processed_paths.append(cleaned_path)
            
    return processed_paths

def get_project_root():
    """
    动态获取项目根目录
    Returns:
        tuple: (根目录绝对路径, 项目名称)
    """
    script_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(script_path)
    
    # 查找包含.git目录的最近父目录作为项目根目录
    while current_dir != os.path.dirname(current_dir):
        if os.path.exists(os.path.join(current_dir, '.git')):
            return current_dir, os.path.basename(current_dir)
        current_dir = os.path.dirname(current_dir)
    
    return os.path.dirname(script_path), os.path.basename(os.path.dirname(script_path))

def normalize_path(path, project_root, project_name):
    """规范化路径：移除引号，转换为相对路径"""
    # 移除首尾的引号和空格
    path = path.strip().strip("'").strip('"').strip()
    
    # 统一路径分隔符
    path = path.replace('\\', '/')
    project_root = project_root.replace('\\', '/')
    
    # 如果已经是相对路径，验证并返回
    if not os.path.isabs(path):
        abs_path = os.path.abspath(os.path.join(project_root, path))
        if not abs_path.startswith(project_root):
            raise ValueError(f"路径 '{path}' 不在项目目录内")
        return path

    # 处理绝对路径
    try:
        # 尝试从项目名称后开始截取相对路径
        if project_name in path:
            rel_path = path.split(project_name + '/')[-1]
        else:
            # 如果路径中没有项目名称，尝试直接相对于根目录计算
            rel_path = os.path.relpath(path, project_root)
            
        # 验证处理后的路径
        abs_path = os.path.abspath(os.path.join(project_root, rel_path))
        if not abs_path.startswith(project_root):
            raise ValueError(f"路径 '{path}' 不在项目目录内")
        return rel_path
    except Exception as e:
        raise ValueError(f"无法处理路径 '{path}': {str(e)}")

def remove_comments(content, file_extension):
    """Remove comments from code based on file type"""
    try:
        # JavaScript/TypeScript style comments
        if file_extension in ['.js', '.ts', '.jsx', '.tsx', '.mjs', '.cjs', '.vue', '.json']:
            content = re.sub(r'/\*\*[\s\S]*?\*/', '', content)  # JSDoc
            content = re.sub(r'/\*[\s\S]*?\*/', '', content)    # Multi-line
            content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)  # Single-line
        
        # Python style comments
        elif file_extension in ['.py', '.pyi', '.pyx', '.pxd', '.pyw']:
            content = re.sub(r'"""[\s\S]*?"""', '', content)  # Docstrings
            content = re.sub(r"'''[\s\S]*?'''", '', content)  # Docstrings
            content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)  # Single-line

        # Remove empty lines and clean up
        content = re.sub(r'\n\s*\n+', '\n\n', content)
        return content.strip()
    except Exception as e:
        print(f"Error removing comments: {str(e)}")
        return content

def get_all_text_extensions():
    """Flatten all extensions into a single set."""
    all_extensions = set()
    for category in PROGRAMMING_EXTENSIONS.values():
        all_extensions.update(category)
    return all_extensions

def should_ignore_directory(dir_path):
    """Check if a directory should be ignored"""
    dir_name = os.path.basename(dir_path)
    return dir_name in IGNORE_DIRS

def should_ignore(file_path):
    """Enhanced file ignore checking function"""
    dir_path = os.path.dirname(file_path)
    if should_ignore_directory(dir_path):
        return True
    
    file_name = os.path.basename(file_path)
    file_path = file_path.replace('\\', '/')
    
    for pattern in IGNORE_LIST:
        if fnmatch.fnmatch(file_path.lower(), pattern.lower()):
            return True
        if fnmatch.fnmatch(file_name.lower(), pattern.lower()):
            return True
    return False

def is_text_file(file_path):
    """Check if a file is a text file based on its extension."""
    text_extensions = get_all_text_extensions()
    file_path_lower = file_path.lower()
    
    return any(file_path_lower.endswith(ext.lower()) for ext in text_extensions)

def read_file_content(file_path):
    """Read and return file content with comment removal"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            stats.total_chars += len(content)  # 统计字符数
            _, ext = os.path.splitext(file_path)
            return remove_comments(content, ext.lower())
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return f"Error reading file: {str(e)}"

def process_single_file(file_path, root_dir, base_path=''):
    """Process a single file"""
    try:
        stats.scanned_files += 1  # 增加扫描文件计数
        
        if base_path:
            rel_file_path = os.path.join(base_path, os.path.basename(file_path))
        else:
            rel_file_path = os.path.relpath(file_path, root_dir)
        
        rel_file_path = rel_file_path.replace('\\', '/')
        
        if should_ignore(file_path):
            stats.ignored_files += 1  # 增加忽略文件计数
            print(f"Ignoring file: {rel_file_path}")
            return None

        content = []
        content.append(f"# {rel_file_path}")

        if is_text_file(file_path):
            file_content = read_file_content(file_path)
            content.append(file_content)
            stats.processed_files += 1  # 增加处理文件计数
        else:
            content.append(f"Binary file: {os.path.basename(file_path)}")

        content.append('--')
        return '\n'.join(content)
        
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return None

def process_directory(directory, root_dir=None, base_path=''):
    """Process directory and gather file contents"""
    if root_dir is None:
        root_dir = directory

    content = []
    try:
        for root, dirs, files in os.walk(directory):
            # Remove ignored directories
            dirs[:] = [d for d in dirs if not should_ignore_directory(os.path.join(root, d))]
            
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    stats.scanned_files += 1  # 增加扫描文件计数
                    
                    # 计算相对于根目录的路径
                    if base_path:
                        rel_file_path = os.path.join(base_path, os.path.relpath(file_path, directory))
                    else:
                        rel_file_path = os.path.relpath(file_path, root_dir)
                    
                    # 统一使用正斜杠
                    rel_file_path = rel_file_path.replace('\\', '/')
                    
                    if should_ignore(file_path):
                        stats.ignored_files += 1  # 增加忽略文件计数
                        print(f"Ignoring file: {rel_file_path}")
                        continue

                    content.append(f"# {rel_file_path}")

                    if is_text_file(file_path):
                        file_content = read_file_content(file_path)
                        content.append(file_content)
                        stats.processed_files += 1  # 增加处理文件计数
                    else:
                        content.append(f"Binary file: {file}")

                    content.append('--')
                except Exception as e:
                    print(f"Error processing file {file}: {str(e)}")
                    continue

    except Exception as e:
        print(f"Error processing directory {directory}: {str(e)}")
    
    return '\n'.join(content)

def process_path(path, root_dir=None, base_path=''):
    """
    Process a path that could be either a file or directory
    Args:
        path: 要处理的路径
        root_dir: 项目根目录
        base_path: 相对路径前缀
    """
    if root_dir is None:
        root_dir = os.path.dirname(os.path.abspath(__file__))

    if os.path.isfile(path):
        return process_single_file(path, root_dir, base_path)
    elif os.path.isdir(path):
        return process_directory(path, root_dir, base_path)
    else:
        return None

def process_paths(paths):
    """处理输入的路径列表"""
    if not paths:
        return []
        
    project_root, project_name = get_project_root()
    normalized_paths = []
    errors = []
    
    # 预处理路径，处理引号和连接的路径
    paths = preprocess_paths(paths)
    
    for path in paths:
        try:
            norm_path = normalize_path(path, project_root, project_name)
            if norm_path and norm_path not in normalized_paths:  # 避免重复路径
                normalized_paths.append(norm_path)
        except ValueError as e:
            errors.append(str(e))
            
    if errors:
        print("\n路径处理错误：")
        for error in errors:
            print(f"- {error}")
            
    return normalized_paths

def process_directories(paths=None):
    """Process multiple paths (files or directories) or current directory"""
    project_root, project_name = get_project_root()
    errors = []
    content = []

    if paths:
        normalized_paths = process_paths(paths)
        processed_paths = set()  # 用于跟踪已处理的路径
        
        for path in normalized_paths:
            try:
                if path in processed_paths:  # 跳过重复的路径
                    continue
                    
                abs_path = os.path.abspath(os.path.join(project_root, path))
                
                # Validate path is within project directory
                if not abs_path.startswith(project_root):
                    errors.append(f"路径 '{path}' 不在项目目录内")
                    continue
                    
                if not os.path.exists(abs_path):
                    errors.append(f"路径 '{path}' 不存在")
                    continue

                # Get the normalized base path
                base_path = os.path.dirname(path).replace('\\', '/')
                
                # Process the path
                result = process_path(abs_path, project_root, base_path)
                if result:
                    content.append(result)
                    processed_paths.add(path)
                
            except Exception as e:
                errors.append(f"处理路径 '{path}' 时出错: {str(e)}")
    else:
        # Process entire root directory if no paths specified
        content.append(process_directory(project_root, project_root))

    return '\n'.join(content), errors

def main():
    """Main execution function"""
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='合并指定目录或文件的代码')
    parser.add_argument('-d', '--dir', nargs='+', help='要处理的目录或文件列表（相对于脚本所在目录的路径）')
    parser.add_argument('-n', '--name', help='输出文件的自定义名称（可选）')
    args = parser.parse_args()

    print("Starting to process paths...")
    
    try:
        # 处理路径
        content, errors = process_directories(args.dir)

        # 生成输出文件名
        timestamp = int(time.time() * 1000)
        project_root, project_name = get_project_root()
        
        if args.name:
            # 如果提供了自定义名称，使用它
            # 确保文件名以.txt结尾
            output_filename = args.name if args.name.endswith('.txt') else f"{args.name}.txt"
        else:
            # 使用原有的命名策略
            output_filename = f"{project_name}-{timestamp}.txt"

        # 写入文件
        with open(output_filename, 'w', encoding='utf-8') as output_file:
            output_file.write(content)

        print(f"\nFile created successfully: {output_filename}")

        # 打印统计信息
        stats.print_stats()

        # 显示错误信息
        if errors:
            print("\n处理过程中遇到以下问题：")
            for error in errors:
                print(f"- {error}")

    except Exception as e:
        print(f"\n程序执行出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()