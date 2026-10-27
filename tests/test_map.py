"""Tests for skills/map/scripts/map.py. Run: python3 -m unittest discover tests

Each test builds a tiny repo in a temp dir with a known right answer and checks the graph.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

MAP = os.path.join(os.path.dirname(__file__), "..", "skills", "map", "scripts", "map.py")


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


if __name__ == "__main__":
    unittest.main()
