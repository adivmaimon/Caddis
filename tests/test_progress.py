"""Tests for the build progress reporter (plugin/skills/build/scripts/progress.sh)."""

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


class ProgressTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
