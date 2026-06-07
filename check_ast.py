import ast
try:
    with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/agents/gmail_triage.py") as f:
        ast.parse(f.read())
except SyntaxError as e:
    print(repr(e))
    print(e.text)
    print(e.offset)
