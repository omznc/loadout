---
name: audit-docs
description: Audit and clean up the agent instruction files of a repository (CLAUDE.md, AGENTS.md, nested workspace files, and the docs they point to). Measures what each file costs in context, finds stale facts, misplaced rules, duplicates and long narrative in always-loaded files, then moves, trims and fixes them with no loss of rules. Use when asked to audit, clean up, split, slim down or update CLAUDE.md / AGENTS.md files, or /audit-docs. Pass "report" to stop after the audit.
---

# Audit the agent docs

The goal: each rule loads when, and only when, an agent touches the code that it is about. An always-loaded file holds rules. An on-demand doc holds the narrative that explains the rules.

Mode: if the arguments contain `report`, do phases 1 to 3 only. Otherwise do all phases, and stop for approval after phase 3.

## How the files load (Claude Code)

- The root `CLAUDE.md` (and `~/.claude/CLAUDE.md`) loads at the start of each session.
- A nested `CLAUDE.md` loads when the agent reads a file in that folder or below it.
- A file that a `CLAUDE.md` only names (for example `docs/domains/x.md`) does not load. The agent must choose to read it.
- An `@path` import in a `CLAUDE.md` loads the imported file at the same time as the importer. It does not save context. Do not use it to "split" a file.
- Codex and similar tools read `AGENTS.md` on the path from the root to the start folder. If both names exist, check whether one is a symlink to the other. Keep that set-up.

Thus a rule for `apps/web/src/server/x.ts` that lives in `apps/cli/CLAUDE.md` never loads when an agent edits `x.ts`. A misplaced rule is a bug, not a style problem.

## Phase 1: Inventory and measure

1. List every instruction file and every doc that one of them points to:
   `git ls-files '*CLAUDE.md' '*AGENTS.md' '.cursorrules' '.github/copilot-instructions.md' '.cursor/rules/*'`
   Then collect each `docs/...` path that the files name.
2. For each file, print the lines, the bytes and the symlink target. Estimate tokens as bytes / 4.
3. List the workspaces or packages (from `package.json` workspaces, `pnpm-workspace.yaml`, `Cargo.toml`, `go.work`, or the top-level folders). Mark each one that has no instruction file.
4. Compute the context cost of a typical task: root + the nested files on the path of a normal change (for example root + web + core). Write this number down. Phase 6 compares against it.

Bytes matter more than lines. A file with one paragraph per line can have 50 lines and 15 KB.

## Phase 2: Read and check

Read each always-loaded and nested file in full. For a long file, read it in parts. Delegate the reads of the on-demand docs to a subagent if there are many. Ask it for a list of the claims and the paths each doc makes, not for a summary.

Check each item below. Record each finding with `file:line`, the evidence and the fix.

1. **Stale facts.** Check each concrete claim against the code: "X has no tests", "the only place that does Y", a file path, a script name, a command, a count, a version, an env var name. Use `git ls-files`, `rg` and the `package.json` scripts. A path that does not exist and a claim that the code contradicts are both stale. The code is correct. Fix the doc.
2. **Misplaced rules.** For each rule, find the files that it is about. If those files are not under the folder of the instruction file, the rule is misplaced. Move it to the nearest instruction file that covers those files, or to the root if the rule applies everywhere.
3. **Duplicates.** The same rule, list, table or command block in more than one file. Keep one copy in the most specific file that always loads when needed. Replace the other copies with nothing, or with a one-line pointer when the reader needs the link.
4. **Narrative in always-loaded files.** A bullet or section that explains history, reasons in depth, a design, a sequence of events or a full API is narrative. Keep the rule as one or two sentences. Move the rest to an on-demand doc. Indicators: more than about 600 bytes for one bullet, "because ... because ...", issue numbers, incident stories, a list of every file in a folder.
5. **Derivable content.** A file list, a folder tree, a list of scripts, a dependency list: the agent can get it from `ls`, `package.json` or the code. Delete it, unless an item has a note that is not obvious. Keep only those notes.
6. **Missing files.** A workspace with its own rules (its own design system, a published API, a release process, platform rules) and no instruction file. Propose a short file (about 15 to 30 lines) with the rules only and pointers to its docs.
7. **Wrong kind of content.** Release steps, on-call procedures and user-facing setup belong in a `README`, `RELEASING.md` or `docs/`. A tool's history belongs beside the tool.
8. **Contradictions.** Two files that state different rules for the same thing. Check the code to find which one is correct.
9. **Dead pointers.** A pointer to a doc, ADR, skill or section that does not exist.
10. **Large on-demand docs.** A doc over about 25 KB that an agent must read in full for most tasks in its area. Propose a split by sub-topic only if the parts are read for different tasks. Low priority.

Do not flag a rule only because it is long, if every sentence is a rule. Do not delete a rule because it looks obvious. A rule usually exists because an agent broke it.

## Phase 3: Report

Give one report. Use this format:

1. A table of the files: size, tokens, when the file loads.
2. The typical-task cost from phase 1.
3. The findings, grouped by the categories above, with the most severe first. Stale facts and misplaced rules come first, because they cause wrong work. Each finding has `file:line`, a one-line problem and a one-line fix.
4. The proposed moves: a list of "text from `A:lines` goes to `B` (new or existing)", and "`A:lines` stays as: <the one-line rule>".
5. The estimated cost after the change.

Then stop. Ask the user which groups to apply. If the mode is `report`, end here.

## Phase 4: Apply

Rules:
- **No loss of rules.** Each rule that you remove from a file must exist after the change in a file that loads when it applies, or in an on-demand doc that a loaded file points to. Before you delete a paragraph, write where each of its rules goes.
- Move text. Do not rewrite it when it is correct. Keep the style of the repository (its language rules, its tone, its format). If a global or a repository rule sets a prose style, use it for new text.
- Keep the symlink set-up (`AGENTS.md` -> `CLAUDE.md`). Give each new nested `CLAUDE.md` the same symlink, if the repository uses one.
- A new on-demand doc goes in the folder that the repository already uses for docs (`docs/`, `docs/domains/`, `docs/architecture/`). Add it to the index table or list of docs, if one exists.
- A pointer line names the doc and what to read it for: "Read `docs/x.md` before you change Y."
- Do not change code. Do not change a doc that is not an instruction file, except to receive moved text or to fix a stale fact that you found.
- Work on a branch if the repository asks for one. Do not commit unless the user asks.

Order of the work:
1. Fix the stale facts.
2. Move the misplaced rules.
3. Remove the duplicates.
4. Move the narrative out and leave the one-line rules.
5. Delete the derivable content.
6. Add the missing workspace files.

## Phase 5: Verify

1. Each path, script and command that the changed files name exists. Check with `git ls-files` and the `package.json` scripts.
2. Each pointer resolves to a file and, if it names one, a section.
3. Make a list of the rules in the old files (`git diff` on the removed lines). Find each one in the new set of files. Report any rule that you did not find. Fix it before you continue.
4. Run the format and lint scripts of the repository, if they cover Markdown.

## Phase 6: Final report

- The size table before and after, and the typical-task cost before and after.
- The list of moves and new files.
- The stale facts that you fixed.
- The findings that you did not apply, and why.
- What you did not check.
