import os
def resolve_file(path):
    with open(path, 'r') as f:
        lines = f.readlines()
    out = []
    in_conflict = False
    for line in lines:
        if line.startswith('<<<<<<< HEAD'):
            in_conflict = True
        elif line.startswith('======='):
            pass
        elif line.startswith('>>>>>>> origin/main'):
            in_conflict = False
        else:
            out.append(line)
    with open(path, 'w') as f:
        f.writelines(out)

resolve_file('.claude/worktrees/identity-verification/90-docs/adr/README.md')
resolve_file('.claude/worktrees/identity-verification/CLAUDE.md')
