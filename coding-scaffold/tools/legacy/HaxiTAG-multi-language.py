import os
import re
import pandas as pd
from langdetect import detect

# 定义要扫描的目录
directories_to_scan = ['components', 'src']

# 初始化一个列表来保存提取的数据
data = []

# 语言检测函数
def detect_language(text):
    try:
        return detect(text)
    except:
        return 'unknown'

# 扫描文件并提取文本的函数
def scan_files():
    for directory in directories_to_scan:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 提取字符串
                        matches = re.findall(r'"([^"]*)"', content)
                        for match in matches:
                            language = detect_language(match)
                            if language in ['zh-cn', 'en']:
                                data.append({
                                    'file_path': os.path.relpath(file_path),
                                    'file_name': file,
                                    'text': match,
                                    'language': language
                                })

# 保存数据到Excel的函数
def save_to_excel():
    df = pd.DataFrame(data)
    df['chinese'] = df.apply(lambda x: x['text'] if x['language'] == 'zh-cn' else '', axis=1)
    df['english'] = df.apply(lambda x: x['text'] if x['language'] == 'en' else '', axis=1)
    df.to_excel('ui_elements.xlsx', index=False, columns=['file_path', 'file_name', 'chinese', 'english'])

# 生成language.yaml的函数
def generate_language_package():
    language_data = {}
    for item in data:
        key = item['text'].replace(' ', '_')
        language_data[key] = item['text']
    
    with open('data/language.yaml', 'w', encoding='utf-8') as f:
        for key, value in language_data.items():
            f.write(f"{key}: {value}\n")

# 执行函数
scan_files()
save_to_excel()
generate_language_package()