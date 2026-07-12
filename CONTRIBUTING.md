# Contributing to Auris

Thanks for your interest! Auris is small on purpose — most contributions fit in
a single file. *(Sinta-se à vontade para abrir issues e PRs em português.)*

## Getting set up

```bash
git clone https://github.com/abrahao-dev/auris.git
cd auris
python -m venv .venv
# Windows:  .venv\Scripts\activate      Linux: source .venv/bin/activate
pip install -r requirements.txt

python -m auris --cli        # quickest way to see live decoded advertisements
python tests/test_protocol.py   # or: pip install pytest && pytest
```

Python 3.10+ and a Bluetooth LE adapter are required to run the app; the
decoder tests run anywhere.

## What to contribute

- **Bug reports** — include your OS, earbud model, and if possible a few lines
  of `python -m auris --cli` output (it contains no personal data — just the
  battery payload).
- **New model ids** — if your device shows up as *Unknown*, grab the model id
  from `--cli` output and add it to `auris/models.py` with a test.
- **Decoder improvements** — `auris/protocol.py` is fully unit-tested; any
  change there should come with a test in `tests/test_protocol.py` built from a
  hand-crafted advertisement.
- **Translations** — READMEs exist in English and Portuguese; fixes and new
  languages are welcome.
- **Platform quirks** — tray behavior differs across desktops (GNOME, KDE,
  Windows 10 vs 11); reports and fixes are valuable.

## Pull request workflow

1. Fork and create a branch from `main`.
2. Keep the change focused — one topic per PR.
3. Run the tests (`pytest` or `python tests/test_protocol.py`).
4. If you changed user-visible behavior, add a line to `CHANGELOG.md` under an
   *Unreleased* heading.
5. Open the PR — a short description of *why* beats a long description of *what*.

There is no linter gate; just match the style of the surrounding code
(type hints, small modules, no new dependencies without discussion).

## Scope guardrails

Auris deliberately only **listens** to BLE advertisements. PRs that make it
pair, connect, or transmit will need prior discussion in an issue — that is a
different threat/permission model and a jump in complexity.

## Questions

Open a [discussion or issue](https://github.com/abrahao-dev/auris/issues) —
there are no dumb questions about reverse-engineered protocols.
