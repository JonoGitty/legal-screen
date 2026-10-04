# Setup

Two parts: **Jeff**, the small AI model that runs as a local server, and
**legal-screen**, this tool, which talks to it.

## What you need

- **A graphics card.**
  - **Tested:** an NVIDIA RTX 3070 Ti Laptop GPU with 8 GB, under Ubuntu
    in WSL2 on Windows. With Jeff loaded, the card showed about 1.4 GB in
    use.
  - **Untested here:** Jeff's README also documents Apple-silicon Macs
    (MLX), but legal-screen hasn't been tried on one, or on native
    Windows Python.
- **Python 3.10 or newer** for legal-screen, which uses only the standard
  library, and Python 3.12 or newer for Jeff.
- **About 1.7 GB of disk** for Jeff's model weights.
- **An internet connection for setup only:** to install Jeff, download its
  weights, and optionally download the public test contracts. Checking a
  contract needs no internet.

## 1. Install and start Jeff

Follow [Jeff's own README](https://github.com/firelex/jeff#quick-start).
legal-screen needs only the base model, so you can skip the adapters. In
outline, on an NVIDIA machine:

```bash
git clone https://github.com/firelex/jeff && cd jeff
uv sync --no-default-groups --extra lora --extra cuda     # Jeff's README: --extra mac on Apple silicon
uv run --no-default-groups hf download mstrasser/Jeff-Qwen3.5-0.8B --revision v1.2 --local-dir Jeff-Qwen3.5-0.8B-v1.2
JEFF_CHECKPOINT=Jeff-Qwen3.5-0.8B-v1.2 PORT=8765 uv run --no-default-groups --extra lora jeff-serve
```

These are Jeff's documented commands with the adapter steps left out, because
`JEFF_ADAPTERS` is optional. They are not the exact commands tested here.

**Check it is up:** `curl http://127.0.0.1:8765/health` should say
`"status":"ready"`.

**What was actually tested here:**
- A plain virtualenv on WSL2 with torch 2.8.0 (CUDA 12.8), torchvision
  0.23 and transformers 5.17.
- Jeff pins a newer torch, but serving worked with this combination.
- torchvision was needed even for text-only use: the server fails at
  start-up without it.

## 2. Get legal-screen

```bash
git clone https://github.com/JonoGitty/legal-screen && cd legal-screen
python3 -m unittest discover -s tests       # 14 tests; no Jeff or network needed
```

There is nothing to install. It uses Python's standard library only.

## 3. Check a contract

```bash
python3 -m legal_screen contract.docx --html report.html
```

- A table is printed. The HTML version is written to `report.html`, to
  open in a browser.
- Accepted formats: `.docx` and `.txt`. A PDF needs saving as Word or text
  first.
- If Jeff isn't running, it says so, and nothing is sent anywhere.

## 4. Redact a contract (optional)

```bash
python3 -m legal_screen redact contract.txt
```

This writes `contract.redacted.txt`, and `contract.redacted.mapping.json`,
which holds the real names. **Read the redacted text before using it
anywhere**; see [privacy.md](privacy.md).

## 5. Reproduce the measurements (optional)

```bash
python3 eval/get_cuad.py                      # public contracts, ~18 MB
python3 eval/cuad_eval.py score               # ~85 min on an 8 GB laptop GPU; resumable
python3 eval/cuad_eval.py report
python3 eval/bands.py
python3 eval/pseudo_eval.py train             # no GPU needed
```

## Settings

| Variable | Default | Meaning |
|---|---|---|
| `JEFF_URL` | `http://127.0.0.1:8765` | Where Jeff is. Must be on this machine; see below |
| `JEFF_MODEL` | `jeff-qwen3.5-0.8b` | The model name Jeff reports |
| `LEGAL_SCREEN_ALLOW_REMOTE_JEFF` | unset | Set to `1` to allow a Jeff server on another machine. That machine then sees the contract text |

## If something goes wrong

| Message | What it means |
|---|---|
| "Jeff is not reachable" | Start Jeff (step 1) and check `/health` |
| "Jeff timed out … is something else using the GPU?" | Another app (a game, another AI tool) is busy on the graphics card. Close it or wait |
| "refusing to send contract text to …" | `JEFF_URL` points away from this computer. That is deliberate; see [privacy.md](privacy.md) |
| "PDF is not read yet" | Save the PDF as .docx or .txt first |
