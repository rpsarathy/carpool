# carpool

A modern Python project scaffold using the src/ layout.

## Features
- src/ layout for import safety
- pyproject.toml (PEP 621 with setuptools)
- Simple CLI (`python -m carpool` or `carpool` after install)
- pytest test suite

## Quickstart

1) Create and activate a virtual environment

   macOS/Linux:
   python3 -m venv .venv
   source .venv/bin/activate

   Windows (PowerShell):
   py -m venv .venv
   .venv\Scripts\Activate.ps1

2) Install the project in editable mode with dev tools

   pip install -U pip
   pip install -e .[dev]

3) Run the tests

   pytest -q

4) Use the CLI

   carpool --help
   # or without installing
   python -m carpool --help

## Project Structure

c  carpool/
├─ .gitignore
├─ pyproject.toml
├─ README.md
├─ pytest.ini
├─ src/
│  └─ carpool/
│     ├─ __init__.py
│     ├─ __main__.py
│     └─ cli.py
└─ tests/
   └─ test_sanity.py

## Releasing (optional)
- Build: `python -m build`
- Publish: `python -m twine upload dist/*`
