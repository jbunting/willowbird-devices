#!/usr/bin/env python3
"""Fail a PR that bumps a vendored file's `# vendored-from:` digest without
actually re-syncing the file, when upstream changed that file.

Vendored configs under devices/vendor/ are copies of an upstream file, recorded
in the header as:

    #   github://<owner>/<repo>/<path>
    # renovate: datasource=git-refs depName=<owner>/<repo>
    # vendored-from: main @<sha>

Renovate bumps `@<sha>` whenever upstream's default branch moves — but that's
branch-level, so most bumps don't touch our specific file. This check compares
the upstream file at the OLD vs NEW sha:

  - upstream file unchanged  -> OK (safe digest bump, nothing to re-vendor)
  - upstream file changed AND our copy only bumped the digest -> FAIL (re-sync)
  - upstream file changed AND our copy was updated too         -> OK (re-vendored)

Env: BASE_SHA (PR base commit). HEAD is the checked-out working tree.
"""
import difflib
import os
import pathlib
import re
import subprocess
import sys
import urllib.request

VENDOR_DIR = "devices/vendor"
DIGEST_RE = re.compile(r"#\s*vendored-from:.*@([0-9a-fA-F]{7,40})")
SRC_RE = re.compile(r"github://([^/\s]+)/([^/\s]+)/(\S+\.ya?ml)")


def digest(content):
    m = DIGEST_RE.search(content or "")
    return m.group(1) if m else None


def strip_digest(content):
    """Normalize away the digest so we can tell a digest-only change from a real edit."""
    return DIGEST_RE.sub("# vendored-from: <digest>", content or "")


def decide(base, head, fetch):
    """Pure decision logic. `fetch(owner, repo, path, sha) -> str` returns upstream content.
    Returns (status, message) where status is 'ok' | 'fail' | 'skip'."""
    hd, bd = digest(head), digest(base)
    if not bd or not hd:
        return ("skip", "no vendored-from digest on both sides")
    if bd == hd:
        return ("skip", "digest unchanged")
    m = SRC_RE.search(head)
    if not m:
        return ("skip", "no upstream github:// source line")
    owner, repo, path = m.groups()
    up_base = fetch(owner, repo, path, bd)
    up_head = fetch(owner, repo, path, hd)
    if up_base == up_head:
        return ("ok", f"upstream {path} unchanged between {bd[:7]}..{hd[:7]} — safe digest bump")
    if strip_digest(base) == strip_digest(head):
        diff = "".join(
            difflib.unified_diff(
                up_base.splitlines(keepends=True),
                up_head.splitlines(keepends=True),
                fromfile=f"upstream@{bd[:7]}",
                tofile=f"upstream@{hd[:7]}",
            )
        )
        return ("fail", f"upstream {path} changed but only the digest was bumped — re-sync required.\n{diff}")
    return ("ok", f"upstream {path} changed and the vendored copy was updated — re-vendored")


def _git_show(rev, path):
    r = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def _fetch(owner, repo, path, sha):
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{sha}/{path}"
    with urllib.request.urlopen(url, timeout=20) as resp:
        return resp.read().decode()


def _selftest():
    body = "esphome:\n  min_version: 2026.3.2\n"
    hdr = "#   github://o/r/esphome-config/x.yaml\n# vendored-from: main @{}\n"
    a = "a" * 40
    b = "b" * 40
    base = hdr.format(a) + body
    head_digest_only = hdr.format(b) + body
    head_revendored = hdr.format(b) + body + "web_server:\n  version: 3\n"

    def fetch_same(*_):
        return "UPSTREAM V1"

    up = {a: "UPSTREAM V1", b: "UPSTREAM V2"}

    def fetch_changed(owner, repo, path, sha):
        return up[sha]

    cases = [
        ("safe bump (upstream unchanged)", decide(base, head_digest_only, fetch_same), "ok"),
        ("re-sync needed", decide(base, head_digest_only, fetch_changed), "fail"),
        ("re-vendored", decide(base, head_revendored, fetch_changed), "ok"),
        ("no bump", decide(base, base, fetch_changed), "skip"),
    ]
    ok = True
    for name, (status, _), expected in cases:
        flag = "PASS" if status == expected else "FAIL"
        if status != expected:
            ok = False
        print(f"  [{flag}] {name}: got {status!r}, expected {expected!r}")
    sys.exit(0 if ok else 1)


def main():
    if os.environ.get("SELFTEST") == "1":
        _selftest()
    base_sha = os.environ["BASE_SHA"]
    changed = subprocess.run(
        ["git", "diff", "--name-only", base_sha, "--", VENDOR_DIR],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    changed = [f for f in changed if f.endswith((".yaml", ".yml"))]

    failures = []
    for f in changed:
        head = pathlib.Path(f).read_text()
        base = _git_show(base_sha, f)
        if base is None:
            print(f"{f}: new vendored file — skip")
            continue
        status, msg = decide(base, head, _fetch)
        prefix = {"fail": "::error::", "skip": "", "ok": ""}[status]
        print(f"{prefix}{f}: {msg}")
        if status == "fail":
            failures.append(f)

    if failures:
        print(f"\nvendored-resync FAILED — re-sync needed for: {', '.join(failures)}")
        sys.exit(1)
    print("vendored-resync OK")


if __name__ == "__main__":
    main()
