#!/usr/bin/env python3
"""
Parse a `choco list` output file and emit a PowerShell script
that installs all packages via a $packages array and a foreach loop,
formatted nicely for GitHub Actions logs and job summary.
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="choco_list.txt",
        help="Path to file containing `choco list` output.",
    )
    return parser.parse_args()


def extract_packages(text: str) -> List[str]:
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


def build_powershell_script(packages: List[str]) -> str:
    """
    Build a PowerShell script that defines a $packages array
    and installs each package in a foreach loop.
    """
    if not packages:
        return "# No packages found in choco_list.txt"

    lines: List[str] = []

    lines.append("$packages = @(")
    for pkg in packages:
        lines.append(f"  '{pkg}'")
    lines.append(")")
    lines.append("")
    lines.append("foreach ($pkg in $packages) {")
    lines.append('    Write-Host "Installing $pkg..." -ForegroundColor Cyan')
    lines.append("    choco install $pkg -y")
    lines.append("}")

    return "\n".join(lines)


def print_for_logs(script: str) -> None:
    """
    Make the script very obvious in GitHub Actions logs
    using a group and loud markers.
    """
    print("::group::Chocolatey reinstall script")
    print("=== BEGIN CHOCO INSTALL POWERSHELL SCRIPT ===")
    print(script)
    print("=== END CHOCO INSTALL POWERSHELL SCRIPT ===")
    print("::endgroup::")


def write_step_summary(script: str) -> None:
    """
    Also write the script into the GitHub Actions step summary
    if available, so it shows up on the run page.
    """
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    try:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write("## Chocolatey reinstall PowerShell script\n\n")
            fh.write("```powershell\n")
            fh.write(script + "\n")
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
    script = build_powershell_script(packages)

    print_for_logs(script)
    write_step_summary(script)


if __name__ == "__main__":
    main()
