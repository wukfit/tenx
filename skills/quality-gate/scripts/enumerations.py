"""Emit raw material for the quality-gate Required Enumerations.

This is deliberately NOT a findings scanner. It prints three deterministic
listings the lead agent must turn into the E1/E2/E4 tables:

1. Exported symbols defined in changed files, with call sites in files the
   diff did NOT touch (blast-radius candidates for E1).
2. Added lines that look permission/config relevant (capability-parity raw
   material for E2).
3. Added lines that introduce remote calls (failure-audit raw material for E4).

Every listed item is a prompt for review, not proof of a problem. Truncation
is always reported explicitly so silence never reads as coverage.
"""

import argparse
import re
from pathlib import Path

from quality_scan import added_lines_by_file, changed_files, repo_root, resolve_base, run_git

MAX_SYMBOLS = 60
MAX_CALLERS_PER_SYMBOL = 20

# Languages whose public symbols the E1 section can extract. Changed code
# files outside this set are reported as unparsed, never silently skipped.
SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".go", ".rb", ".rs", ".php"}

# Code files E1 cannot parse for exports; listed so absence is visible.
UNPARSED_CODE_SUFFIXES = {".java", ".kt", ".kts", ".cs", ".swift", ".scala", ".c", ".cc", ".cpp", ".h", ".hpp", ".ex", ".exs", ".clj", ".fs", ".dart", ".m", ".mm"}

EXPORT_PATTERNS = [
    re.compile(r"^export\s+(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)"),  # js/ts
    re.compile(r"^export\s+(?:const|let|var)\s+([A-Za-z_$][\w$]*)"),  # js/ts
    re.compile(r"^export\s+(?:abstract\s+)?class\s+([A-Za-z_$][\w$]*)"),  # js/ts
    re.compile(r"^def\s+([a-z_][\w]*)"),  # python/ruby top-level
    re.compile(r"^class\s+([A-Z][\w]*)"),  # python/ruby top-level
    re.compile(r"^func\s+([A-Z][\w]*)"),  # go exported
    re.compile(r"^pub\s+(?:async\s+)?fn\s+([a-z_][\w]*)"),  # rust
    re.compile(r"^pub\s+struct\s+([A-Z][\w]*)"),  # rust
    re.compile(r"^\s*public\s+(?:static\s+)?function\s+([A-Za-z_][\w]*)"),  # php
]

# Permission/identity hints across ecosystems: AWS (arn:, PolicyStatement,
# AssumeRole), GCP (roles/, gserviceaccount), Azure (role_assignment),
# Kubernetes (RoleBinding, ServiceAccount, secretKeyRef), Terraform (_iam_),
# SQL grants, plus env-var credential reads.
PERMISSION_PATTERN = re.compile(
    r"arn:[a-z-]+:|PolicyStatement|addToRolePolicy|addToPrincipalPolicy|grant[A-Z]\w*\(|"
    r"Effect\.(ALLOW|DENY)|\bactions:\s*\[|\biam:|AssumeRole|process\.env\.[A-Z]|os\.environ|"
    r"\broles/[a-zA-Z.]+|\.gserviceaccount\.com|role_assignment|roleRef|RoleBinding|ClusterRole|"
    r"serviceAccountName|ServiceAccount\b|secretKeyRef|_iam_|\bGRANT\s+(SELECT|INSERT|UPDATE|DELETE|ALL)\b"
)

# Remote/network call hints: AWS SDK command/send, JS fetch/axios, Python
# requests/httpx/urllib/boto3, Go net/http, generic .invoke(.
REMOTE_CALL_PATTERN = re.compile(
    r"new\s+\w+Command\(|\.send\(|\bfetch\(|axios\.|https?\.request\(|\.invoke\(|boto3\.|"
    r"requests\.(get|post|put|patch|delete)\(|httpx\.|urllib\.request|http\.(Get|Post|NewRequest)\(|"
    r"HttpClient\b|WebClient\b|RestTemplate\b"
)

TEST_HINT = re.compile(r"(\.test\.|\.spec\.|_test\.|test_|/tests?/|/__tests__/|/fixtures?/)")

# Names that appear as exports in nearly every module of common frameworks;
# caller lists for these are all noise (route handlers, lambda entrypoints).
GENERIC_SYMBOLS = {"handler", "main", "default", "GET", "POST", "PUT", "PATCH", "DELETE", "config", "middleware"}

# Above this many callers the symbol is almost certainly too generic for a
# useful listing; report the count and leave enumeration to the lead.
GENERIC_CALLER_THRESHOLD = 50


def is_source(rel: str) -> bool:
    return Path(rel).suffix in SOURCE_SUFFIXES and not TEST_HINT.search(rel)


def exported_symbols(root: Path, rel: str) -> list[str]:
    path = root / rel
    if not path.is_file():
        return []
    names: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    for line in text.splitlines():
        for pattern in EXPORT_PATTERNS:
            match = pattern.match(line)
            if match:
                names.append(match.group(1))
    return names


def callers_outside_changed_set(root: Path, symbol: str, defining_file: str, changed: set[str]) -> list[str]:
    output = run_git(["grep", "-n", "--", rf"\b{symbol}\b"], root, allow_fail=True)
    callers: list[str] = []
    for raw in output.splitlines():
        rel, _, rest = raw.partition(":")
        if rel == defining_file or TEST_HINT.search(rel):
            continue
        if rel in changed or Path(rel).suffix not in SOURCE_SUFFIXES:
            continue
        callers.append(f"{rel}:{rest.partition(':')[0]}")
    return callers


def section_blast_radius(root: Path, files: list[str], changed: set[str]) -> None:
    print("== E1 raw material: exported symbols in changed files with UNCHANGED callers ==")
    print("(Each unchanged caller inherits this PR's behavior change without review. Classify every one.)")
    unparsed = sorted(rel for rel in files if Path(rel).suffix in UNPARSED_CODE_SUFFIXES and not TEST_HINT.search(rel))
    if unparsed:
        print(f"  NOTE: cannot extract exports from {len(unparsed)} changed file(s); enumerate their public symbols manually:")
        for rel in unparsed:
            print(f"    {rel}")
    emitted = 0
    truncated = False
    seen: set[tuple[str, str]] = set()
    for rel in files:
        if not is_source(rel):
            continue
        for symbol in exported_symbols(root, rel):
            if symbol in GENERIC_SYMBOLS or (symbol, rel) in seen:
                continue
            seen.add((symbol, rel))
            callers = callers_outside_changed_set(root, symbol, rel, changed)
            if not callers:
                continue
            if emitted >= MAX_SYMBOLS:
                truncated = True
                break
            emitted += 1
            if len(callers) > GENERIC_CALLER_THRESHOLD:
                print(
                    f"  {symbol}  (defined in {rel}) -> {len(callers)} unchanged callers; "
                    "name too common for a useful listing - enumerate manually if its behavior changed."
                )
                continue
            shown = callers[:MAX_CALLERS_PER_SYMBOL]
            print(f"  {symbol}  (defined in {rel}) -> {len(callers)} unchanged caller(s):")
            for caller in shown:
                print(f"    {caller}")
            if len(callers) > len(shown):
                print(f"    ... {len(callers) - len(shown)} more caller(s) NOT shown - enumerate them.")
        if truncated:
            break
    if truncated:
        print(f"  TRUNCATED at {MAX_SYMBOLS} symbols - remaining symbols were NOT listed; enumerate them manually.")
    if emitted == 0:
        print("  none found")
    print()


DOC_SUFFIXES = {".md", ".mdx", ".txt", ".rst"}


def section_added_lines(
    title: str,
    hint: str,
    pattern: re.Pattern[str],
    added: dict[str, list[tuple[int | None, str]]],
) -> None:
    print(f"== {title} ==")
    print(f"({hint})")
    emitted = 0
    for rel in sorted(added):
        if TEST_HINT.search(rel) or Path(rel).suffix in DOC_SUFFIXES:
            continue
        for line_no, line in added[rel]:
            if pattern.search(line):
                location = rel if line_no is None else f"{rel}:{line_no}"
                print(f"  {location}  {line.strip()[:160]}")
                emitted += 1
    if emitted == 0:
        print("  none found")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit raw material for quality-gate Required Enumerations.")
    parser.add_argument("--base", default="auto", help="Base ref (same semantics as quality_scan.py).")
    args = parser.parse_args()

    root = repo_root()
    base = resolve_base(root, args.base)
    files = changed_files(root, base)
    changed = set(files)
    added = added_lines_by_file(root, base)

    print(f"Base ref: {base}")
    print(f"Changed files: {len(files)}")
    print()
    section_blast_radius(root, files, changed)
    section_added_lines(
        "E2 raw material: permission/config-relevant added lines",
        "Build the capability-parity table: every code path that newly reaches an external resource x every "
        "runtime/principal that executes it x grant/env evidence at file:line, or MISSING.",
        PERMISSION_PATTERN,
        added,
    )
    section_added_lines(
        "E4 raw material: remote calls introduced by added lines",
        "For each, quote the enclosing catch/fallback or record 'none - whole request fails'; compare siblings.",
        REMOTE_CALL_PATTERN,
        added,
    )
    return 0


if __name__ == "__main__":
    main()
