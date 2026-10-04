"""Phase 2 (first cut): do party names survive pseudonymisation?

CUAD labels each contract's parties. A label counts as leaked if its name
still appears, word-bounded and case-insensitive, in the pseudonymised text.
Labels that are role words ("the Customer") or sentences are not names, and
are skipped. Over-redaction is reported as placeholders per contract, with
a sample of what was replaced, to read by eye.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from legal_screen.pseudo import _is_role, pseudonymise  # noqa: E402


def gold_names(qas):
    names = set()
    for qa in qas:
        if not re.search(r"__Parties(?:_\d+)?$", qa["id"]):
            continue
        for a in qa["answers"]:
            t = a["text"].split(":")[-1].strip(" ,.;\"'()")
            if not t or len(t) > 70 or re.search(r"referred|individually|collectively|hereinafter", t, re.I):
                continue
            if _is_role(t) or not re.search(r"[A-Za-z]{2}", t):
                continue
            names.add(t)
    return names


def main():
    split = sys.argv[1] if len(sys.argv) > 1 else "test"
    # "train" = CUAD's 408 other contracts: the rules were never fixed while looking at them
    name = {"test": "test.json", "train": "train_separate_questions.json"}[split]
    data = json.loads((ROOT / "data" / "cuad" / name).read_text(encoding="utf-8"))["data"]
    print(f"split: {split}")
    total = leaked = docs_clean = 0
    examples = []
    placeholders = []
    for doc in data:
        para = doc["paragraphs"][0]
        names = gold_names(para["qas"])
        p = pseudonymise(para["context"])
        placeholders.append(sum(1 for k in p.mapping if "PARTY" in k or "ORG" in k))
        doc_leaks = [n for n in names if re.search(rf"(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])", p.text, re.I)]
        total += len(names)
        leaked += len(doc_leaks)
        docs_clean += not doc_leaks
        examples += [(doc["title"][:40], n) for n in doc_leaks]
    print(f"{len(data)} contracts, {total} labelled party names")
    print(f"caught {total - leaked}/{total} = {100 * (total - leaked) / total:.1f}%   leaked {leaked}")
    print(f"contracts with no party-name leak: {docs_clean}/{len(data)}")
    print(f"PARTY/ORG placeholders per contract: median {sorted(placeholders)[len(placeholders) // 2]}, max {max(placeholders)}")
    print("leaks (first 25):")
    for t, n in examples[:25]:
        print(f"  {t:40}  {n}")


if __name__ == "__main__":
    main()
