import os
import glob
import re

def process_file(f):
    with open(f, 'r') as fd:
        content = fd.read()
    
    if 'psycopg' not in content and 'RW_URL' not in content:
        return

    # Replace imports
    content = re.sub(r'import psycopg', 'from kotodama.kotoba_datomic import get_kotoba_client\nimport asyncio', content)
    # Some files might already import asyncio, but it's fine if it's duplicated or we can just ignore it since it's already there in most langgraph scripts. Let's do a cleaner replacement.
    content = re.sub(r'_RW_URL = os\.environ\.get\("RW_URL"\).*?\n', '', content)
    content = re.sub(r'if not _RW_URL:\n\s+return\s+\{.*?"error":.*?"RW_URL not set".*?\}\n', '', content)
    content = re.sub(r'if not _RW_URL:\n\s+return.*?\n', '', content)
    content = re.sub(r'conn = await psycopg\.AsyncConnection\.connect\(_RW_URL[^\)]*\)\n', '', content)
    
    # We will just write a python AST transformer or line by line state machine.
    # Actually, manual replacements using multiple `replace` tool calls might be tedious.
    pass

