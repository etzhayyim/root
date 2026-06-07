import re

# bunken_app
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/bunken_app.py") as f: t = f.read()
lines = t.split('\n')
for i in range(180, 220):
    if i < len(lines) and lines[i].startswith('                "'):
        lines[i] = '        ' + lines[i].lstrip()
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/bunken_app.py", "w") as f: f.write('\n'.join(lines))

# business_manager
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/business_manager_app.py") as f: t = f.read()
lines = t.split('\n')
for i in range(133, 160):
    if i < len(lines) and lines[i].startswith('            '):
        lines[i] = '        ' + lines[i].lstrip()
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/business_manager_app.py", "w") as f: f.write('\n'.join(lines))

# hazelcast
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/hazelcast_bridge.py") as f: t = f.read()
lines = t.split('\n')
for i in range(300, 500):
    if i < len(lines) and lines[i].startswith('                '):
        lines[i] = '            ' + lines[i].lstrip()
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/hazelcast_bridge.py", "w") as f: f.write('\n'.join(lines))

# jp_fiscal
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/jp_fiscal.py") as f: t = f.read()
lines = t.split('\n')
for i in range(116, 150):
    if i < len(lines) and lines[i].startswith('                        '):
        lines[i] = '            ' + lines[i].lstrip()
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/jp_fiscal.py", "w") as f: f.write('\n'.join(lines))

# open_lei
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/open_lei.py") as f: t = f.read()
lines = t.split('\n')
for i in range(320, 340):
    if i < len(lines) and lines[i].startswith('                        except'):
        lines[i] = '                    except' + lines[i].lstrip(' except')
    elif i < len(lines) and lines[i].startswith('                            '):
        lines[i] = '                        ' + lines[i].lstrip()
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/open_lei.py", "w") as f: f.write('\n'.join(lines))

# patent
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/patent.py") as f: t = f.read()
lines = t.split('\n')
for i in range(370, 420):
    if i < len(lines) and lines[i].startswith('            rows_inserted'):
        lines[i] = '        rows_inserted' + lines[i].lstrip(' rows_inserted')
    if i < len(lines) and lines[i].startswith('            batch = []'):
        lines[i] = '        batch = []'
    if i < len(lines) and lines[i].startswith('            kotoba_batch = []'):
        lines[i] = '        kotoba_batch = []'
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/patent.py", "w") as f: f.write('\n'.join(lines))

