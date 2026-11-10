"""Runs the build panel mod's render tests (tests/panel/) with `claude plugin test`.

The plugin directory scans every file in plugin/, so the test file lives here. This copies
plugin/ and the test to a temp folder and runs the tests there. Skipped when the `claude`
CLI isn't installed.
"""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = shutil.which("claude")


@unittest.skipUnless(CLAUDE, "the claude CLI is not installed")
class PanelTest(unittest.TestCase):
    def test_panel_render_tests_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod = Path(tmp) / "caddis"
            shutil.copytree(ROOT / "plugin", mod, ignore=shutil.ignore_patterns(".DS_Store"))
            shutil.copytree(ROOT / "tests/panel", mod / "tests")
            run = subprocess.run([CLAUDE, "plugin", "test", str(mod)], capture_output=True,
                                 text=True, timeout=300)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
