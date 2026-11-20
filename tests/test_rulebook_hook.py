"""Tests for the rulebook hook (plugin/hooks/rulebook.sh)."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugin/hooks/rulebook.sh"

RULEBOOK = """# Rulebook

> Intro.

## CSS

1. No `<style>` blocks in "Vue" files. (owner, 2026-11-20)
<!-- a comment -->

## Retired

- 2. Old rule - dropped (owner, 2026-11-01)
"""

CONFIG = """<!-- caddis-config: 0.9.0 -->
# Caddis config

## Invariants

<!-- Rules that hold on every code path,
no exceptions. -->

1. Nothing leaves the device without consent.

## Risk

- Payments
"""


class RulebookHookTest(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo)

    def write(self, name, text):
        (self.repo / ".caddis").mkdir(exist_ok=True)
        (self.repo / ".caddis" / name).write_text(text)

    def run_hook(self, mode="session"):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.repo))
        r = subprocess.run(["bash", str(SCRIPT), mode], env=env, capture_output=True,
                           text=True, stdin=subprocess.DEVNULL)
        self.assertEqual(r.returncode, 0)
        return r.stdout

    def test_silent_without_caddis(self):
        self.assertEqual(self.run_hook(), "")
        self.assertEqual(self.run_hook("subagent"), "")

    def test_silent_with_empty_invariants_and_no_rulebook(self):
        self.write("caddis.md", "# Caddis config\n\n## Invariants\n\n<!-- none yet -->\n\n## Risk\n")
        self.assertEqual(self.run_hook(), "")

    def test_session_prints_rules_without_retired(self):
        self.write("rulebook.md", RULEBOOK)
        out = self.run_hook()
        self.assertIn("No `<style>` blocks", out)
        self.assertIn("update .caddis/rulebook.md in the same turn", out)
        self.assertNotIn("Old rule", out)
        self.assertNotIn("a comment", out)

    def test_invariants_section_only(self):
        self.write("caddis.md", CONFIG)
        out = self.run_hook()
        self.assertIn("Nothing leaves the device", out)
        self.assertNotIn("Payments", out)
        self.assertNotIn("no exceptions", out)

    def test_subagent_output_is_valid_json(self):
        self.write("rulebook.md", RULEBOOK.replace("files.", "files.\t\\ end"))
        self.write("caddis.md", CONFIG)
        data = json.loads(self.run_hook("subagent"))
        out = data["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "SubagentStart")
        self.assertIn('"Vue" files', out["additionalContext"])
        self.assertIn("\t\\ end", out["additionalContext"])
        self.assertIn("Nothing leaves the device", out["additionalContext"])


if __name__ == "__main__":
    unittest.main()
