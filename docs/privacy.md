# Privacy and confidentiality

What this tool does with a document, what is enforced in code, and what
isn't.

## What stays on your computer

**The checker** (`python3 -m legal_screen <contract>`):
- **Reads the file locally.** A .docx is unzipped with Python's standard
  library, so neither Word nor an upload is involved.
- **Sends passages only to a Jeff server on the same computer.**
- **Writes its report to your screen,** and to a local HTML file if you
  ask for one.

**The redactor** (`python3 -m legal_screen redact <contract>`):
- **Makes no network calls at all.** It is rules only.
- **Writes the redacted text and the mapping file beside the original.**
  The mapping holds the real names, so keep it on the machine.

Nothing is sent to a cloud AI. That step is planned, not built; see
[overview.md](overview.md).

## Enforced in code (`legal_screen/jeff.py`)

Each of these has a test, and each test was checked to fail with the
protection removed:

| Protection | What it prevents |
|---|---|
| **Local addresses only.** A Jeff address whose host isn't `localhost`, `127.0.0.1` or `::1` is refused *before anything is sent* | Pointing the tool, by mistake or design, at a server somewhere else |
| **No redirects followed** | A local server bouncing the text to another address |
| **Proxy settings ignored** (`HTTP_PROXY` and similar) | A proxy configured on the machine seeing the text |

To use a Jeff server on another machine, you must deliberately set
`LEGAL_SCREEN_ALLOW_REMOTE_JEFF=1`. That machine then sees the text, so it
should be one you control.

**The only other network call in the code** is `eval/get_cuad.py`, which
downloads the public test contracts. It sends nothing.

## What is NOT guaranteed

- **Pseudonymising is incomplete.** On public contracts it caught 86% of
  party names. It misses:
  - people named without a title
  - short nicknames defined deep in a contract
  - names with no company suffix

  It also cannot see **indirect identifiers**: a unique deal, a distinctive
  asset, or a date and place that together point to a client. So redacted
  text must be read by a person before it goes anywhere. The planned
  "outbox" exists for exactly that.
- **The machine itself.** The tool doesn't encrypt anything, and it relies
  on the computer being yours and secure.
- **Jeff's server.** Jeff is third-party open-source software (firelex/jeff)
  that you run yourself. This tool doesn't control what that server logs.
  Out of the box it runs on your machine, with no account or key.
- **Your firm's rules.** Whether a given workflow is acceptable under your
  professional obligations and your firm's policies is for you and your
  firm to decide. This tool is designed to make the local-first choice
  practical, not to make that judgement.

## For the planned cloud step

The design rule: **nothing leaves the machine without a person reading
exactly what is sent and clicking send.**
- Only the passages needed for the question go, pseudonymised.
- The mapping back to real names never leaves the machine.
- Every send is logged locally: what went, when, and on whose approval.
