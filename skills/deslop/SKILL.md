---
name: deslop
description: "Diff-scoped cleanup of AI slop in any repository: remove comment slop, defensive-check slop, type laundering and style drift from the diff of the current branch, with no behavior change. Run it before pr-review, never instead of it."
---

# Deslop

Clean only the diff of the current branch. Keep the behavior exactly the same.

## 0. Use the repository's own copy first

Look for `.agents/skills/deslop/SKILL.md` and `.claude/skills/deslop/SKILL.md`
in the repository root. If one exists, read it and follow it in place of this
file. It holds the rules and the commands of that repository.

## 1. Learn the repository

1. Find the default branch: `git symbolic-ref --short refs/remotes/origin/HEAD`.
   If that fails, use `origin/main`, then `origin/master`.
2. Read the root `AGENTS.md` or `CLAUDE.md`, and the one of each folder that the
   diff touches. Their rules apply to the diff.
3. Find the format and lint commands. Read the scripts in `package.json`,
   `Makefile`, `justfile`, `pyproject.toml` or `Cargo.toml`. Use the package
   manager that the lockfile shows (`bun.lock`, `pnpm-lock.yaml`,
   `package-lock.json`, `uv.lock`).

## 2. Checklist

1. Scope the pass to `git diff $(git merge-base <default branch> HEAD)`.
   Include the uncommitted changes. Never clean the whole repository.
2. Examine each changed hunk for these items:
   - A comment that a maintainer would not write: narration, an explanation of
     the syntax, or prose that restates the code. A comment must state a
     reason: why the code does what it does, or which invariant it keeps.
   - A defensive check or a `try`/`catch` block that is not normal for the
     module, or that protects only a state that cannot occur.
   - A cast that launders a type, for example `as any`, `as unknown as T`, or a
     widen-then-assert flow. Do not add a cast. If the repository asks for a
     comment on a cast (for example `SAFETY:`), keep that rule.
   - A redundant intermediate variable, or a helper with one use, that adds no
     domain meaning, removes no duplication and does not make the control flow
     simpler.
   - A compatibility shim, an alias, a retry or a fallback branch with no named
     contract and no plan to remove it.
   - Naming, control flow, imports, formatting or other style that conflicts
     with the file around it. Match that file.
3. Make no functional edit. If a cleanup can change the behavior, leave the
   code and report it.
4. Fix an item in place only when the fix is trivial and keeps the behavior.
   Otherwise, note it for the author.
5. Run the formatter and the linter of the repository. Report the result in one
   to three sentences. Say if anything changed. Name each item that you left
   for review.

## 3. Do not repeat the linter

Run the linter first and read its output. Look at what a linter cannot see:
comments, needless defensive code, one-use helpers, and drift from the style
of the file. Do not add a new warning.

## 4. Commits

If you commit a cleanup, follow the commit rules of the repository and of the
user. Stage each file by its path. Never run `git add -A`, `git add .` or
`git commit -a`. Never run `git stash`. Do not push.

## 5. Order of work

Run `deslop` before `pr-review`. Never run it in place of `pr-review`.
`pr-review` is the review gate for correctness and safety.
