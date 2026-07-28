#!/usr/bin/env bash
# TenX deterministic phase gate (Claude Code, Claude desktop agent mode, Codex).
# Blocks entry to Investigate/Slice/Implement unless the required .tenx/ records
# exist, and blocks PR/MR creation in TenX-managed repos without full approvals.
# Exit 2 = deny (stderr shown to the model).
set -euo pipefail
payload="$(cat)"
exec python3 - "$payload" <<'PY'
import glob
import json
import os
import re
import subprocess
import sys

data = json.loads(sys.argv[1])
tool = data.get("tool_name") or ""
ti = data.get("tool_input") or {}
cwd = data.get("cwd") or os.getcwd()

SKILL_RE = re.compile(r"skills/(investigate|slice|implement)/SKILL\.md")
PATH_RE = re.compile(r"(\S*skills/(?:investigate|slice|implement)/SKILL\.md)")
SHIP_RE = re.compile(r"\bgh\s+pr\s+create\b|\bglab\s+mr\s+create\b")


def is_tenx_phase_file(fp):
    # Identify by content marker, not path shape: every gated tenx phase file
    # references .tenx/ records. Unreadable/absent file -> not gated (Read will
    # error on its own).
    if not os.path.isfile(fp):
        return False
    try:
        return ".tenx/" in open(fp, encoding="utf-8", errors="replace").read()
    except OSError:
        return False


def is_dev_copy(fp):
    # The source repo (has .git at the plugin root) stays readable for editing;
    # installed copies (claude/codex caches, desktop agent mounts) have no .git.
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(fp))))
    return os.path.exists(os.path.join(root, ".git"))


def gated_phase_from_path(fp):
    m = SKILL_RE.search(fp)
    if m and is_tenx_phase_file(fp) and not is_dev_copy(fp):
        return m.group(1)
    return None


phase = None
ship = False
if tool == "Skill":
    s = (ti.get("skill") or "").strip()
    if s in ("tenx:investigate", "tenx:slice", "tenx:implement"):
        phase = s.split(":", 1)[1]
elif tool == "Read":
    phase = gated_phase_from_path(ti.get("file_path") or "")
elif tool == "Bash":
    cmd = ti.get("command") or ""
    m = PATH_RE.search(cmd)
    if m:
        p = m.group(1).strip("'\"")
        if not os.path.isabs(p):
            p = os.path.join(cwd, p)
        phase = gated_phase_from_path(p)
    if SHIP_RE.search(cmd):
        ship = True

if phase is None and not ship:
    sys.exit(0)


def repo_root(path):
    try:
        r = subprocess.run(
            ["git", "-C", path, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return path


root = repo_root(cwd)
tenx = os.path.join(root, ".tenx")


def record_exists(name):
    return bool(glob.glob(os.path.join(tenx, "*", name)))


def investigate_pass():
    for f in glob.glob(os.path.join(tenx, "*", "review-investigate-*.md")):
        try:
            if "PASS" in open(f, encoding="utf-8", errors="replace").read():
                return True
        except OSError:
            pass
    return False


def deny(msg):
    sys.stderr.write(msg)
    sys.exit(2)


if ship:
    # Only gate shipping in repos where TenX is engaged.
    if os.path.isdir(tenx):
        missing = []
        if not record_exists("understand.approval.md"):
            missing.append("understand.approval.md")
        if not investigate_pass():
            missing.append("review-investigate-r<N>.md containing PASS")
        if not record_exists("slice.approval.md"):
            missing.append("slice.approval.md")
        if missing:
            deny(
                "TenX ship gate (deterministic hook): this repository has TenX records "
                "(.tenx/ exists at %s) but PR/MR creation requires the full approval chain. "
                "Missing under .tenx/<issue-id>/: %s. Complete the owning phases first. "
                "If this PR is intentionally outside TenX, ask the user to confirm before shipping."
                % (root, "; ".join(missing))
            )
    if phase is None:
        sys.exit(0)

missing = []
if not record_exists("understand.approval.md"):
    missing.append(".tenx/<issue-id>/understand.approval.md (approved Understand record)")
if phase in ("slice", "implement") and not investigate_pass():
    missing.append(".tenx/<issue-id>/review-investigate-r<N>.md containing PASS")
if phase == "implement" and not record_exists("slice.approval.md"):
    missing.append(".tenx/<issue-id>/slice.approval.md (approved slice sequence)")

if missing:
    deny(
        "TenX gate (deterministic hook): cannot enter %s — missing: %s. "
        "Records exist only as files under .tenx/<issue-id>/ at the repository root (%s). "
        "Request detail is never a record and never an approval. "
        "Route via tenx:index; with no records the phase is Understand."
        % (phase, "; ".join(missing), root)
    )
sys.exit(0)
PY
