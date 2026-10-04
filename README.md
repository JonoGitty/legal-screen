# legal-screen (working name)

Check legal documents for what's in them, and what contradicts what, on an
ordinary PC. Nothing leaves the machine unless the lawyer approves exactly
what is sent.

Started in October 2026, after a conversation with a lawyer about two concerns:
- **Confidentiality:** client documents shouldn't go to a cloud AI by default.
- **Hardware:** a normal gaming-class PC should be enough. Nobody wants to
  buy a £15K workstation to run AI locally.

## The idea

```
document ─► chunks (~4K chars) ─► 1. deterministic search ─► 2. Jeff (local) ─► results table
                                     keywords, regex,            fixed yes/no            question · where ·
                                     ranked text search          questions + P(yes)      confidence · exact quote
                                                                        │
                                                         hard questions only (contradictions,
                                                         interpretation)
                                                                        ▼
                                     3. pseudonymise locally ─► lawyer sees the outbox ─► cloud model (e.g. Claude)
                                        names → [PARTY_A]…         and clicks send          on redacted text only
                                        mapping kept locally                                     │
                                                                        results re-identified locally ◄┘
```

1. **Deterministic search.** Keywords, regex and ranked text search find
   candidate passages ("indemnif", "governing law", "liabilit"). They are
   cheap and explainable, and they decide what Jeff checks *first*. They
   never decide what it *skips*: "is X anywhere?" needs every chunk checked.
2. **Jeff:** an open-source 0.8B "System One" model
   ([firelex/jeff](https://github.com/firelex/jeff)). It answers fixed
   questions with a probability instead of writing prose, and runs locally.
   - It is checklist-shaped: "Does this passage contain a
     limitation-of-liability clause?"
   - Measured on an 8 GB laptop GPU (RTX 3070 Ti): about 140 ms per
     decision on 1.5K characters, and about 270 ms on 4K.
   - Not Jev: Jev is TypeSafe's hosted equivalent, so documents would leave
     the machine.
3. **Results.** Each question comes back with where it was found, how
   confident Jeff is, and the exact quote. Unsure answers are shown as
   unsure. **"Not found" is never presented as "not in the document".**
   Missing a clause is the costly error, so thresholds are set for recall.
4. **Escalation (optional).** For what a 0.8B model is weak at, such as
   contradictions between clauses and interpretation, the passages
   concerned are pseudonymised locally and shown to the lawyer, and sent
   only on their click. The answer is mapped back to the real names locally.

## Pseudonymising locally (mostly not Jeff)

Jeff answers questions; it doesn't find and replace names. Finding what to
redact is a span-finding job:

1. **The contract names its own parties.** The parties and definitions
   clauses ("ACME Ltd (the "Supplier")") give the names and their variants.
   Replace every occurrence.
2. **Pattern rules for things with a shape:**
   - contact details: emails, phone numbers, postcodes
   - identifiers: company and registration numbers, bank details, case
     references
   - amounts and dates
3. **A local name-finder for the rest:** people, organisations, places.
   Off-the-shelf open tools do this on a CPU, e.g. Microsoft Presidio (rules
   plus spaCy models) or a small zero-shot entity model such as GLiNER.
   Choose by measuring them (PLAN.md, phase 2).
4. **A consistent, reversible mapping kept on the PC.** The same entity
   always gets the same placeholder, so the cloud model's answer still
   makes sense and can be mapped back.
5. **Jeff as the checker afterwards.** It asks of each redacted passage:
   "Does this still identify a person, company or the deal?" Anything
   flagged goes to the lawyer.

**The limit:** indirect identifiers. A unique deal fact can identify a
client with every name removed. That is why sending is always a human
decision, never automatic.

## Use it

Needs Python 3.10+ (standard library only) and a local Jeff server on
:8765. Jeff's own README covers setup
([firelex/jeff](https://github.com/firelex/jeff)). On a CUDA machine,
[Patchwork Harness](https://github.com/JonoGitty/patchwork-harness)'s
`scripts/jeff/serve.sh` starts it in one command.

```bash
python3 eval/get_cuad.py                                   # the public test contracts (CUAD, ~18 MB)
python3 -m legal_screen contract.docx --html report.html   # check it (local only)
python3 -m legal_screen redact contract.txt                # pseudonymise it; the mapping stays beside it
python3 -m unittest discover -s tests                      # tests, no Jeff needed
```

## Status (4 Oct 2026)

- **Phase 1 measured.** On 102 lawyer-labelled public contracts, Jeff on an
  8 GB laptop GPU found 94.7% of the clauses that were there (AUC 0.94),
  against 82.7% for keywords.
- **Bands tested on held-out contracts.** "Found" was right 92% of the time,
  and "not found" hid 1 real clause in 204.
- **Weak spots:** uncapped liability, change of control, liquidated damages.
- **Pseudonymiser v0 (rules)** catches 86% of party names on 408 unseen
  contracts. It is useful, and not safe without the lawyer reading.

Full numbers: [RESULTS.md](RESULTS.md). Plan: [PLAN.md](PLAN.md).

## Not legal advice

This is a screening aid, not a lawyer. It can miss a clause ("not found"
is not proof of absence), and it can flag one that isn't there. The
pseudonymiser misses some names. Every result needs a lawyer's review, and
nothing should leave a machine without a person reading exactly what is
sent.

## Credits

- **[Jeff](https://github.com/firelex/jeff)** by Mathias Strasser: MIT
  code, Apache 2.0 weights. It is not bundled here; you run your own Jeff
  server.
- **[CUAD](https://www.atticusprojectai.org/cuad)**, the Contract
  Understanding Atticus Dataset, by The Atticus Project (Hendrycks, Burns,
  Chen and Ball, NeurIPS 2021), CC BY 4.0. It is downloaded by
  `eval/get_cuad.py`, not redistributed. The clause names and descriptions
  in `legal_screen/checklist.py` and two short passages in `tests/` come
  from it.

## Licence

[Apache 2.0](LICENSE). See [NOTICE](NOTICE) for the third-party credits.
