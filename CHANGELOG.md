# Changelog

## [0.1.0] — 2026-10-05

First public version.

### Checker
- **`python3 -m legal_screen <contract>`**, with an optional `--html`
  report. It checks a .txt or .docx contract for 12 clause types:
  - the contract is split into overlapping passages
  - a keyword search picks where to look first and which sentence to quote
  - a local Jeff server answers each question about every passage
- **Verdicts:**
  - **found**, P ≥ 0.91
  - **check**, 0.15–0.91
  - **not found**, P < 0.15 in every passage. It reports the highest P
    seen and never says "absent".
- **Measured on the CUAD test split** (102 contracts): 94.7% of clause
  types present scored 0.5 or above, counted per contract and clause type,
  against 82.7% for keywords. On held-out contracts,
  "found" was right 92% of the time and "not found" hid 1 of 204 clauses.

### Pseudonymiser
- **`python3 -m legal_screen redact <contract>`**, rules only. It replaces
  party names and their short forms, organisations, people with a title,
  emails, web addresses, phone numbers, amounts, dates and addresses with
  consistent placeholders. The mapping back is kept locally.
- **Measured:** it catches 86.3% of labelled party names on 408 unseen
  contracts.

### Privacy
- Contract text goes only to a Jeff server on the same machine.
  - Non-local addresses are refused before sending, unless
    `LEGAL_SCREEN_ALLOW_REMOTE_JEFF=1` is set.
  - Redirects are not followed.
  - Proxy settings are ignored.

### Evaluation and tests
- `eval/`: download CUAD, score clause finding (three approaches against
  the constant baseline), set and test the verdict bands, and measure name
  leaks.
- 14 unit tests, with no Jeff or network needed.
