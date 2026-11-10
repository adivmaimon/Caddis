#!/usr/bin/env python3
"""Groups Caddis projects into build waves: projects in one wave can build side by side.

Reads each project file's `**Depends on:**` line and the paths in its `## Changes` section
(the table's first column and bullet lines, every backticked path, notes in brackets
ignored). Two projects conflict when they share a path, after dropping the paths given with
--ignore (files the integrator reconciles by rule, such as a version file). A project with no
Changes section conflicts with every other, so it gets a wave of its own.

Projects are first put in build order: the order given, moved only as far as needed so each
comes after every listed project it depends on. A dependency not in the list (already built)
is ignored. A project goes in the wave after the latest of its dependencies and of the earlier
projects it conflicts with, so build order holds wherever it matters.

Prints JSON: {"waves": [[path, ...], ...], "sequenced": [{"project", "after", "files"}]}.
"sequenced" names each earlier project a project waits for because they share files.
Standard library only, Python 3.8+. Exits 2 on a missing project file or a dependency cycle.

Usage: waves.py [--ignore <path>[,<path>...]]... <project-path>...
"""

import argparse
import json
import re
import sys
from pathlib import Path

BACKTICKED = re.compile(r"`([^`]+)`")
BRACKETED = re.compile(r"\([^)]*\)")
DEPENDS = re.compile(r"^\*\*Depends on:\*\*\s*(.*)$", re.M)


def stem(name):
    """A project's name as other projects refer to it: file name without .md."""
    name = Path(name.strip()).name
    return name[:-3] if name.endswith(".md") else name


def norm(path):
    path = path.strip()
    return path[2:] if path.startswith("./") else path


def is_path(span):
    """A backticked span that names a file or folder, not a command or a phrase."""
    return bool(span) and " " not in span and ("/" in span or "." in span)


def changes_section(text):
    """The lines under `## Changes`, or None when the project has no such section."""
    lines, found = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            if found:
                break
            found = line.strip() == "## Changes"
        elif found:
            lines.append(line)
    return lines if found else None


def changed_paths(text):
    """Every path a project's Changes names, or None when it has no Changes section."""
    lines = changes_section(text)
    if lines is None:
        return None
    paths = set()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            cells = stripped.strip("|").split("|")
            first = cells[0] if cells else ""
            if set(first.strip()) <= set("-: "):
                continue  # the separator row
            source = first
        elif stripped.startswith(("- ", "* ")):
            source = stripped[2:]
        else:
            continue
        for span in BACKTICKED.findall(BRACKETED.sub("", source)):
            if is_path(span):
                paths.add(norm(span))
    return paths


def depends_on(text):
    match = DEPENDS.search(text)
    if not match:
        return set()
    value = match.group(1).strip()
    if value.lower() in ("", "none", "-", "n/a"):
        return set()
    return {stem(part) for part in value.split(",") if part.strip()}


def build_order(info):
    """The projects in the order given, each moved after every listed project it depends on."""
    names = {p["name"] for p in info}
    placed, ordered, pending = set(), [], list(info)
    while pending:
        ready = next((p for p in pending if (p["deps"] & names) <= placed), None)
        if ready is None:
            raise ValueError("dependency cycle among: " + ", ".join(p["name"] for p in pending))
        pending.remove(ready)
        placed.add(ready["name"])
        ordered.append(ready)
    return ordered


def waves(projects, ignore):
    """projects: [(path, text)] in build order. Returns (waves, sequenced)."""
    info = []
    for path, text in projects:
        files = changed_paths(text)
        if files is not None:
            files -= ignore
        info.append({"path": path, "name": stem(path), "deps": depends_on(text), "files": files})
    info = build_order(info)
    wave_of, sequenced = {}, []
    for i, p in enumerate(info):
        level = 0
        for q in info[:i]:
            if q["name"] in p["deps"]:
                level = max(level, wave_of[q["name"]] + 1)
                continue
            if p["files"] is None or q["files"] is None:
                shared = None
            else:
                shared = sorted(p["files"] & q["files"])
                if not shared:
                    continue
            level = max(level, wave_of[q["name"]] + 1)
            sequenced.append({"project": p["path"], "after": q["path"], "files": shared or []})
        wave_of[p["name"]] = level
    grouped = [[] for _ in range(max(wave_of.values(), default=-1) + 1)]
    for p in info:
        grouped[wave_of[p["name"]]].append(p["path"])
    return grouped, sequenced


def main(argv=None):
    parser = argparse.ArgumentParser(description="Group Caddis projects into build waves.")
    parser.add_argument("--ignore", action="append", default=[],
                        help="paths every project may share, comma-separated; repeatable")
    parser.add_argument("projects", nargs="+")
    args = parser.parse_args(argv)
    ignore = {norm(p) for item in args.ignore for p in item.split(",") if p.strip()}
    projects = []
    for path in args.projects:
        try:
            projects.append((path, Path(path).read_text(encoding="utf-8")))
        except OSError as exc:
            print("waves.py: cannot read %s: %s" % (path, exc), file=sys.stderr)
            return 2
    try:
        grouped, sequenced = waves(projects, ignore)
    except ValueError as exc:
        print("waves.py: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps({"waves": grouped, "sequenced": sequenced}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
