# legal-screen: the idea, in plain English

*For lawyers and anyone else who wants to know what this is, whether it
works, and what it would take to try it. No technical knowledge needed. The
technical detail is in [how-it-works.md](how-it-works.md).*

## The problem

AI can now read a contract and tell you what is in it. But the most capable
AI models are usually used as cloud services, so using them means sending
client documents off your premises. For many lawyers that is a
confidentiality problem before it is anything else.

The alternative is running AI on your own computer, which many people
assume needs expensive, specialist hardware. Part of what this project
tests is how far an ordinary PC gets.

This project asks whether there is a middle way:

> Can an **ordinary PC** (a normal gaming-class machine) check a contract
> for the things a lawyer looks for, **without the document leaving the
> computer**, and send only the hard parts to a more powerful cloud AI,
> **with names stripped out and only when the lawyer says so**?

## The idea

### 1. Most of the work happens on your computer

A contract review often starts with a checklist. Is there a limitation of
liability? Governing law? An automatic renewal? A change-of-control
clause? Those are **yes/no questions about the text**, and yes/no questions
don't need a giant AI.

[Jeff](https://github.com/firelex/jeff) is a small, free, open-source AI
model built for exactly that kind of question. It doesn't write essays. It
reads a passage and answers a fixed question with a confidence score from
0 to 1. It is small enough to run on an ordinary graphics card.

The tool works like this:

1. **Split the contract** into passages of about a page each.
2. **Search it** the old-fashioned way, with keywords and phrases ("governed
   by", "assign", "liability shall not exceed"), to find where to look
   first.
3. **Ask Jeff each checklist question about every passage.** Every passage
   is checked, not a sample, because "is X anywhere in this contract?"
   needs the whole thing read.
4. **Report back** for each question:
   - **found**, with the exact wording and where it is
   - **check**, meaning Jeff isn't sure, so a lawyer should look
   - **not found**, meaning no passage looked like it. That is not proof
     the clause is absent; see below.

In these four steps the passages go only to the Jeff server on the same
computer: by default the tool refuses any other address. Overriding that
takes a deliberate setting, and Jeff is software you run yourself; see
[privacy.md](privacy.md).

### 2. The hard parts can go to a cloud AI, with names removed and your approval

Some questions are beyond a small model. Two examples: "does anything in
this contract contradict the payment terms?", and "what does this clause
actually mean for my client?" Those are where a frontier model (such as
Anthropic's Claude) earns its keep. The plan for those:

1. **Pseudonymise on your computer.** Party names, people, addresses,
   amounts and dates are replaced with placeholders such as `⟦PARTY_A⟧`
   and `⟦AMOUNT_1⟧`. The key that maps them back stays on your machine.
2. **Show you exactly what would be sent:** the "outbox". Nothing is sent
   automatically, ever.
3. **Send only on your click,** and only the passages needed.
4. **Put the real names back** into the answer, on your computer.

The first step exists today, as a first version. Steps 2 to 4 are planned,
not built (see [Status](#status)).

### 3. Maybe you don't need the clever bit at all

Before building a cloud step, it is worth checking whether the firm already
accepts a cloud route. Some firms use AI through their own cloud provider
in a UK data centre, or under contract terms with no data retention. If the
firm has approved sending the relevant documents to such a service, the
local tool is still useful for speed and triage, and pseudonymising *may*
become a convenience rather than a necessity. That depends on the firm's
policy, the client's instructions and the documents themselves, and is for
the firm and client to decide, not the tool.

## Does it work? What has been measured

The test used [CUAD](https://www.atticusprojectai.org/cuad), a public
collection of real commercial contracts (filed with the US SEC) in which
**lawyers annotated clauses** of 41 types. We checked 12 of those types
across the 102 contracts set aside for testing. The test PC was a laptop
with an 8 GB NVIDIA graphics card. No client data was involved.

Each question asks whether a contract has that kind of clause, so the
measure counts contract-and-clause-type pairs. A contract with two
liability caps counts once.

Here "spotted" means a passage scored 0.5 or more: the halfway mark, not
the stricter 0.91 needed for the **found** verdict below.

| How the clauses were looked for | Clause types present that were spotted (P ≥ 0.5) | Points to the right passage |
|---|---|---|
| Keyword search alone | 82.7% | – |
| **Jeff checking every passage** | **94.7%** | 91% of the time |

**What a lawyer would see.** The cut-offs for the three verdicts were set
on half of the contracts, then tested on the other half. On that second
half:

| Verdict | How often it came up | How often it was right |
|---|---|---|
| **found** | about 3 of every 12 questions | 92% of the time the clause really was there |
| **check** | about 5 of every 12 | about 1 in 5 was a real clause |
| **not found** | about 4 of every 12 | 1 real clause in 204 ended up here |

In short, **it rarely misses a clause**, and the price is review time on
the "check" items.

| Strong | Weak |
|---|---|
| Governing law, anti-assignment, cap on liability, renewal, insurance, audit rights | Uncapped liability (69% spotted at P ≥ 0.5), change of control (73%), liquidated damages (71%) |

Why these three are weaker isn't known yet. One guess to test: uncapped
liability is usually written as an *exception* ("the cap does not apply
to…"), which may be harder for a small model to spot. They are the obvious
next thing to improve.

**Speed.**
- A 5-page contract (about 15,000 characters) with all 12 questions takes
  about 15 seconds when the graphics card isn't busy with anything else.
- Each extra question adds about a quarter of a second per passage.

**Removing names.** The first version uses rules only, with no AI. Across
408 contracts it had never seen, it caught **86% of the party names** the
lawyers had marked, so roughly 1 in 7 got through. Examples of what it
misses:
- people named without a title ("Adam D. Portnoy")
- short nicknames for a company defined deep in the contract
- names with no company suffix ("Thrivent Financial for Lutherans")

That is useful, but **not safe to send without a person reading it first**,
and the design already assumes that.

An example of real output, on a public contract, is in
[example-report.md](example-report.md). Every figure here comes from
[RESULTS.md](../RESULTS.md).

## What it does not do (yet)

- **It is not legal advice and not a lawyer.** It is a screening aid. Every
  result needs a lawyer's eye, especially "not found".
- **It has only been tested on US contracts.** UK-drafted contracts use
  different wording ("shall not be liable save in respect of…"), and
  haven't been tested.
- **It doesn't check for contradictions yet.** A first step is planned
  using ContractNLI, a public set of NDAs labelled for whether each contract
  supports, contradicts or doesn't mention a given statement. That is
  related to, but not the same as, finding clauses that contradict each
  other, which would need its own test set.
- **It doesn't read PDFs yet.** Save as Word (.docx) or plain text first.
- **There's no point-and-click app yet.** It runs from a command line. A
  simple local window is planned.
- **The checklist is fixed** at 12 clause types for now. A lawyer's own
  checklist is the obvious next step.

## Status

| Part | State |
|---|---|
| Checking a contract for 12 clause types, locally | **Built and measured** |
| Verdict bands (found, check, not found) | **Built, set on half the test contracts and tested on the other half** |
| Refusing to send text off the computer | **Built and tested** |
| Pseudonymising (rules only) | **Built, first version, measured** |
| Better name-finding (people's names) | Planned |
| Contradiction checking | Planned |
| The outbox and cloud step, with your approval | Planned |
| A simple app window | Planned |
| UK contracts | Not tested |

The full plan is in [PLAN.md](../PLAN.md).

## What a pilot would need

If a practising lawyer wanted to try this:

1. **Their checklist.** Which clauses and issues matter most in their
   work? That decides the questions.
2. **Their PC's spec,** especially the graphics card. An NVIDIA card with
   8 GB worked here. Jeff also supports Apple-silicon Macs, but this tool
   hasn't been tried on one.
3. **A few documents to try it on,** on their own machine, local only. The
   honest test is whether it finds what they would have found.
4. **Whether their firm already accepts a cloud route** (see part 3 above).

Questions and answers: [faq.md](faq.md).
