import pytest
from pathlib import Path
from holographic.store import MemoryStore
from holographic.holographic import phases_to_bytes, bytes_to_phases

def test_store_default_dim_is_4096(tmp_path):
    store = MemoryStore(db_path=str(tmp_path / "m.db"))
    assert store.hrr_dim == 4096

def test_roundtrip_4096_blob(tmp_path):
    import numpy as np
    vec = np.zeros(4096)
    blob = phases_to_bytes(vec)
    out = bytes_to_phases(blob, dim=4096)
    assert out.shape == (4096,)

def test_rebuild_produces_4096_blobs(tmp_path):
    store = MemoryStore(db_path=str(tmp_path / "m.db"))
    fid = store.add_fact("test fact about alpha", category="test", tags="test")
    store.rebuild_all_vectors()
    row = store._conn.execute(
        "SELECT hrr_vector FROM facts WHERE fact_id = ?", (fid,)
    ).fetchone()
    assert len(row["hrr_vector"]) == 16388  # 4 + 4096*4 float32
