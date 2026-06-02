import os
import re

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False
        
    new_content = content.replace('com.etzhayyim', 'com.etzhayyim')
    new_content = new_content.replace('com.etzhayyim', 'com.etzhayyim')
    
    # Also handle slash variants if they are used as NSID paths
    new_content = new_content.replace('com/etzhayyim', 'com/etzhayyim')
    new_content = new_content.replace('com/etzhayyim', 'com/etzhayyim')
    
    if content != new_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    modified_files = 0
    
    # Walk the directory tree from bottom up so directory renames don't mess up paths
    for root, dirs, files in os.walk('.', topdown=False):
        if '.git' in root or '.pytest_cache' in root or 'node_modules' in root:
            continue
            
        # Files text replace
        for file in files:
            filepath = os.path.join(root, file)
            if replace_in_file(filepath):
                modified_files += 1
                
        # File renames
        for file in files:
            if 'com.etzhayyim' in file or 'com.etzhayyim' in file:
                old_path = os.path.join(root, file)
                new_file = file.replace('com.etzhayyim', 'com.etzhayyim').replace('com.etzhayyim', 'com.etzhayyim')
                new_path = os.path.join(root, new_file)
                os.rename(old_path, new_path)
                print(f"Renamed file: {old_path} -> {new_path}")
                
        # Directory renames (specifically for com.etzhayyim, com.etzhayyim, com/etzhayyim, com/etzhayyim)
        # Note: since we walk bottom-up, we rename directories after processing their contents
        
    print(f"Modified {modified_files} files.")

if __name__ == '__main__':
    main()
