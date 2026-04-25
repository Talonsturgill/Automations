#!/usr/bin/env python3
"""Lightweight Mermaid syntax check for GitHub renderer compatibility.

Catches the patterns that cause GitHub's Mermaid renderer to silently fail:
- Unquoted node labels containing <br/>, @, :, &, <, >
- Arrow tokens (`->`, `<-`) inside node labels (parsed as edges)

Exits non-zero if any issues are found, with file:line:column-style messages.

Usage: python3 scripts/check_mermaid.py
"""
import os
import re
import sys


NODE_LABEL_RE = re.compile(
    r"\b\w+(\[\([^\)\]]+\)\]|\(\[[^\)\]]+\]\)|\(\([^\)]+\)\)|\{[^\}]+\}|\[[^\]]+\])"
)


def check_block(lines, block_offset, source):
    """Yield (line_no, col_no, message) for each issue in a Mermaid block."""
    issues = []
    for i, line in enumerate(lines):
        line_no = block_offset + i + 1  # +1 for the ```mermaid line itself
        for m in NODE_LABEL_RE.finditer(line):
            full = m.group(1)
            # Strip outer brackets
            if full.startswith("[(") and full.endswith(")]"):
                inner = full[2:-2]
            elif full.startswith("([") and full.endswith("])"):
                inner = full[2:-2]
            elif full.startswith("((") and full.endswith("))"):
                inner = full[2:-2]
            elif full.startswith("{") and full.endswith("}"):
                inner = full[1:-1]
            elif full.startswith("[") and full.endswith("]"):
                inner = full[1:-1]
            else:
                continue
            # Skip if already quoted
            stripped = inner.strip()
            if stripped.startswith('"') and stripped.endswith('"'):
                continue
            # Check for risky chars
            risky = sorted(set(re.findall(r"[@&:<>]", inner)))
            arrows = "->" in inner or "<-" in inner
            if risky or arrows:
                tag = ", ".join(risky + (["arrow"] if arrows else []))
                col = m.start(1) + 1
                issues.append(
                    (line_no, col, f"unquoted node label `{full}` contains {tag}")
                )
    return issues


def check_file(path):
    with open(path) as f:
        text = f.read()
    issues = []
    pos = 0
    line_offset = 0
    for m in re.finditer(r"```mermaid\n(.*?)```", text, re.DOTALL):
        # Compute line number where the mermaid block starts
        block_start = m.start(1)
        block_line = text.count("\n", 0, block_start)
        block_text = m.group(1)
        block_lines = block_text.split("\n")
        for line_no, col, msg in check_block(block_lines, block_line, path):
            issues.append((path, line_no, col, msg))
    return issues


def main():
    md_files = []
    for root, _, files in os.walk("."):
        if ".git" in root.split(os.sep) or "node_modules" in root.split(os.sep):
            continue
        for f in files:
            if f.endswith(".md"):
                md_files.append(os.path.join(root, f))

    all_issues = []
    for md in sorted(md_files):
        all_issues.extend(check_file(md))

    if all_issues:
        for path, line, col, msg in all_issues:
            # GitHub Actions error annotation format
            print(f"::error file={path},line={line},col={col}::{msg}")
            print(f"{path}:{line}:{col}: {msg}", file=sys.stderr)
        print(f"\n{len(all_issues)} Mermaid issue(s) found", file=sys.stderr)
        sys.exit(1)

    print(f"Checked {len(md_files)} markdown files. No Mermaid issues found.")


if __name__ == "__main__":
    main()
