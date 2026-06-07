import os
import glob
import re

def rewrite_file(filepath):
    with open(filepath, 'r') as f:
        code = f.read()

    # 1. Remove RW_URL definition
    code = re.sub(r'^[ \t]*_RW_URL\s*=\s*os\.environ\.get\("RW_URL"\).*?\n', '', code, flags=re.MULTILINE)

    # 2. Remove RW_URL checks
    code = re.sub(r'^[ \t]*if not _RW_URL:\n[ \t]*return\s*\{[^\}]*"RW_URL not set"[^\}]*\}\n', '', code, flags=re.MULTILINE)
    code = re.sub(r'^[ \t]*if not _RW_URL:\n(?:[ \t]*return.*?\n)?', '', code, flags=re.MULTILINE)

    # 3. Replace psycopg imports
    # In some places it's inside functions
    code = re.sub(r'^[ \t]*import psycopg\n[ \t]*conn\s*=\s*await psycopg\.AsyncConnection\.connect\(_RW_URL[^\n]*\n(?:[ \t]*try:\n)?(?:[ \t]*cur\s*=\s*conn\.cursor\(\)\n)?', 
                  '    client = get_kotoba_client()\n', code, flags=re.MULTILINE)
    
    # Also add import at the top
    if 'get_kotoba_client' not in code:
        code = re.sub(r'from typing import Any', 'from typing import Any\nfrom kotodama.kotoba_datomic import get_kotoba_client', code, count=1)
        if 'import asyncio' not in code:
            code = re.sub(r'import logging', 'import asyncio\nimport logging', code, count=1)

    # Fix Finally close blocks
    code = re.sub(r'^[ \t]*finally:\n[ \t]*await conn\.close\(\)\n', '', code, flags=re.MULTILINE)
    
    with open(filepath, 'w') as f:
        f.write(code)

files = glob.glob('60-apps/etzhayyim-project-yukkuri/lg/lg_yukkuri/graphs/*.py')
for file in files:
    rewrite_file(file)
