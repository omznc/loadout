#!/usr/bin/env python3
"""Hook guard that keeps secrets out of Claude sessions.

Usage: secret-guard.py prompt|pretool|sessionend
The hook JSON comes on stdin. On any error, the guard exits 0 with no output.
"""
import importlib.util
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load_lib():
    spec = importlib.util.spec_from_file_location(
        "secret_lib", os.path.join(HERE, "secret-lib.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def do_prompt(data, lib):
    prompt = data.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        return 0
    if not lib.find_secrets(prompt):
        return 0
    new_text, names = lib.redact(prompt)
    if not names:
        return 0
    shown = new_text[:1500]
    reason = (
        "A secret value in your message was stored in the keyring as: %s. "
        "The prompt was blocked so that the value stays out of the session. "
        "Send the message again with this redacted text:\n\n%s\n\n"
        "Claude: to use a secret, run `sec get NAME` or use `$(sec get NAME)` "
        "in a command. Do not ask for the value."
    ) % (", ".join(names), shown)
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


def do_pretool(data, lib):
    tool = data.get("tool_name")
    inp = data.get("tool_input")
    if not isinstance(inp, dict):
        return 0
    if tool == "Bash":
        text = inp.get("command")
    elif tool == "Write":
        text = inp.get("content")
    elif tool == "Edit":
        text = inp.get("new_string")
    else:
        return 0
    if not isinstance(text, str) or not text:
        return 0
    found = lib.find_secrets(text)
    if not found:
        return 0
    kinds = sorted({f[0] for f in found})
    names = sorted({lib.name_for(f[0], f[1]) for f in found})
    msg = (
        "Blocked: the input has a literal secret (%d match, kind: %s). "
        "Do not write the secret value in a command or a file. "
        "Store the value in the keyring with `sec set NAME`. "
        "The value comes from stdin. Suggested name: %s. "
        "Then use `$(sec get NAME)` in the command."
    ) % (len(found), ", ".join(kinds), ", ".join(names))
    sys.stderr.write(msg + "\n")
    return 2


def do_sessionend(data, _lib):
    path = data.get("transcript_path")
    if not isinstance(path, str) or not path:
        return 0
    subprocess.run(
        [os.path.join(HERE, "scrub-transcripts"), "--apply", "--transcript", path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=120,
    )
    return 0


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    raw = sys.stdin.buffer.read()
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        return 0
    lib = load_lib()
    if mode == "prompt":
        return do_prompt(data, lib)
    if mode == "pretool":
        return do_pretool(data, lib)
    if mode == "sessionend":
        return do_sessionend(data, lib)
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except BaseException:
        code = 0
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(code)
