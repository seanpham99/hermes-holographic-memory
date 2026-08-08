"""White-box artifact export: facts + entities as human-readable markdown.

TencentDB-style inspectability — memory is not a black box. No LLM.

"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

def export_artifacts(store, out_dir: str) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    facts = store.list_facts(limit=10_000)
    lines = [
        "# Memory Facts",
        "",
        f"Exported: {datetime.now().isoformat(timespec='seconds')}",
        f"Total: {len(facts)}",
        "",
        "| ID | Trust | Cat | Tags | Content |",
        "|----|-------|-----|------|---------|",
    ]
    for f in facts:
        tags = f.get("tags") or ""
        lines.append(
            f"| {f['fact_id']} | {f['trust_score']:.2f} | {f.get('category','')} "
            f"| {tags} | {f['content']} |"
        )
    (out / "facts.md").write_text("\n".join(lines), encoding="utf-8")

    ents = store._conn.execute(
        "SELECT e.name, e.entity_type, COUNT(fe.fact_id) AS n "
        "FROM entities e LEFT JOIN fact_entities fe USING (entity_id) "
        "GROUP BY e.entity_id ORDER BY n DESC"
    ).fetchall()
    elines = ["# Entities", "", "| Entity | Type | Fact Count |", "|--------|------|-----------|"]
    for e in ents:
        elines.append(f"| {e['name']} | {e['entity_type']} | {e['n']} |")
    (out / "entities.md").write_text("\n".join(elines), encoding="utf-8")

    scenarios = build_scenarios(facts)
    slines = ["# Scenarios", "", f"Clusters: {len(scenarios)}", ""]
    for sc in scenarios:
        slines.append(f"## Scenario {sc['scenario_id']}: {sc['name']}")
        slines.append(f"score={sc['score']} facts={len(sc['fact_ids'])}")
        for fid in sc["fact_ids"]:
            f = next((x for x in facts if x["fact_id"] == fid), None)
            if f:
                slines.append(f"- [{f['fact_id']}] {f['content']}")
        slines.append("")
    (out / "scenarios.md").write_text("\n".join(slines), encoding="utf-8")

    return {
        "facts": len(facts),
        "entities": len(ents),
        "scenarios": len(scenarios),
        "out_dir": str(out),
    }


def build_scenarios(facts: list[dict]) -> list[dict]:
    """Cluster facts into scenarios by entity overlap + token overlap.

    Heuristic, no LLM: two facts join a scenario if they share >= 2
    significant tokens or share a linked entity. Scenario name = most
    frequent shared entity/token.
    """
    import re
    STOP = {"the", "and", "for", "with", "use", "uses", "used", "from", "this", "that", "on"}

    def toks(text: str) -> tuple[set[str], set[str]]:
        words = re.findall(r"[a-zA-Z0-9]+", text)
        sig = {w.lower() for w in words if w.lower() not in STOP}
        ents = {
            w.lower()
            for w in words
            if len(w) > 1 and w[0].isupper() and w.lower() not in STOP
        }
        return sig, ents

    fact_info = [(f["fact_id"], *toks(f["content"])) for f in facts]
    assigned: set[int] = set()
    scenarios: list[dict] = []

    for i, (fid, sig_i, ent_i) in enumerate(fact_info):
        if fid in assigned:
            continue
        cluster = [fid]
        name = facts[i]["content"].split(" ")[:3]
        name = " ".join(name)
        for j in range(i + 1, len(fact_info)):
            fid2, sig_j, ent_j = fact_info[j]
            if fid2 in assigned:
                continue
            if len(sig_i & sig_j) >= 2 or (ent_i & ent_j):
                cluster.append(fid2)
                assigned.add(fid2)
        assigned.add(fid)
        if len(cluster) >= 2:
            scenarios.append({
                "scenario_id": len(scenarios) + 1,
                "name": name,
                "fact_ids": cluster,
                "score": round(len(cluster) / len(facts), 3),
            })
    return scenarios


def main() -> int:
    import argparse
    from plugins.memory.holographic.store import MemoryStore
    ap = argparse.ArgumentParser(description="Export holographic memory artifacts")
    ap.add_argument("--db", default=str(Path.home() / ".hermes" / "memory_store.db"))
    ap.add_argument("--out", default=str(Path.home() / ".hermes" / "artifact" / "memory-export"))
    args = ap.parse_args()
    store = MemoryStore(db_path=args.db)
    result = export_artifacts(store, args.out)
    print(f"Exported {result['facts']} facts, {result['entities']} entities, {result['scenarios']} scenarios → {args.out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
