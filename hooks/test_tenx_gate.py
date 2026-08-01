#!/usr/bin/env python3
"""Regression tests for the TenX phase gate.

Each test builds a real .tenx/ fixture and asks the gate whether a phase entry
is allowed. Exit 0 = allowed, exit 2 = denied.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

GATE = Path(__file__).with_name("tenx-gate.sh")


def gate(cwd: Path, tool_name: str, tool_input: dict) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({"tool_name": tool_name, "tool_input": tool_input, "cwd": str(cwd)})
    return subprocess.run(
        ["bash", str(GATE)], input=payload, text=True, capture_output=True, cwd=str(cwd)
    )


def enter(cwd: Path, phase: str) -> subprocess.CompletedProcess[str]:
    return gate(cwd, "Skill", {"skill": f"tenx:{phase}"})


def ship(cwd: Path) -> subprocess.CompletedProcess[str]:
    return gate(cwd, "Bash", {"command": "gh pr create --title x --body y"})


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def init_repo(root: Path) -> None:
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main"], cwd=root, check=True,
        capture_output=True,
    )


def approve(issue: Path, record: str) -> None:
    """Write a valid <record>.approval.md binding the record's current digest."""
    path = issue / f"{record}.md"
    write(
        issue / f"{record}.approval.md",
        f"# Approval\n- SHA-256: {digest(path)}\n\n> yes, approved\n",
    )


def pass_review(issue: Path, phase: str = "investigate", revision: int = 1) -> None:
    record = issue / f"{phase}.md"
    write(
        issue / f"review-{phase}-r{revision}.md",
        f"# Independent review\n- Reviewed record SHA-256: {digest(record)}\n\n"
        f"## Verdict\n\nVerdict: PASS\n",
    )


def approved_issue(root: Path, name: str, through: str = "slice") -> Path:
    """Build a fully valid issue directory up through the named phase."""
    issue = root / ".tenx" / name
    write(issue / "understand.md", f"# Understand {name}\n")
    approve(issue, "understand")
    if through in ("investigate", "slice"):
        write(issue / "investigate.md", f"# Investigate {name}\n")
        pass_review(issue, "investigate")
    if through == "slice":
        write(issue / "slice.md", f"# Slice {name}\n")
        approve(issue, "slice")
    return issue


def set_current(root: Path, name: str) -> None:
    write(root / ".tenx" / "current", f"{name}\n")


# --- regressions ------------------------------------------------------------


def test_completed_issue_does_not_unlock_a_new_one() -> None:
    """The regression: a fully approved past issue must not unlock BRAND-NEW."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        approved_issue(root, "OLD-DONE", through="slice")
        write(root / ".tenx" / "BRAND-NEW" / "understand.md", "unapproved draft\n")
        set_current(root, "BRAND-NEW")

        result = enter(root, "implement")
        assert result.returncode == 2, f"expected deny, got {result.returncode}"
        assert "never satisfy the gate for another" in result.stderr, result.stderr


def test_chain_may_not_be_split_across_issue_directories() -> None:
    """Understand from one issue plus Slice from another is not a chain."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        approved_issue(root, "ISSUE-A", through="understand")
        issue_b = root / ".tenx" / "ISSUE-B"
        write(issue_b / "investigate.md", "# Investigate B\n")
        pass_review(issue_b, "investigate")
        write(issue_b / "slice.md", "# Slice B\n")
        approve(issue_b, "slice")
        set_current(root, "ISSUE-B")

        result = enter(root, "implement")
        assert result.returncode == 2, f"expected deny, got {result.returncode}"


def test_missing_or_bogus_current_pointer_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        approved_issue(root, "ISSUE-A", through="slice")

        # No pointer at all.
        result = enter(root, "implement")
        assert result.returncode == 2, f"expected deny, got {result.returncode}"
        assert ".tenx/current" in result.stderr, result.stderr

        # Pointer naming a directory that does not exist.
        set_current(root, "NOPE")
        assert enter(root, "implement").returncode == 2

        # Pointer must be a bare id, not a traversal path.
        write(root / ".tenx" / "current", "../ISSUE-A\n")
        assert enter(root, "implement").returncode == 2

        # Empty pointer.
        write(root / ".tenx" / "current", "\n")
        assert enter(root, "implement").returncode == 2


def test_failing_review_containing_template_words_is_not_a_pass() -> None:
    """A FAIL verdict must deny even when the prose mentions PASS."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        issue = approved_issue(root, "ISSUE-A", through="understand")
        set_current(root, "ISSUE-A")
        record = write(issue / "investigate.md", "# Investigate\n")
        write(
            issue / "review-investigate-r1.md",
            f"- Reviewed record SHA-256: {digest(record)}\n\n"
            f"## Verdict\n\nVerdict: FAIL\n\n"
            f"This does not PASS: three callers are unenumerated.\n",
        )

        result = enter(root, "slice")
        assert result.returncode == 2, f"expected deny, got {result.returncode}"


def test_unfilled_review_placeholder_is_not_a_pass() -> None:
    """The shipped template must not satisfy the gate before a reviewer fills it."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        issue = approved_issue(root, "ISSUE-A", through="understand")
        set_current(root, "ISSUE-A")
        record = write(issue / "investigate.md", "# Investigate\n")
        template = (Path(__file__).parents[1] / "references/templates/review-investigate.md").read_text()
        write(issue / "review-investigate-r1.md", template + f"\n{digest(record)}\n")

        result = enter(root, "slice")
        assert result.returncode == 2, f"expected deny, got {result.returncode}"


def test_review_bound_to_a_stale_digest_is_not_a_pass() -> None:
    """Editing the record after review invalidates the PASS."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        issue = approved_issue(root, "ISSUE-A", through="understand")
        set_current(root, "ISSUE-A")
        write(issue / "investigate.md", "# Investigate\n")
        pass_review(issue, "investigate")
        write(issue / "investigate.md", "# Investigate, edited after review\n")

        result = enter(root, "slice")
        assert result.returncode == 2, f"expected deny, got {result.returncode}"


def test_approval_bound_to_a_stale_digest_is_not_valid() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        issue = approved_issue(root, "ISSUE-A", through="understand")
        set_current(root, "ISSUE-A")
        write(issue / "understand.md", "# Understand, edited after approval\n")

        result = enter(root, "investigate")
        assert result.returncode == 2, f"expected deny, got {result.returncode}"


def test_valid_single_issue_chain_is_allowed() -> None:
    """The gate must not be vacuously strict — a real chain passes."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        approved_issue(root, "ISSUE-A", through="slice")
        set_current(root, "ISSUE-A")

        for phase in ("investigate", "slice", "implement"):
            result = enter(root, phase)
            assert result.returncode == 0, f"{phase} denied: {result.stderr}"
        assert ship(root).returncode == 0


def test_ship_is_gated_by_the_active_issues_own_chain() -> None:
    """A complete past issue must not authorise shipping the active one."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        approved_issue(root, "OLD-DONE", through="slice")
        write(root / ".tenx" / "BRAND-NEW" / "understand.md", "unapproved\n")
        set_current(root, "BRAND-NEW")
        result = ship(root)
        assert result.returncode == 2, f"expected deny, got {result.returncode}"
        assert "never count" in result.stderr, result.stderr

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        approved_issue(root, "ISSUE-A", through="investigate")
        set_current(root, "ISSUE-A")
        result = ship(root)
        assert result.returncode == 2, f"expected deny, got {result.returncode}"


def test_ship_is_not_gated_in_repos_without_tenx() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        assert ship(root).returncode == 0


def test_unrelated_tool_calls_are_untouched() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        assert gate(root, "Bash", {"command": "ls -la"}).returncode == 0
        assert gate(root, "Read", {"file_path": str(root / "README.md")}).returncode == 0


def test_reading_the_phase_file_directly_is_gated() -> None:
    """Reading SKILL.md must not bypass the Skill-tool gate."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        skill = write(
            root / "plugin/skills/implement/SKILL.md",
            "# Implement\nRecords live under .tenx/<issue-id>/.\n",
        )
        assert gate(root, "Read", {"file_path": str(skill)}).returncode == 2
        assert gate(root, "Bash", {"command": f"cat {skill}"}).returncode == 2


def test_dev_marker_exempts_a_plugin_working_copy() -> None:
    """The exemption keys off .tenx-dev, never off .git."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        skill = write(
            root / "plugin/skills/implement/SKILL.md",
            "# Implement\nRecords live under .tenx/<issue-id>/.\n",
        )
        # A git clone alone must NOT exempt it — installed plugins are clones.
        init_repo(root / "plugin")
        assert gate(root, "Read", {"file_path": str(skill)}).returncode == 2

        write(root / "plugin" / ".tenx-dev", "")
        assert gate(root, "Read", {"file_path": str(skill)}).returncode == 0


def test_malformed_payload_fails_closed() -> None:
    result = subprocess.run(
        ["bash", str(GATE)], input="not json at all", text=True, capture_output=True
    )
    assert result.returncode == 2, f"expected deny, got {result.returncode}"


def main() -> int:
    tests = [
        test_completed_issue_does_not_unlock_a_new_one,
        test_chain_may_not_be_split_across_issue_directories,
        test_missing_or_bogus_current_pointer_fails_closed,
        test_failing_review_containing_template_words_is_not_a_pass,
        test_unfilled_review_placeholder_is_not_a_pass,
        test_review_bound_to_a_stale_digest_is_not_a_pass,
        test_approval_bound_to_a_stale_digest_is_not_valid,
        test_valid_single_issue_chain_is_allowed,
        test_ship_is_gated_by_the_active_issues_own_chain,
        test_ship_is_not_gated_in_repos_without_tenx,
        test_unrelated_tool_calls_are_untouched,
        test_reading_the_phase_file_directly_is_gated,
        test_dev_marker_exempts_a_plugin_working_copy,
        test_malformed_payload_fails_closed,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
