"""Data paths of the UI, relative to the repo root (Streamlit runs there)."""

from pathlib import Path

PRESETS = Path("data/input/presets")
GALLERY = Path("data/gallery")  # one report per preset, grows by commit only (ADR 0023)
