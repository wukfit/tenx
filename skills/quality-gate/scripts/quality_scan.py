#!/usr/bin/env python3
"""Mechanical pre-review scan for generic quality gates."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# str.removeprefix and PEP 585 builtin generics (under the __future__ import)
# both require 3.9. Fail with a readable message instead of a SyntaxError or
# TypeError from deep inside the module.
MIN_PYTHON = (3, 9)
if sys.version_info < MIN_PYTHON:
    sys.exit(
        f"quality-gate scripts require Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+; "
        f"this interpreter is {sys.version.split()[0]} ({sys.executable})."
    )


@dataclass
class Finding:
    check: str
    severity: str
    path: str
    line: int | None
    message: str


DOC_SUFFIXES = {".md", ".mdx", ".txt", ".rst", ".adoc"}
TEXT_SUFFIXES = DOC_SUFFIXES | {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".mts",
    ".cts",
    ".py",
    ".go",
    ".rb",
    ".java",
    ".kt",
    ".cs",
    ".rs",
    ".php",
    ".swift",
}
LOCAL_DOC_PATTERNS = [
    (re.compile(r"/Users/[A-Za-z0-9._-]+"), "contributor-local /Users path"),
    (re.compile(r"/home/[A-Za-z0-9._-]+"), "contributor-local /home path"),
    (re.compile(r"~/Downloads|/Downloads/|\bDownloads/"), "Downloads path"),
    (re.compile(r"~/Desktop|/Desktop/|\bDesktop/"), "Desktop path"),
    (re.compile(r"\bthis machine\b", re.IGNORECASE), "machine-specific wording"),
    (re.compile(r"\blocal scratch\b|\bscratch file\b", re.IGNORECASE), "scratch-file provenance"),
]
CREDENTIALISH_RE = re.compile(
    r"`?(?:[/A-Za-z0-9_.:-]+[-_/])?(?:api[-_]?key|secret|password|token|credential|ssm[-_]?parameter)(?:[-_/][A-Za-z0-9_.:-]+)+`?",
    re.IGNORECASE,
)
BROAD_TEST_WORDS_RE = re.compile(r"\b(both|all|multiple|various|several)\b|,", re.IGNORECASE)
TEST_NAME_PATTERNS = [
    re.compile(r"\b(?:describe|it|test)\s*\(\s*([\"'`])(?P<name>.*?)(?<!\\)\1", re.DOTALL),
    re.compile(r"\bfunc\s+(?P<name>Test[A-Za-z0-9_]+)\s*\(", re.DOTALL),
    re.compile(r"\bdef\s+(?P<name>test_[A-Za-z0-9_]+)\s*\(", re.DOTALL),
    re.compile(r"\bclass\s+(?P<name>Test[A-Za-z0-9_]+)\b", re.DOTALL),
]
LABEL_RULE_RE = re.compile(r"label each as:\s*(?P<labels>.+)", re.IGNORECASE)
POLICY_EXAMPLE_RE = re.compile(
    r"\b(avoid|do not|don't|should not|must not|not secrets|example|placeholder|redacted|generic)\b",
    re.IGNORECASE,
)
CODE_FENCE_OPEN_RE = re.compile(r"^\s*```[A-Za-z0-9_-]+")
FORBIDS_CODE_FENCES_RE = re.compile(
    r"\b(?:no|without|do not use|do not include|must not include)\s+(?:markdown\s+)?code fences?\b",
    re.IGNORECASE,
)
DOCUMENTATION_ONLY_FENCE_RE = re.compile(
    r"(?:fenced examples?|code fences?).{0,120}(?:documentation-only|documentation readability|for readability)"
    r"|(?:documentation-only|documentation readability|for readability).{0,120}(?:fenced examples?|code fences?)",
    re.IGNORECASE | re.DOTALL,
)
FORBIDS_COMMENTARY_RE = re.compile(
    r"(?:json only|only json|return json).{0,120}(?:no commentary|without commentary|no extra text|no prose)"
    r"|(?:no commentary|without commentary|no extra text|no prose).{0,120}(?:json only|only json|return json)",
    re.IGNORECASE | re.DOTALL,
)
MARKDOWN_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(?P<title>.+?)\s*#*\s*$")
WORD_RE = re.compile(r"\w+", re.UNICODE)
JS_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".mts", ".cts"}
CODE_SUFFIXES = TEXT_SUFFIXES - DOC_SUFFIXES
CONFLICT_MARKER_RE = re.compile(r"^(?:<{7}|>{7})(?:\s|$)")
FOCUSED_TEST_RE = re.compile(r"\.only\s*\(|\bf(?:it|describe)\s*\(")
SKIPPED_TEST_RE = re.compile(r"\.skip\s*\(|\bx(?:it|describe)\s*\(|@pytest\.mark\.skip\b|@unittest\.skip\b")
TODO_ADDED_RE = re.compile(r"\b(?:TODO|FIXME|HACK|XXX)\b")
JS_DEBUG_RE = re.compile(r"\bconsole\.(?:log|debug)\s*\(|^\s*debugger\s*;?\s*$")
PY_DEBUG_RE = re.compile(r"\bpdb\.set_trace\s*\(|(?<![\w.])breakpoint\s*\(\s*\)")
RB_DEBUG_RE = re.compile(r"\bbinding\.pry\b")
SECRET_PATTERNS = [
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id"),
    (re.compile(r"\bghp_[A-Za-z0-9]{36}\b"), "GitHub personal access token"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"), "GitHub fine-grained token"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "Slack token"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key block"),
]


def run_git(args: list[str], cwd: Path, allow_fail: bool = False) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode and not allow_fail:
        raise SystemExit(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def repo_root() -> Path:
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True, check=False)
    if result.returncode:
        raise SystemExit("Run this script inside a git repository.")
    return Path(result.stdout.strip())


def changed_files(root: Path, base: str) -> list[str]:
    names: set[str] = set()
    for args in (
        ["diff", "--name-only", f"{base}...HEAD"],
        ["diff", "--name-only"],
        ["diff", "--cached", "--name-only"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        output = run_git(args, root, allow_fail=True)
        names.update(line.strip() for line in output.splitlines() if line.strip())
    return sorted(names)


def added_lines_by_file(root: Path, base: str) -> dict[str, list[tuple[int | None, str]]]:
    added: dict[str, list[tuple[int | None, str]]] = {}
    for args in (
        ["diff", "--unified=0", f"{base}...HEAD"],
        ["diff", "--unified=0"],
        ["diff", "--cached", "--unified=0"],
    ):
        output = run_git(args, root, allow_fail=True)
        current: str | None = None
        new_line: int | None = None
        for raw in output.splitlines():
            if raw.startswith("+++ b/"):
                current = raw.removeprefix("+++ b/")
                new_line = None
                continue
            if raw.startswith("@@"):
                match = re.search(r"\+(\d+)(?:,(\d+))?", raw)
                new_line = int(match.group(1)) if match else None
                continue
            if current is None or raw.startswith("+++") or raw.startswith("---"):
                continue
            if raw.startswith("+"):
                added.setdefault(current, []).append((new_line, raw[1:]))
                if new_line is not None:
                    new_line += 1
            elif raw.startswith("-"):
                continue
            elif new_line is not None:
                new_line += 1
    untracked = run_git(["ls-files", "--others", "--exclude-standard"], root, allow_fail=True)
    for rel in (line.strip() for line in untracked.splitlines() if line.strip()):
        path = root / rel
        if path.is_file():
            added[rel] = [(idx, line) for idx, line in enumerate(read_lines(root, rel), start=1)]
    return added


def read_lines(root: Path, rel: str) -> list[str]:
    path = root / rel
    if not path.exists() or not path.is_file():
        return []
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return []


def scan_doc_headings(root: Path, files: list[str], added_lines: dict[str, list[tuple[int | None, str]]]) -> list[Finding]:
    findings: list[Finding] = []
    for rel in files:
        if Path(rel).suffix.lower() not in DOC_SUFFIXES:
            continue
        for line_number, line in added_lines.get(rel, []):
            match = MARKDOWN_HEADING_RE.match(line)
            if not match:
                continue
            words = [word.casefold() for word in WORD_RE.findall(match.group("title"))]
            for current, previous in zip(words[1:], words):
                if current != previous:
                    continue
                findings.append(
                    Finding(
                        "doc-heading-duplicate",
                        "review",
                        rel,
                        line_number,
                        f"Heading repeats `{current}` in adjacent words; verify this is intentional and not copy/paste drift.",
                    )
                )
                break
    return findings


def scan_docs(root: Path, files: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for rel in files:
        if Path(rel).suffix.lower() not in DOC_SUFFIXES:
            continue
        for idx, line in enumerate(read_lines(root, rel), start=1):
            if not POLICY_EXAMPLE_RE.search(line):
                for pattern, label in LOCAL_DOC_PATTERNS:
                    if pattern.search(line):
                        findings.append(Finding("portable-docs", "should", rel, idx, f"Replace {label} with durable source provenance."))
            credential_match = CREDENTIALISH_RE.search(line)
            if credential_match and not POLICY_EXAMPLE_RE.search(line):
                findings.append(
                    Finding(
                        "portable-docs",
                        "review",
                        rel,
                        idx,
                        f"Check whether `{credential_match.group(0).strip('`')}` is an unnecessary concrete credential/parameter name.",
                    )
                )
    return findings


def scan_test_names(root: Path, files: list[str], added_lines: dict[str, list[tuple[int | None, str]]]) -> list[Finding]:
    findings: list[Finding] = []
    for rel in files:
        if not re.search(r"(test|spec)", rel, re.IGNORECASE):
            continue
        if Path(rel).suffix.lower() not in TEXT_SUFFIXES:
            continue
        added_text = "\n".join(line for _, line in added_lines.get(rel, []))
        for pattern in TEST_NAME_PATTERNS:
            for match in pattern.finditer(added_text):
                name = " ".join(match.group("name").split())
                if not BROAD_TEST_WORDS_RE.search(name):
                    continue
                line = None
                matched_prefix = added_text[: match.start()].count("\n")
                if rel in added_lines and matched_prefix < len(added_lines[rel]):
                    line = added_lines[rel][matched_prefix][0]
                findings.append(
                    Finding(
                        "test-truthfulness",
                        "review",
                        rel,
                        line,
                        f"Broad test name `{name}`: verify fixtures/assertions exercise every promised case or split the test.",
                    )
                )
    return findings


def scan_prompt_contracts(root: Path, files: list[str], added_lines: dict[str, list[tuple[int | None, str]]]) -> list[Finding]:
    findings: list[Finding] = []
    for rel in files:
        if Path(rel).suffix.lower() not in DOC_SUFFIXES:
            continue
        if not re.search(r"(prompt|spec|instruction|template)", rel, re.IGNORECASE):
            continue
        lines = read_lines(root, rel)
        if not lines:
            continue
        text = "\n".join(lines)
        forbids_em_dash = re.search(r"no em dash|no em dashes|do not use em dash", text, re.IGNORECASE)
        forbids_horizontal_rule = re.search(r"no horizontal rule|no horizontal separator|do not use.*three consecutive hyphens", text, re.IGNORECASE)
        forbids_code_fences = FORBIDS_CODE_FENCES_RE.search(text)
        forbids_commentary = FORBIDS_COMMENTARY_RE.search(text)
        for idx, line in enumerate(lines, start=1):
            if forbids_em_dash and "—" in line:
                findings.append(
                    Finding(
                        "prompt-contract",
                        "review",
                        rel,
                        idx,
                        "Prompt forbids em dashes but still includes the literal em dash character; verify examples/instructions do not reinforce forbidden output.",
                    )
                )
            if forbids_horizontal_rule and re.match(r"^\s*---\s*$", line):
                findings.append(
                    Finding(
                        "prompt-contract",
                        "review",
                        rel,
                        idx,
                        "Prompt forbids horizontal rules but still includes a standalone `---` divider.",
                    )
                )
            if forbids_code_fences and CODE_FENCE_OPEN_RE.match(line) and not is_documentation_only_fence(lines, idx - 1):
                findings.append(
                    Finding(
                        "prompt-contract",
                        "review",
                        rel,
                        idx,
                        "Prompt forbids code fences but includes a fenced example; clarify whether fences are documentation-only and forbidden in model output.",
                    )
                )
            if forbids_commentary and is_commentary_example_line(lines, idx - 1):
                findings.append(
                    Finding(
                        "prompt-contract",
                        "review",
                        rel,
                        idx,
                        "Prompt forbids commentary around JSON but includes prose in an example response; verify examples cannot teach decorated model output.",
                    )
                )
        findings.extend(scan_label_example_casing(rel, lines))
    return findings


def is_commentary_example_line(lines: list[str], index: int) -> bool:
    line = lines[index].strip()
    if not line or line.startswith(("#", "{", "[", "`")):
        return False
    window_start = max(0, index - 3)
    nearby = "\n".join(lines[window_start : index + 1])
    if not re.search(r"\bexample(?:\s+(?:response|output))?\b", nearby, re.IGNORECASE):
        return False
    return bool(re.search(r"[A-Za-z]", line))


def is_documentation_only_fence(lines: list[str], index: int) -> bool:
    window_start = max(0, index - 4)
    nearby = "\n".join(lines[window_start : index + 1])
    return bool(DOCUMENTATION_ONLY_FENCE_RE.search(nearby))


def scan_label_example_casing(rel: str, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for idx, line in enumerate(lines, start=1):
        match = LABEL_RULE_RE.search(line)
        if not match:
            continue
        labels = [part.strip(" .`\"'") for part in re.split(r"\bor\b|,|/", match.group("labels")) if part.strip()]
        labels = [label for label in labels if any(char.isupper() for char in label)]
        if not labels:
            continue
        lower_labels = {label.lower(): label for label in labels}
        for example_idx, example in enumerate(lines[idx : min(len(lines), idx + 25)], start=idx + 1):
            for lower_label, label in lower_labels.items():
                if lower_label in example and label not in example:
                    findings.append(
                        Finding(
                            "prompt-contract",
                            "review",
                            rel,
                            example_idx,
                            f"Example may use `{lower_label}` where declared label casing is `{label}`; verify prompt examples obey the declared output contract.",
                        )
                    )
                    break
    return findings


def scan_added_line_hygiene(files: list[str], added_lines: dict[str, list[tuple[int | None, str]]]) -> list[Finding]:
    findings: list[Finding] = []
    for rel in files:
        suffix = Path(rel).suffix.lower()
        is_test_path = bool(re.search(r"(test|spec)", rel, re.IGNORECASE))
        for line_number, line in added_lines.get(rel, []):
            if CONFLICT_MARKER_RE.match(line):
                findings.append(
                    Finding("merge-conflict", "must", rel, line_number, "Added line contains a merge conflict marker; resolve the conflict before review.")
                )
            for pattern, label in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        Finding("secret-material", "must", rel, line_number, f"Added line matches {label} format; remove the committed secret and rotate it.")
                    )
            if suffix in CODE_SUFFIXES and TODO_ADDED_RE.search(line):
                findings.append(
                    Finding("todo-added", "review", rel, line_number, "Added line introduces TODO/FIXME-style debt; resolve it or convert it to a tracked issue.")
                )
            if is_test_path and suffix in CODE_SUFFIXES:
                if FOCUSED_TEST_RE.search(line):
                    findings.append(
                        Finding("focused-test", "should", rel, line_number, "Added focused test (`.only`/`fit`/`fdescribe`) would silently skip the rest of the suite.")
                    )
                if SKIPPED_TEST_RE.search(line):
                    findings.append(
                        Finding("skipped-test", "review", rel, line_number, "Added skipped test; confirm the skip is intentional and tracked.")
                    )
            if not is_test_path:
                if suffix in JS_SUFFIXES and JS_DEBUG_RE.search(line):
                    findings.append(
                        Finding("debug-leftover", "should", rel, line_number, "Added `console.log`/`debugger` in non-test code; remove it or route through the project logger.")
                    )
                if suffix == ".py" and PY_DEBUG_RE.search(line):
                    findings.append(
                        Finding("debug-leftover", "should", rel, line_number, "Added Python `breakpoint()`/`pdb.set_trace()` in non-test code; remove before merge.")
                    )
                if suffix == ".rb" and RB_DEBUG_RE.search(line):
                    findings.append(
                        Finding("debug-leftover", "should", rel, line_number, "Added `binding.pry` in non-test code; remove before merge.")
                    )
    return findings


def resolve_base(root: Path, base: str) -> str:
    if base != "auto":
        if not run_git(["rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"], root, allow_fail=True).strip():
            raise SystemExit(f"Base ref `{base}` does not resolve in this repository; pass a --base ref that exists.")
        return base
    head_ref = run_git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], root, allow_fail=True).strip()
    if head_ref:
        return head_ref
    for candidate in ("origin/main", "origin/master", "main", "master"):
        if run_git(["rev-parse", "--verify", "--quiet", candidate], root, allow_fail=True).strip():
            return candidate
    return "HEAD"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run generic mechanical quality-gate checks.")
    parser.add_argument(
        "--base",
        default="auto",
        help="Base ref for committed branch diff (default: auto-detect origin default branch, then origin/main, origin/master, main, master).",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON findings.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 when findings are present.")
    args = parser.parse_args()

    root = repo_root()
    base = resolve_base(root, args.base)
    files = changed_files(root, base)
    added_lines = added_lines_by_file(root, base)
    findings: list[Finding] = []
    findings.extend(scan_docs(root, files))
    findings.extend(scan_doc_headings(root, files, added_lines))
    findings.extend(scan_test_names(root, files, added_lines))
    findings.extend(scan_prompt_contracts(root, files, added_lines))
    findings.extend(scan_added_line_hygiene(files, added_lines))

    if args.json:
        print(json.dumps([asdict(finding) for finding in findings], indent=2))
    else:
        print(f"Base ref: {base}")
        print(f"Changed files scanned: {len(files)}")
        if not findings:
            print("No mechanical quality-gate findings.")
        for finding in findings:
            location = finding.path if finding.line is None else f"{finding.path}:{finding.line}"
            print(f"[{finding.severity}] {finding.check} {location} - {finding.message}")

    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    sys.exit(main())
