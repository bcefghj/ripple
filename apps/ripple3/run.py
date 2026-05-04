"""Ripple 3.0 — entry point.

Usage:
  python run.py              — show CLI help
  python run.py ui           — launch Gradio Web UI
  python run.py flow <domain> — run full pipeline
  python run.py radar <domain> — scan domain ecosystem
  python run.py idea <domain> — generate topic ideas
  ...
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cli.main import app

if __name__ == "__main__":
    app()
