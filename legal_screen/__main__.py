"""python -m legal_screen <contract>            check it against the checklist (local)
python -m legal_screen redact <contract>     pseudonymise it (local); the mapping is written beside it
"""
import json
import sys
from pathlib import Path

if len(sys.argv) > 1 and sys.argv[1] == "redact":
    import argparse

    from .check import read_document
    from .pseudo import pseudonymise

    ap = argparse.ArgumentParser(prog="python -m legal_screen redact")
    ap.add_argument("cmd")
    ap.add_argument("document")
    ap.add_argument("--out", help="redacted text (default: <name>.redacted.txt)")
    a = ap.parse_args()
    src = Path(a.document)
    p = pseudonymise(read_document(str(src)))
    out = Path(a.out) if a.out else src.with_suffix(".redacted.txt")
    mapping = out.with_suffix(".mapping.json")
    out.write_text(p.text, encoding="utf-8")
    mapping.write_text(json.dumps(p.mapping, indent=2, ensure_ascii=False), encoding="utf-8")
    kinds: dict[str, int] = {}
    for ph in p.mapping:
        k = ph.strip("⟦⟧").rsplit("_", 1)[0]
        kinds[k] = kinds.get(k, 0) + 1
    print(f"redacted: {out}")
    print(f"mapping:  {mapping}  (keep it on this computer: it holds the real names)")
    print("replaced: " + ", ".join(f"{n} {k.lower()}" for k, n in sorted(kinds.items())))
    print("Read the redacted text before it goes anywhere: names with no company suffix or title, and unique deal facts, can survive.")
else:
    from .check import main

    main()
