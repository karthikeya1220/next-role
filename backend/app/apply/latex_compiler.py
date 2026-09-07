"""LaTeX → PDF compiler.

Compiles .tex files server-side using lualatex (CV) or xelatex (cover letter).
Returns the raw PDF bytes or raises RuntimeError if TeX is unavailable.
"""

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

TexEngine = Literal["lualatex", "xelatex"]


def _find_engine(engine: TexEngine) -> str:
    """Return the full path to *engine* or raise RuntimeError."""
    path = shutil.which(engine)
    if not path:
        raise RuntimeError(
            f"{engine} not found. Install a TeX distribution:\n"
            f"  macOS: brew install --cask mactex-no-gui\n"
            f"  Linux: apt-get install texlive-full\n"
            f"  Minimal: https://yihui.org/tinytex/"
        )
    return path


def compile_latex(tex_source: str, engine: TexEngine = "lualatex") -> bytes:
    """Compile *tex_source* and return the PDF bytes.

    Runs the engine twice to resolve cross-references, in a temp directory
    that is cleaned up automatically.
    """
    exe = _find_engine(engine)
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = Path(tmpdir) / "document.tex"
        tex_path.write_text(tex_source, encoding="utf-8")

        for run in range(2):
            result = subprocess.run(
                [exe, "-interaction=nonstopmode", "-halt-on-error", "document.tex"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                log_tail = result.stdout[-3000:] + result.stderr[-1000:]
                raise RuntimeError(
                    f"{engine} failed (run {run + 1}):\n{log_tail}"
                )

        pdf_path = Path(tmpdir) / "document.pdf"
        if not pdf_path.exists():
            raise RuntimeError(f"{engine} ran successfully but produced no PDF.")
        return pdf_path.read_bytes()


def is_latex_available() -> dict:
    """Check which TeX engines are available."""
    return {
        "lualatex": shutil.which("lualatex") is not None,
        "xelatex": shutil.which("xelatex") is not None,
    }
