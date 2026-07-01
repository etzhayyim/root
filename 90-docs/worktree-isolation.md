# Worktree isolation (CRITICAL — concurrent-agent safety)

> Relocated from `CLAUDE.md` (2026-06-29) to keep the index lean. This is the
> authoritative text; `CLAUDE.md` keeps only the one-paragraph summary + the
> `worktree cleanup` / `closing` command triggers. No content changed.

**This repo's main checkout (`/Users/junkawasaki/github/etzhayyim-root`) is shared and
raced by multiple concurrent Claude agents** that `git checkout` different feature branches
in the *same* working tree. Untracked / uncommitted work in the shared checkout is fragile:
a sibling agent's `checkout` / `reset` / `clean` can wipe it without warning (observed
2026-06-04 — an entire untracked actor scaffold vanished mid-session).

**Rule — before ANY substantive multi-file work, Claude MUST isolate into a git worktree:**

1. **Enter a worktree first.** Use the `EnterWorktree` tool (creates an isolated checkout
   under `.claude/worktrees/<name>` on a fresh branch off `origin/main`) — or, outside this
   harness, `git worktree add .claude/worktrees/<name> origin/main`. Do the work there, not
   in the shared main checkout. (The `ooyake` agent already runs isolated in `/private/tmp/owt56`.)
2. **Commit early and often inside the worktree.** A commit is the only durable unit in a
   raced tree; a `git reset --hard` by a sibling cannot destroy a commit (recoverable via
   reflog), but it *will* destroy untracked files. Never leave a completed unit of work
   uncommitted.
3. **Scope commits to your own paths.** When the shared index already holds another agent's
   staged files, commit with an explicit pathspec (`git commit -- <your paths>`) so you do
   not sweep up a sibling's work.
4. **Branch off `origin/main`, not the current shared HEAD**, so a sibling's in-flight
   commit (e.g. another actor landing on the branch you happened to be on) does not become
   part of your history.
5. **Back up irreplaceable untracked work outside the git tree** (`cp -R … /tmp/…`) if you
   cannot commit immediately — insurance against a concurrent wipe.
6. **Treat the shared main checkout as read-only / not-yours.** It stays chronically dirty +
   divergent (uncommitted edits + a HEAD that is both ahead and behind `origin`); its working
   tree is a mix of *other* agents' in-flight work. Never commit it wholesale or assume its
   uncommitted state is yours.
7. **1 branch = 1 owner.** Do NOT push a divergent local commit onto a sibling's actively-CI'd
   PR branch (you'd graft onto their in-flight work + risk conflicts). To land such a commit,
   spin a fresh worktree off `origin/main`, `cherry-pick` it, and open its OWN PR (done
   2026-06-06: local `9a8600db59` → PR #1188, leaving the sibling's PR #1174 untouched).
   **Before pushing MORE commits to an existing branch, check whether ITS OWN PR already
   merged** — not just a sibling's: automation or the user can merge your own PR mid-session
   while you keep working on the same local branch. `gh pr view --head <branch> --json
   state,mergedAt` (or `gh pr list --head <branch> --state all`) first. If `state: MERGED`,
   do not push — the branch's ancestry is now orphaned from `origin/main`'s new (often
   squash-merged) history, and a later `git fetch`/`git merge` will surface as a genuine
   `diverged` state or a shallow-clone-flavored `refusing to merge unrelated histories`
   (see root `CLAUDE.md`'s ancestry-verification section to tell the two apart). Treat it
   exactly like the sibling case above: fresh worktree off `origin/main`, `cherry-pick` the
   new commit(s), open a new PR. Observed 2026-07-01: PR #2818 squash-merged (by the owner)
   while follow-up commits kept landing on `tsukuru-coverage-maturity`; recovered via
   fresh-worktree + cherry-pick → PR #2826, after closing the resulting dirty-diff PR #2825.
8. **cherry-picks from the shared checkout drag in yoro build artifacts.** Conflicts in
   `60-apps/etzhayyim-project-yoro/**/static/_app/immutable/*` (hashed SvelteKit chunks) are
   generated noise — resolve by restoring yoro to `origin/main` (`git checkout origin/main --
   60-apps/etzhayyim-project-yoro && git add`), never hand-merge them.

**Shell gotcha (zsh):** `$PIPESTATUS` is unset in zsh (it's `$pipestatus`, 1-indexed), so
`cmd | tail; echo ${PIPESTATUS[0]}` silently reports `tail`'s exit, not `cmd`'s. Check a
command's real exit before piping it (e.g. `git apply` failed-but-looked-OK this way).

Exit with `ExitWorktree` (`keep` to preserve the branch). The session's cron `/loop`
iterations continue inside whatever worktree the session is in.

**Rule — clean up once the branch is MERGED.** A worktree + branch is durable only while its
work is in flight. **After the branch's PR is merged into `origin/main`, delete BOTH the
worktree and the branch** — a merged branch left on disk is dead weight that clutters
`git worktree list` / `git branch` and invites confusion (a sibling agent checking out a
stale merged branch). Do NOT delete before merge (an open PR's branch is the only durable
copy of the work). Sequence once merge is confirmed:

1. `ExitWorktree` with `action: "remove"` (removes the `.claude/worktrees/<name>` checkout +
   its branch). It refuses if there are uncommitted/unmerged changes — that refusal means the
   merge is NOT actually complete, so stop and investigate, do not force.
2. Outside the harness, the equivalent is `git worktree remove .claude/worktrees/<name>` then
   `git branch -d <branch>` (lowercase `-d` = merged-only; it refuses an unmerged branch — use
   `-D` ONLY after confirming the work is truly merged). Prune stale registrations with
   `git worktree prune`. The `clean_gone` command also sweeps branches whose remote is `[gone]`.

Only the worktree whose PR is still open (or whose work is unmerged) is kept.

**Command — "worktree cleanup".** When the user says **`worktree cleanup`** (or asks to clean
up worktrees), run this exact sweep over the current branch + every worktree
(`git worktree list`); resolve each branch's PR state with `gh pr list --head <branch> --state all`:

- **PR MERGED** (or branch fully contained in `origin/main`, or remote `[gone]`) → **delete** the
  worktree + branch (`git worktree remove …` then `git branch -d/-D …`, per the sequence above).
- **No PR yet** and the branch has commits ahead of `origin/main` → **open a PR** (`git push -u`
  then `gh pr create --base main`). Skip a branch with nothing ahead of main.
- **PR already OPEN (unmerged)** → **leave it** untouched.

Then **reintegrate every stash** (`git stash list`): for each entry (newest first), **merge it back**
with `git stash pop` (apply + merge into the working tree). **On conflict, resolve it** — keep the
stash's genuine local edits; for raced substrate / generated build artifacts follow the main-priority
rule above (`git checkout --ours/--theirs -- <file>` as appropriate, restoring yoro `_app/immutable/*`
to `origin/main`), then `git add` the resolved paths. Once the apply is clean, **drop the stash**
(`git stash drop`; a clean `pop` already drops it). **Leave no stash behind after cleanup** — this
overrides the conservative "温存 / keep the stash" stance used during routine `main` sync, because
`worktree cleanup` is an explicit reconcile-and-finish request. (Skip a stash only if its conflict
genuinely cannot be resolved — surface it and stop rather than discard real work.)

Never commit/push the shared main checkout's dirty working tree (other agents' in-flight work);
push only the branch's committed HEAD. Report the final categorized outcome (worktrees + branches +
stashes reintegrated/dropped).

**Command — "closing" (one-shot close-out).** When the user's instruction contains the word
**`closing`** (英語語 "closing" を含む場合), take the CURRENT worktree's work all the way to
landed **without further confirmation** — run this sequence end-to-end for the active branch:

1. **Commit** any uncommitted work in the worktree (scoped to your own paths, per the
   worktree-isolation rules above).
2. **PR create** — `git push -u origin <branch>` then `gh pr create --base main` (skip if a PR
   already exists for the branch; reuse it).
3. **Merge to repo** — merge the PR into `origin/main` (`gh pr merge <#> --squash --delete-branch`,
   or the repo's standard merge). This is the explicit standing authorization to merge that the
   `closing` keyword grants; do not ask again. If merge is blocked (failing required checks,
   conflicts, review gates), STOP and report — do not force-merge past a real gate.
4. **Cleanup** — run the **"worktree cleanup"** sweep above (delete the now-merged worktree +
   branch via `ExitWorktree action: "remove"` / `git worktree remove` + `git branch -d`).

`closing` is the single keyword that authorizes the otherwise-confirmation-gated merge step;
absent it, stop at PR-open and leave merge to the user. Report the final state (PR URL, merge
commit, worktrees removed).
