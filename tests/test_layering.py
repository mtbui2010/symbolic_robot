"""Rules of CLAUDE.md that a test can enforce: layered imports, no private names, size limits that do not grow."""
import ast
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "symbolic_robot"
GLUE = {"server.py", "server_skills.py"}                    # the only core modules that may import robot_agent
PRIVATE = re.compile("|".join(["kc" + "are", "ka" + "air", "clo" + "bot", "buche" + "on"]), re.I)
FROZEN_NAME = re.compile("home" + "loop", re.I)
# where the household names may appear (the merged household simulator and benchmark, their tests, docs and recorded results, and the
# docs that explain the merge): nowhere in the core, the factory domain or the generic bench modules
HOUSEHOLD_OK = ("symbolic_robot/domains/home/", "bench/suites/home/", "tests/home/", "docs/home/", "results/", "docs/migration_home.md", "docs/bench.md",
                "docs/architecture.md", "docs/CHANGELOG.md", "docs/domains.md", "README.md", "CLAUDE.md", "tests/test_home_parity.py", "tests/test_home_baseline.py",
                "tests/test_bench.py", "tests/test_server.py", "tests/test_layering.py", "Makefile", "pyproject.toml")
RETIRED = ("homeloop_robot", "homeloop_bench")           # the standalone packages: nothing imports them any more
# robot_agent in bench/: only the household planners' adapter files, and only inside functions (so listing planners needs no robot_agent)
BENCH_RA_OK = ("bench/suites/home/planners/robot_agent_adapter.py", "bench/suites/home/planners/robot_agent_fake.py")
# the only file that names a private project: the later-step plan for the sibling simulator (to be removed before publishing)
PRIVATE_OK = ("docs/migration_" + "kc" + "are_sim.md", "tests/test_layering.py")
MAX_FUNC, MAX_FILE = 80, 600


def files(*suffixes):
    out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    return [ROOT / f for f in out if f.endswith(suffixes) and (ROOT / f).is_file() and f != "env.local.mk"]


def imports(path: Path):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            yield from (a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            yield node.module or ""


def test_core_and_domains_never_import_bench():
    bad = [str(p.relative_to(ROOT)) for p in CORE.rglob("*.py") if any(m == "bench" or m.startswith("bench.") for m in imports(p))]
    assert not bad, bad


def test_nothing_imports_the_retired_standalone_packages():
    bad = [str(p.relative_to(ROOT)) for p in files(".py") if any(m.split(".")[0] in RETIRED for m in imports(p))]
    assert not bad, bad


def test_robot_agent_only_in_server_glue_and_domain_packs():
    bad = []
    for p in CORE.rglob("*.py"):
        rel = p.relative_to(CORE)
        in_pack = "configs" in rel.parts and rel.parts[0] == "domains"      # a domain's robot_agent pack is robot_agent's own plug-in format
        if not in_pack and p.name not in GLUE and any(m.split(".")[0] == "robot_agent" for m in imports(p)):
            bad.append(str(rel))
    assert not bad, bad
    for p in ROOT.joinpath("bench").rglob("*.py"):
        rel = str(p.relative_to(ROOT))
        if rel in BENCH_RA_OK:
            top = [n for n in ast.parse(p.read_text()).body if isinstance(n, (ast.Import, ast.ImportFrom))]
            assert not any(m.split(".")[0] == "robot_agent" for n in top for m in ([a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ""])), p
            continue
        assert not any(m.split(".")[0] == "robot_agent" for m in imports(p)), p       # elsewhere bench talks to the server over HTTP only


def test_domains_do_not_import_each_other_or_the_server():
    for p in (CORE / "domains").rglob("*.py"):
        dom = p.relative_to(CORE / "domains").parts[0]
        for m in imports(p):
            assert not (m.startswith("symbolic_robot.domains.") and m.split(".")[2] != dom), (p, m)
            assert not m.startswith("symbolic_robot.server"), (p, m)


def test_no_private_names_anywhere():
    bad = []
    for p in files(".py", ".md", ".yaml", ".yml", ".toml", ".mk", ".txt", ".json", ".cfg", "Makefile"):
        rel = str(p.relative_to(ROOT))
        if rel in PRIVATE_OK:
            continue
        if PRIVATE.search(p.read_text(errors="ignore")) or PRIVATE.search(rel):
            bad.append(rel)
    assert not bad, bad


def test_household_names_appear_only_in_the_home_parts_and_the_docs_about_them():
    bad = []
    for p in files(".py", ".md", ".yaml", ".toml", "Makefile"):
        rel = str(p.relative_to(ROOT))
        if not rel.startswith(HOUSEHOLD_OK) and FROZEN_NAME.search(p.read_text(errors="ignore")):
            bad.append(rel)
    assert not bad, bad


def function_sizes(path: Path):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield f"{path.relative_to(ROOT)}::{node.name}", node.end_lineno - node.lineno + 1


def test_size_limits_do_not_grow():
    base = json.loads((ROOT / "tests" / "size_baseline.json").read_text())
    over = {}
    for p in files(".py"):
        n = len(p.read_text().splitlines())
        if n > MAX_FILE:
            over[str(p.relative_to(ROOT))] = n
        for name, size in function_sizes(p):
            if size > MAX_FUNC:
                over[name] = size
    for k, v in over.items():
        assert k in base["allowed"] and v <= base["allowed"][k]["max"], f"{k} is {v} lines (limit {MAX_FUNC}/{MAX_FILE}); justify it in tests/size_baseline.json"
    stale = [k for k in base["allowed"] if k not in over]
    assert not stale, f"entries no longer needed, remove them from the baseline: {stale}"
