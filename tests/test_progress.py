"""Tests for the build progress reporter (plugin/skills/build/scripts/progress.sh)."""

import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "plugin/skills/build/scripts/progress.sh"
PLAN = ".caddis/projects/active/project-demo.md"
TWO_PHASES = "### Phase 1 - One - DONE (2026-01-01)\n\n### Phase 2 - Two\n"


class ScriptTest(unittest.TestCase):
    """A temp git repo with Caddis project folders, and a way to run the script in it."""

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        (self.repo / ".caddis/projects/active").mkdir(parents=True)
        (self.repo / ".caddis/projects/completed").mkdir()

    def write_plan(self, text=TWO_PHASES):
        (self.repo / PLAN).write_text(text)

    def run_for(self, minutes_ago, estimate, seconds=1.5, start=None):
        """Run the script for a moment and return what it printed, and its exit code or None."""
        start = start or int(time.time()) - minutes_ago * 60
        env = dict(os.environ, CADDIS_PROGRESS_TICK="1")
        proc = subprocess.Popen(
            ["bash", str(SCRIPT), str(start), str(estimate), PLAN],
            cwd=self.repo, env=env, stdout=subprocess.PIPE, text=True,
        )
        try:
            out, _ = proc.communicate(timeout=seconds)
            return out, proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill()
            out, _ = proc.communicate()
            return out, None


class ProgressTest(ScriptTest):
    def test_short_build_stays_silent(self):
        self.write_plan()
        out, code = self.run_for(0, 3)
        self.assertEqual(out, "")
        self.assertIsNone(code)

    def test_report_names_progress_and_current_phase(self):
        self.write_plan()
        out, _ = self.run_for(6, 20)
        self.assertEqual(len(out.splitlines()), 1)
        self.assertIn("1/2 phases, 6m elapsed, about 14m left", out)
        self.assertIn("project-demo Phase 2 - Two", out)

    def test_low_estimate_starts_reporting_once_overrun(self):
        self.write_plan()
        out, _ = self.run_for(6, 3)
        self.assertIn("past the 3m estimate", out)

    def test_interval_widens_with_estimate(self):
        self.write_plan()
        self.assertEqual(self.run_for(6, 45)[0], "")
        self.assertIn("about 34m left", self.run_for(11, 45)[0])

    def test_quiet_build_is_flagged(self):
        self.write_plan()
        old = time.time() - 30 * 60
        os.utime(self.repo / PLAN, (old, old))
        out, _ = self.run_for(30, 60)
        self.assertIn("Possibly stuck", out)

    def test_rearm_keeps_the_report_clock(self):
        self.write_plan()
        start = int(time.time()) - 6 * 60
        self.assertIn("Caddis build", self.run_for(6, 20, start=start)[0])
        self.assertEqual(self.run_for(6, 20, start=start)[0], "")

    def test_moved_plan_ends_silently(self):
        self.write_plan()
        shutil.move(self.repo / PLAN, self.repo / ".caddis/projects/completed/project-demo.md")
        out, code = self.run_for(6, 20)
        self.assertEqual((out, code), ("", 0))

    def test_plan_without_phases_counts_as_one(self):
        self.write_plan("Just a task.\n")
        out, _ = self.run_for(6, 20)
        self.assertIn("0/1 phases", out)
        self.assertIn("Current: project-demo.", out)


class StatusFileTest(ScriptTest):
    """caddis-build.json, written every tick for the build panel mod."""

    def status(self):
        return json.loads((self.repo / ".git/caddis-build.json").read_text())

    def test_phases_and_current_phase_per_project(self):
        self.write_plan()
        self.run_for(1, 20)
        s = self.status()
        self.assertEqual((s["phases_done"], s["phases_total"], s["done"]), (1, 2, False))
        self.assertEqual(s["estimate"], 1200)
        p = s["projects"][0]
        self.assertEqual(p["name"], "project-demo")
        self.assertEqual(p["phases"], [{"name": "Phase 1 - One", "done": True},
                                       {"name": "Phase 2 - Two", "done": False}])
        self.assertEqual(p["current"], "Phase 2 - Two")
        self.assertFalse(p["complete"])

    def test_decisions_are_counted_under_their_heading_only(self):
        self.write_plan(TWO_PHASES + "\n## Decisions During Build\n- one\n- two\n\n## Notes\n- not a decision\n")
        self.run_for(1, 20)
        self.assertEqual(self.status()["projects"][0]["decisions"], 2)

    def test_quiet_flag_follows_last_activity(self):
        self.write_plan()
        old = time.time() - 30 * 60
        os.utime(self.repo / PLAN, (old, old))
        self.run_for(30, 60)
        self.assertTrue(self.status()["quiet"])
        self.write_plan()
        self.run_for(30, 60)
        self.assertFalse(self.status()["quiet"])

    def hide_caddis(self):
        """Ignore .caddis/ as a repo that keeps its projects private does."""
        with open(self.repo / ".git/info/exclude", "a") as f:
            f.write(".caddis/\n")

    def test_commit_on_a_builder_branch_counts_as_activity(self):
        self.hide_caddis()
        self.write_plan()
        old = time.time() - 30 * 60
        os.utime(self.repo / PLAN, (old, old))
        self.run_for(30, 60)
        self.assertTrue(self.status()["quiet"])
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        tree = subprocess.run(["git", "write-tree"], cwd=self.repo, env=env, check=True,
                              capture_output=True, text=True).stdout.strip()
        commit = subprocess.run(["git", "commit-tree", tree, "-m", "builder"], cwd=self.repo,
                                env=env, check=True, capture_output=True, text=True).stdout.strip()
        subprocess.run(["git", "update-ref", "refs/heads/caddis/x", commit], cwd=self.repo, check=True)
        self.run_for(30, 60)
        self.assertFalse(self.status()["quiet"])

    def test_touched_project_file_counts_when_caddis_is_ignored(self):
        self.hide_caddis()
        self.write_plan()
        old = time.time() - 30 * 60
        os.utime(self.repo / PLAN, (old, old))
        self.run_for(30, 60)
        self.assertTrue(self.status()["quiet"])
        os.utime(self.repo / PLAN, None)
        self.run_for(30, 60)
        self.assertFalse(self.status()["quiet"])

    def test_done_after_the_last_project_moves(self):
        self.write_plan()
        self.run_for(1, 20)
        shutil.move(self.repo / PLAN, self.repo / ".caddis/projects/completed/project-demo.md")
        out, code = self.run_for(1, 20)
        self.assertEqual(code, 0)
        s = self.status()
        self.assertTrue(s["done"])
        self.assertEqual((s["phases_done"], s["phases_total"]), (2, 2))
        self.assertTrue(s["projects"][0]["complete"])
        self.assertTrue(all(ph["done"] for ph in s["projects"][0]["phases"]))

    def test_phase_name_with_a_quote_and_a_tab_stays_valid_json(self):
        self.write_plan('### Phase 1 - Say "hi"\\now\tthen\n')
        self.run_for(1, 20)
        p = self.status()["projects"][0]
        self.assertEqual(p["phases"][0]["name"], 'Phase 1 - Say "hi"\\nowthen')
        self.assertEqual(p["current"], 'Phase 1 - Say "hi"\\nowthen')


    def test_activity_counts_changes_outside_caddis_in_this_checkout(self):
        self.write_plan()
        (self.repo / "app.py").write_text("x = 1\n")
        (self.repo / "lib.py").write_text("y = 2\n")
        self.run_for(5, 20)
        a = self.status()["projects"][0]["activity"]
        self.assertEqual(a["changed"], 2)
        self.assertGreaterEqual(a["last_edit"], int(time.time()) - 10)

    def test_activity_before_any_edit_has_no_last_edit(self):
        self.write_plan()
        old = time.time() - 30 * 60
        os.utime(self.repo / PLAN, (old, old))
        self.run_for(5, 20)
        self.assertEqual(self.status()["projects"][0]["activity"], {"changed": 0, "last_edit": None})

    def test_activity_reads_the_builders_worktree(self):
        self.write_plan()
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        (self.repo / "app.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "-A"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=self.repo, env=env, check=True)
        wt = Path(tempfile.mkdtemp()) / "wt"
        self.addCleanup(shutil.rmtree, wt.parent)
        subprocess.run(["git", "worktree", "add", "-q", "-b", "caddis/demo", str(wt)],
                       cwd=self.repo, check=True)
        (wt / "app.py").write_text("x = 2\n")
        (wt / "new.py").write_text("z = 3\n")
        (self.repo / "other.py").write_text("not the builder's\n")
        self.run_for(5, 20)
        self.assertEqual(self.status()["projects"][0]["activity"]["changed"], 2)

    def test_agent_worktrees_inside_the_checkout_are_not_edits(self):
        self.write_plan()
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "base"], cwd=self.repo,
                       env=env, check=True)
        subprocess.run(["git", "worktree", "add", "-q", "-b", "worktree-agent-x",
                        ".claude/worktrees/agent-x"], cwd=self.repo, check=True)
        self.run_for(5, 20)
        self.assertEqual(self.status()["projects"][0]["activity"]["changed"], 0)

    def test_complete_project_has_no_activity(self):
        self.write_plan()
        shutil.move(self.repo / PLAN, self.repo / ".caddis/projects/completed/project-demo.md")
        self.run_for(1, 20)
        self.assertIsNone(self.status()["projects"][0]["activity"])


if __name__ == "__main__":
    unittest.main()
