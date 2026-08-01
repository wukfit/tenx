#!/usr/bin/env python3
"""TenX deterministic phase gate.

Blocks entry to Investigate/Slice/Implement unless valid, digest-bound .tenx/
records exist, and blocks PR/MR creation in TenX-managed repos without the full
approval chain. Exit 2 = deny (stderr is shown to the model); exit 0 = allow.

Every check is per-issue: one single .tenx/<issue-id>/ directory must satisfy
the whole prefix chain for the requested phase. Approvals never combine across
issue directories.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import subprocess
import sys

SKILL_RE = re.compile(r"skills/(investigate|slice|implement)/SKILL\.md")
PATH_RE = re.compile(r"(\S*skills/(?:investigate|slice|implement)/SKILL\.md)")
SHIP_RE = re.compile(r"\bgh\s+pr\s+create\b|\bglab\s+mr\s+create\b")

# The reviewer's verdict must be its own line, written verbatim. An unfilled
# template placeholder ("Verdict: <PASS or FAIL>") must never satisfy this.
VERDICT_PASS_RE = re.compile(r"^[ \t]*Verdict:[ \t]*PASS[ \t]*$", re.MULTILINE)

# This hook governs the plugin it ships inside, and only that copy. The module
# lives at <plugin_root>/hooks/tenx_gate.py.
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NO_FABRICATION = (
    "A denial is an instruction to run the owning phase, NEVER to create the missing "
    "file yourself: an approval file is valid only when it quotes the user's literal "
    "approving message and embeds the record file's current SHA-256; a review PASS is "
    "valid only as an independent reviewer's verbatim output embedding the reviewed "
    "record's SHA-256 on a line reading exactly 'Verdict: PASS'. Fabricating either is "
    "the gravest TenX control violation."
)

REQ = {
    "understand": (
        "understand.md plus understand.approval.md quoting the user's approval and "
        "embedding understand.md's current SHA-256"
    ),
    "investigate": (
        "investigate.md plus review-investigate-r<N>.md whose verdict line reads exactly "
        "'Verdict: PASS' and which embeds investigate.md's current SHA-256"
    ),
    "slice": (
        "slice.md plus slice.approval.md quoting the user's approval and embedding "
        "slice.md's current SHA-256"
    ),
}

# Which records a phase requires, in order. The phase itself is not included:
# entering Slice requires Understand and Investigate, not Slice.
CHAIN = {
    "investigate": ["understand"],
    "slice": ["understand", "investigate"],
    "implement": ["understand", "investigate", "slice"],
}


def read_text(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return ""


def sha256_of(path: str) -> str | None:
    try:
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        return None


def is_tenx_phase_file(path: str) -> bool:
    return os.path.isfile(path) and ".tenx/" in read_text(path)


def is_own_plugin_file(path: str) -> bool:
    """True when the path is one of THIS plugin's own files.

    Reading a phase file directly is how the Skill gate gets sidestepped, so
    those reads are blocked — but only for the copy this hook belongs to. A
    checkout of the TenX source somewhere else is just files on disk: editing
    the plugin is not using it, and the hook has no business policing it. That
    also removes any need to tell a development copy from an installed one,
    which is guesswork the hook kept getting wrong.
    """
    try:
        return os.path.commonpath(
            [os.path.realpath(path), os.path.realpath(PLUGIN_ROOT)]
        ) == os.path.realpath(PLUGIN_ROOT)
    except (OSError, ValueError):  # different drives, or an unresolvable path
        return False


def gated_phase_from_path(path: str) -> str | None:
    match = SKILL_RE.search(path)
    if match and is_own_plugin_file(path) and is_tenx_phase_file(path):
        return match.group(1)
    return None


def repo_root(path: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return path


def approval_valid(issue_dir: str, record: str, approval: str) -> bool:
    """The approval must embed the record file's CURRENT sha256 — this binds the
    approval to exact content and forces record/approval separation."""
    digest = sha256_of(os.path.join(issue_dir, record))
    if digest is None:
        return False
    return digest in read_text(os.path.join(issue_dir, approval))


def understand_ok(issue_dir: str) -> bool:
    return approval_valid(issue_dir, "understand.md", "understand.approval.md")


def investigate_ok(issue_dir: str) -> bool:
    digest = sha256_of(os.path.join(issue_dir, "investigate.md"))
    if digest is None:
        return False
    for path in glob.glob(os.path.join(issue_dir, "review-investigate-*.md")):
        text = read_text(path)
        if VERDICT_PASS_RE.search(text) and digest in text:
            return True
    return False


def slice_ok(issue_dir: str) -> bool:
    return approval_valid(issue_dir, "slice.md", "slice.approval.md")


CHECKS = {
    "understand": understand_ok,
    "investigate": investigate_ok,
    "slice": slice_ok,
}


def issue_dirs(tenx: str) -> list[str]:
    return sorted(d for d in glob.glob(os.path.join(tenx, "*")) if os.path.isdir(d))


def missing_for(issue_dir: str, required: list[str]) -> list[str]:
    return [name for name in required if not CHECKS[name](issue_dir)]


def active_issue(tenx: str) -> tuple[str | None, str | None]:
    """Resolve the issue this session is working on.

    The gate verifies ONE directory: the one named by .tenx/current. Without
    that pointer there is no way to tell an approved past issue from the
    unapproved new one, so a completed issue would silently unlock every later
    phase. Returns (issue_dir, error_message).
    """
    pointer = os.path.join(tenx, "current")
    if not os.path.isfile(pointer):
        return None, (
            "no .tenx/current pointer names the issue being worked on. The gate verifies "
            "the records of exactly one issue; without the pointer, a previously completed "
            "issue would unlock this phase. Route via tenx:index, which determines "
            "<issue-id> and writes it to .tenx/current"
        )
    name = read_text(pointer).strip()
    if not name:
        return None, ".tenx/current is empty; it must contain exactly one <issue-id>"
    if os.sep in name or name in ("", ".", ".."):
        return None, ".tenx/current must contain a bare <issue-id>, not a path (%r)" % name
    issue_dir = os.path.join(tenx, name)
    if not os.path.isdir(issue_dir):
        return None, (
            ".tenx/current names %r but .tenx/%s/ does not exist" % (name, name)
        )
    return issue_dir, None


def deny(message: str) -> None:
    sys.stderr.write(message + " " + NO_FABRICATION)
    sys.exit(2)


def parse_request(data: dict) -> tuple[str | None, bool]:
    """Return (gated_phase, is_ship_attempt) for this tool call."""
    tool = data.get("tool_name") or ""
    tool_input = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    phase: str | None = None
    ship = False

    if tool == "Skill":
        skill = (tool_input.get("skill") or "").strip()
        if skill in ("tenx:investigate", "tenx:slice", "tenx:implement"):
            phase = skill.split(":", 1)[1]
    elif tool == "Read":
        phase = gated_phase_from_path(tool_input.get("file_path") or "")
    elif tool == "Bash":
        command = tool_input.get("command") or ""
        match = PATH_RE.search(command)
        if match:
            path = match.group(1).strip("'\"")
            if not os.path.isabs(path):
                path = os.path.join(cwd, path)
            phase = gated_phase_from_path(path)
        if SHIP_RE.search(command):
            ship = True
    return phase, ship


def run(data: dict) -> int:
    phase, ship = parse_request(data)
    if phase is None and not ship:
        return 0

    root = repo_root(data.get("cwd") or os.getcwd())
    tenx = os.path.join(root, ".tenx")

    if ship:
        # Only gate shipping in repos where TenX is engaged.
        if os.path.isdir(tenx):
            issue_dir, error = active_issue(tenx)
            if issue_dir is None:
                deny(
                    "TenX ship gate (deterministic hook): this repository has TenX records "
                    "(.tenx/ exists at %s) but %s. If this PR is intentionally outside TenX, "
                    "ask the user to confirm before shipping." % (root, error)
                )
            missing = missing_for(issue_dir, ["understand", "investigate", "slice"])
            if missing:
                deny(
                    "TenX ship gate (deterministic hook): PR/MR creation for %s requires the "
                    "full valid approval chain in that issue's own directory. Missing or "
                    "invalid: %s. Approvals recorded under a different .tenx/<issue-id>/ never "
                    "count. Complete the owning phases first. If this PR is intentionally "
                    "outside TenX, ask the user to confirm before shipping."
                    % (issue_dir, "; ".join(REQ[name] for name in missing))
                )
        if phase is None:
            return 0

    issue_dir, error = active_issue(tenx)
    if issue_dir is None:
        deny(
            "TenX gate (deterministic hook): cannot enter %s — %s. Records exist only as files "
            "under .tenx/<issue-id>/ at the repository root (%s). Request detail is never a "
            "record and never an approval. With no valid records the phase is Understand."
            % (phase, error, root)
        )
    missing = missing_for(issue_dir, CHAIN[phase])
    if missing:
        deny(
            "TenX gate (deterministic hook): cannot enter %s for %s — missing or invalid: %s. "
            "Records for one issue never satisfy the gate for another. Request detail is never "
            "a record and never an approval. Route via tenx:index; with no valid records the "
            "phase is Understand."
            % (phase, issue_dir, "; ".join(REQ[name] for name in missing))
        )
    return 0


def main(argv: list[str]) -> int:
    try:
        data = json.loads(argv[1]) if len(argv) > 1 else json.load(sys.stdin)
    except Exception as exc:  # fail closed: an unreadable payload is not a pass
        sys.stderr.write(
            "TenX gate: could not parse the hook payload (%s). Refusing to allow an "
            "unverified phase entry. %s" % (exc, NO_FABRICATION)
        )
        return 2
    try:
        return run(data)
    except SystemExit:
        raise
    except Exception as exc:  # fail closed: an internal error is not a pass
        sys.stderr.write(
            "TenX gate: internal error while verifying records (%r). Refusing to allow an "
            "unverified phase entry. %s" % (exc, NO_FABRICATION)
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
