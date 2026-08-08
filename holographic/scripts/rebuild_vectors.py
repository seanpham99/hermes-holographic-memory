"""Recovery utility: rebuild all HRR vectors + banks at a consistent dim.

Run: venv/bin/python plugins/memory/holographic/scripts/rebuild_vectors.py
Backs up the DB first, then recomputes vectors from text at dim=4096.
"""
import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))  # repo root

from plugins.memory.holographic.store import MemoryStore

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(Path.home() / ".hermes" / "memory_store.db"))
    ap.add_argument("--dim", type=int, default=4096)
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    db = Path(args.db).expanduser()
    if not db.exists():
        print(f"DB not found: {db}", file=sys.stderr)
        return 1

    if not args.no_backup:
        backup_dir = Path.home() / ".hermes" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        dst = backup_dir / f"memory_store.{ts}.db"
        shutil.copy2(db, dst)
        print(f"Backup: {dst}")

    store = MemoryStore(db_path=str(db), hrr_dim=args.dim)
    n = store.rebuild_all_vectors(dim=args.dim)
    print(f"Rebuilt {n} facts at dim={args.dim}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
