"""Check one contract against the checklist, on this machine only.

Every chunk is checked for every item ("not found" has to mean "checked
everywhere"). Search only decides which passage to quote. The verdict bands
were set on half of CUAD's test contracts and checked on the other half
(eval/bands.py, 4 Oct 2026, Jeff v1.2, "short" wording). On the held-out
half:
  found      P >= 0.91   92% really present
  check      0.15-0.91   22% really present; the lawyer looks
  not found  P < 0.15    1 of 204 real clauses fell here; never reported as "absent"
"""
import html
import re
import time
from dataclasses import dataclass
from pathlib import Path

from .checklist import CHECKLIST, Item
from .chunk import Chunk, chunk_text
from .jeff import ask
from .search import BM25, rank_chunks, regex_hits, tokens

FOUND, UNSURE = 0.91, 0.15


@dataclass
class Finding:
    item: Item
    verdict: str  # "found" | "check" | "not found"
    p: float
    chunk: Chunk
    quote: str
    chunks_checked: int


def read_document(path: str) -> str:
    """Plain text, or .docx read with the standard library (no Word, no upload)."""
    p = Path(path)
    if p.suffix.lower() == ".docx":
        import zipfile

        xml = zipfile.ZipFile(p).read("word/document.xml").decode("utf-8")
        paras = []
        for para in re.findall(r"<w:p[ >].*?</w:p>", xml, re.DOTALL):
            runs = re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", para, re.DOTALL)
            paras.append(html.unescape("".join(runs)))
        return "\n".join(paras)
    if p.suffix.lower() == ".pdf":
        raise SystemExit("PDF is not read yet: save it as .docx or .txt first")
    return p.read_text(encoding="utf-8", errors="replace")


_SENT = re.compile(r"(?<=[.;:])\s+(?=[A-Z(\"'0-9])|\n+")


def best_quote(item: Item, chunk: Chunk, limit: int = 400) -> str:
    """The sentence in the chunk most likely to be the clause: a pattern hit, else the best word overlap."""
    sents = [s.strip() for s in _SENT.split(chunk.text) if s.strip()]
    if not sents:
        return chunk.text[:limit]
    with_hit = [s for s in sents if regex_hits(item, s)]
    if with_hit:
        # a full sentence over a heading ("LIMITATION OF LIABILITY"); a heading
        # alone is quoted with the sentence that follows it
        s = next((x for x in with_hit if len(x) >= 60), None)
        if s is None:
            i = sents.index(with_hit[0])
            s = with_hit[0] + (f" — {sents[i + 1]}" if i + 1 < len(sents) else "")
    else:
        q = set(tokens(f"{item.name} {item.description}"))
        s = max(sents, key=lambda x: len(q & set(tokens(x))))
    return s if len(s) <= limit else s[: limit - 1] + "…"


def check(text: str, checklist=CHECKLIST, progress=None) -> list[Finding]:
    chunks = chunk_text(text)
    questions = {i.key: i.question("short") for i in checklist}
    ps: dict[int, dict[str, float]] = {}
    for c in chunks:
        ps[c.index] = ask(c.text, questions)
        if progress:
            progress(c.index + 1, len(chunks))
    bm25 = BM25([c.text for c in chunks])
    out = []
    for item in checklist:
        # highest P wins; search breaks ties and picks the quote
        rank = {i: r for r, (i, _) in enumerate(rank_chunks(item, chunks, bm25))}
        best = max(chunks, key=lambda c: (ps[c.index][item.key], -rank[c.index]))
        p = ps[best.index][item.key]
        verdict = "found" if p >= FOUND else "check" if p >= UNSURE else "not found"
        out.append(Finding(item, verdict, p, best, best_quote(item, best), len(chunks)))
    return out


def render_markdown(findings: list[Finding], name: str) -> str:
    lines = [f"# {name}", "", "| Clause | Verdict | P | Where | Passage |", "|---|---|---|---|---|"]
    for f in findings:
        where = f"chars {f.chunk.start:,}–{f.chunk.end:,}"
        if f.verdict == "not found":
            lines.append(f"| {f.item.name} | not found in any of {f.chunks_checked} passages | {f.p:.2f} (highest) | – | – |")
        else:
            q = f.quote.replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {f.item.name} | **{f.verdict}** | {f.p:.2f} | {where} | {q} |")
    lines += ["", f"_Checked on this computer only. \"Not found\" means no passage scored {UNSURE} or more; it is not proof the clause is absent (on public test contracts, 1 in 204 real clauses fell there)._"]
    return "\n".join(lines)


def render_html(findings: list[Finding], name: str, seconds: float) -> str:
    rows = []
    for f in findings:
        cls = {"found": "found", "check": "check", "not found": "none"}[f.verdict]
        if f.verdict == "not found":
            body = f"<td>not found in any of {f.chunks_checked} passages</td><td>{f.p:.2f} <small>highest</small></td><td></td><td></td>"
        else:
            body = (
                f"<td><b>{f.verdict}</b></td><td>{f.p:.2f}</td><td>{f.chunk.start:,}–{f.chunk.end:,}</td>"
                f"<td class=q>{html.escape(f.quote)}</td>"
            )
        rows.append(f"<tr class={cls}><td>{html.escape(f.item.name)}</td>{body}</tr>")
    return f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Clause check</title>
<style>
:root{{--bg:#fff;--fg:#1d1d1f;--muted:#6e6e73;--line:#e5e5ea;--found:#e8f5e9;--check:#fff8e1;--none:#f5f5f7}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111;--fg:#f2f2f7;--muted:#98989d;--line:#2c2c2e;--found:#14301a;--check:#3a3000;--none:#1c1c1e}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif;margin:0;padding:24px 16px;max-width:1100px;margin:auto}}
h1{{font-size:20px;margin:0 0 4px}} p{{color:var(--muted);margin:0 0 16px}}
table{{border-collapse:collapse;width:100%}} td,th{{text-align:left;vertical-align:top;padding:8px;border-bottom:1px solid var(--line)}}
tr.found td{{background:var(--found)}} tr.check td{{background:var(--check)}} tr.none td{{background:var(--none);color:var(--muted)}}
td.q{{font-family:Georgia,serif;font-size:14px}} small{{color:var(--muted)}}
@media (max-width:640px){{td:nth-child(4),th:nth-child(4){{display:none}}}}
</style>
<h1>{html.escape(name)}</h1>
<p>Checked on this computer only, in {seconds:.0f} s. <b>found</b> was right 92% of the time on held-out public contracts; <b>check</b> needs your eye (about 1 in 5 is real). "Not found" means no passage scored {UNSURE} or more: it is not proof the clause is absent (1 in 204 real clauses fell there).</p>
<table><tr><th>Clause</th><th>Verdict</th><th>P</th><th>Where (chars)</th><th>Passage</th></tr>
{"".join(rows)}
</table>"""


def main(argv=None):
    import argparse
    import sys

    ap = argparse.ArgumentParser(prog="python -m legal_screen", description="Check a contract for clauses, locally.")
    ap.add_argument("document", help=".txt or .docx")
    ap.add_argument("--html", help="also write an HTML report here")
    a = ap.parse_args(argv)
    text = read_document(a.document)
    t0 = time.time()
    findings = check(text, progress=lambda i, n: print(f"\r  passage {i}/{n}", end="", file=sys.stderr, flush=True))
    print(file=sys.stderr)
    name = Path(a.document).name
    print(render_markdown(findings, name))
    if a.html:
        Path(a.html).write_text(render_html(findings, name, time.time() - t0), encoding="utf-8")
        print(f"\nHTML report: {a.html}", file=sys.stderr)
