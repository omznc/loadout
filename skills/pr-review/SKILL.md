---
name: pr-review
description: "Review a branch or pull request in any repository for correctness before it is marked ready, or review another person's PR. Checks each dependency claim against its source, sweeps for sibling sites and other paths into the changed code, and runs the tests on the base and on the branch. Use one time before marking a PR ready, again only after a fix that changes code logic, or when asked to review a PR."
argument-hint: "[PR number | branch | commit] [--post]"
context: fork
model: opus
effort: high
---

# PR review

Review one change as a careful maintainer does. Find the defects that the
author's own tests cannot find. The tests check the author's assumptions, and
the defects are in those assumptions.

The review is read-only. Do not edit, commit, push, comment or approve. Post to
GitHub only when the caller gives `--post` (see "Report").

## 0. Use the repository's own copy first

Look for `.agents/skills/pr-review/SKILL.md` and
`.claude/skills/pr-review/SKILL.md` in the repository root. If one exists, read
it and follow it in place of this file. It holds the rules, the commands and
the callers of that repository.

## 1. Pin the target

Find the default branch: `git symbolic-ref --short refs/remotes/origin/HEAD`.
If that fails, use `origin/main`, then `origin/master`.

Resolve the argument to one commit and one base:

- A PR number: `gh pr view <n> --json headRefOid,baseRefName,body,title`.
  Fetch the head commit: `git fetch origin pull/<n>/head`.
- A branch: its head, against the default branch.
- Nothing: the current branch head, against the default branch.

Find the base with `git merge-base <head> origin/<base>`. Write the short head
SHA at the top of the report ("At `abc1234`: ..."). A later round then reviews
only the commits after that SHA. If an earlier review on the PR names a SHA,
read that review first. Review only `git log <old>..<head>`. Do not raise a
finding again that the author already answered.

Do not review in the main checkout. Run `git worktree add --detach` on the head
commit in a folder outside the repository. Install the dependencies there with
the package manager that the lockfile shows. If the repository has a worktree
setup script, run it. Remove the worktree at the end. Never run `git stash`.

## 2. Read before you judge

1. Read the PR body, the linked issue and the full diff
   (`git diff <base>..<head>`).
2. Read each changed file in full, not only the hunks.
3. Read the root `AGENTS.md` or `CLAUDE.md`, and the one of each folder that the
   diff touches.
4. Read each document that those files name for the changed code, for example
   a `docs/` page or an ADR. Read the ADRs when the change can contradict a
   decision.
5. Find the test, lint and typecheck commands in the scripts of the repository.

## 3. The checks

Do every check.

### 3.1 Dependency contracts: cite the source

For each place where the diff depends on a library, a framework, a runtime or
an external API (what it calls, throws, returns, emits or swallows), find the
proof and cite it:

- A package: the file and the line in the installed dependency, for example in
  `node_modules`, the virtual environment or the module cache.
- An external API: the documentation page and the quoted sentence. Fetch the
  page. Do not answer from memory.
- A runtime: run a small probe script when the documentation is not clear.

Then ask what the dependency does in the cases that the diff does not handle.
Examples:

- An error state that arrives inside a 200 response.
- A preload or a prefetch that runs the same code path as a navigation.
- A timeout that throws a different error class than an abort.

A claim with no citation is a finding.

### 3.2 Siblings: the same fix in other places

- Search for each string, constant, error message and pattern that the diff
  adds or changes. If the diff adds a constant, find each literal that still
  has the same value. If the diff fixes a pattern, find each other place with
  the same pattern.
- When the diff fixes a defect in one function, find the functions with the
  same shape and check them for the same defect.

### 3.3 Other paths into the changed code

List each caller of each changed exported function, for example a web handler,
a REST route, a CLI command, a background job, a queue consumer or an agent
tool. Say how the change affects each caller. If the PR fixes a problem for one
caller, check if another caller has the same problem. If the PR body says that
a caller is left out on purpose, check the reason.

### 3.4 Cost under load

Say what the change costs on the server when many clients use it at the same
time. Examples:

- A deploy that makes each open tab request a missing file.
- An agent loop that reads a range again and again.
- A 404 that runs a full server render.

A cost that the change did not cause is still a finding when it is on the path
that the change works on. Mark it "pre-existing" and recommend the fix.

### 3.5 The rules of the repository

Check the diff against each rule in the `AGENTS.md` or `CLAUDE.md` files that
you read. Also check secrets: no token, key or password in the code, a log
line, a test fixture or the PR body.

### 3.6 Tests on both sides

Run the tests of each touched package on the base and on the head. Run the base
and the head one after the other, never at the same time. Limit the test
workers to 4 (`--maxWorkers=4` for jest and vitest, `--test-concurrency=4` for
`node --test`). One jest run with the default workers can use 10 GiB. Run the lint
and the typecheck on the head. For each new test, check that it fails on the
base. A test that passes on both sides does not prove the fix. If a
`test-audit` skill is available, follow it for the value of each new test.

Each behaviour change that the PR body lists needs a test that holds it. A
listed fix with no test is a finding, also when the pure helpers around it have
tests.

### 3.6a Old behaviour against new behaviour

The checks above compare the new code with its claims. This check compares the
new code with the old code. Do it for each replaced expression, helper call or
moved block, also in a refactor that says "no behaviour change".

- Boundary inputs. When a call site moves to a new helper (for example
  `Number(env)` to `durationFromEnv(env)`), give the old code and the new code
  the same edge values: `0`, empty, unset, negative, `null`, `NaN`. Each output
  that is different is a finding, unless the PR body states it for that call
  site.
- Lost output. When the diff wraps, filters or reduces a value that goes to a
  log, a toast, an error or a response, list the fields that the old code showed
  and the new code drops. A dropped field is a finding, unless the PR body says
  why.
- Swallowed errors. Each new `catch` that does not rethrow must log the error or
  state why it does not.
- Order and concurrency. A sequence that becomes `Promise.all`, or a parallel
  call that becomes a sequence, is a behaviour change. Say what happens now when
  the first call fails.
- One write, many readers. When a write path writes more than one record (two
  tombstones, a row and an event), find each reader that reads more than one of
  them. Check that a count or a total does not add the same thing two times.

### 3.6b Decisions in documents

When the diff changes an ADR or a domain document to reverse a decision, the
new text must name its source (an issue, a thread, a person). A reason such as
"at the owner's request" with no source is a finding.

### 3.7 What a person sees

For a UI change, start the app and look at the change in a browser. Check the
empty state, the error state and a slow network. If you cannot start the app,
say so in the report.

### 3.8 The PR body

Each claim in the PR body must be true at the head SHA. A false claim is a
finding.

### 3.9 Lean

This check comes from the `ponytail-review` skill of
[DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) (MIT).

Find code in the diff that should not exist or should be smaller. `deslop`
removes surface slop (comments, defensive checks, casts). This check asks
whether the structure is necessary.

- Delete: dead code, an option that no caller sets, a speculative feature.
- Reuse: the repository already has the helper. Name its path.
- Standard library: the language or the platform already does it, or a new
  dependency replaces a few lines.
- YAGNI: an abstraction with one implementation, a config value that nobody
  sets.
- Merge: near-copies that must change together.
- Split: one function that does unrelated jobs. Split by job, never by line
  count.

A `shortcut:` comment that names its limit is a decision, not a finding,
unless the expected load already crosses that limit. Each lean finding needs a
concrete case, as in section 4. A lean finding never blocks a merge.

## 4. Verify each finding

Before you report a finding, try to prove it wrong. Read the code that would
make it wrong. Run a probe when you can. Drop a finding that you cannot support
with a file and a line, a quoted source or a command output. Keep a finding as
"uncertain" only when you name the one fact that would decide it.

## 5. Report

Start with: `At <short SHA>: <what you read>, <what you ran and the result>.`
Then say if the fix is correct and in the correct layer, in one or two
sentences.

Then list each finding, most severe first:

- `file:line` and one sentence that states the defect.
- The concrete failure: the input or the state, and the wrong result.
- The proof: the citation, the search result or the command output.
- The change that you recommend.

Then list the notes that need no change.

When section 3.9 found lean findings, end with `Lean: -<N> lines possible.`

If the caller gave `--post` and the target is a PR:

- Post one review with `gh api repos/{owner}/{repo}/pulls/<n>/reviews`, with
  one inline comment for each finding.
- Use `REQUEST_CHANGES` when a finding needs a change, and `COMMENT` otherwise.
  Never use `APPROVE`.
- Follow the writing rules of the user. Add no signature or attribution.

Without `--post`, return the report to the caller only.
