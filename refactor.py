import os
import glob
import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        code = f.read()

    # 1. Imports
    if 'import psycopg' in code:
        code = code.replace('import psycopg\n', '')
    if 'from kotodama.kotoba_datomic import get_kotoba_client' not in code:
        code = code.replace('from typing import Any', 'from typing import Any\nfrom kotodama.kotoba_datomic import get_kotoba_client')

    if 'import asyncio' not in code:
        code = code.replace('import logging', 'import asyncio\nimport logging')

    # 2. _RW_URL
    code = re.sub(r'^[ \t]*_RW_URL\s*=\s*os\.environ\.get\("RW_URL"\).*?\n', '', code, flags=re.MULTILINE)
    
    # 3. RW checks
    code = re.sub(r'^[ \t]*if not _RW_URL:\n[ \t]*return\s*\{[^\}]*"RW_URL not set"[^\}]*\}\n', '', code, flags=re.MULTILINE)
    code = re.sub(r'^[ \t]*if not _RW_URL:\n(?:[ \t]*return.*?\n)?', '', code, flags=re.MULTILINE)
    code = re.sub(r'if not video_id or not _RW_URL:', 'if not video_id:', code)

    with open(filepath, 'w') as f:
        f.write(code)

files = glob.glob('60-apps/etzhayyim-project-yukkuri/lg/lg_yukkuri/graphs/*.py')
for file in files:
    process_file(file)
