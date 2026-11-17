"""Shared secret detection and keyring storage for the Claude helpers.

The detectors match known formats only. This keeps false positives low.
The keyring entries use the attributes: service claude-helper, key NAME.
This module never prints a secret value.
"""
import hashlib
import os
import re
import subprocess

SERVICE = "claude-helper"

# A token that starts here is not a literal value.
_NOT_LITERAL = "${(<*"

_PLACEHOLDER = re.compile(
    r"^(password|passwd|changeme|change_me|example|examples?_?\w*|x{3,}|\*+|"
    r"redacted|null|none|true|false|your[_\-].*|<.*>|secret|test|testing)$",
    re.I,
)

# (kind, compiled regex, group index of the secret value)
DETECTORS = [
    ("cloudflare-access", re.compile(r"(?<![A-Za-z0-9])cfast_[A-Za-z0-9]{20,}"), 0),
    ("sanctum", re.compile(r"\b\d{1,4}\|[A-Za-z0-9]{36,}\b"), 0),
    ("github", re.compile(r"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{30,}"), 0),
    ("github-pat", re.compile(r"(?<![A-Za-z0-9])github_pat_[A-Za-z0-9_]{40,}"), 0),
    ("sk", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_\-]{24,}"), 0),
    ("slack", re.compile(r"(?<![A-Za-z0-9])xox[abprs]-[A-Za-z0-9\-]{20,}"), 0),
    ("aws", re.compile(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])"), 0),
    ("bearer", re.compile(r"\bBearer[ \t]+([A-Za-z0-9._\-|]{24,})"), 1),
    (
        "password",
        re.compile(
            r"(?i)(?<![A-Za-z])password\\*[\"']?[ \t]*[:=][ \t]*\\*[\"']?"
            r"([^\s\"'\\,;&)(}\]<>`]{6,})"
        ),
        1,
    ),
]

# A command that reads a secret from the keyring is safe.
_SAFE_REF = re.compile(r"\$\(\s*(?:sec\s+get|secret-tool\s+lookup)\b[^)]*\)")
_SEC_TOKEN = re.compile(r"\{sec:[^}\s]*\}")


def _plausible(kind, value):
    """Return True if the value looks like a real secret."""
    if value[0] in _NOT_LITERAL:
        return False
    if kind == "bearer":
        # An all-lowercase word without a digit is a name, not a token.
        return not re.fullmatch(r"[a-z_.\-]+", value)
    if kind == "password":
        if _PLACEHOLDER.match(value):
            return False
        # A plain word is a type name or a variable name.
        if re.fullmatch(r"[A-Za-z_]+", value):
            return False
        if value.lower().startswith(("your_", "your-", "process.", "env.")):
            return False
        # A URL, a host:port value, or a property access is not a password.
        if "://" in value or re.fullmatch(r"[\w.\-]+:\d+(/.*)?", value):
            return False
        if re.fullmatch(r"[A-Za-z_]\w*(\.[A-Za-z_]\w*)+", value):
            return False
        # A real password has a digit or a special character.
        if not re.search(r"[0-9!@#$%^&*+=?~]", value):
            return False
    if kind == "sanctum":
        # A real token has letters. A long digit string is not a token.
        return bool(re.search(r"[A-Za-z]", value.split("|", 1)[1]))
    return True


def find_secrets(text):
    """Return a list of (kind, value, start, end) with no overlap."""
    skip = [m.span() for m in _SAFE_REF.finditer(text)]
    skip += [m.span() for m in _SEC_TOKEN.finditer(text)]
    found = []
    for kind, rx, grp in DETECTORS:
        for m in rx.finditer(text):
            start, end = m.span(grp)
            value = m.group(grp)
            if not _plausible(kind, value):
                continue
            if any(a <= start and end <= b for a, b in skip):
                continue
            found.append((kind, value, start, end))
    # Keep the longest match first. Drop any match that overlaps.
    found.sort(key=lambda f: (f[2], -(f[3] - f[2])))
    result = []
    last_end = -1
    for item in found:
        if item[2] >= last_end:
            result.append(item)
            last_end = item[3]
    return result


def name_for(kind, value):
    digest = hashlib.sha256(value.encode("utf-8", "surrogateescape")).hexdigest()
    return "auto-%s-%s" % (kind, digest[:8])


# `sec` picks the keyring of the OS (Secret Service or the macOS Keychain).
_SEC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sec")


def exists(name):
    r = subprocess.run([_SEC, "get", name], capture_output=True, timeout=30)
    return r.returncode == 0 and len(r.stdout) > 0


def store(kind, value):
    """Store the value in the keyring. Return the name. Raise on failure."""
    name = name_for(kind, value)
    if exists(name):
        return name
    r = subprocess.run(
        [_SEC, "set", name],
        input=value.encode("utf-8", "surrogateescape"),
        capture_output=True,
        timeout=30,
    )
    if r.returncode != 0:
        raise RuntimeError("sec set failed for " + name)
    return name


def apply_redactions(text, found, names):
    """Replace each found value with {sec:NAME}. names maps value to name."""
    out = []
    pos = 0
    for kind, value, start, end in found:
        out.append(text[pos:start])
        out.append("{sec:%s}" % names[(kind, value)])
        pos = end
    out.append(text[pos:])
    return "".join(out)


def redact(text):
    """Store each secret, then return (new_text, [names])."""
    found = find_secrets(text)
    if not found:
        return text, []
    names = {}
    for kind, value, _s, _e in found:
        if (kind, value) not in names:
            names[(kind, value)] = store(kind, value)
    new_text = apply_redactions(text, found, names)
    ordered = []
    for n in names.values():
        if n not in ordered:
            ordered.append(n)
    return new_text, ordered
