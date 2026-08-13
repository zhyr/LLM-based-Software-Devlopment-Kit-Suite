import os
import sys
import fnmatch

class DirectoryExplorer:
    def __init__(self, root_path, max_depth=10, max_files=100):
        self.root_path = root_path
        self.max_depth = max_depth
        self.max_files = max_files
        self.output = []
        self.deep_directories = set()
        self.large_directories = set()
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
            'HaxiTAG-DirectoryExplorer.py',
            'SECURITY.md',
            'CODE_OF_CONDUCT.md',
            '.eslintrc.json',
            '需求说明.md',
            '*-目录.txt',
            'README.md.txt',
            '*.npmrc',
            '*/.DS_Store',
            '*.DS_Store',
            '*.log',
            '.env.local',
            'findIncorrectLinks.js',
            'check-env-permissions.js',
            'HaxiTAG_file_merger.py',
            'posts/*',
            '*/images/*',
            '*/logo/*',
            '.dockerignore',
            '.nvmrc',
            'Dockerfile',
            'HaxiTAG- AI-CMS-deployment-guide.md',
            'checkPostsJson.js',
            'scan-link-error.js',
            'check-links.js',
            'feishu-token-generator.js',
            'scan-link-error.js',
            'privacy-policy.md'
        ]

    def should_ignore(self, file_path):
        for pattern in self.IGNORE_LIST:
            if fnmatch.fnmatch(file_path.lower(), pattern.lower()):
                return True
        return False

    def explore(self):
        self.output = [f"/{os.path.basename(self.root_path)}"]
        self._explore_recursive(self.root_path, 0)
        
        dir_name = os.path.basename(self.root_path)
        output_filename = f"{dir_name}-目录.txt"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.output))
            
            if self.deep_directories:
                f.write('\n\n以下目录深度超过10级：\n')
                for dir_path in self.deep_directories:
                    f.write(f"- {dir_path}\n")
            
            if self.large_directories:
                f.write('\n\n以下目录包含超过100个文件：\n')
                for dir_path in self.large_directories:
                    f.write(f"- {dir_path}\n")
        
        print(f"目录列表已保存到 {output_filename}")

    def _explore_recursive(self, current_path, depth):
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
            
            if self.should_ignore(relative_item_path):
                continue

            is_last = (i == len(items) - 1)
            if is_last:
                branch = '└── '
            else:
                branch = '├── '

            if os.path.isdir(item_path):
                self.output.append(f"{prefix}{branch}{item}")
                self._explore_recursive(item_path, depth + 1)
            else:
                self.output.append(f"{prefix}{branch}{item}")

            if is_last and depth > 0:
                self.output.append(f"{prefix}")

def main():
    if len(sys.argv) > 1:
        root_path = sys.argv[1]
    else:
        root_path = os.getcwd()

    explorer = DirectoryExplorer(root_path)
    explorer.explore()

if __name__ == "__main__":
    main()