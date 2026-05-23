import re

with open("20-actors/magatama/py/src/pymagatama/narou_worker_main.py", "r") as f:
    content = f.read()

# Remove the old async functions that were left behind
content = re.sub(r'async def task_narou_list_novels.*?return {"novels": novels, "total": len\(novels\), "offset": offset, "limit": limit}', '', content, flags=re.DOTALL)
content = re.sub(r'async def task_narou_get_chapter.*?return \{"chapter": dict\(row\)\}', '', content, flags=re.DOTALL)
content = re.sub(r'async def task_narou_list_chapters.*?return \{"chapters": chapters, "total": len\(chapters\), "offset": offset, "limit": limit\}', '', content, flags=re.DOTALL)
content = re.sub(r'async def task_narou_search_novels.*?return \{"novels": novels, "total": len\(filtered\), "offset": offset, "limit": limit\}', '', content, flags=re.DOTALL)

with open("20-actors/magatama/py/src/pymagatama/narou_worker_main.py", "w") as f:
    f.write(content)
