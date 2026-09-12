#!/usr/bin/env python3
"""Maintain the leading status emoji on the calling Unpeel session's title.

Hook entry: `title-status.py <emoji>` (see plugin.json; one entry per
lifecycle event). Mirrors the Codex thread-title convention: exactly one
leading status emoji, title body otherwise untouched.

Mechanism, mirroring unpeel-core's session_ops::set_title + state_bus
announce: rewrite title.json in the session dir, then POST
{"change":"session-markers"} to every port in ~/.unpeel/app-ports so
frontends refresh the row.

Fail-silent by design (exit 0 on every path): a title hook must never break
the agent loop.
"""

import json
import os
import re
import socket
import subprocess
import sys
import time

STATUSES = ("🔄", "✅", "❌", "⏳")
STRIP_RE = re.compile(r"^(?:🔄|✅|❌|⏳)\s*")


def recover_from_parent(key, pattern):
    """Muse scrubs hook env; recover Unpeel vars from the parent process."""
    try:
        out = subprocess.run(
            ["ps", "eww", str(os.getppid())],
            capture_output=True, text=True, timeout=5,
        ).stdout
    except Exception:
        return None
    match = re.search(r"%s=(%s)" % (re.escape(key), pattern), out)
    return match.group(1) if match else None


def main():
    # Consume stdin (hook payload) so the writer never blocks on us.
    try:
        sys.stdin.read()
    except Exception:
        pass
    if len(sys.argv) != 2 or sys.argv[1] not in STATUSES:
        return 0
    status = sys.argv[1]

    session_dir = os.environ.get("UNPEEL_SESSION_DIR") or recover_from_parent(
        "UNPEEL_SESSION_DIR", r"\S+"
    )
    home = os.environ.get("UNPEEL_HOME") or os.path.expanduser("~/.unpeel")
    if not session_dir or not os.path.isdir(session_dir):
        return 0

    current = None
    title_path = os.path.join(session_dir, "title.json")
    try:
        with open(title_path, encoding="utf-8") as handle:
            current = json.load(handle).get("title")
    except Exception:
        current = None
    if not current:
        try:
            with open(os.path.join(session_dir, "manifest.json"), encoding="utf-8") as handle:
                current = json.load(handle).get("session", {}).get("label")
        except Exception:
            current = None
    if not current or not current.strip():
        return 0

    body = STRIP_RE.sub("", current).strip()
    if not body:
        return 0
    new_title = "%s %s" % (status, body)
    if new_title == current:
        return 0

    try:
        tmp_path = title_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(
                {"title": new_title, "updated_at": int(time.time() * 1000)}, handle
            )
        os.rename(tmp_path, title_path)
    except Exception:
        return 0

    # state_bus announce: POST /state-changed to every registered frontend.
    try:
        with open(os.path.join(home, "app-ports"), encoding="utf-8") as handle:
            ports = [
                int(line.strip())
                for line in handle
                if line.strip().isdigit() and int(line.strip()) != 0
            ]
    except Exception:
        return 0
    payload = json.dumps({"change": "session-markers"}).encode()
    request = (
        b"POST /state-changed HTTP/1.1\r\nHost: 127.0.0.1\r\n"
        b"Content-Type: application/json\r\nContent-Length: %d\r\n"
        b"Connection: close\r\n\r\n" % len(payload)
    ) + payload
    for port in dict.fromkeys(ports):
        try:
            sock = socket.create_connection(("127.0.0.1", port), timeout=0.25)
            sock.settimeout(0.25)
            sock.sendall(request)
            sock.close()
        except Exception:
            continue
    return 0


if __name__ == "__main__":
    sys.exit(main())
