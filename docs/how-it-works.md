# How it works

The technical companion to [overview.md](overview.md). The code is small
and uses only the Python standard library. Each module is listed below.

```
contract (.txt / .docx)
   │  read_document()                      check.py: .docx read with zipfile, no Word needed
   ▼
chunks of ~4,000 chars, 400 overlapping    chunk.py: cut at paragraph or sentence ends; offsets kept
   │
   ├─► search: regex hits + BM25           search.py: orders passages, picks the quote
   │
   ├─► Jeff: 12 yes/no questions × every chunk    jeff.py → POST /v1/systemone on localhost
   │         P(yes) per question per chunk
   ▼
per question: highest P over all chunks → verdict band → quote from that chunk
   ▼
report: Markdown to stdout, optional HTML  check.py
```

## The pieces

### Chunking (`legal_screen/chunk.py`)
- Chunks of up to 4,000 characters, overlapping by 400, so a clause
  straddling a boundary is whole in at least one chunk.
- Each cut is made at a paragraph break or sentence end in the last
  quarter of the window, where one exists.
- Every chunk keeps its character offsets, so the report can say *where*.

### The checklist (`legal_screen/checklist.py`)
- 12 clause types, named and described as in CUAD, so they can be scored
  against CUAD's lawyer labels.
- Each has a short question for Jeff ("Does this passage of a contract
  contain a governing law clause?") and a few regex patterns.
- The patterns were written before any results were seen, and must not
  be tuned on the test contracts.

### Search (`legal_screen/search.py`)
- **Regex hits per clause type, plus BM25** (a standard keyword-ranking
  formula) of the clause description against each chunk.
- **It decides the order passages are considered in, and which sentence
  is quoted.** It never decides which passages are skipped: "not found"
  must mean every passage was checked.
- **Measured as a shortcut:** letting search pick only the top 3 passages
  for Jeff cuts Jeff's work about 5×, and costs about 4 points of recall
  (RESULTS.md). The checker doesn't take that shortcut.

### Jeff (`legal_screen/jeff.py`)
- **What it is:** [Jeff](https://github.com/firelex/jeff) by Mathias
  Strasser, a 0.8-billion-parameter "System One" model. It answers fixed
  questions with calibrated probabilities instead of generating text.
- **How it's used:** zero-shot, the base model with no adapter, version
  v1.2.
- **Cost:** each question costs about 0.25 s per 4K chunk on an 8 GB
  laptop GPU. Asking several questions in one call saves nothing, so the
  cost is chunks × questions.
- **The client:**
  - It only talks to a Jeff server on the same machine; see
    [privacy.md](privacy.md).
  - It retries Jeff's "busy" answer (HTTP 529, Jeff serves one request at
    a time) and timeouts, which happen when other apps share the GPU.

### Verdicts (`legal_screen/check.py`)
- **For each question, the chunk with the highest P wins.** Ties go to
  the passage search ranked higher.
- **Bands:** found if P ≥ 0.91; check if 0.15 ≤ P < 0.91; not found if
  P < 0.15 in every chunk.
- **How the bands were set** (`eval/bands.py`):
  - The 102 CUAD test contracts were split alternately by title.
  - On half A, the lowest "not found" cut-off was chosen that hides at
    most 2% of real clauses, and the lowest "found" cut-off that is at
    least 90% right.
  - Those cut-offs were applied unchanged to half B, which is what is
    reported.
- **The quote:**
  - It is the first sentence in the winning chunk with a regex hit,
    preferring a full sentence over a heading.
  - A heading on its own is quoted with the sentence that follows it.
  - With no hit, it is the sentence sharing the most words with the
    clause description.

### Pseudonymiser (`legal_screen/pseudo.py`), rules only, v0
1. **Parties the contract defines.** For each `("Short Name")` definition
   in the preamble, work backwards to the name, dropping descriptors like
   ", a Delaware corporation". The name, the name without its suffix, and
   the short name share one placeholder. A short name that is a role word
   ("the Customer") is kept, because it identifies no one.
2. **Organisations with a company suffix anywhere:** Inc., Ltd, LLC,
   GmbH, Trust, Bank, Company and so on, case-insensitive. "A Florida
   corporation" is skipped, because it is a description, not a name.
3. **Things with a shape:**
   - emails, web addresses, phone numbers
   - money, dates, street addresses, US ZIP codes and UK postcodes
   - people with a title (Mr, Ms, Dr)
   - signature lines (By:, Name:, Attention:)
4. **Placeholders** look like `⟦PARTY_A⟧`, `⟦ORG_1⟧` and `⟦AMOUNT_2⟧`. The
   same entity always gets the same placeholder, and `restore()` maps them
   back. Text that already contains `⟦` is refused, so placeholders can
   never collide.

**Measured** (`eval/pseudo_eval.py`): it catches 86.3% of CUAD's labelled
party names on 408 contracts it had never seen.

**Known gaps:**
- people named without a title
- short forms defined deep in the body
- names with no company suffix
- *indirect identifiers*: a unique deal fact can identify a client with
  every name gone. No rule catches that.

## Evaluation

| Script | What it does |
|---|---|
| `eval/get_cuad.py` | Downloads CUAD, about 18 MB, into `data/cuad/` (not committed). |
| `eval/cuad_eval.py score` | Runs Jeff over every chunk of the 102 test contracts for all 12 questions, about 85 minutes. Results are appended to `runs/jeff_<wording>.jsonl`, so a stopped run resumes. |
| `eval/cuad_eval.py report` | Scores keywords only, Jeff on every chunk, and search-then-Jeff (top *k*), each against the constant "never present". Reports recall, precision, AUC, calibration (ECE), whether the passage is right, and the work per contract. |
| `eval/bands.py` | Sets the verdict bands on one half of the contracts and reports them on the other. |
| `eval/pseudo_eval.py [test\|train]` | Measures party-name leaks after pseudonymising. |

There is no training, so there is no leakage between training and testing.
The bands are set and reported on different halves. The pseudonymiser's
rules were fixed while looking at the test split, so its honest number
comes from the 408 training contracts, which were never looked at.

## Tests

`python3 -m unittest discover -s tests` runs 14 tests, with no Jeff and no
network needed. They cover:
- chunk offsets and overlap
- party finding
- what is redacted and what is kept
- consistent placeholders, and restoring them
- regressions for each bug found while building
- verdict bands and the honest "not found" wording
- quoting
- reading .docx files
- the local-only, no-redirect and no-proxy rules
- retrying after a timeout

For the regression tests and the local-only rules, the protection they
test was removed on purpose to confirm each test fails without it.
