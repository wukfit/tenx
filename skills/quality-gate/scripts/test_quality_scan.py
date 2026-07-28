#!/usr/bin/env python3
"""Regression tests for quality_scan.py."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("quality_scan.py")


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=True)


def init_repo(root: Path) -> None:
    run(["git", "init", "--quiet"], root)
    run(["git", "config", "user.email", "quality-gate@example.test"], root)
    run(["git", "config", "user.name", "Quality Gate"], root)
    (root / "README.md").write_text("# Fixture\n", encoding="utf-8")
    run(["git", "add", "README.md"], root)
    run(["git", "commit", "--quiet", "-m", "chore: baseline"], root)


def scan(root: Path) -> list[dict[str, object]]:
    result = run(["python3", str(SCRIPT), "--base", "HEAD", "--json"], root)
    return json.loads(result.stdout)


def prompt_fence_fixture(body: str) -> list[dict[str, object]]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        prompt_dir = root / "prompts"
        prompt_dir.mkdir()
        (prompt_dir / "edited-content-prompt.md").write_text(body, encoding="utf-8")
        return scan(root)


def repo_fixture(files: dict[str, str]) -> list[dict[str, object]]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        for rel, body in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        return scan(root)


def assert_finding(findings: list[dict[str, object]], message_fragment: str) -> None:
    messages = [str(finding["message"]) for finding in findings]
    if not any(message_fragment in message for message in messages):
        raise AssertionError(f"Expected finding containing {message_fragment!r}, got: {messages}")


def assert_no_prompt_contract_findings(findings: list[dict[str, object]]) -> None:
    prompt_contracts = [finding for finding in findings if finding["check"] == "prompt-contract"]
    if prompt_contracts:
        raise AssertionError(f"Expected no prompt-contract findings, got: {prompt_contracts}")


def assert_no_findings_for_check(findings: list[dict[str, object]], check: str) -> None:
    matches = [finding for finding in findings if finding["check"] == check]
    if matches:
        raise AssertionError(f"Expected no {check} findings, got: {matches}")


def test_forbidden_code_fence_examples_are_flagged() -> None:
    findings = prompt_fence_fixture(
        """# Edited content prompt

Return JSON only. Do not use code fences.

```json
{"decision":"send"}
```
"""
    )

    assert_finding(findings, "forbids code fences")


def test_json_only_commentary_examples_are_flagged() -> None:
    findings = prompt_fence_fixture(
        """# Edited content prompt

Return JSON only with no commentary.

Example response:
The decision is:
{"decision":"send"}
"""
    )

    assert_finding(findings, "forbids commentary")


def test_documentation_only_fenced_examples_are_allowed() -> None:
    findings = prompt_fence_fixture(
        """# Edited content prompt

Return JSON only. Do not use code fences.

The fenced examples below are documentation-only for readability. Do not include code fences in your output.

```json
{"decision":"send"}
```
"""
    )

    assert_no_prompt_contract_findings(findings)


def test_merge_conflict_markers_are_flagged() -> None:
    findings = repo_fixture({"src/app.ts": "<<<<<<< HEAD\nconst a = 1;\n>>>>>>> feature\n"})
    assert_finding(findings, "conflict marker")


def test_focused_tests_are_flagged() -> None:
    findings = repo_fixture({"src/app.test.ts": "describe.only('clamp', () => {});\n"})
    assert_finding(findings, "focused test")


def test_skipped_tests_are_flagged() -> None:
    findings = repo_fixture(
        {"tests/test_app.py": "import pytest\n\n@pytest.mark.skip\ndef test_clamp():\n    pass\n"}
    )
    assert_finding(findings, "skipped test")


def test_debug_leftovers_are_flagged() -> None:
    findings = repo_fixture(
        {
            "src/app.ts": "console.log('debug');\n",
            "src/job.py": "breakpoint()\n",
        }
    )
    assert_finding(findings, "console.log")
    assert_finding(findings, "breakpoint")


def test_debug_logging_in_test_files_is_allowed() -> None:
    findings = repo_fixture({"src/app.test.ts": "console.log('inspect fixture');\n"})
    assert_no_findings_for_check(findings, "debug-leftover")


def test_secret_material_is_flagged() -> None:
    aws_key = "AKIA" + "ABCDEFGHIJKLMNOP"
    findings = repo_fixture(
        {
            "src/config.ts": f'const key = "{aws_key}";\n',
            "deploy/key.pem": "-----BEGIN RSA PRIVATE KEY-----\n",
        }
    )
    assert_finding(findings, "AWS access key")
    assert_finding(findings, "private key")


def test_added_todos_in_code_are_flagged() -> None:
    findings = repo_fixture({"src/app.ts": "// TODO: handle retries\n"})
    assert_finding(findings, "TODO")


def test_todos_in_docs_are_not_flagged() -> None:
    findings = repo_fixture({"notes/plan.md": "- TODO: draft rollout plan\n"})
    assert_no_findings_for_check(findings, "todo-added")


def test_default_base_autodetects_local_main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        run(["git", "init", "--quiet", "-b", "main"], root)
        run(["git", "config", "user.email", "quality-gate@example.test"], root)
        run(["git", "config", "user.name", "Quality Gate"], root)
        (root / "README.md").write_text("# Fixture\n", encoding="utf-8")
        run(["git", "add", "README.md"], root)
        run(["git", "commit", "--quiet", "-m", "chore: baseline"], root)
        run(["git", "checkout", "--quiet", "-b", "feature"], root)
        (root / "src").mkdir()
        (root / "src" / "app.ts").write_text("// TODO: handle retries\n", encoding="utf-8")
        run(["git", "add", "."], root)
        run(["git", "commit", "--quiet", "-m", "feat: add app"], root)
        result = run(["python3", str(SCRIPT), "--json"], root)
        findings = json.loads(result.stdout)
        assert_finding(findings, "TODO")


def test_missing_explicit_base_ref_fails_loudly() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        result = subprocess.run(
            ["python3", str(SCRIPT), "--base", "origin/main", "--json"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            raise AssertionError("Expected nonzero exit for unresolvable base ref, got success.")
        if "origin/main" not in result.stderr:
            raise AssertionError(f"Expected stderr to name the missing base ref, got: {result.stderr!r}")


def main() -> int:
    tests = [
        test_forbidden_code_fence_examples_are_flagged,
        test_json_only_commentary_examples_are_flagged,
        test_documentation_only_fenced_examples_are_allowed,
        test_merge_conflict_markers_are_flagged,
        test_focused_tests_are_flagged,
        test_skipped_tests_are_flagged,
        test_debug_leftovers_are_flagged,
        test_debug_logging_in_test_files_is_allowed,
        test_secret_material_is_flagged,
        test_added_todos_in_code_are_flagged,
        test_todos_in_docs_are_not_flagged,
        test_default_base_autodetects_local_main,
        test_missing_explicit_base_ref_fails_loudly,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
