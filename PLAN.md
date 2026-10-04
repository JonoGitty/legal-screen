# Plan

Each phase has to prove itself before the next one starts. Every number
comes from a real run, and each measure is scored against a trivial
baseline (always "no", or keywords alone), not just reported as accuracy.

## Phase 1: Can a gaming PC find clauses? Public data only, $0

**Status, 4 Oct: measured on CUAD.** The answer is yes for most clause types. See RESULTS.md. Still to do: the "described" wording, ContractNLI (contradictions), and an adapter for the weak types.

**Data.** Contracts that lawyers have already labelled, so no client data
and no model-made labels:
- **CUAD** (The Atticus Project): about 500 commercial contracts, with 41
  clause types marked by lawyers. Tests "is clause X in here, and where?".
- **ContractNLI** (Stanford): NDAs, each labelled *entailed*, *contradicted*
  or *not mentioned* for a fixed list of statements. Tests "does the
  contract support or contradict this statement?". That is close to, but not
  the same as, clauses contradicting each other; for that, see the
  simulated contracts below.
- Check both licences before any data is copied anywhere.

**Arms**, on the same chunks:
1. Keywords, regex and ranked text search alone.
2. Jeff alone, zero-shot, with the question wording tried both ways. On
   an earlier task (grounding claims in coding-agent output), wording alone
   moved Jeff from 78% to 93.7%.
3. The cascade: search sets the order, Jeff decides.

**Scoring.** `eval/cuad_eval.py`, using the same method as
[Patchwork Harness](https://github.com/JonoGitty/patchwork-harness)'s
`eval classifier`. It gives:
- accuracy against the constant baseline
- **recall on "present"**, the number that matters
- AUC and calibration (ECE)
- speed per document on this laptop

Split by contract, so no contract is in both training and test data.

**Decides.** Whether zero-shot Jeff is good enough, needs an adapter
trained on CUAD, or is the wrong tool.

## Phase 2: Pseudonymisation that can be trusted

**Status, 4 Oct: v0 with rules only.** It catches 86.3% of party names on 408 unseen contracts. Still to do: Presidio or GLiNER for people, and the Jeff leftover check.

- Compare these on the public contracts, whose party names are known:
  - definitions-clause extraction
  - pattern rules
  - Presidio and GLiNER
  - each of the above with a Jeff leftover check
- Measure recall on names (missed names are the costly error) and how
  readable the redacted text stays.
- Build the reversible mapping, and a test that a round trip restores the
  original exactly.

## Phase 3: The gateway

- **Outbox preview.** The lawyer sees exactly what would be sent, and sends
  it with one click. Nothing is ever sent automatically.
- **The cloud step.** Contradictions and interpretation on redacted
  passages, with the results re-identified locally.
- **An audit log** of what was sent, when, and on whose approval.

## Later: stress-test on many simulated contracts

Use Patchwork Harness and a frontier model to generate large numbers of
synthetic contracts, with labels known because each is built to order.
They would cover what CUAD can't:
- UK drafting
- clauses phrased as exceptions ("the cap does not apply to…")
- planted clauses beside near-miss decoys
- contradictions placed on purpose
- long and messy documents

Synthetic text can be easier than real drafting, so real labelled contracts
stay the yardstick. Synthetic sets find blind spots; real sets give the
number.

## Alongside: a simple app window

The checker runs from a command line, which is no good for most lawyers.
The plan is deliberately *not* a full web app:
- one command opens a page served from the lawyer's own computer
- no framework, no internet, nothing to install beyond Python
- drop a contract in and get the report, with the redact screen doubling
  as the outbox preview
- reports saved as HTML, plus plain Markdown and JSON for anything else to
  read

## Phase 4: Pilot with a practising lawyer

- On the lawyer's own PC, with their own documents, local-only first.
- Their real checklist decides the questions.
- Before this phase:
  - Confirm the PC spec, especially the GPU and its VRAM.
  - Check whether the firm already accepts a cloud route, such as Claude
    through a UK-region cloud provider, or contract terms with no data
    retention. If it does, the gateway is a convenience, not a necessity.

## Open questions

- The pilot lawyer's checklist: which clauses and issues matter most?
- Their hardware.
- Who owns this, and is it a product or a tool for one firm?
- A real name for the project.
