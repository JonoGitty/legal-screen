"""Set the verdict bands on half the contracts; report what they do on the other half.

Contracts are split by title, alternating, so neither half is picked by
result. "found" must be right most of the time; "not found" must rarely
hide a real clause. The bands are chosen on half A only.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval.cuad_eval import RUNS, load_contracts  # noqa: E402
from legal_screen.checklist import CHECKLIST  # noqa: E402
from legal_screen.chunk import chunk_text  # noqa: E402


def doc_pairs(contracts, scores):
    out = []
    for title, text, gold in contracts:
        n = len(chunk_text(text))
        for item in CHECKLIST:
            p = max(scores[title][i]["p"][item.key] for i in range(n))
            out.append((p, int(bool(gold[item.key]))))
    return out


def bands(pairs, lo, hi):
    def stat(sel):
        return len(sel), (sum(y for _, y in sel) / len(sel) if sel else None)
    return {
        "found": stat([x for x in pairs if x[0] >= hi]),
        "check": stat([x for x in pairs if lo <= x[0] < hi]),
        "not found": stat([x for x in pairs if x[0] < lo]),
        "missed": sum(y for p, y in pairs if p < lo),
        "present": sum(y for _, y in pairs),
    }


def main(wording="short"):
    scores = {}
    for line in (RUNS / f"jeff_{wording}.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        scores.setdefault(r["doc"], {})[r["chunk"]] = r
    contracts = [c for c in load_contracts() if c[0] in scores]
    a, b = contracts[0::2], contracts[1::2]
    pa, pb = doc_pairs(a, scores), doc_pairs(b, scores)
    # choose on A: "not found" may hide at most 2% of A's present clauses; "found" must be >= 90% right
    present_a = sum(y for _, y in pa)
    grid = [x / 100 for x in range(1, 100)]
    lo = max(t for t in grid if sum(y for p, y in pa if p < t) <= 0.02 * present_a)
    hi = min((t for t in grid if t > lo and (lambda s: s and sum(y for _, y in s) / len(s) >= 0.90)([x for x in pa if x[0] >= t])), default=0.99)
    print(f"bands chosen on half A ({len(a)} contracts): not found < {lo:.2f} <= check < {hi:.2f} <= found")
    for name, pairs, n in (("A (chosen on)", pa, len(a)), ("B (held out)", pb, len(b))):
        r = bands(pairs, lo, hi)
        f, c, nf = r["found"], r["check"], r["not found"]
        print(f"  half {name}: {n} contracts, {len(pairs)} decisions, {r['present']} clauses present")
        print(f"    found      {f[0]:4d}  really present {100 * (f[1] or 0):5.1f}%")
        print(f"    check      {c[0]:4d}  really present {100 * (c[1] or 0):5.1f}%")
        print(f"    not found  {nf[0]:4d}  really present {100 * (nf[1] or 0):5.1f}%   = {r['missed']}/{r['present']} clauses missed")
    json.dump({"lo": lo, "hi": hi}, open(RUNS / f"bands_{wording}.json", "w"))


if __name__ == "__main__":
    main(*(sys.argv[1:] or ["short"]))
