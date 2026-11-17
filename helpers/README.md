# Helpers

The installer links each helper into `~/.claude/helpers/`. It also links
`sec`, `vfy`, `pr-wait` and `scrub-transcripts` into `~/.local/bin/`.
Run a helper with no arguments to see its usage.

- `sec` - Read and write secrets in the keyring (Secret Service on Linux,
  Keychain on macOS). Example: `sec run API_KEY=my-token -- ./deploy.sh`
- `secret-guard.py` - Hook guard. Modes: `prompt`, `pretool`,
  `sessionend`. It stores a pasted secret in the keyring, refuses a tool
  call that holds a secret value, and scrubs the transcript at the end.
- `secret-lib.py` - Shared secret patterns and keyring storage for the
  two tools above and for `scrub-transcripts`.
- `scrub-transcripts` - Dry run by default. Replace secrets in the saved
  transcripts with `{sec:NAME}`. Example: `scrub-transcripts --apply`
- `bash-guard` - PreToolUse hook. Refuses `cd <dir> &&`, `sed -n`,
  `sleep N`, `grep -r`, heredoc edits, and a `model` override on a
  `worker`. Skip one command with `# guard:ok`. Test: `bash-guard --self-test`
- `session-peers` - SessionStart hook. Lists the other Claude sessions in
  the same git repository.
- `vfy` - Run the typecheck, check-types, check and lint scripts in the
  git root. Example: `vfy`
- `pr-wait` - Wait for the checks of a pull request and print a short
  result. Example: `pr-wait 123 --fail-fast`

Requirements: `python3`, `jq`, `gh` (for `pr-wait`), and `secret-tool`
(Linux, package `libsecret`) or `security` (macOS).
