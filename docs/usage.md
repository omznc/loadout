# Usage analysis

This analysis selects the contents of the kit. The data comes from the
saved Claude Code transcripts on one machine, from 2026-10 to 2026-11.
All numbers are approximate. A subagent transcript can repeat the
context of its parent, so some calls count two times. Use the numbers as
a ranking only.

## Skills (Skill tool calls)

| Skill | Calls | Source |
| --- | ---: | --- |
| `pr-review` | ~404 | original |
| `deslop` | ~367 | original |
| `modern-web-guidance` | ~133 | GoogleChrome/modern-web-guidance |
| `test-audit` | ~18 | adapted from openclaw/openclaw |
| `apple-design` | ~16 | emilkowalski/skill |
| `mattpocock-skills:grilling` | ~5 | plugin |
| `mattpocock-skills:domain-modeling` | ~4 | plugin |
| `improve-animations` | ~4 | emilkowalski/skill |
| `good-css` | ~4 | vojtaholik/good-css |
| `audit-website` | ~2 | squirrelscan/skills |
| `audit-docs` | ~2 | original |
| `animate` | ~2 | emilkowalski/skill |
| `improve` | ~1 | shadcn/improve |

`deslop` and `pr-review` run together: a CLAUDE.md rule runs them before
each branch is done.

## Subagents (Agent tool calls)

| Agent | Calls |
| --- | ---: |
| `worker` | ~1700 |
| `general-purpose` | ~1550 |
| `Explore` | ~150 |
| `researcher` | ~130 |
| `lookup` | ~7 |

## Helpers (calls in Bash commands)

| Helper | Calls |
| --- | ---: |
| `cccc` | ~2900 |
| `sec` | ~1650 |
| `pr-wait` | ~600 |
| `scrub-transcripts` | ~30 |
| `vfy` | ~25 |

The hooks (`secret-guard.py`, `bash-guard`, `session-peers`) run on each
prompt, tool call or session, so they have no call count.

## Not in the kit

- Skills that `skillOverrides` turned off: the planetscale skills,
  `find-skills`, `review-animations`, `squirrelscan`.
- The mattpocock skills from the skills lock. The `mattpocock-skills`
  plugin has the same skills.
- `reverse-engineer-anything`. It needs the REA MCP server. Install it
  from https://github.com/morluto/rea if you need it.
- Helpers for one machine or one project (servers, games, mobile builds).
