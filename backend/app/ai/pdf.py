"""Render a resume to an ATS-safe PDF.

Everything here is a deliberate parseability choice, not a style choice:

* **Single column.** Multi-column layouts are the number one cause of garbled ATS
  parsing — extractors read in text order and interleave the columns.
* **Real text, no images, no tables, no text boxes.** A resume rendered as
  graphics parses as nothing at all.
* **Standard section headings** ("Experience", "Projects", "Skills", "Education")
  because parsers look for exactly these words to segment the document.
* **Core font (Helvetica).** No embedded/exotic fonts to mangle extraction.

The layout is fixed and code-owned — the LLM writes words, never markup, so a bad
generation can never produce an unparseable document.
"""
from pathlib import Path

from fpdf import FPDF

PAGE_MARGIN = 14
LINE = 4.6


class _Resume(FPDF):
    def header(self) -> None:  # no running header: it confuses parsers
        pass

    def footer(self) -> None:
        pass


def render(profile, resume: dict, out_path: Path) -> Path:
    """Write the resume PDF and return its path."""
    pdf = _Resume(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=PAGE_MARGIN)
    pdf.set_margins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
    pdf.add_page()

    _header(pdf, profile)
    if resume.get("summary"):
        _section(pdf, "Summary")
        _body(pdf, resume["summary"])
    if resume.get("skills"):
        _section(pdf, "Skills")
        _body(pdf, ", ".join(resume["skills"]))

    for section in ("Experience", "Projects", "Achievements"):
        items = [b for b in resume.get("bullets", []) if b.get("section") == section]
        if items:
            _section(pdf, section)
            _bullets(pdf, items)

    if getattr(profile, "education", ""):
        _section(pdf, "Education")
        _body(pdf, profile.education)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))
    return out_path


def _header(pdf: FPDF, profile) -> None:
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 7, _safe(profile.name or "Your Name"), new_x="LMARGIN", new_y="NEXT")

    contact = " | ".join(
        p for p in [profile.email, profile.phone, profile.location] if p
    )
    links = " | ".join(str(v) for v in (profile.links or {}).values() if v)
    pdf.set_font("Helvetica", "", 9)
    for line in (contact, links):
        if line:
            pdf.cell(0, LINE, _safe(line), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.5)


def _section(pdf: FPDF, title: str) -> None:
    pdf.ln(1.5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 5.5, _safe(title.upper()), new_x="LMARGIN", new_y="NEXT")
    y = pdf.get_y()
    pdf.line(PAGE_MARGIN, y, pdf.w - PAGE_MARGIN, y)
    pdf.ln(1)


def _body(pdf: FPDF, text: str) -> None:
    pdf.set_font("Helvetica", "", 9.5)
    # multi_cell leaves the cursor at the RIGHT edge by default, which makes the
    # next full-width call fail with "not enough horizontal space".
    pdf.multi_cell(0, LINE, _safe(text), new_x="LMARGIN", new_y="NEXT")


def _bullets(pdf: FPDF, items: list[dict]) -> None:
    """Group bullets under their role/project heading.

    Bullets arrive ordered by relevance, so the same project can appear more than
    once; grouping first keeps each heading on the page exactly once.
    """
    grouped: dict[str, list[dict]] = {}
    for item in items:
        grouped.setdefault(item.get("title") or "", []).append(item)

    for heading, group in grouped.items():
        meta = " | ".join(
            p for p in [group[0].get("company"), group[0].get("date_range")] if p
        )
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 5, _safe(heading), new_x="LMARGIN", new_y="NEXT")
        if meta:
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, LINE, _safe(meta), new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 9.5)
        for item in group:
            # "- " not a bullet glyph: plain ASCII always survives extraction.
            pdf.multi_cell(
                0, LINE, _safe(f"- {item['text']}"), new_x="LMARGIN", new_y="NEXT"
            )
        pdf.ln(0.5)


def _safe(text: str) -> str:
    """Core PDF fonts are latin-1; replace anything outside it (em dashes, emoji)."""
    replacements = {"–": "-", "—": "-", "’": "'", "‘": "'",
                    "“": '"', "”": '"', "•": "-", " ": " "}
    for bad, good in replacements.items():
        text = (text or "").replace(bad, good)
    return text.encode("latin-1", "ignore").decode("latin-1")
