"""Phase 1: can a gaming PC find clauses? Scored against CUAD's lawyer labels.

  python3 eval/cuad_eval.py score  [--wording short|described] [--docs N]
      Runs Jeff once over every chunk of the CUAD test contracts for all 12
      checklist items. Appends to runs/jeff_<wording>.jsonl, and resumes
      where it stopped.
  python3 eval/cuad_eval.py report [--wording short|described]
      Scores three arms on the same contracts:
        K     keywords alone (regex hits anywhere in the contract)
        J     Jeff alone (max P over every chunk)
        C@k   search then Jeff (Jeff checks only the k chunks search ranks highest)
      Writes runs/report_<wording>.json and prints a table.

Each arm is scored against the constant "never present" answer. Recall on
"present" is the headline number: a missed clause is the costly error.
Zero-shot, so there is no training split. Only CUAD's test split is used.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from legal_screen.checklist import CHECKLIST  # noqa: E402
from legal_screen.chunk import chunk_text  # noqa: E402
from legal_screen.jeff import ask  # noqa: E402
from legal_screen.search import BM25, rank_chunks, regex_hits  # noqa: E402

DATA = ROOT / "data" / "cuad" / "test.json"
RUNS = ROOT / "runs"


def load_contracts():
    """[(title, text, {item_key: [(start, end), ...]})], sorted by title."""
    by_name = {i.name: i.key for i in CHECKLIST}
    out = []
    for doc in json.loads(DATA.read_text(encoding="utf-8"))["data"]:
        para = doc["paragraphs"][0]
        gold = {i.key: [] for i in CHECKLIST}
        for qa in para["qas"]:
            key = by_name.get(qa["id"].split("__")[-1])
            if key:
                gold[key] = [(a["answer_start"], a["answer_start"] + len(a["text"])) for a in qa["answers"]]
        out.append((doc["title"], para["context"], gold))
    return sorted(out, key=lambda x: x[0])


def score(wording: str, max_docs: int | None) -> None:
    RUNS.mkdir(exist_ok=True)
    path = RUNS / f"jeff_{wording}.jsonl"
    done = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            done.add((r["doc"], r["chunk"]))
    questions = {i.key: i.question(wording) for i in CHECKLIST}
    contracts = load_contracts()[:max_docs]
    total = sum(len(chunk_text(t)) for _, t, _ in contracts)
    n = len(done)
    t0 = time.time()
    with path.open("a", encoding="utf-8") as f:
        for title, text, _ in contracts:
            for c in chunk_text(text):
                if (title, c.index) in done:
                    continue
                t = time.time()
                p = ask(c.text, questions)
                f.write(json.dumps({"doc": title, "chunk": c.index, "start": c.start, "end": c.end, "p": p, "ms": round((time.time() - t) * 1000)}) + "\n")
                f.flush()
                n += 1
                if n % 25 == 0:
                    rate = (time.time() - t0) / max(1, n - len(done))
                    print(f"{n}/{total} chunks  ~{(total - n) * rate / 60:.0f} min left", flush=True)
    print(f"done: {n}/{total} chunks in {path}")


def auc(pos: list[float], neg: list[float]) -> float | None:
    if not pos or not neg:
        return None
    wins = sum((p > q) + 0.5 * (p == q) for p in pos for q in neg)
    return wins / (len(pos) * len(neg))


def ece(pairs: list[tuple[float, int]], bins: int = 10) -> float:
    total = 0.0
    for b in range(bins):
        sel = [(p, y) for p, y in pairs if (b / bins <= p < (b + 1) / bins) or (b == bins - 1 and p == 1.0)]
        if sel:
            total += len(sel) * abs(sum(p for p, _ in sel) / len(sel) - sum(y for _, y in sel) / len(sel))
    return total / max(1, len(pairs))


def metrics(pairs: list[tuple[float, int]], threshold: float) -> dict:
    pos = [p for p, y in pairs if y]
    neg = [p for p, y in pairs if not y]
    tp = sum(1 for p in pos if p >= threshold)
    fp = sum(1 for p in neg if p >= threshold)
    n = len(pairs)
    return {
        "n": n,
        "present": len(pos),
        "auc": auc(pos, neg),
        "recall": tp / len(pos) if pos else None,
        "precision": tp / (tp + fp) if tp + fp else None,
        "accuracy": (tp + len(neg) - fp) / n if n else None,
        "constant_accuracy": len(neg) / n if n else None,
    }


def overlaps(span: tuple[int, int], gold: list[tuple[int, int]]) -> bool:
    return any(span[0] < g1 and g0 < span[1] for g0, g1 in gold)


def report(wording: str, ks=(1, 2, 3), threshold: float = 0.5, max_docs: int | None = None) -> dict:
    rows = [json.loads(x) for x in (RUNS / f"jeff_{wording}.jsonl").read_text(encoding="utf-8").splitlines()]
    scores: dict[str, dict[int, dict]] = {}
    for r in rows:
        scores.setdefault(r["doc"], {})[r["chunk"]] = r
    contracts = [c for c in load_contracts()[:max_docs] if c[0] in scores]
    # only contracts whose every chunk was scored
    contracts = [c for c in contracts if len(scores[c[0]]) == len(chunk_text(c[1]))]
    arms: dict[str, list[tuple[float, int]]] = {"K": [], "J": [], **{f"C@{k}": [] for k in ks}}
    per_item: dict[str, dict[str, list]] = {i.key: {a: [] for a in arms} for i in CHECKLIST}
    located = {"J": [0, 0], **{f"C@{k}": [0, 0] for k in ks}}
    jeff_calls = {"J": 0, **{f"C@{k}": 0 for k in ks}}
    for title, text, gold in contracts:
        chunks = chunk_text(text)
        bm25 = BM25([c.text for c in chunks])
        for item in CHECKLIST:
            y = int(bool(gold[item.key]))
            hits = len(regex_hits(item, text))
            k_score = 1.0 if hits else 0.0
            ps = {c.index: scores[title][c.index]["p"][item.key] for c in chunks}
            order = [i for i, _ in rank_chunks(item, chunks, bm25)]
            cands = {"J": list(ps)}
            for k in ks:
                cands[f"C@{k}"] = order[:k]
            arms["K"].append((k_score, y))
            per_item[item.key]["K"].append((k_score, y))
            for arm, idxs in cands.items():
                best = max(idxs, key=lambda i: ps[i])
                p = ps[best]
                arms[arm].append((p, y))
                per_item[item.key][arm].append((p, y))
                jeff_calls[arm] += len(idxs)
                if y and p >= threshold:
                    located[arm][1] += 1
                    if overlaps((chunks[best].start, chunks[best].end), gold[item.key]):
                        located[arm][0] += 1
    out = {
        "wording": wording,
        "threshold": threshold,
        "contracts": len(contracts),
        "arms": {a: metrics(v, 0.5 if a == "K" else threshold) for a, v in arms.items()},
        "ece": {a: ece(v) for a, v in arms.items() if a != "K"},
        "located_when_found": {a: (v[0] / v[1] if v[1] else None) for a, v in located.items()},
        "jeff_calls_per_contract": {a: v / max(1, len(contracts)) for a, v in jeff_calls.items()},
        "per_item": {k: {a: metrics(v, 0.5 if a == "K" else threshold) for a, v in arms_.items()} for k, arms_ in per_item.items()},
    }
    (RUNS / f"report_{wording}.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def fmt(x, pct=True):
    return "  -  " if x is None else (f"{100 * x:5.1f}%" if pct else f"{x:5.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["score", "report"])
    ap.add_argument("--wording", default="short", choices=["short", "described"])
    ap.add_argument("--docs", type=int, default=None, help="first N contracts (by title)")
    ap.add_argument("--threshold", type=float, default=0.5)
    a = ap.parse_args()
    if a.cmd == "score":
        score(a.wording, a.docs)
        return
    r = report(a.wording, threshold=a.threshold, max_docs=a.docs)
    print(f"{r['contracts']} contracts x {len(CHECKLIST)} clause types, wording={r['wording']}, Jeff threshold {r['threshold']}")
    print(f"{'arm':6} {'recall':>7} {'precis':>7} {'acc':>7} {'const':>7} {'AUC':>6} {'ECE':>6} {'located':>8} {"checks/doc":>10}")
    for arm, m in r["arms"].items():
        print(
            f"{arm:6} {fmt(m['recall'])} {fmt(m['precision'])} {fmt(m['accuracy'])} {fmt(m['constant_accuracy'])} "
            f"{fmt(m['auc'], False)} {fmt(r['ece'].get(arm), False)} {fmt(r['located_when_found'].get(arm)):>8} "
            f"{r["jeff_calls_per_contract"].get(arm, 0):10.1f}"
        )
    print("\nper clause type (recall / AUC):")
    for key, arms_ in r["per_item"].items():
        cells = "  ".join(f"{a} {fmt(m['recall'])}/{fmt(m['auc'], False)}" for a, m in arms_.items() if a in ("K", "J", "C@3"))
        print(f"  {key:28} present {arms_['J']['present']:3d}  {cells}")


if __name__ == "__main__":
    main()
