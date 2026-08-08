from hrr_memory.store import MemoryStore
from hrr_memory.export import build_scenarios, export_artifacts

def test_build_scenarios_groups_by_entity_overlap(tmp_path):
    s = MemoryStore(db_path=str(tmp_path / "m.db"))
    s.add_fact("PTG deploys on merge to main", category="project", tags="ptg")
    s.add_fact("PTG uses ECR and ECS Fargate", category="project", tags="ptg")
    s.add_fact("the cat sat on the mat", category="general")
    sc = build_scenarios(s.list_facts())
    assert len(sc) >= 1
    ptg = [x for x in sc if "PTG" in x["name"]]
    assert ptg, "expected a PTG scenario cluster"

def test_export_includes_scenarios(tmp_path):
    s = MemoryStore(db_path=str(tmp_path / "m.db"))
    s.add_fact("PTG deploys on merge to main", category="project", tags="ptg")
    s.add_fact("PTG uses ECR and ECS Fargate", category="project", tags="ptg")
    out = tmp_path / "a"
    r = export_artifacts(s, str(out))
    assert r["scenarios"] >= 1
    assert (out / "scenarios.md").exists()
