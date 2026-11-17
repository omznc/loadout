#!/usr/bin/env bash
# Install loadout into the Claude Code config folder with symlinks.
# A second run changes nothing. Usage: ./install.sh [--force] [--extras] [--no-plugins] [--no-cccc]
set -euo pipefail

REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CLAUDE_DIR=${CLAUDE_CONFIG_DIR:-$HOME/.claude}
BIN=$HOME/.local/bin
FORCE=0 EXTRAS=0 PLUGINS=1 CCCC=1
STAMP=$(date +%Y%m%d-%H%M%S)

# Official marketplace plugins. EXTRA_PLUGINS are third-party: install them only with --extras.
OFFICIAL_PLUGINS=(context7 claude-security mattpocock-skills)
EXTRA_MARKETPLACES=(DietrichGebert/ponytail)
EXTRA_PLUGINS=(ponytail@ponytail)
BIN_HELPERS=(sec vfy pr-wait scrub-transcripts)

for arg in "$@"; do
  case $arg in
    --force) FORCE=1 ;;
    --extras) EXTRAS=1 ;;
    --no-plugins) PLUGINS=0 ;;
    --no-cccc) CCCC=0 ;;
    -h|--help) sed -n '2,3p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

say() { printf '%s\n' "$*"; }
warn() { printf 'warn: %s\n' "$*" >&2; }

# link SRC DST: make DST a symlink to SRC. Keep a foreign DST unless --force (then back it up).
link() {
  local src=$1 dst=$2
  if [[ -L $dst && $(readlink "$dst") == "$src" ]]; then return; fi
  if [[ -e $dst || -L $dst ]]; then
    if (( ! FORCE )); then warn "skip $dst (exists; use --force to back it up and replace it)"; return; fi
    # Back up outside the skills and agents folders, so that Claude does not load the copy.
    local bak=$CLAUDE_DIR/backups/loadout-$STAMP/${dst#"$HOME"/}
    mkdir -p "$(dirname "$bak")"
    mv "$dst" "$bak"
    say "backup $bak"
  fi
  ln -s "$src" "$dst"
  say "link $dst"
}

check_deps() {
  local cmd
  for cmd in git jq python3 curl; do
    command -v "$cmd" >/dev/null || warn "$cmd is not installed; some steps or helpers need it"
  done
  if [[ $(uname -s) == Darwin ]]; then
    command -v security >/dev/null || warn "security is missing; sec needs the macOS Keychain"
  else
    command -v secret-tool >/dev/null || warn "secret-tool is missing; sec needs it (dnf install libsecret / apt install libsecret-tools)"
  fi
}

init_submodules() {
  [[ -e $REPO/.git ]] || return 0
  git -C "$REPO" submodule update --init --depth 1 --quiet
}

link_files() {
  local f
  mkdir -p "$CLAUDE_DIR"/{skills,agents,helpers} "$BIN"
  for f in "$REPO"/skills/*; do link "$f" "$CLAUDE_DIR/skills/${f##*/}"; done
  for f in "$REPO"/agents/*.md; do link "$f" "$CLAUDE_DIR/agents/${f##*/}"; done
  for f in "$REPO"/helpers/*; do
    if [[ -f $f && ${f##*/} != README.md ]]; then link "$f" "$CLAUDE_DIR/helpers/${f##*/}"; fi
  done
  for f in "${BIN_HELPERS[@]}"; do link "$REPO/helpers/$f" "$BIN/$f"; done
  link "$REPO" "$CLAUDE_DIR/loadout"
  case :$PATH: in *:"$BIN":*) ;; *) warn "$BIN is not on PATH; add it so that sec, vfy and pr-wait resolve" ;; esac
}

import_rules() {
  local file=$CLAUDE_DIR/CLAUDE.md line="@$CLAUDE_DIR/loadout/CLAUDE.md"
  touch "$file"
  if grep -qxF "$line" "$file"; then return; fi
  printf '\n%s\n' "$line" >>"$file"
  say "import added to $file"
}

# Merge settings.json: keys that exist in the user's file win; hook groups are added once.
merge_settings() {
  local file=$CLAUDE_DIR/settings.json tmp
  [[ -s $file ]] || echo '{}' >"$file"
  tmp=$(mktemp)
  jq --arg dir "$CLAUDE_DIR" --slurpfile frag "$REPO/settings.json" '
    def dedupe: reduce .[] as $x ([]; if any(.[]; . == $x) then . else . + [$x] end);
    ($frag[0] | walk(if type == "string" then gsub("\\$HOME/\\.claude"; $dir) else . end)) as $f
    | . as $cur
    | ($f | del(.hooks)) * $cur
    | .hooks = reduce ($f.hooks | keys[]) as $ev (($cur.hooks // {});
        .[$ev] = ((.[$ev] // []) + $f.hooks[$ev] | dedupe))
  ' "$file" >"$tmp"
  # Compare the content, not the bytes: Claude Code writes the file in a different format.
  if [[ $(jq -S . "$tmp") == "$(jq -S . "$file")" ]]; then rm "$tmp"; return; fi
  cp "$file" "$file.bak.$STAMP"
  mv "$tmp" "$file"
  say "settings merged into $file (backup: $file.bak.$STAMP)"
}

cccc_asset() {
  local os arch
  os=$(uname -s) arch=$(uname -m)
  [[ $arch == arm64 ]] && arch=aarch64
  case $os in
    Linux) echo "$arch-unknown-linux-musl" ;;
    Darwin) echo "$arch-apple-darwin" ;;
    *) return 1 ;;
  esac
}

install_cccc() {
  (( CCCC )) || return 0
  if command -v cccc >/dev/null; then return; fi
  local target tag name dir
  target=$(cccc_asset) || { warn "no cccc build for $(uname -s); see https://github.com/moznion/cccc"; return; }
  tag=$(curl -fsSL https://api.github.com/repos/moznion/cccc/releases/latest | jq -r .tag_name)
  name="cccc-$tag-$target.tar.gz"
  dir=$(mktemp -d)
  curl -fsSL -o "$dir/$name" "https://github.com/moznion/cccc/releases/download/$tag/$name"
  curl -fsSL -o "$dir/$name.sha256" "https://github.com/moznion/cccc/releases/download/$tag/cccc-$tag-$target.sha256"
  if command -v sha256sum >/dev/null; then
    (cd "$dir" && sha256sum -c --quiet "$name.sha256")
  else
    (cd "$dir" && shasum -a 256 -c --quiet "$name.sha256")
  fi
  tar -xzf "$dir/$name" -C "$dir" cccc
  install -m 755 "$dir/cccc" "$BIN/cccc"
  rm -rf "$dir"
  say "cccc $tag installed in $BIN"
}

install_plugins() {
  (( PLUGINS )) || return 0
  command -v claude >/dev/null || { warn "claude is not on PATH; skip plugins"; return; }
  local p m
  claude plugin marketplace add anthropics/claude-plugins-official >/dev/null 2>&1 || true
  for p in "${OFFICIAL_PLUGINS[@]}"; do
    claude plugin install "$p@claude-plugins-official" >/dev/null 2>&1 && say "plugin $p" || warn "plugin $p did not install"
  done
  (( EXTRAS )) || return 0
  for m in "${EXTRA_MARKETPLACES[@]}"; do claude plugin marketplace add "$m" >/dev/null 2>&1 || true; done
  for p in "${EXTRA_PLUGINS[@]}"; do
    claude plugin install "$p" >/dev/null 2>&1 && say "plugin $p" || warn "plugin $p did not install"
  done
}

check_deps
init_submodules
link_files
import_rules
merge_settings
install_cccc
install_plugins
say "done. Start a new Claude Code session to load the changes."
