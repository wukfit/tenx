#!/usr/bin/env python3
"""Regression tests for enumerations.py."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("enumerations.py")


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=True)


def init_repo(root: Path) -> None:
    run(["git", "init", "--quiet", "--initial-branch=main"], root)
    run(["git", "config", "user.email", "test@example.com"], root)
    run(["git", "config", "user.name", "Test"], root)


def commit_all(root: Path, message: str) -> None:
    run(["git", "add", "-A"], root)
    run(["git", "commit", "--quiet", "-m", message], root)


def scan(root: Path) -> str:
    result = subprocess.run(
        ["python3", str(SCRIPT), "--base", "main"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def build_fixture(root: Path) -> None:
    init_repo(root)
    (root / "lib.ts").write_text("export function doThing(): number {\n    return 1;\n}\n", encoding="utf-8")
    (root / "caller.ts").write_text('import { doThing } from "./lib";\n\ndoThing();\n', encoding="utf-8")
    commit_all(root, "base")
    run(["git", "checkout", "--quiet", "-b", "feature"], root)
    (root / "lib.ts").write_text("export function doThing(): number {\n    return 2;\n}\n", encoding="utf-8")
    (root / "infra.ts").write_text(
        'const statement = new PolicyStatement({ actions: ["s3:GetObject"] });\n'
        "await client.send(new GetObjectCommand({ Key: key }));\n",
        encoding="utf-8",
    )
    (root / "notes.md").write_text("new PolicyStatement in docs should not appear\n", encoding="utf-8")
    commit_all(root, "change")


def test_unchanged_caller_of_changed_export_is_listed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build_fixture(root)
        output = scan(root)
        assert "doThing" in output, output
        assert "caller.ts" in output, output


def test_permission_lines_and_remote_calls_are_listed_but_docs_are_not() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build_fixture(root)
        output = scan(root)
        assert "infra.ts:1" in output, output
        assert "client.send(" in output, output
        assert "notes.md" not in output, output


def test_unparsed_language_files_are_reported_not_skipped() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        (root / "Service.java").write_text("public class Service {}\n", encoding="utf-8")
        commit_all(root, "base")
        run(["git", "checkout", "--quiet", "-b", "feature"], root)
        (root / "Service.java").write_text("public class Service { int x; }\n", encoding="utf-8")
        commit_all(root, "change")
        output = scan(root)
        assert "cannot extract exports" in output, output
        assert "Service.java" in output, output


def test_generic_symbol_names_are_skipped() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_repo(root)
        (root / "route.ts").write_text("export function GET(): number {\n    return 1;\n}\n", encoding="utf-8")
        (root / "other.ts").write_text('import { GET } from "./route";\n\nGET();\n', encoding="utf-8")
        commit_all(root, "base")
        run(["git", "checkout", "--quiet", "-b", "feature"], root)
        (root / "route.ts").write_text("export function GET(): number {\n    return 2;\n}\n", encoding="utf-8")
        commit_all(root, "change")
        output = scan(root)
        assert "other.ts" not in output, output


def main() -> int:
    tests = [
        test_unchanged_caller_of_changed_export_is_listed,
        test_permission_lines_and_remote_calls_are_listed_but_docs_are_not,
        test_unparsed_language_files_are_reported_not_skipped,
        test_generic_symbol_names_are_skipped,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
