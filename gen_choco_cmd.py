#!/usr/bin/env python3
"""
Parse a `choco list` output file and emit a one-line
`choco install -y ...` command, formatted nicely for
GitHub Actions logs and job summary.
"""

import argparse
import os
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="choco_list.txt",
        help="Path to file containing `choco list` output.",
    )
    return parser.parse_args()


def extract_packages(text: str) -> list[str]:
    """
    Extract package names of the form:

        name version

    from `choco list` output.
    """
    pattern = re.compile(r"^([A-Za-z0-9.\-_]+)\s+\d")
    packages: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = pattern.match(line)
        if not match:
            continue

        name = match.group(1)

        # Skip the 'Chocolatey v2.5.1' header if it ever matches.
        if name.lower().startswith("chocolatey v"):
            continue

        packages.add(name)

    return sorted(packages, key=str.lower)


def build_command(packages: list[str]) -> str:
    if not packages:
        return "REM No packages found in choco_list.txt"
    return "choco install -y " + " ".join(packages)


def print_for_logs(command: str) -> None:
    """
    Make the command very obvious in GitHub Actions logs
    using a group and loud markers.
    """
    print("::group::Chocolatey reinstall command")
    print("=== BEGIN CHOCO INSTALL ONE-LINER ===")
    print(command)
    print("=== END CHOCO INSTALL ONE-LINER ===")
    print("::endgroup::")


def write_step_summary(command: str) -> None:
    """
    Also write the command into the GitHub Actions step summary
    if available, so it shows up on the run page.
    """
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    try:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write("## Chocolatey reinstall command\n\n")
            fh.write("```powershell\n")
            fh.write(command + "\n")
            fh.write("```\n")
    except OSError as exc:
        print(f"::warning::Failed to write step summary: {exc}", file=sys.stderr)


def main() -> None:
    args = parse_args()
    path = Path(args.input)

    if not path.is_file():
        print(f"::error::Input file not found: {path}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8")
    packages = extract_packages(text)
    command = build_command(packages)

    print_for_logs(command)
    write_step_summary(command)


if __name__ == "__main__":
    main()
