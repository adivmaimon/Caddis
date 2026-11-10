"""Tests for the update notice in the session-start hook (plugin/hooks/session-start.sh)."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugin/hooks/session-start.sh"
PLUGIN = ROOT / "plugin"


class SessionStartTest(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo)
        self.version = subprocess.run(
            ["sed", "-n", r's/.*"version": "\(.*\)".*/\1/p', str(PLUGIN / ".claude-plugin/plugin.json")],
            capture_output=True, text=True, check=True).stdout.strip()

    def run_hook(self, first_line=None):
        if first_line is not None:
            (self.repo / ".caddis").mkdir()
            (self.repo / ".caddis/caddis.md").write_text(first_line + "\n# Caddis config\n")
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.repo), CLAUDE_PLUGIN_ROOT=str(PLUGIN))
        r = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True,
                           stdin=subprocess.DEVNULL)
        self.assertEqual(r.returncode, 0)
        return r.stdout

    def test_silent_without_caddis(self):
        self.assertEqual(self.run_hook(), "")

    def test_current_config_is_silent(self):
        self.assertEqual(self.run_hook(f"<!-- caddis-config: {self.version} -->"), "")

    def test_newer_config_is_silent(self):
        self.assertEqual(self.run_hook("<!-- caddis-config: 99.0.0 -->"), "")

    def test_older_config_gets_one_notice(self):
        out = self.run_hook("<!-- caddis-config: 0.1.0 -->")
        self.assertIn(f"Caddis was updated to {self.version}", out)
        self.assertIn("/caddis:config", out)

    def test_config_without_marker_counts_as_older(self):
        self.assertIn("/caddis:config", self.run_hook("# Caddis config"))

    def test_versions_compare_as_numbers(self):
        # 0.10.0 is newer than 0.6.0, though it sorts lower as text.
        self.assertEqual(self.run_hook("<!-- caddis-config: 0.10.0 -->"), "")


if __name__ == "__main__":
    unittest.main()
