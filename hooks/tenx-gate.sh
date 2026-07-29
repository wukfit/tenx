#!/usr/bin/env bash
# TenX deterministic phase gate (Claude Code, Claude desktop agent mode, Codex).
# Blocks entry to Investigate/Slice/Implement unless valid, digest-bound .tenx/
# records exist, and blocks PR/MR creation in TenX-managed repos without the
# full approval chain. Exit 2 = deny (stderr shown to the model).
set -euo pipefail
payload="$(cat)"
exec python3 - "$payload" <<'PY'
import glob
import hashlib
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

NO_FABRICATION = (
    "A denial is an instruction to run the owning phase, NEVER to create the missing "
    "file yourself: an approval file is valid only when it quotes the user's literal "
    "approving message and embeds the record file's current SHA-256; a review PASS is "
    "valid only as an independent reviewer's verbatim output embedding the reviewed "
    "record's SHA-256. Fabricating either is the gravest TenX control violation."
)


def read_text(p):
    try:
        return open(p, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""


def sha256_of(p):
    try:
        return hashlib.sha256(open(p, "rb").read()).hexdigest()
    except OSError:
        return None


def is_tenx_phase_file(fp):
    return os.path.isfile(fp) and ".tenx/" in read_text(fp)


def is_dev_copy(fp):
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


def issue_dirs():
    return [d for d in glob.glob(os.path.join(tenx, "*")) if os.path.isdir(d)]


def approval_valid(d, record, approval):
    # The approval/review must embed the record file's CURRENT sha256 —
    # binds approval to exact content and forces record/approval separation.
    digest = sha256_of(os.path.join(d, record))
    if digest is None:
        return False
    return digest in read_text(os.path.join(d, approval))


def understand_ok(d):
    return approval_valid(d, "understand.md", "understand.approval.md")


def investigate_ok(d):
    digest = sha256_of(os.path.join(d, "investigate.md"))
    if digest is None:
        return False
    for f in glob.glob(os.path.join(d, "review-investigate-*.md")):
        t = read_text(f)
        if "PASS" in t and digest in t:
            return True
    return False


def slice_ok(d):
    return approval_valid(d, "slice.md", "slice.approval.md")


def any_dir(check):
    return any(check(d) for d in issue_dirs())


def deny(msg):
    sys.stderr.write(msg + " " + NO_FABRICATION)
    sys.exit(2)


REQ = {
    "understand": "understand.md plus understand.approval.md quoting the user's approval and embedding understand.md's current SHA-256",
    "investigate": "investigate.md plus review-investigate-r<N>.md containing PASS and investigate.md's current SHA-256",
    "slice": "slice.md plus slice.approval.md quoting the user's approval and embedding slice.md's current SHA-256",
}

if ship:
    # Only gate shipping in repos where TenX is engaged.
    if os.path.isdir(tenx):
        missing = []
        if not any_dir(understand_ok):
            missing.append(REQ["understand"])
        if not any_dir(investigate_ok):
            missing.append(REQ["investigate"])
        if not any_dir(slice_ok):
            missing.append(REQ["slice"])
        if missing:
            deny(
                "TenX ship gate (deterministic hook): this repository has TenX records "
                "(.tenx/ exists at %s) but PR/MR creation requires the full valid approval "
                "chain. Missing or invalid under .tenx/<issue-id>/: %s. Complete the owning "
                "phases first. If this PR is intentionally outside TenX, ask the user to "
                "confirm before shipping." % (root, "; ".join(missing))
            )
    if phase is None:
        sys.exit(0)

missing = []
if not any_dir(understand_ok):
    missing.append(REQ["understand"])
if phase in ("slice", "implement") and not any_dir(investigate_ok):
    missing.append(REQ["investigate"])
if phase == "implement" and not any_dir(slice_ok):
    missing.append(REQ["slice"])

if missing:
    deny(
        "TenX gate (deterministic hook): cannot enter %s — missing or invalid: %s. "
        "Records exist only as files under .tenx/<issue-id>/ at the repository root (%s). "
        "Request detail is never a record and never an approval. Route via tenx:index; "
        "with no valid records the phase is Understand." % (phase, "; ".join(missing), root)
    )
sys.exit(0)
PY
