# loadout rules

An import line in `~/.claude/CLAUDE.md` loads this file in each session.

# No attribution

Never add attribution to Claude, Claude Code, or Anthropic in a commit,
a pull request, an issue, a comment, a file, or a changelog. The user is
the only author.

# Commit messages

Write the subject line in the imperative mood: "add", "fix", "remove".
Write a maximum of 50 characters where possible, never more than 72, and
no period at the end. Read the last 20 subjects of the repository first,
and use the same prefix convention (conventional commits, a subsystem
prefix, or no prefix). In the body, explain the reason for the change.
Wrap the body at 72 characters.

# Git staging

Stage only the files that you changed. Stage each file by its path. Do
not use `git add -A`, `git add .`, or `git commit -a`. These commands can
commit changes from the user or from a different session.

# Review before a branch is done

Run the `deslop` skill, then the `pr-review` skill, on the work. Do this
one time, before you mark a PR ready or tell the user that the branch is
done. Do this for every non-default branch, and for every repository
that the user does not own.

- Run `deslop` first. Never run it in place of `pr-review`.
- `pr-review` is expensive. Run it in a background `Agent`, and do other
  work until the notification arrives.
- Run `pr-review` again only after a fix that changes the logic of the
  code. A fix to a comment, a name or a format does not need a new review.

# Delegation

Give a task with a clear scope to a subagent. Keep the plan, the
decisions, and the review in the main session.
- Use `worker` to change files, and to run a build or a test.
- Use `lookup` to find a known file or symbol.
- Use `researcher` for documentation and web sources.
- Use `general-purpose` only for a task that needs heavy reasoning.
- Do not pass `model` to a `worker`. The `bash-guard` hook refuses it.

# Parallel sessions

The `session-peers` SessionStart hook lists the other Claude sessions in
the same git repository. If it lists a session:
- Tell the user which sessions it found.
- Use a worktree if the other session can change the same files, or if
  your task changes the git state (branch, stash, commit, rebase).
- Do not reset, stash, or commit files that the other session changed.

# Tool use

The `bash-guard` PreToolUse hook enforces these rules. Add `# guard:ok`
to a command only when no other way works.
- To read part of a file, use the Read tool with offset and limit. Do not
  use `sed -n`.
- To search, use `rg -n -g '*.ts' "pattern"`. Do not use `grep -r`.
- Use absolute paths. Do not start a command with `cd <repo> &&`.
- To wait for a condition, use Monitor with an until-loop, or
  `run_in_background`. Do not use `sleep N`.
- To change a file, use the Edit tool. Do not use a script heredoc that
  replaces text. A shell edit cannot be undone with `/rewind`.

# Tool output

Each tool result stays in the context. Keep the results small:
- Pipe a build, a test or a log command through `tail -n 50` or `rg`.
- Do not read a file again if it did not change.
- Read a large file in parts with offset and limit.

# Secrets

- Never write a secret value in a command, a file, a commit or a
  message.
- To use a secret, run `sec get NAME` inside the command, for example
  `Authorization: Bearer $(sec get github-token)`.
- If the user pastes a secret, the `secret-guard.py` hook stores it in
  the keyring and tells you the name. Use the name.
- Remind the user to rotate a secret that was pasted in the open or
  printed in a log.

# Code complexity (cccc)

After you write or change code, run
`cccc --table --max-cognitive 15 --max-cyclomatic 10 <changed files>`.
- If a function that you wrote is over a limit, split it. Do not split it
  if the split makes the code harder to read.
- Do not refactor old code only to pass the limits. Report it.
- If the repository has a `cccc.toml`, use the limits from that file.
- Do not use `--cache`.

# Checks

- Run `vfy` to run the typecheck, check and lint scripts of the
  repository.
- Run `pr-wait <PR>` to wait for the checks of a pull request.

# Web UI

Before you write or change a web UI, run the `modern-web-guidance` skill
one time for each task.

# Verification

Before you say that a UI, a build or a script works, check the real
result. Run the program, or take a screenshot. If you cannot check the
result, say so in the first sentence.
