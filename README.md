# legal-screen

**Check a contract for the clauses a lawyer looks for, on an ordinary PC,
without the document leaving the computer.**

A small open-source AI model ([Jeff](https://github.com/firelex/jeff))
answers checklist questions about each passage: is there a limitation of
liability? governing law? an automatic renewal? For each one you get back
**found**, **check** or **not found**, with the exact wording and where it
is. It runs on a normal gaming-class graphics card. Measured on 102 real
contracts labelled by lawyers, it scored **94.7%** of the clause types
present at 0.5 or above (the halfway mark; the stricter **found** verdict
needs 0.91).

> **New here?** Start with the plain-English **[overview](docs/overview.md)**:
> the idea, what has been measured, and what it can't do yet.

## In one picture

```
your contract ─► split into passages ─► keyword search ─► Jeff, on your PC ─► report
                                         (where to look)   12 yes/no questions   found · check · not found
                                                           × every passage       + the exact wording
                                                                │
                                   planned: hard questions only ▼
                     names swapped for ⟦PARTY_A⟧… ─► you read the outbox ─► cloud AI ─► names put back
                     on your PC                       and click send                    on your PC
```

## What has been measured

On the 102 test contracts of [CUAD](https://www.atticusprojectai.org/cuad)
(The Atticus Project), with 12 clause types and a laptop with an 8 GB
graphics card:

| | Clause types present that scored ≥ 0.5 | AUC |
|---|---|---|
| Keyword search alone | 82.7% | 0.82 |
| **Jeff, checking every passage** | **94.7%** | **0.94** |

**The verdicts on held-out contracts** (the cut-offs were set on the other
half of the contracts):
Each figure counts contract-and-clause-type pairs: "does this contract have
a liability cap?".

- **found** was right 92% of the time
- **check** turned out to be real about 1 in 5 times
- **not found** hid 1 real clause in 204

**Strong:** governing law, assignment, caps on liability, renewal,
insurance and audit rights. **Weak:** uncapped liability, change of control
and liquidated damages.

All the figures, and how they were produced: **[RESULTS.md](RESULTS.md)**.
A real report on a public contract: **[example](docs/example-report.md)**.

## Status

| | |
|---|---|
| Clause checking (12 types), local only | **built and measured** |
| Refusing to send text off the computer | **built and tested** |
| Pseudonymising: party names, contacts, amounts, dates | **first version.** Catches 86% of party names, so not safe without a person reading it |
| People's names, contradiction checking, the outbox and cloud step, a simple app window | planned ([PLAN.md](PLAN.md)) |
| PDF input | not supported yet (save as .docx or .txt) |
| UK-drafted contracts, Macs | not tested yet |

## Try it

You need a local Jeff server; see **[setup](docs/setup.md)**.
legal-screen itself needs Python 3.10+ and nothing else.

```bash
python3 -m legal_screen contract.docx --html report.html   # check a contract (local only)
python3 -m legal_screen redact contract.txt                # pseudonymise it; the name mapping stays beside it
python3 -m unittest discover -s tests                      # 14 tests, no Jeff needed
```

## Documentation

| | |
|---|---|
| [Overview](docs/overview.md) | The idea in plain English: problem, approach, results, limits, and what a pilot would need |
| [Example report](docs/example-report.md) | Real output on a public contract, checked against the lawyers' labels |
| [Privacy](docs/privacy.md) | What stays local, what is enforced in code, and what isn't guaranteed |
| [How it works](docs/how-it-works.md) | Chunking, search, Jeff, verdict bands, quoting, the pseudonymiser, the evaluation |
| [Setup](docs/setup.md) | Hardware, installing Jeff, running the checker, reproducing the numbers |
| [FAQ](docs/faq.md) | Short answers to the obvious questions |
| [Results](RESULTS.md) · [Plan](PLAN.md) · [Changelog](CHANGELOG.md) | The numbers, the roadmap, the versions |

## Not legal advice

This is a screening aid, not a lawyer. It can miss a clause ("not found"
is not proof of absence), and it can flag one that isn't there. The
pseudonymiser misses some names. Every result needs a lawyer's review, and
nothing should leave a machine without a person reading exactly what is
sent.

## Credits

- **[Jeff](https://github.com/firelex/jeff)** by Mathias Strasser: MIT
  code, Apache 2.0 weights. It is not bundled; you run your own Jeff
  server.
- **[CUAD](https://www.atticusprojectai.org/cuad)**, the Contract
  Understanding Atticus Dataset, by The Atticus Project (Hendrycks, Burns,
  Chen and Ball, NeurIPS 2021), CC BY 4.0. It is downloaded by
  `eval/get_cuad.py`, not redistributed. The clause names, descriptions
  and two short test passages come from it.

## Licence

[Apache 2.0](LICENSE). See [NOTICE](NOTICE) for the third-party credits.
