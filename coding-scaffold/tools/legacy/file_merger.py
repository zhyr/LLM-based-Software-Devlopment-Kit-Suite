import os
import time
from datetime import datetime
import fnmatch

# Define the list of files and patterns to ignore
IGNORE_LIST = [
    'config.css',
    'readme.md',
    'file_merger.py',
    'ollama-api-readme.md',
    '.DS_Store',
    'styles.css',
    'icon*.png',
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
    'images/*',
    'logo/*',

    # Add more files or patterns to ignore as needed
]

def should_ignore(file_path):
    """Check if the file should be ignored based on the IGNORE_LIST."""
    for pattern in IGNORE_LIST:
        if fnmatch.fnmatch(file_path.lower(), pattern.lower()):
  return True
    return False

def is_text_file(file_path):
    text_extensions = ['.js', '.css', '.html', '.json', '.txt', '.md', '.py', '.xml', '.csv','.tsx','.log']
    return any(file_path.lower().endswith(ext) for ext in text_extensions)

def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
  return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return f"Error reading file: {str(e)}"

def process_directory(directory):
    content = []
    dir_name = os.path.basename(directory)
    
    # Add the directory name at the beginning
    content.append(f"# {dir_name}")
    content.append('--')

    for root, dirs, files in os.walk(directory):
        # Remove ignored directories
        dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d))]
        
        for file in files:
  file_path = os.path.join(root, file)
  rel_file_path = os.path.relpath(file_path, directory)
  
  # Check if the file should be ignored
  if should_ignore(rel_file_path):
      print(f"Ignoring file: {rel_file_path}")
      continue

  # Add the full path with directory name and '#' prefix
  content.append(f"# {dir_name}/{rel_file_path}")

  if is_text_file(file_path):
      file_content = read_file_content(file_path)
      content.append(file_content)
  else:
      content.append(f"Binary file: {file}")

  content.append('--')

    return '\n'.join(content)

def main():
    current_dir = os.getcwd()
    dir_name = os.path.basename(current_dir)
    timestamp = int(time.time() * 1000)  # 13-digit millisecond timestamp
    output_filename = f"{dir_name}-{timestamp}.txt"

    content = process_directory(current_dir)

    with open(output_filename, 'w', encoding='utf-8') as output_file:
        output_file.write(content)

    print(f"File created: {output_filename}")

if __name__ == "__main__":
    main()