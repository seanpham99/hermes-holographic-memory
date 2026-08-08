def test_bm25_ranks_exact_match_first(tmp_path):
    from holographic.store import MemoryStore
    from holographic.retrieval import FactRetriever
    s = MemoryStore(db_path=str(tmp_path / "m.db"))
    s.add_fact("deploy deploy deploy the workflow", category="ops")
    s.add_fact("deploy workflow", category="ops")
    r = FactRetriever(s)
    res = r.search("deploy workflow", category="ops", limit=2)
    assert res[0]["content"] == "deploy workflow"
    assert res[0]["score"] > res[1]["score"]

def test_bm25_score_field_present(tmp_path):
    from holographic.store import MemoryStore
    from holographic.retrieval import FactRetriever
    s = MemoryStore(db_path=str(tmp_path / "m.db"))
    s.add_fact("alpha beta gamma", category="ops")
    r = FactRetriever(s)
    res = r.search("alpha", limit=1)
    assert "bm25" in res[0] or res[0]["score"] > 0

def test_single_hit_fts_rank_is_one(tmp_path):
    from holographic.store import MemoryStore
    from holographic.retrieval import FactRetriever
    s = MemoryStore(db_path=str(tmp_path / "m.db"))
    s.add_fact("alpha beta gamma", category="ops")
    r = FactRetriever(s)
    res = r.search("alpha", limit=1)
    assert len(res) == 1
    assert res[0]["fts_rank"] == 1.0  # single-hit tie must not zero the FTS weight
    assert res[0]["score"] > 0
