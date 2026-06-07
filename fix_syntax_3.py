import glob

files = glob.glob("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/**/*.py", recursive=True)
for path in files:
    with open(path, "r") as f:
        text = f.read()
    
    orig = text
    
    if "gmail_triage.py" in path:
        text = text.replace('description = ([("col",)] if _res else [])",', 'description = EXCLUDED.description",')
        text = text.replace('JSON used as `([("col",)] if _res else [])`', 'JSON used as `event.description`')
    
    text = text.replace('([("col",)] if _res else [])', '[]')
    
    if text != orig:
        with open(path, "w") as f:
            f.write(text)
        print(f"Fixed {path}")
