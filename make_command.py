#!/usr/bin/env python3
import re
from pathlib import Path

def parse_choco_list(path: str) -> str:
    """
    Parse `choco list` output and return a one-liner:
    choco install -y pkg1 pkg2 ...
    """
    text = Path(path).read_text(encoding="utf-8").splitlines()
    pkgs = set()

    line_pattern = re.compile(r"^([a-zA-Z0-9\.\-_]+)\s+\d")

    for line in text:
        m = line_pattern.match(line)
        if not m:
            continue
        name = m.group(1)
        pkgs.add(name)

    # drop meta-lines like `Chocolatey v2.5.1` by filtering again
    pkgs = {p for p in pkgs if not p.lower().startswith("chocolatey v")}

    # output sorted for determinism
    ordered = sorted(pkgs, key=str.lower)

    return "choco install -y " + " ".join(ordered)


if __name__ == "__main__":
    cmd = parse_choco_list("choco_list.txt")
    print(cmd)
