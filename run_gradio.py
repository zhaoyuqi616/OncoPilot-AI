import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from app.gradio_ui import build_ui

if __name__ == "__main__":
    build_ui().launch(server_name="127.0.0.1", server_port=7860)
