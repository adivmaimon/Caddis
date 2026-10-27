#!/usr/bin/env python3
"""Caddis codebase map: a deterministic file-level import graph.

Reads source files, extracts imports with per-language rules, resolves them to files
in the repo, and writes:
  .caddis/map/graph.json  every source file, its lines, internal imports and packages
  .caddis/map/summary.md  areas, hubs, entry points, cross-area edges, packages

Claude writes .caddis/map/STRUCTURE.md on top of summary.md. This script never guesses
an edge: an import it cannot resolve is counted as unresolved, not invented.

Commands:
  build              write graph.json and summary.md, stamped with the current commit
  status [--hook]    is the map stale? which areas changed since it was built
  uses <path>        what imports this file (add --depth N for transitive)
  deps <path>        what this file imports
  area <dir>         files in an area with their in and out degree
  orphans            source files nothing imports (entry points or dead code)
  stamp              the commit stamp line to put at the top of STRUCTURE.md

graph.json and summary.md are a cache: queries rebuild them when the tree has moved on.
STRUCTURE.md is committed, and `status` measures staleness against its stamp.

Standard library only, Python 3.8+.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

VERSION = "0.1.2"

# Directories never mapped, even when tracked by git.
ALWAYS_SKIP = {
    ".git", ".caddis", ".claude", "node_modules", "bower_components", "Pods", "DerivedData",
    "__pycache__", ".venv", "venv", ".tox", "site-packages", ".next", ".nuxt", ".svelte-kit",
    ".expo", ".turbo",
}
# Also skipped when there is no git, so no .gitignore to trust.
SKIP_DIRS = ALWAYS_SKIP | {
    "dist", "build", "out", ".cache", "coverage", "vendor", "target", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".gradle", ".idea", ".vscode",
}
MAX_BYTES = 512 * 1024

LANG = {}
for _ext, _lang in [
    ("js jsx mjs cjs ts tsx mts cts vue svelte astro", "js"),
    ("py", "py"), ("go", "go"), ("rs", "rs"), ("php", "php"), ("rb", "rb"),
    ("java kt kts scala", "jvm"), ("swift", "swift"), ("cs", "cs"), ("dart", "dart"),
    ("c h cc cpp cxx hpp hh m mm", "c"), ("css scss sass less", "css"),
]:
    for e in _ext.split():
        LANG["." + e] = _lang

JS_EXTS = [".ts", ".tsx", ".d.ts", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts", ".vue", ".svelte", ".astro", ".json"]
# React Native and Expo resolve platform files first: Button.ios.tsx before Button.tsx.
JS_PLATFORMS = ["", ".native", ".ios", ".android", ".web"]
ENTRY_NAMES = re.compile(
    r"(^|/)(main|index|app|server|cli|cmd|manage|wsgi|asgi|__main__|lib|mod|_layout|layout|page|"
    r"route|routes|router|worker|handler|setup|conftest)\.[a-z]+$|(^|/)(bin|scripts?|cmd|pages|app|routes)/",
    re.I,
)
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|specs|e2e|fixtures?)/|[._-](test|spec)\.[a-z]+$|^test_|/test_", re.I)

# Standard libraries, tagged "std:" so the package list shows real dependencies.
PY_STD = set(getattr(sys, "stdlib_module_names", ())) or set(
    "abc argparse array ast asyncio base64 bisect builtins calendar collections concurrent "
    "contextlib copy csv ctypes dataclasses datetime decimal difflib email enum errno "
    "fnmatch fractions functools gc getpass glob gzip hashlib heapq hmac html http "
    "importlib inspect io ipaddress itertools json logging lzma math mimetypes "
    "multiprocessing operator os pathlib pickle platform pprint queue random re secrets "
    "select shlex shutil signal socket sqlite3 ssl stat statistics string struct "
    "subprocess sys tarfile tempfile textwrap threading time timeit traceback types "
    "typing unicodedata unittest urllib uuid warnings weakref xml zipfile zlib __future__".split()
)
NODE_STD = set(
    "assert async_hooks buffer child_process cluster console crypto dgram dns events fs "
    "http http2 https inspector module net os path perf_hooks process querystring readline "
    "repl stream string_decoder test timers tls tty url util v8 vm worker_threads zlib".split()
)


def run(cmd, cwd):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def is_git(root):
    return run(["git", "rev-parse", "--is-inside-work-tree"], root).strip() == "true"


def head_commit(root):
    return run(["git", "rev-parse", "--short", "HEAD"], root).strip() or None


def skipped(rel, skip=ALWAYS_SKIP):
    parts = rel.split("/")
    return any(p in skip for p in parts[:-1])


def list_files(root):
    if is_git(root):
        out = run(["git", "ls-files", "-co", "--exclude-standard", "-z"], root)
        files = [f for f in out.split("\0") if f and not skipped(f)]
    else:
        files = []
        for d, dirs, names in os.walk(root):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
            for n in names:
                files.append(os.path.relpath(os.path.join(d, n), root).replace(os.sep, "/"))
    return sorted(f for f in files if not skipped(f, SKIP_DIRS if not is_git(root) else ALWAYS_SKIP)
                  and os.path.isfile(os.path.join(root, f)))


def read(root, rel):
    try:
        with open(os.path.join(root, rel), "rb") as fh:
            data = fh.read(MAX_BYTES + 1)
    except OSError:
        return None
    if b"\0" in data[:4096]:
        return None
    return data[:MAX_BYTES].decode("utf-8", "replace")


def strip_json_comments(text):
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
            out.append(c)
        elif text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        else:
            out.append(c)
        i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def load_json(root, rel):
    text = read(root, rel)
    if text is None:
        return None
    try:
        return json.loads(strip_json_comments(text))
    except ValueError:
        return None


def norm(path):
    path = os.path.normpath(path).replace(os.sep, "/")
    return "" if path == "." else path


class Resolver:
    def __init__(self, root, files):
        self.root = root
        self.files = files
        self.fileset = set(files)
        self.dirs = defaultdict(list)
        for f in files:
            self.dirs[os.path.dirname(f)].append(f)
        self._js_configs()
        self._py_roots()
        self._go_mods()
        self._php_psr4()
        self._suffix_index()
        self._dart()

    # ---- helpers
    def nearest(self, rel, marker_dirs):
        d = os.path.dirname(rel)
        while True:
            if d in marker_dirs:
                return d
            if not d:
                return None
            d = os.path.dirname(d)

    def first_existing(self, cands):
        for c in cands:
            c = norm(c)
            if c in self.fileset:
                return c
        return None

    # ---- JS / TS
    def _js_configs(self):
        self.pkg_dirs = {os.path.dirname(f) for f in self.files if os.path.basename(f) == "package.json"}
        self.ts_paths = {}
        for f in self.files:
            if re.search(r"(^|/)(tsconfig|jsconfig)[\w.]*\.json$", f):
                cfg = load_json(self.root, f) or {}
                opts = cfg.get("compilerOptions") or {}
                ext = cfg.get("extends")
                if not opts.get("paths") and isinstance(ext, str) and ext.startswith("."):
                    parent = norm(os.path.join(os.path.dirname(f), ext))
                    if not parent.endswith(".json"):
                        parent += ".json"
                    popts = (load_json(self.root, parent) or {}).get("compilerOptions") or {}
                    if popts.get("paths"):
                        opts = dict(popts, **{k: v for k, v in opts.items() if k != "paths"})
                        base_dir = os.path.dirname(parent)
                    else:
                        base_dir = os.path.dirname(f)
                else:
                    base_dir = os.path.dirname(f)
                paths = opts.get("paths") or {}
                base = norm(os.path.join(base_dir, opts.get("baseUrl", ".")))
                d = os.path.dirname(f)
                if paths and d not in self.ts_paths:
                    self.ts_paths[d] = (base, paths)

    def js_candidates(self, base):
        cands = [base] + [base + p + e for p in JS_PLATFORMS for e in JS_EXTS]
        cands += [base + "/index" + p + e for p in JS_PLATFORMS for e in JS_EXTS]
        m = re.match(r"(.*)\.(m?js|cjs|jsx)$", base)
        if m:
            cands += [m.group(1) + e for e in (".ts", ".tsx", ".mts", ".cts")]
        return cands

    def resolve_js(self, rel, spec):
        spec = spec.split("?")[0]
        if spec.startswith("."):
            hit = self.first_existing(self.js_candidates(os.path.join(os.path.dirname(rel), spec)))
            return ("file", hit) if hit else ("unresolved", spec)
        cfg_dir = self.nearest(rel, set(self.ts_paths))
        if cfg_dir is not None:
            base, paths = self.ts_paths[cfg_dir]
            for pattern, targets in paths.items():
                pre, star, post = pattern.partition("*")
                if star and spec.startswith(pre) and spec.endswith(post) and len(spec) >= len(pre) + len(post):
                    mid = spec[len(pre): len(spec) - len(post)] if post else spec[len(pre):]
                elif not star and spec == pattern:
                    mid = ""
                else:
                    continue
                for t in targets:
                    hit = self.first_existing(self.js_candidates(os.path.join(base, t.replace("*", mid))))
                    if hit:
                        return ("file", hit)
        if spec[:2] in ("@/", "~/") or spec.startswith("~~/"):
            pkg = self.nearest(rel, self.pkg_dirs) or ""
            tail = spec.split("/", 1)[1]
            for b in ("src", "app", ""):
                hit = self.first_existing(self.js_candidates(os.path.join(pkg, b, tail)))
                if hit:
                    return ("file", hit)
            return ("unresolved", spec)
        if spec.startswith("/"):
            return ("unresolved", spec)
        parts = spec.split("/")
        name = "/".join(parts[:2]) if spec.startswith("@") and len(parts) > 1 else parts[0]
        if name.startswith("node:") or name in NODE_STD:
            return ("pkg", "std:" + name.replace("node:", ""))
        return ("pkg", name)

    # ---- Python
    def _py_roots(self):
        markers = {"pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "manage.py"}
        roots = {""}
        init_dirs = {os.path.dirname(f) for f in self.files if f.endswith("/__init__.py") or f == "__init__.py"}
        for f in self.files:
            b, d = os.path.basename(f), os.path.dirname(f)
            if b in markers:
                roots.add(d)
            if os.path.basename(d) == "src":
                roots.add(d)
        for d in init_dirs:
            parent = os.path.dirname(d)
            if parent not in init_dirs:
                roots.add(parent)
        self.py_roots = sorted(roots, key=lambda r: -len(r))

    def py_module(self, base, dotted):
        p = os.path.join(base, *dotted.split(".")) if dotted else base
        return self.first_existing([p + ".py", os.path.join(p, "__init__.py")])

    def resolve_py(self, rel, mod, names):
        out = []
        if mod.startswith("."):
            level = len(mod) - len(mod.lstrip("."))
            base = os.path.dirname(rel)
            for _ in range(level - 1):
                base = os.path.dirname(base)
            rest = mod.lstrip(".")
            for n in names or [None]:
                hit = self.py_module(base, ".".join(x for x in (rest, n) if x)) if n else None
                hit = hit or self.py_module(base, rest)
                out.append(("file", hit) if hit else ("unresolved", mod))
            return out
        here = os.path.dirname(rel)
        anc = [r for r in self.py_roots if r == "" or here == r or here.startswith(r + "/")]
        order = [here] + anc + [r for r in self.py_roots if r not in anc]
        for root in order:
            for n in names or [None]:
                hit = (self.py_module(root, mod + "." + n) if n else None) or self.py_module(root, mod)
                if hit and hit != rel:
                    out.append(("file", hit))
            if out:
                return out
        top = mod.split(".")[0]
        return [("pkg", ("std:" if top in PY_STD else "") + top)]

    # ---- Go
    def _go_mods(self):
        self.go_mods = []
        for f in self.files:
            if os.path.basename(f) == "go.mod":
                m = re.search(r"^module\s+(\S+)", read(self.root, f) or "", re.M)
                if m:
                    self.go_mods.append((m.group(1), os.path.dirname(f)))

    def resolve_go(self, spec):
        for mod, d in self.go_mods:
            if spec == mod or spec.startswith(mod + "/"):
                pdir = norm(os.path.join(d, spec[len(mod) + 1:]) if spec != mod else d)
                hits = [f for f in self.dirs.get(pdir, []) if f.endswith(".go") and not f.endswith("_test.go")]
                return [("file", h) for h in hits[:20]] or [("unresolved", spec)]
        return [("pkg", spec if "." in spec.split("/")[0] else "std:" + spec.split("/")[0])]

    # ---- Rust
    def crate_src(self, rel):
        d = os.path.dirname(rel)
        while True:
            if os.path.join(d, "Cargo.toml").lstrip("/") in self.fileset or (not d and "Cargo.toml" in self.fileset):
                return norm(os.path.join(d, "src"))
            if not d:
                return None
            d = os.path.dirname(d)

    def rs_mod_dir(self, rel):
        b = os.path.basename(rel)
        return os.path.dirname(rel) if b in ("mod.rs", "lib.rs", "main.rs") else rel[:-3]

    def rs_path(self, base, segs):
        for k in range(len(segs), 0, -1):
            p = os.path.join(base, *segs[:k])
            hit = self.first_existing([p + ".rs", os.path.join(p, "mod.rs")])
            if hit:
                return hit
        return None

    def resolve_rs_mod(self, rel, name):
        d = self.rs_mod_dir(rel)
        hit = self.first_existing([os.path.join(d, name + ".rs"), os.path.join(d, name, "mod.rs")])
        return ("file", hit) if hit else ("unresolved", "mod " + name)

    def resolve_rs_use(self, rel, path):
        segs = [s for s in re.split(r"::", path) if s and s != "{" and re.match(r"^\w+$", s)]
        if not segs:
            return None
        head = segs[0]
        if head == "crate":
            src = self.crate_src(rel)
            hit = self.rs_path(src, segs[1:]) if src is not None and len(segs) > 1 else None
            return ("file", hit) if hit else ("unresolved", path)
        if head in ("self", "super"):
            base = self.rs_mod_dir(rel)
            rest = segs[1:]
            if head == "super":
                base = os.path.dirname(base)
                while rest and rest[0] == "super":
                    base, rest = os.path.dirname(base), rest[1:]
            if not rest:  # `use super::*` names the parent module, already linked by `mod`
                return None
            hit = self.rs_path(base, rest)
            return ("file", hit) if hit else ("unresolved", path)
        if head in ("std", "core", "alloc"):
            return ("pkg", "std:" + head)
        return ("pkg", head)

    # ---- PHP
    def _php_psr4(self):
        self.psr4 = []
        for f in self.files:
            if os.path.basename(f) == "composer.json":
                cfg = load_json(self.root, f) or {}
                for sect in ("autoload", "autoload-dev"):
                    for ns, dirs in ((cfg.get(sect) or {}).get("psr-4") or {}).items():
                        for d in dirs if isinstance(dirs, list) else [dirs]:
                            self.psr4.append((ns, norm(os.path.join(os.path.dirname(f), d))))
        self.psr4.sort(key=lambda x: -len(x[0]))

    def resolve_php_use(self, cls):
        cls = cls.lstrip("\\")
        for ns, d in self.psr4:
            if cls.startswith(ns):
                hit = self.first_existing([os.path.join(d, *cls[len(ns):].split("\\")) + ".php"])
                if hit:
                    return ("file", hit)
        hit = self.by_suffix("/".join(cls.split("\\")[-2:]), (".php",))
        if hit:
            return ("file", hit)
        return ("pkg", cls.split("\\")[0])

    # ---- suffix lookups (JVM, C, PHP fallback)
    def _suffix_index(self):
        self.by_stem = defaultdict(list)
        for f in self.files:
            self.by_stem[os.path.splitext(os.path.basename(f))[0]].append(f)

    def by_suffix(self, path, exts):
        stem = os.path.basename(path)
        hits = [f for f in self.by_stem.get(stem, []) if os.path.splitext(f)[1] in exts
                and os.path.splitext(f)[0].endswith(path)]
        return hits[0] if len(hits) == 1 else None

    # ---- Dart
    def _dart(self):
        self.dart_pkgs = {}
        for f in self.files:
            if os.path.basename(f) == "pubspec.yaml":
                m = re.search(r"^name:\s*(\S+)", read(self.root, f) or "", re.M)
                if m:
                    self.dart_pkgs[m.group(1)] = norm(os.path.join(os.path.dirname(f), "lib"))


RX = {
    "js_static": re.compile(r"""(?:^|[;\s])(?:import|export)\s+(?:type\s+)?(?:[^'";]*?\s+from\s+)?['"]([^'"\n]+)['"]""", re.M),
    "js_call": re.compile(r"""(?:\brequire|\bimport)\s*\(\s*['"]([^'"\n]+)['"]\s*\)"""),
    "py_import": re.compile(r"^[ \t]*import[ \t]+([\w.]+(?:[ \t]*,[ \t]*[\w.]+)*)", re.M),
    "py_from": re.compile(r"^[ \t]*from[ \t]+(\.*[\w.]*)[ \t]+import[ \t]+(\([^)]*\)|[^\n#]+)", re.M),
    "go_single": re.compile(r'^\s*import\s+(?:[\w.]+\s+)?"([^"]+)"', re.M),
    "go_block": re.compile(r"^\s*import\s*\((.*?)\)", re.M | re.S),
    "go_line": re.compile(r'"([^"]+)"'),
    "rs_mod": re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?mod\s+(\w+)\s*;", re.M),
    "rs_use": re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?use\s+([\w:]+)", re.M),
    "php_use": re.compile(r"^\s*use\s+([\w\\]+)(?:\s+as\s+\w+)?\s*;", re.M),
    "php_req": re.compile(r"""(?:require|include)(?:_once)?\s*\(?\s*(?:__DIR__\s*\.\s*)?['"]([^'"]+\.php)['"]"""),
    "rb_rel": re.compile(r"""^\s*require_relative\s+['"]([^'"]+)['"]""", re.M),
    "rb_req": re.compile(r"""^\s*require\s+['"]([^'"]+)['"]""", re.M),
    "jvm": re.compile(r"^\s*import\s+(?:static\s+)?([\w.]+)\s*;?\s*$", re.M),
    "c_inc": re.compile(r'^\s*#\s*(?:include|import)\s+"([^"]+)"', re.M),
    "css": re.compile(r"""@(?:import|use|forward)\s+(?:url\()?['"]([^'"]+)['"]"""),
    "dart": re.compile(r"""^\s*(?:import|export|part)\s+['"]([^'"]+)['"]""", re.M),
    "swift": re.compile(r"^\s*(?:@testable\s+)?import\s+(\w+)", re.M),
}


def strip_comments_c(text):
    return re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)


def extract(r, rel, lang, text):
    """Return a list of (kind, value): kind is file, pkg or unresolved."""
    res = []
    if lang == "js":
        text = strip_comments_c(text)
        text = re.sub(r"^\s*//.*$", "", text, flags=re.M)
        specs = RX["js_static"].findall(text) + RX["js_call"].findall(text)
        res = [r.resolve_js(rel, s) for s in specs]
    elif lang == "py":
        for line in RX["py_import"].findall(text):
            for mod in re.split(r"\s*,\s*", line.strip()):
                res += r.resolve_py(rel, mod, None)
        for mod, names in RX["py_from"].findall(text):
            names = [n.split(" as ")[0].strip() for n in names.strip("() \t").replace("\n", " ").split(",")]
            names = [n for n in names if re.match(r"^\w+$", n)]
            res += r.resolve_py(rel, mod, names)
    elif lang == "go":
        specs = RX["go_single"].findall(text)
        for block in RX["go_block"].findall(text):
            specs += RX["go_line"].findall(block)
        for s in specs:
            res += r.resolve_go(s)
    elif lang == "rs":
        text = strip_comments_c(text)
        res = [r.resolve_rs_mod(rel, m) for m in RX["rs_mod"].findall(text)]
        res += [x for x in (r.resolve_rs_use(rel, u) for u in RX["rs_use"].findall(text)) if x]
    elif lang == "php":
        res = [r.resolve_php_use(c) for c in RX["php_use"].findall(text)]
        for s in RX["php_req"].findall(text):
            if "vendor/" in s:  # Composer's autoloader, not repo code
                res.append(("pkg", "composer"))
                continue
            here = os.path.dirname(rel)
            cands = [os.path.join(here, s.lstrip("/")), s.lstrip("/")]
            cands += [os.path.join(here, *[".."] * k, s.lstrip("/")) for k in range(1, 4)]
            hit = r.first_existing(cands)
            res.append(("file", hit) if hit else ("unresolved", s))
    elif lang == "rb":
        for s in RX["rb_rel"].findall(text):
            p = os.path.join(os.path.dirname(rel), s)
            hit = r.first_existing([p, p + ".rb"])
            res.append(("file", hit) if hit else ("unresolved", s))
        for s in RX["rb_req"].findall(text):
            hit = r.first_existing([os.path.join(d, s + ".rb") for d in ("lib", "app", "")])
            res.append(("file", hit) if hit else ("pkg", s.split("/")[0]))
    elif lang == "jvm":
        for imp in RX["jvm"].findall(text):
            if imp.endswith("*"):
                continue
            hit = r.by_suffix(imp.replace(".", "/"), (".java", ".kt", ".kts", ".scala"))
            res.append(("file", hit) if hit else ("pkg", ".".join(imp.split(".")[:2])))
    elif lang == "c":
        for s in RX["c_inc"].findall(text):
            hit = r.first_existing([os.path.join(os.path.dirname(rel), s)]) or r.by_suffix(os.path.splitext(s)[0], (os.path.splitext(s)[1],))
            res.append(("file", hit) if hit else ("unresolved", s))
    elif lang == "css":
        for s in RX["css"].findall(text):
            if s.startswith(("http:", "https:", "//")):
                continue
            if s.startswith(("sass:", "~")):
                res.append(("pkg", s.lstrip("~").split("/")[0]))
                continue
            base = os.path.join(os.path.dirname(rel), s)
            d, b = os.path.dirname(base), os.path.basename(base)
            cands = [base] + [os.path.join(d, p + b + e) for p in ("", "_") for e in (".scss", ".sass", ".css", ".less")]
            cands += [os.path.join(base, p + "index" + e) for p in ("", "_") for e in (".scss", ".css")]
            hit = r.first_existing(cands)
            if hit:
                res.append(("file", hit))
            elif s.startswith("."):
                res.append(("unresolved", s))
            else:  # Sass tries local files first, then load paths and packages
                res.append(("pkg", s.split("/")[0]))
    elif lang == "dart":
        for s in RX["dart"].findall(text):
            if s.startswith("dart:"):
                res.append(("pkg", s))
            elif s.startswith("package:"):
                pkg, _, rest = s[8:].partition("/")
                if pkg in r.dart_pkgs:
                    hit = r.first_existing([os.path.join(r.dart_pkgs[pkg], rest)])
                    res.append(("file", hit) if hit else ("unresolved", s))
                else:
                    res.append(("pkg", pkg))
            else:
                hit = r.first_existing([os.path.join(os.path.dirname(rel), s)])
                res.append(("file", hit) if hit else ("unresolved", s))
    elif lang == "swift":
        res = [("pkg", m) for m in RX["swift"].findall(text)]
    return res


# ---------------------------------------------------------------- areas

def compute_areas(files):
    """Group files into areas: top-level folders, split further where one folder dominates."""
    total = max(len(files), 1)

    def key(f, depth):
        parts = f.split("/")
        return "/".join(parts[:depth]) if len(parts) > depth else ("/".join(parts[:-1]) or "(root)")

    depth_of = {}

    def split(group, depth):
        buckets = defaultdict(list)
        for f in group:
            buckets[key(f, depth)].append(f)
        for k, fs in buckets.items():
            subdirs = {f.split("/")[depth] for f in fs if len(f.split("/")) > depth + 1}
            if depth < 6 and len(fs) > 0.3 * total and len(fs) > 40 and len(subdirs) >= 3:
                split(fs, depth + 1)
            else:
                for f in fs:
                    depth_of[f] = k

    split(files, 1)
    return depth_of


def area_of(path, areas):
    """Area for a path not in the graph (new file): longest known area prefix."""
    best = "(root)" if "/" not in path else path.split("/")[0]
    for a in areas:
        if a != "(root)" and (path == a or path.startswith(a + "/")) and len(a) > len(best):
            best = a
    return best


# ---------------------------------------------------------------- build

def build(root, out_dir, quiet=False):
    files = list_files(root)
    r = Resolver(root, files)
    graph, unresolved, other = {}, [], 0
    for rel in files:
        lang = LANG.get(os.path.splitext(rel)[1].lower())
        if not lang or rel.endswith((".min.js", ".min.css", ".map")):
            other += 1
            continue
        text = read(root, rel)
        if text is None:
            other += 1
            continue
        imports, pkgs = set(), set()
        for kind, val in extract(r, rel, lang, text):
            if kind == "file" and val and val != rel:
                imports.add(val)
            elif kind == "pkg":
                pkgs.add(val)
            elif kind == "unresolved":
                unresolved.append((rel, val))
        graph[rel] = {"lang": lang, "lines": text.count("\n") + 1, "imports": sorted(imports), "packages": sorted(pkgs)}

    # Edges to non-source files (e.g. a .json import) are dropped from the graph.
    for node in graph.values():
        node["imports"] = [i for i in node["imports"] if i in graph]

    areas = compute_areas(sorted(graph))
    for f, a in areas.items():
        graph[f]["area"] = a

    data = {
        "version": VERSION,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit": head_commit(root),
        "root": os.path.basename(os.path.abspath(root)),
        "other_files": other,
        "unresolved": len(unresolved),
        "files": graph,
    }
    os.makedirs(out_dir, exist_ok=True)
    ignore = os.path.join(out_dir, ".gitignore")
    if not os.path.exists(ignore):
        with open(ignore, "w") as fh:
            fh.write("# Regenerated by map.py on demand. STRUCTURE.md is the committed map.\ngraph.json\nsummary.md\n")
    with open(os.path.join(out_dir, "graph.json"), "w") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)
    with open(os.path.join(out_dir, "summary.md"), "w") as fh:
        fh.write(summary(data, unresolved))
    edges = sum(len(n["imports"]) for n in graph.values())
    if quiet:
        return data
    print(f"Mapped {len(graph)} source files, {edges} internal edges, {len(set(areas.values()))} areas, "
          f"{len(unresolved)} unresolved imports -> {norm(os.path.relpath(out_dir, root))}/")


def reverse(graph):
    rev = defaultdict(set)
    for f, n in graph.items():
        for i in n["imports"]:
            rev[i].add(f)
    return rev


def summary(data, unresolved):
    g = data["files"]
    rev = reverse(g)
    L = []
    w = L.append
    w(f"# Map summary: {data['root']}\n")
    w(f"Generated {data['generated']} at commit `{data['commit'] or 'none'}` by map.py {data['version']}. "
      "Machine-written; do not edit. `STRUCTURE.md` is the human map.\n")
    langs = Counter(n["lang"] for n in g.values())
    w(f"{len(g)} source files ({', '.join(f'{k} {v}' for k, v in langs.most_common())}), "
      f"{sum(n['lines'] for n in g.values())} lines, {data['other_files']} other files.\n")

    by_area = defaultdict(list)
    for f, n in g.items():
        by_area[n["area"]].append(f)
    cross = Counter()
    for f, n in g.items():
        for i in n["imports"]:
            if g[i]["area"] != n["area"]:
                cross[(n["area"], g[i]["area"])] += 1

    w("## Areas\n")
    w("| Area | Files | Lines | Languages | Uses areas | Used by areas |")
    w("| --- | --- | --- | --- | --- | --- |")
    for a in sorted(by_area, key=lambda a: (-len(by_area[a]), a)):
        fs = by_area[a]
        lg = Counter(g[f]["lang"] for f in fs)
        uses = sorted({b for (x, b) in cross if x == a})
        used = sorted({x for (x, b) in cross if b == a})
        w(f"| `{a}` | {len(fs)} | {sum(g[f]['lines'] for f in fs)} | {', '.join(k for k, _ in lg.most_common(3))} "
          f"| {', '.join(uses[:6]) + (' ...' if len(uses) > 6 else '') or '-'} "
          f"| {', '.join(used[:6]) + (' ...' if len(used) > 6 else '') or '-'} |")

    w("\n## Hubs (most imported)\n")
    w("Change these with care: `map.py uses <file>` shows everything that depends on them.\n")
    for f in sorted(rev, key=lambda f: (-len(rev[f]), f))[:20]:
        w(f"- `{f}`: imported by {len(rev[f])}")

    w("\n## Likely entry points\n")
    w("Not imported by anything in the repo, but import other files. Excludes tests.\n")
    entries = [f for f, n in g.items() if not rev.get(f) and n["imports"] and not TEST_PATH.search(f)]
    entries.sort(key=lambda f: (not ENTRY_NAMES.search(f), -len(g[f]["imports"]), f))
    for f in entries[:30]:
        w(f"- `{f}` ({len(g[f]['imports'])} imports)")
    if len(entries) > 30:
        w(f"- ...and {len(entries) - 30} more (`map.py orphans`)")

    w("\n## Cross-area dependencies\n")
    for (a, b), c in cross.most_common(25):
        w(f"- `{a}` -> `{b}`: {c}")
    if not cross:
        w("- none")

    w("\n## Packages (by files importing)\n")
    pk = Counter(p for n in g.values() for p in n["packages"] if not p.startswith("std:"))
    for p, c in pk.most_common(25):
        w(f"- `{p}`: {c}")
    if not pk:
        w("- none found")

    w("\n## Accuracy\n")
    w(f"{len(unresolved)} relative or aliased imports could not be resolved and are not in the graph.")
    if unresolved:
        w("Examples:")
        for f, s in unresolved[:10]:
            w(f"- `{f}` imports `{s}`")
    if langs.get("swift") or langs.get("cs"):
        w("\nSwift and C# files share modules without file-level imports, so they appear as nodes without edges.")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- queries

# graph.json and summary.md are a cache (gitignored). STRUCTURE.md is committed and carries
# the commit it describes in a `<!-- caddis-map commit: abc1234 -->` line; staleness is
# measured against that, because the human map is what Claude relies on.
STAMP = re.compile(r"caddis-map commit:\s*([0-9a-f]{4,40})")


def changed_since(root, commit):
    """Source files changed since commit, including uncommitted work. (changed, commits behind)."""
    if not is_git(root) or not commit:
        return set(), 0
    changed = {f for f in run(["git", "diff", "--name-only", commit, "--"], root).split("\n") if f}
    for line in run(["git", "status", "--porcelain", "--untracked-files=all"], root).split("\n"):
        if line:
            changed.add(line[3:].split(" -> ")[-1].strip('"'))
    # Commits that touched anything outside .caddis: committing STRUCTURE.md itself doesn't count.
    behind = len([x for x in run(["git", "rev-list", f"{commit}..HEAD", "--", ".", ":(exclude).caddis"], root).split("\n") if x])
    return {f for f in changed if LANG.get(os.path.splitext(f)[1].lower()) and not skipped(f)}, behind


def load(root, out_dir):
    """The graph, rebuilt first if missing or older than the working tree. Builds take seconds."""
    p = os.path.join(out_dir, "graph.json")
    data = None
    if os.path.exists(p):
        with open(p) as fh:
            data = json.load(fh)
        changed, behind = changed_since(root, data.get("commit"))
        built = os.path.getmtime(p)
        dirty = any(os.path.exists(os.path.join(root, f)) and os.path.getmtime(os.path.join(root, f)) > built
                    or not os.path.exists(os.path.join(root, f)) and f in data["files"] for f in changed)
        if behind or dirty or data.get("version") != VERSION:
            data = None
    return data or build(root, out_dir, quiet=True)


def structure_commit(out_dir):
    try:
        with open(os.path.join(out_dir, "STRUCTURE.md")) as fh:
            m = STAMP.search(fh.read(4000))
        return m.group(1) if m else None
    except OSError:
        return None


def find(g, path):
    path = norm(path)
    if path in g:
        return path
    hits = [f for f in g if f.endswith("/" + path)] or [f for f in g if f.endswith(path)]
    if len(hits) == 1:
        return hits[0]
    sys.exit(f"'{path}' {'matches ' + str(len(hits)) + ' files: ' + ', '.join(hits[:8]) if hits else 'is not in the map'}")


def cmd_uses(root, out_dir, path, depth):
    g = load(root, out_dir)["files"]
    f = find(g, path)
    rev = reverse(g)
    seen, frontier = {f: 0}, [f]
    for d in range(1, depth + 1):
        nxt = []
        for x in frontier:
            for y in sorted(rev.get(x, ())):
                if y not in seen:
                    seen[y] = d
                    nxt.append(y)
        frontier = nxt
    users = sorted((d, y) for y, d in seen.items() if d)
    print(f"{f}: used by {len(users)} file(s){' within depth ' + str(depth) if depth > 1 else ''}")
    for d, y in users:
        print(f"{'  ' * d}{y}  [{g[y]['area']}]")


def cmd_deps(root, out_dir, path):
    g = load(root, out_dir)["files"]
    f = find(g, path)
    print(f"{f} [{g[f]['area']}] imports {len(g[f]['imports'])} file(s)")
    for i in g[f]["imports"]:
        print(f"  {i}  [{g[i]['area']}]")
    if g[f]["packages"]:
        print("  packages: " + ", ".join(g[f]["packages"]))


def cmd_area(root, out_dir, area):
    g = load(root, out_dir)["files"]
    rev = reverse(g)
    area = norm(area)
    fs = sorted(f for f, n in g.items() if n["area"] == area or f.startswith(area + "/"))
    if not fs:
        sys.exit(f"No files in '{area}'. Areas: " + ", ".join(sorted({n['area'] for n in g.values()})))
    print(f"{area}: {len(fs)} files (in = imported by, out = imports)")
    for f in fs:
        print(f"  {f}  in {len(rev.get(f, ()))}  out {len(g[f]['imports'])}  {g[f]['lines']} lines")


def cmd_orphans(root, out_dir):
    g = load(root, out_dir)["files"]
    rev = reverse(g)
    orph = sorted(f for f in g if not rev.get(f) and not TEST_PATH.search(f))
    print(f"{len(orph)} source files that nothing imports (tests excluded). Entry points, config, or dead code:")
    for f in orph:
        tag = "entry?" if ENTRY_NAMES.search(f) else ("leaf" if not g[f]["imports"] else "")
        print(f"  {f}  {tag}")


def cmd_status(root, out_dir, hook):
    commit = structure_commit(out_dir)
    if not commit:
        if not hook:
            print("No STRUCTURE.md yet (or it has no caddis-map commit stamp). Run the map skill.")
        return
    changed, behind = changed_since(root, commit)
    if not changed:
        if not hook:
            print(f"Map is fresh: STRUCTURE.md describes commit {commit} and no source files changed since.")
        return
    g = load(root, out_dir)["files"]
    areas = sorted({n["area"] for n in g.values()})
    by_area = Counter(g[f]["area"] if f in g else area_of(f, areas) for f in changed)
    then = set(run(["git", "ls-tree", "-r", "--name-only", commit], root).split("\n"))
    gone = [f for f in changed if not os.path.exists(os.path.join(root, f))]
    new = [f for f in changed if f not in gone and f not in then]
    when = f"{behind} commit(s) behind" if behind else "on the current commit"
    msg = (f"Caddis map: STRUCTURE.md is {when}, and {len(changed)} source file(s) have changed since "
           f"({len(new)} new, {len(gone)} deleted) in " + ", ".join(f"{a} ({c})" for a, c in by_area.most_common(8)) + ".")
    if hook:
        print(msg + " Refresh it with the caddis map skill before relying on it.")
    else:
        print(msg)
        for f in sorted(changed):
            print(f"  {'-' if f in gone else '+' if f in new else '~'} {f}")


def main():
    ap = argparse.ArgumentParser(description="Caddis codebase map")
    ap.add_argument("--root", default=".", help="repo root (default: current directory)")
    ap.add_argument("--out", default=None, help="output dir (default: <root>/.caddis/map)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    s = sub.add_parser("status")
    s.add_argument("--hook", action="store_true", help="print only when stale")
    u = sub.add_parser("uses")
    u.add_argument("path")
    u.add_argument("--depth", type=int, default=1)
    d = sub.add_parser("deps")
    d.add_argument("path")
    a = sub.add_parser("area")
    a.add_argument("dir")
    sub.add_parser("orphans")
    sub.add_parser("stamp", help="print the commit stamp line for STRUCTURE.md")
    sub.add_parser("version")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    out_dir = args.out or os.path.join(root, ".caddis", "map")
    if args.cmd == "build":
        build(root, out_dir)
    elif args.cmd == "status":
        try:
            cmd_status(root, out_dir, args.hook)
        except Exception:  # a hook must never break a session
            if not args.hook:
                raise
    elif args.cmd == "uses":
        cmd_uses(root, out_dir, args.path, args.depth)
    elif args.cmd == "deps":
        cmd_deps(root, out_dir, args.path)
    elif args.cmd == "area":
        cmd_area(root, out_dir, args.dir)
    elif args.cmd == "orphans":
        cmd_orphans(root, out_dir)
    elif args.cmd == "stamp":
        print(f"<!-- caddis-map commit: {head_commit(root) or 'none'} -->")
    elif args.cmd == "version":
        print(VERSION)


if __name__ == "__main__":
    main()
