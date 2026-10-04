# Results

> **In plain English.** On 102 real contracts that lawyers had already
> marked up, a small AI model on a laptop scored the clause 0.5 or above in
> about 95 of every 100 cases where a contract had that kind of clause. When it said **found** it was right about 9
> times in 10, and only 1 of 204 real clauses ended up marked **not
> found**. The price is a "check" pile, about 4 in 10 answers, for a person
> to glance at. Removing names catches about 6 in 7 party names, which is
> useful but not safe without a person reading it. The overview tells the
> story: [docs/overview.md](docs/overview.md).

Every number below comes from a real run on a laptop (RTX 3070 Ti Laptop
GPU, 8 GB), using Jeff v1.2 (`jeff-qwen3.5-0.8b`, base model, no adapter,
zero-shot). The data is the CUAD test split: 102 public commercial contracts
labelled by lawyers (The Atticus Project, CC BY 4.0). No client data was used.

## Phase 1: finding clauses (4 Oct 2026)

**Setup.**
- 12 clause types × 102 contracts = 1,224 decisions, of which 433 are
  clauses really present.
- Contracts are cut into 1,480 chunks of about 4K characters, with overlap.
- Question wording: "Does this passage of a contract contain a {clause} clause?"
- Reproduce with `python3 eval/cuad_eval.py score` then `report`.

| Arm | Recall | Precision | Accuracy | AUC | Points to the lawyer-marked passage | Jeff checks / contract |
|---|---|---|---|---|---|---|
| Always "not present" | 0% | – | 64.6% | 0.50 | – | 0 |
| Keywords only (regex) | 82.7% | 71.5% | 82.2% | 0.82 | – | 0 |
| **Jeff on every chunk** | **94.7%** | 62.9% | 78.3% | **0.94** | 91.2% | 174 |
| Search → Jeff, top 1 chunk | 82.2% | 77.2% | 85.1% | 0.92 | 93.0% | 12 |
| Search → Jeff, top 3 chunks | 90.5% | 69.9% | 82.8% | 0.94 | 93.6% | 33 |

The table uses a 0.5 threshold. Recall is the headline because a missed
clause is the costly error. AUC is threshold-free.

**By clause type.** Recall and AUC for Jeff on every chunk:

| Clause | Present | Keywords | Jeff |
|---|---|---|---|
| Governing law | 83 | 100% / 0.87 | 100% / 1.00 |
| Anti-assignment | 72 | 74% / 0.87 | 99% / 0.99 |
| Cap on liability | 44 | 68% / 0.81 | 98% / 0.95 |
| Renewal term | 26 | 69% / 0.83 | 100% / 0.98 |
| Insurance | 32 | 100% / 0.89 | 100% / 1.00 |
| Audit rights | 38 | 84% / 0.85 | 100% / 0.97 |
| Non-compete | 23 | 91% / 0.92 | 96% / 0.97 |
| Exclusivity | 33 | 97% / 0.71 | 97% / 0.90 |
| Termination for convenience | 29 | 83% / 0.74 | 86% / 0.73 |
| Change of control | 26 | 81% / 0.71 | 73% / 0.88 |
| Liquidated damages | 14 | 57% / 0.78 | 71% / 0.94 |
| **Uncapped liability** | 13 | 31% / 0.61 | **69% / 0.68** |

**What the table shows.**
- **Jeff is strong on clause types with a recognisable shape,** such as
  governing law and insurance. Why it is weaker on uncapped liability,
  change of control and liquidated damages isn't known yet. A hypothesis to
  test for uncapped liability: it is usually written as an exception ("the
  cap does not apply to…").
- **Search before Jeff is a real speed lever.** Checking only the top 3
  chunks search picks costs about 5× fewer Jeff checks, for −4 points of
  recall.

### Verdict bands, chosen on one half and tested on the other

`eval/bands.py`: contracts were split alternately by title. The bands were
chosen on half A ("not found" may hide at most 2% of clauses; "found" must
be at least 90% right), then applied unchanged to half B.

| Verdict (held-out half B, 51 contracts, 612 decisions) | Decisions | Really present |
|---|---|---|
| **found**, P ≥ 0.91 | 156 | 92.3% |
| **check**, 0.15 ≤ P < 0.91 | 266 | 22.2% |
| **not found**, P < 0.15 | 190 | 0.5%: **1 of 204** real clauses |

**In practice.** Of 12 questions per contract, about 3 come back "found",
4 "not found", and 5 "check" for the lawyer to look at, of which about 1 in
5 is real. Misses are rare; the cost is review time.

**Speed.**
- Each question costs about 0.25 s per chunk; asking several in one call
  saves nothing.
- A 15K-character contract with all 12 questions took 14.5 s end to end.
- The 102 contracts took about 85 minutes.

## Phase 2 (first cut): pseudonymisation, rules only

`eval/pseudo_eval.py`: a party name counts as leaked if any part of CUAD's
"Parties" label survives in the redacted text.

| Split | Contracts | Labelled party names | Caught |
|---|---|---|---|
| test: the rules were fixed while looking at these | 102 | 439 | 89.5% |
| **train: never looked at** | 408 | 1,606 | **86.3%** |

**Real misses.**
- People named with no title ("ADAM D. PORTNOY").
- Short forms defined deep in the body ("THI", "Premier").
- Names with no company suffix ("Thrivent Financial for Lutherans").

Some counted "leaks" are role words in the labels ("Servicer", "Party B"),
so 86.3% is a conservative figure.

**What this means.** The rules are useful, but nowhere near safe enough to
send text without the lawyer reading it. That matches the design: sending
is always a human click. Next is a real name finder (Presidio or GLiNER) and
a Jeff leftover check.

### Question wording: inconclusive so far

The run with the clause description added to each question stopped after
7 contracts. Jeff timed out while other apps were using the GPU. On those 7 contracts the "described" wording scored recall 93.8%
and AUC 0.944, about the same as "short", but 7 contracts is too few to
call. To resume when the GPU is free:
`python3 eval/cuad_eval.py score --wording described --docs 34`, then
`report --docs 34` for each wording.

## Not measured yet

- The "described" question wording on enough contracts (see above).
- Contradictions (ContractNLI).
- An adapter trained on CUAD for the weak clause types.
- Performance on UK-drafted contracts. CUAD is US SEC filings.
