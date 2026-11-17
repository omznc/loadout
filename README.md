# loadout

A Claude Code setup that you can install on a different machine: skills,
subagents, hooks, helpers and rules. The installer links each item into
`~/.claude`, so a `git pull` updates the setup.

The contents come from an analysis of real use. See
[docs/usage.md](docs/usage.md).

## Install

```sh
git clone --recurse-submodules --shallow-submodules https://github.com/omznc/loadout.git ~/loadout
~/loadout/install.sh
```

Then start a new Claude Code session.

The installer:
1. Links each skill, agent and helper into `~/.claude/skills`,
   `~/.claude/agents` and `~/.claude/helpers`.
2. Links `sec`, `vfy`, `pr-wait` and `scrub-transcripts` into
   `~/.local/bin`. Make sure that this folder is on your `PATH`.
3. Adds one import line for [CLAUDE.md](CLAUDE.md) to
   `~/.claude/CLAUDE.md`. It does not change your other rules.
4. Merges [settings.json](settings.json) into `~/.claude/settings.json`:
   the hooks, the status line, and no commit attribution. Your own keys
   stay. It makes a backup first.
5. Installs `cccc` from the GitHub release of
   [moznion/cccc](https://github.com/moznion/cccc), and checks the
   SHA-256 sum.
6. Installs the plugins `context7`, `claude-security` and
   `mattpocock-skills` from the official marketplace.

A second run changes nothing. The installer does not replace a file
that exists. Options:

| Option | Effect |
| --- | --- |
| `--force` | Move a file that exists to `~/.claude/backups/loadout-<time>/`, then link. |
| `--extras` | Also install third-party plugins: `ponytail` (DietrichGebert/ponytail). |
| `--no-plugins` | Do not install plugins. |
| `--no-cccc` | Do not install `cccc`. |

The installer uses `CLAUDE_CONFIG_DIR` if you set it.

Requirements: `git`, `jq`, `curl`, `python3`, and `secret-tool` (Linux,
package `libsecret`) or `security` (macOS). `pr-wait` needs `gh`.

## Contents

### Skills

| Skill | Source | Use |
| --- | --- | --- |
| `deslop` | original | Remove AI slop from the branch diff, with no behavior change. |
| `pr-review` | original | Review a branch or PR for correctness before it is ready. |
| `test-audit` | adapted from [openclaw/openclaw](https://github.com/openclaw/openclaw) (MIT) | Gate new tests, and find low-value tests. |
| `audit-docs` | original | Audit and slim down CLAUDE.md and AGENTS.md files. |
| `modern-web-guidance` | [GoogleChrome/modern-web-guidance](https://github.com/GoogleChrome/modern-web-guidance) | Modern web platform patterns. |
| `good-css` | [vojtaholik/good-css](https://github.com/vojtaholik/good-css) | Modern CSS techniques. |
| `improve` | [shadcn/improve](https://github.com/shadcn/improve) | Read-only codebase survey and plans. |
| `animate`, `apple-design`, `improve-animations`, `find-animation-opportunities` | [emilkowalski/skill](https://github.com/emilkowalski/skill) | Motion and interface design. |
| `audit-website` | [squirrelscan/skills](https://github.com/squirrelscan/skills) | Website audit. Needs the `squirrel` CLI. |

Each upstream skill is a shallow git submodule in `vendor/`. The entry
in `skills/` is a relative symlink into the submodule.

### Subagents

| Agent | Model | Use |
| --- | --- | --- |
| `worker` | Sonnet | Change files, run builds and tests. |
| `lookup` | Haiku | Find a known file or symbol. |
| `researcher` | Sonnet | Read documentation and web sources. |

### Hooks and helpers

See [helpers/README.md](helpers/README.md).

| Hook | Helper | Effect |
| --- | --- | --- |
| UserPromptSubmit | `secret-guard.py prompt` | Store a pasted secret in the keyring, and give Claude only its name. |
| PreToolUse (Bash, Write, Edit) | `secret-guard.py pretool` | Refuse a tool call that holds a secret value. |
| PreToolUse (Bash, Agent) | `bash-guard` | Refuse shell patterns that waste context or cannot be undone. |
| SessionStart | `session-peers` | Show the other Claude sessions in the same repository. |
| SessionEnd | `secret-guard.py sessionend` | Scrub secrets from the transcript. |

### Rules

[CLAUDE.md](CLAUDE.md) holds the rules: no attribution, commit style,
staging by path, `deslop` then `pr-review` before a branch is done,
delegation to subagents, tool use, secrets with `sec`, complexity limits
with `cccc`, and verification.

[rules/ste.md](rules/ste.md) is optional. It makes Claude write all
prose in ASD-STE100 Simplified Technical English. To use it, add this
line to `~/.claude/CLAUDE.md`:

```
@~/.claude/loadout/rules/ste.md
```

## Update

```sh
git -C ~/loadout pull
git -C ~/loadout submodule update --init --depth 1
```

To move the upstream skills to their latest commit, run this command and
commit the result:

```sh
git -C ~/loadout submodule update --remote --depth 1
```

## Add a skill

- Original skill: add a folder with a `SKILL.md` in `skills/`.
- Upstream skill: add the repository as a submodule in
  `vendor/<owner>--<repo>`, then add a relative symlink in `skills/`:

```sh
git submodule add --depth 1 https://github.com/OWNER/REPO.git vendor/OWNER--REPO
git config -f .gitmodules submodule.vendor/OWNER--REPO.shallow true
ln -s ../vendor/OWNER--REPO/skills/NAME skills/NAME
```

Then run `./install.sh` again.

## License

[MIT](LICENSE). Each submodule in `vendor/` keeps the license of its
own repository. `skills/test-audit` is adapted from
[openclaw/openclaw](https://github.com/openclaw/openclaw) (MIT). The
Lean check in `skills/pr-review` comes from
[DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail)
(MIT).
