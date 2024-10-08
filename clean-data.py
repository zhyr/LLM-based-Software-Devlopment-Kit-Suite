import os
import re
import json
import glob

# 文件配置
FILE_CONFIG = {
    "include": [
        "Gmail  |  Google for Developer-20240918-134156.txt",
        # "Tutorial \u2014 Wagtail Documentati-20240917-055603.txt",  # 使用 Unicode 转义序列表示特殊字符
        "*.md",
        "docs/*.txt"
    ],
    "exclude": [
        "readme.md",
        "requirements.txt",
        "temp.txt",
        "*.tmp",
        "drafts/*"
    ]
}

# 清洗策略列表
CLEANING_STRATEGIES = [
    {
        "name": "Remove page and word count",
        "pattern": r'\(共\d+页, 全文\d+字\)',
        "replacement": ''
    },
    {
        "name": "Remove word count and URL",
        "pattern": r'\(本页字数: \d+, URL: [^\)]+\)',
        "replacement": ''
    },
    # 在这里添加更多清洗策略
]


def clean_content(content):
    for strategy in CLEANING_STRATEGIES:
        content = re.sub(strategy["pattern"], strategy["replacement"], content)
    return content.strip()


def should_process_file(file_path):
    # 检查文件是否应该被处理
    include_patterns = [pattern for pattern in FILE_CONFIG["include"] if '*' in pattern]
    include_files = [file for file in FILE_CONFIG["include"] if '*' not in file]
    exclude_patterns = [pattern for pattern in FILE_CONFIG["exclude"] if '*' in pattern]
    exclude_files = [file for file in FILE_CONFIG["exclude"] if '*' not in file]

    # 检查是否直接包含在文件列表中
    if os.path.basename(file_path) in include_files:
        return True

    # 检查是否匹配包含模式
    if any(glob.fnmatch.fnmatch(file_path, pattern) for pattern in include_patterns):
        # 检查是否直接排除
        if os.path.basename(file_path) in exclude_files:
            return False
        # 检查是否匹配排除模式
        if any(glob.fnmatch.fnmatch(file_path, pattern) for pattern in exclude_patterns):
            return False
        return True

    return False


def process_file(file_path):
    if not os.path.exists(file_path):
        print(f"文件 {file_path} 不存在")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            if file_path.endswith('.json'):
                content = json.load(file)
                if isinstance(content, str):
                    cleaned_content = clean_content(content)
                elif isinstance(content, dict):
                    cleaned_content = {k: clean_content(v) if isinstance(v, str) else v for k, v in content.items()}
                else:
                    print(f"Unsupported JSON structure in {file_path}")
                    return
            else:
                content = file.read()
                cleaned_content = clean_content(content)

        # 计算清理后的字数
        if isinstance(cleaned_content, str):
            word_count = len(cleaned_content)
        elif isinstance(cleaned_content, dict):
            word_count = sum(len(v) for v in cleaned_content.values() if isinstance(v, str))
        else:
            word_count = 0

        # 生成新的文件名
        base_name = os.path.splitext(file_path)[0]
        new_file_path = f"{base_name}_cleaned.txt"

        # 写入新文件
        with open(new_file_path, 'w', encoding='utf-8') as file:
            if isinstance(cleaned_content, str):
                file.write(cleaned_content)
            elif isinstance(cleaned_content, dict):
                json.dump(cleaned_content, file, ensure_ascii=False, indent=2)

        print(f"处理完成: {file_path}")
        print(f"清理后字数: {word_count}")
        print(f"清理后文件保存为: {new_file_path}")
        print()
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")


def main():
    for include_item in FILE_CONFIG["include"]:
        if '*' in include_item:
            # 如果是通配符模式，使用 glob 获取匹配的文件
            for file_path in glob.glob(include_item):
                if should_process_file(file_path):
                    process_file(file_path)
        else:
            # 如果是具体文件名，直接处理
            if should_process_file(include_item):
                process_file(include_item)


if __name__ == "__main__":
    main()