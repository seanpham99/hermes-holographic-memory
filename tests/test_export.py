from hrr_memory.store import MemoryStore
from hrr_memory.export import export_artifacts

def test_export_writes_files(tmp_path):
    s = MemoryStore(db_path=str(tmp_path / "m.db"))
    s.add_fact("deploy workflow uses GitHub Actions", category="tool", tags="deploy,ci")
    s.add_fact("PTG deploys on merge to main", category="project", tags="ptg")
    out = tmp_path / "artifacts"
    result = export_artifacts(s, str(out))
    assert result["facts"] == 2
    assert (out / "facts.md").exists()
    assert (out / "entities.md").exists()
    content = (out / "facts.md").read_text()
    assert "deploy workflow" in content
    assert "0.5" in content  # trust score visible
