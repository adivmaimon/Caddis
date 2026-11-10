"""Tests for the build wave planner (plugin/skills/build/scripts/waves.py)."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "plugin/skills/build/scripts/waves.py"


def project(changes=None, depends="none"):
    text = "# Demo\n\n**Status:** Pending\n**Depends on:** %s\n\n## Goal\nA `goal/path.md` outside Changes.\n" % depends
    if changes is not None:
        text += "\n## Changes\n" + changes + "\n## Phases\n- `phases/path.md`\n"
    return text


def table(*rows):
    return "| File | Change |\n| --- | --- |\n" + "".join("| %s | Something in `not/this.md` |\n" % r for r in rows)


class WavesTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)

    def write(self, name, text):
        path = self.dir / name
        path.write_text(text)
        return str(path)

    def run_waves(self, *args):
        proc = subprocess.run([sys.executable, str(SCRIPT)] + list(args),
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def names(self, result):
        return [[Path(p).stem for p in wave] for wave in result["waves"]]

    def test_disjoint_projects_share_a_wave(self):
        a = self.write("project-a.md", project(table("`src/a.py`")))
        b = self.write("project-b.md", project(table("`src/b.py`")))
        result = self.run_waves(a, b)
        self.assertEqual(self.names(result), [["project-a", "project-b"]])
        self.assertEqual(result["sequenced"], [])

    def test_shared_file_splits_them_in_build_order(self):
        a = self.write("project-a.md", project(table("`src/a.py`", "`src/common.py`")))
        b = self.write("project-b.md", project(table("`src/common.py`")))
        c = self.write("project-c.md", project(table("`src/c.py`")))
        result = self.run_waves(a, b, c)
        self.assertEqual(self.names(result), [["project-a", "project-c"], ["project-b"]])
        self.assertEqual(result["sequenced"], [{"project": b, "after": a, "files": ["src/common.py"]}])

    def test_depends_on_orders_waves(self):
        a = self.write("project-a.md", project(table("`src/a.py`")))
        b = self.write("project-b.md", project(table("`src/b.py`"), depends="project-a.md"))
        c = self.write("project-c.md", project(table("`src/c.py`"), depends="project-x.md, project-b"))
        self.assertEqual(self.names(self.run_waves(a, b, c)), [["project-a"], ["project-b"], ["project-c"]])

    def test_missing_changes_gets_a_wave_of_its_own(self):
        a = self.write("project-a.md", project(table("`src/a.py`")))
        b = self.write("project-b.md", project(None))
        c = self.write("project-c.md", project(table("`src/c.py`")))
        self.assertEqual(self.names(self.run_waves(a, b, c)), [["project-a"], ["project-b"], ["project-c"]])

    def test_ignore_lets_the_version_file_be_shared(self):
        version = "`plugin/.claude-plugin/plugin.json`"
        a = self.write("project-a.md", project(table("`src/a.py`", version)))
        b = self.write("project-b.md", project(table("`src/b.py`", version)))
        self.assertEqual(len(self.run_waves(a, b)["waves"]), 2)
        result = self.run_waves("--ignore", "./plugin/.claude-plugin/plugin.json,other.json", a, b)
        self.assertEqual(self.names(result), [["project-a", "project-b"]])

    def test_missing_project_file_fails(self):
        proc = subprocess.run([sys.executable, str(SCRIPT), str(self.dir / "nope.md")],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)


class PathReadingTest(unittest.TestCase):
    """Which paths count as a project's Changes."""

    def paths(self, changes):
        sys.path.insert(0, str(SCRIPT.parent))
        sys.dont_write_bytecode = True  # keep __pycache__ out of plugin/
        try:
            import waves
        finally:
            sys.path.pop(0)
        return waves.changed_paths(project(changes))

    def test_cell_with_several_paths_and_notes(self):
        got = self.paths(table(
            "`tests/test_waves.py` (new), `tests/test_progress.py`",
            "`.caddis/caddis.md` (this repo, local)",
            "`README.md`, `plugin/README.md`",
        ))
        self.assertEqual(got, {"tests/test_waves.py", "tests/test_progress.py", ".caddis/caddis.md",
                               "README.md", "plugin/README.md"})

    def test_backticks_inside_a_bracketed_note_are_ignored(self):
        self.assertEqual(self.paths(table("`src/a.py` (moved from `src/old.py`)")), {"src/a.py"})

    def test_bullet_lines(self):
        got = self.paths("- `src/a.py`: add `run --fast` to `src/b.py`\n* `docs/c.md` (new)\nProse `not/me.md`\n")
        self.assertEqual(got, {"src/a.py", "src/b.py", "docs/c.md"})

    def test_only_the_first_column_and_only_the_changes_section(self):
        got = self.paths(table("`src/a.py`"))
        self.assertEqual(got, {"src/a.py"})


if __name__ == "__main__":
    unittest.main()
