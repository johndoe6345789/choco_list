#!/usr/bin/env python3
"""
Merge:
- your current 'choco list' output
- a PowerShell script with lots of 'choco install' lines (incl. commented)

into a single:
    choco install -y pkg1 pkg2 ...

Usage:
    python merge_choco_lists.py --list choco_list.txt --ps1 setup.ps1
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, List, Set, Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge choco list output with a choco-based setup script."
    )
    parser.add_argument(
        "--list",
        required=True,
        help="Path to text file created by `choco list`.",
    )
    parser.add_argument(
        "--ps1",
        required=True,
        help="Path to PowerShell script containing `choco install` lines.",
    )
    parser.add_argument(
        "--no-sort",
        action="store_true",
        help="Do not sort the final package list; keep discovery order.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"Error reading {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def extract_from_choco_list(text: str) -> List[str]:
    """
    Parse `choco list` output:
        pkgname 1.2.3
    Ignore the header line and footer 'N packages installed.'.
    """
    packages: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip header/footer noise
        if line.lower().startswith("chocolatey v"):
            continue
        if line.lower().endswith("packages installed."):
            continue

        # First token before whitespace is the package ID
        parts = line.split()
        if not parts:
            continue
        name = parts[0]
        packages.append(name)
    return packages


def extract_from_ps1(text: str) -> List[str]:
    """
    Find all `choco install <name>` occurrences,
    including commented ones like `#choco install foo -y`.
    """
    pattern = re.compile(
        r"choco\s+install\s+([A-Za-z0-9.\-_]+)",
        re.IGNORECASE,
    )
    matches = pattern.findall(text)
    # Preserve order but dedupe later when we merge
    return list(matches)


def merge_packages(*sources: Iterable[str]) -> List[str]:
    """
    Merge package name sequences in a case-insensitive way,
    preserving the first-seen capitalization.
    """
    seen: Set[str] = set()
    result: List[str] = []

    for source in sources:
        for name in source:
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(name)

    return result


def maybe_sort(packages: List[str], do_sort: bool) -> List[str]:
    if not do_sort:
        return packages
    return sorted(packages, key=str.lower)


def build_one_liner(packages: List[str]) -> str:
    if not packages:
        return "REM No packages found to install"
    return "choco install -y " + " ".join(packages)


def main() -> None:
    args = parse_args()
    list_path = Path(args.list)
    ps1_path = Path(args.ps1)

    if not list_path.is_file():
        print(f"`--list` file not found: {list_path}", file=sys.stderr)
        sys.exit(1)
    if not ps1_path.is_file():
        print(f"`--ps1` file not found: {ps1_path}", file=sys.stderr)
        sys.exit(1)

    choco_list_text = read_text(list_path)
    ps1_text = read_text(ps1_path)

    from_list = extract_from_choco_list(choco_list_text)
    from_ps1 = extract_from_ps1(ps1_text)

    merged = merge_packages(from_list, from_ps1)
    merged = maybe_sort(merged, do_sort=not args.no_sort)

    command = build_one_liner(merged)
    print("=== MERGED CHOCO INSTALL COMMAND ===")
    print(command)


if __name__ == "__main__":
    main()
