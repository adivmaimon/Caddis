"""Tests for skills/map/scripts/map.py. Run: python3 -m unittest discover tests

Each test builds a tiny repo in a temp dir with a known right answer and checks the graph.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

MAP = os.path.join(os.path.dirname(__file__), "..", "plugin", "skills", "map", "scripts", "map.py")


def sh(cwd, *args):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True).stdout


class Repo:
    def __init__(self, files, git=True):
        self.dir = tempfile.mkdtemp()
        for path, text in files.items():
            full = os.path.join(self.dir, path)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w") as fh:
                fh.write(text)
        if git:
            sh(self.dir, "git", "init", "-q")
            sh(self.dir, "git", "config", "user.email", "t@t")
            sh(self.dir, "git", "config", "user.name", "t")
            self.commit("init")

    def commit(self, msg):
        sh(self.dir, "git", "add", "-A")
        sh(self.dir, "git", "commit", "-qm", msg)

    def map(self, *args):
        return sh(self.dir, sys.executable, MAP, *args)

    def graph(self):
        self.map("build")
        with open(os.path.join(self.dir, ".caddis", "map", "graph.json")) as fh:
            return json.load(fh)["files"]

    def write(self, path, text):
        full = os.path.join(self.dir, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as fh:
            fh.write(text)


class JsTests(unittest.TestCase):
    def test_relative_alias_and_packages(self):
        r = Repo({
            "tsconfig.json": '{ // comment\n "compilerOptions": {"baseUrl": ".", "paths": {"@lib/*": ["src/lib/*"]},},}',
            "src/index.ts": "import a from './a'\nimport { b } from '@lib/b'\nimport fs from 'node:fs'\nimport React from 'react'\nconst c = require('./c.js')\n",
            "src/a/index.tsx": "export default 1\n",
            "src/lib/b.ts": "export const b = 1\n",
            "src/c.ts": "module.exports = 1\n",
        })
        g = r.graph()
        self.assertEqual(g["src/index.ts"]["imports"], ["src/a/index.tsx", "src/c.ts", "src/lib/b.ts"])
        self.assertEqual(g["src/index.ts"]["packages"], ["react", "std:fs"])

    def test_platform_files_and_type_declarations(self):
        r = Repo({
            "app/screen.tsx": "import Btn from './Button'\nimport { T } from './types'\n",
            "app/Button.ios.tsx": "export default 1\n",
            "app/types.d.ts": "export type T = 1\n",
        })
        self.assertEqual(r.graph()["app/screen.tsx"]["imports"], ["app/Button.ios.tsx", "app/types.d.ts"])

    def test_commented_import_is_ignored(self):
        r = Repo({"a.ts": "// import x from './b'\n/* import y from './b' */\n", "b.ts": ""})
        self.assertEqual(r.graph()["a.ts"]["imports"], [])


class PythonTests(unittest.TestCase):
    def test_absolute_relative_and_stdlib(self):
        r = Repo({
            "pyproject.toml": "",
            "pkg/__init__.py": "",
            "pkg/main.py": "import os\nfrom pkg.sub import util\nfrom . import helper\nfrom .sub.util import thing\nimport numpy as np\n",
            "pkg/helper.py": "",
            "pkg/sub/__init__.py": "",
            "pkg/sub/util.py": "thing = 1\n",
        })
        n = r.graph()["pkg/main.py"]
        self.assertEqual(n["imports"], ["pkg/helper.py", "pkg/sub/util.py"])
        self.assertEqual(n["packages"], ["numpy", "std:os"])


class OtherLanguageTests(unittest.TestCase):
    def test_go_module_imports(self):
        r = Repo({
            "go.mod": "module example.com/app\n",
            "main.go": 'package main\nimport (\n  "fmt"\n  "example.com/app/store"\n)\n',
            "store/store.go": "package store\n",
            "store/store_test.go": "package store\n",
        })
        n = r.graph()["main.go"]
        self.assertEqual(n["imports"], ["store/store.go"])

    def test_rust_mod_and_crate_use(self):
        r = Repo({
            "Cargo.toml": "",
            "src/main.rs": "mod db;\nuse crate::db::conn;\nuse super::*;\n",
            "src/db/mod.rs": "pub mod conn;\n",
            "src/db/conn.rs": "",
        })
        g = r.graph()
        self.assertEqual(g["src/main.rs"]["imports"], ["src/db/conn.rs", "src/db/mod.rs"])
        self.assertEqual(g["src/db/mod.rs"]["imports"], ["src/db/conn.rs"])

    def test_php_psr4(self):
        r = Repo({
            "composer.json": '{"autoload": {"psr-4": {"App\\\\": "app/"}}}',
            "app/Http/Controller.php": "<?php\nuse App\\Models\\User;\nuse Illuminate\\Support\\Str;\n",
            "app/Models/User.php": "<?php\n",
        })
        n = r.graph()["app/Http/Controller.php"]
        self.assertEqual(n["imports"], ["app/Models/User.php"])
        self.assertEqual(n["packages"], ["Illuminate"])

    def test_scss_partials(self):
        r = Repo({"styles/main.scss": "@use 'tokens';\n@import './mixins';\n", "styles/_tokens.scss": "", "styles/_mixins.scss": ""})
        self.assertEqual(r.graph()["styles/main.scss"]["imports"], ["styles/_mixins.scss", "styles/_tokens.scss"])


class StatusTests(unittest.TestCase):
    def test_stamp_fresh_then_stale(self):
        r = Repo({"src/a.ts": "import b from './b'\n", "src/b.ts": ""})
        self.assertIn("No STRUCTURE.md", r.map("status"))
        r.write(".caddis/map/STRUCTURE.md", r.map("stamp") + "# Structure\n")
        r.commit("map")
        self.assertIn("fresh", r.map("status"))
        self.assertEqual(r.map("status", "--hook"), "")
        r.write("src/c.ts", "import a from './a'\n")
        r.commit("add c")
        out = r.map("status")
        self.assertIn("1 commit(s) behind", out)
        self.assertIn("+ src/c.ts", out)
        self.assertIn("caddis map skill", r.map("status", "--hook"))

    def test_map_committed_with_the_work_it_describes_is_fresh(self):
        r = Repo({"src/a.ts": ""})
        r.write(".caddis/map/STRUCTURE.md", r.map("stamp") + "# Structure\n")
        r.write("src/b.ts", "import a from './a'\n")
        r.commit("work and map together")
        self.assertIn("fresh", r.map("status"))
        r.write("src/c.ts", "")
        r.commit("later work")
        self.assertIn("1 commit(s) behind", r.map("status"))

    def test_queries_rebuild_when_tree_moves(self):
        r = Repo({"a.ts": "", "b.ts": "import a from './a'\n"})
        self.assertIn("used by 1", r.map("uses", "a.ts"))
        r.write("c.ts", "import a from './a'\n")
        r.commit("c")
        self.assertIn("used by 2", r.map("uses", "a.ts"))

    def test_cache_is_gitignored(self):
        r = Repo({"a.ts": ""})
        r.map("build")
        with open(os.path.join(r.dir, ".caddis", "map", ".gitignore")) as fh:
            self.assertIn("graph.json", fh.read())


class ReachTests(unittest.TestCase):
    # src/core.ts is a hub (4 importers) on the way to the target; src/d.ts imports the target
    # directly and no test reaches it.
    FILES = {
        "src/t.ts": "export const t = 1\n",
        "src/core.ts": "import { t } from './t'\n",
        "src/d.ts": "import { t } from './t'\n",
        "src/a.ts": "import c from './core'\n",
        "src/b.ts": "import c from './core'\n",
        "lib/c.ts": "import c from '../src/core'\n",
        "app/main.ts": "import a from '../src/a'\n",
        "tests/core.test.ts": "import c from '../src/core'\n",
    }

    def reach(self, *paths):
        return json.loads(Repo(self.FILES).map("reach", *paths, "--json"))

    def test_direct_hubs_areas_and_untested(self):
        r = self.reach("src/t.ts")
        self.assertEqual(r["targets"], ["src/t.ts"])
        self.assertEqual(r["direct"], ["src/core.ts", "src/d.ts"])
        self.assertEqual(r["hubs"], [{"file": "src/core.ts", "importers": 4, "target": False}])
        self.assertEqual(len(r["reach"]), 7)
        self.assertEqual(r["via_hubs"], 5)
        areas = {a["area"]: (a["files"], a["via_hubs"]) for a in r["by_area"]}
        self.assertEqual(areas, {"src": (4, 2), "lib": (1, 1), "app": (1, 1), "tests": (1, 1)})
        self.assertEqual(r["untested"], ["src/d.ts"])

    def test_target_hub_is_listed_but_not_counted_as_via(self):
        r = self.reach("src/core.ts")
        self.assertEqual(r["hubs"], [{"file": "src/core.ts", "importers": 4, "target": True}])
        self.assertEqual(r["via_hubs"], 0)
        self.assertEqual(sorted(r["reach"]), ["app/main.ts", "lib/c.ts", "src/a.ts", "src/b.ts", "tests/core.test.ts"])

    def test_json_shape(self):
        r = self.reach("src/t.ts")
        self.assertEqual(sorted(r), ["by_area", "direct", "hubs", "reach", "targets", "unknown", "untested", "via_hubs"])

    def test_unknown_path_is_reported_not_fatal(self):
        r = Repo(self.FILES)
        out = r.map("reach", "src/t.ts", "nope.ts")
        self.assertIn("Skipped: 'nope.ts' is not in the map", out)
        self.assertIn("Direct importers: 2", out)
        self.assertIn("Direct importers no test reaches: 1", out)
        bad = subprocess.run([sys.executable, MAP, "reach", "nope.ts"], cwd=r.dir, capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)


class OrphansTests(unittest.TestCase):
    # main.py is an entry point, lonely.py imports nothing, stray.py imports used.py.
    FILES = {
        "src/main.py": "import os\n",
        "src/lonely.py": "X = 1\n",
        "src/used.py": "Y = 2\n",
        "src/stray.py": "from src import used\n",
    }
    TEXT = (
        "3 source files that nothing imports (tests excluded). Entry points, config, or dead code:\n"
        "  src/lonely.py  leaf\n"
        "  src/main.py  entry?\n"
        "  src/stray.py  \n"
    )

    def test_text_output_is_unchanged(self):
        self.assertEqual(Repo(self.FILES).map("orphans"), self.TEXT)


if __name__ == "__main__":
    unittest.main()
