import sys, pathlib, json
import yaml
ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT))
import pytest

@pytest.fixture(scope="session")
def repo():
    return REPO

@pytest.fixture(scope="session")
def rules(repo):
    return {p.stem: yaml.safe_load(open(p)) for p in (repo / "rules").glob("*.yaml")}

@pytest.fixture(scope="session")
def flows(repo):
    return {p.stem: json.load(open(p)) for p in (repo / "flows").glob("*.json") if p.name != "node-types.json"}

@pytest.fixture(scope="session")
def tools(repo):
    specs = [yaml.safe_load(open(p)) for p in (repo / "tools").glob("*.yaml")]
    return {t["name"]: t for t in specs}

@pytest.fixture(scope="session")
def docs(repo):
    return json.load(open(repo / "evals" / "demo-documents.json"))["documents"]

@pytest.fixture(scope="session")
def glossary(repo):
    return yaml.safe_load(open(repo / "inventory" / "glossary.yaml"))["glossary"]

@pytest.fixture(scope="session")
def golden(repo):
    return json.load(open(repo / "evals" / "golden-questions.json"))["questions"]
