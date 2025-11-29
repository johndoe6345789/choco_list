#!/usr/bin/env python3
"""
Convert a `choco install -y ...` one-liner into a `choco list`-style file.

- Reads an install command from install.txt
- Optionally reads a real `choco list` output from choco_list.txt
- For each package in the install command:
    - If a real version exists in choco_list.txt, use it
    - Otherwise, use a placeholder version 0.0.0
"""

import argparse
from pathlib import Path
from typing import Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--install-file",
        default="install.txt",
        help="File containing a `choco install -y ...` line.",
    )
    parser.add_argument(
        "--list-file",
        default="choco_list.txt",
        help="File containing `choco list` output (optional but recommended).",
    )
    parser.add_argument(
        "--output",
        default="-",
        help="Output file for generated list (default: stdout).",
    )
    return parser.parse_args()


def load_install_line(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "choco" in line and "install" in line:
            return line
    raise ValueError("No `choco install` line found in install file.")


def extract_packages_from_install(line: str) -> list[str]:
    """
    Extract package names from a `choco install` command.

    Example:
        choco install -y 7zip git vscode
        -> ["7zip", "git", "vscode"]
    """
    parts = line.split()
    pkgs: list[str] = []

    # Find the position of "install"
    try:
        idx = next(i for i, p in enumerate(parts) if p.lower() == "install")
    except StopIteration:
        raise ValueError("Install line does not contain `install` keyword.")

    for token in parts[idx + 1 :]:
        # skip flags like -y, /something
        if token.startswith("-") or token.startswith("/"):
            continue
        pkgs.append(token)

    return pkgs


def load_versions_from_choco_list(path: Path) -> Dict[str, str]:
    """
    Build name -> version map from a real `choco list` output.
    Only first two columns are used.
    """
    if not path.is_file():
        return {}

    text = path.read_text(encoding="utf-8", errors="replace")
    versions: Dict[str, str] = {}

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("chocolatey v"):
            continue
        if line.lower().endswith("packages installed."):
            continue

        parts = line.split()
        if len(parts) < 2:
            continue
        name, version = parts[0], parts[1]
        versions[name] = version

    return versions


def build_choco_list(
    packages: list[str],
    versions: Dict[str, str],
    header_version: str = "2.5.1",
) -> str:
    """
    Produce a `choco list`-style block.
    Unknown versions get 0.0.0.
    """
    lines: list[str] = []
    lines.append(f"Chocolatey v{header_version}")

    for name in packages:
        version = versions.get(name, "0.0.0")
        lines.append(f"{name} {version}")

    lines.append(f"{len(packages)} packages listed.")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()

    install_path = Path(args.install_file)
    list_path = Path(args.list_file)

    install_line = load_install_line(install_path)
    packages = extract_packages_from_install(install_line)
    versions = load_versions_from_choco_list(list_path)

    output_text = build_choco_list(packages, versions)

    if args.output == "-":
        print(output_text, end="")
    else:
        Path(args.output).write_text(output_text, encoding="utf-8")


if __name__ == "__main__":
    main()
