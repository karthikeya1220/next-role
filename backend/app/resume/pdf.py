"""PDF → JSON Resume extractor.

Ported from hiring-agent/pdf.py. Rewired to use app.llm_client (OpenRouter)
instead of the Ollama/Gemini provider system.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import pymupdf

from app.llm_client import FAST_MODEL, chat_json
from app.resume.models import (
    Basics,
    JSONResume,
    BasicsSection,
    WorkSection,
    EducationSection,
    SkillsSection,
    ProjectsSection,
    AwardsSection,
)
from app.resume.transform import transform_parsed_data

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "prompts" / "templates"


def _load_template(name: str) -> str:
    path = _TEMPLATES_DIR / f"{name}.jinja"
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    return path.read_text(encoding="utf-8")


def _render(template_text: str, **kwargs) -> str:
    """Very simple variable substitution — templates use {{ var }} syntax."""
    from jinja2 import Environment
    env = Environment()
    return env.from_string(template_text).render(**kwargs)


SECTION_MODELS = {
    "basics": BasicsSection,
    "work": WorkSection,
    "education": EducationSection,
    "skills": SkillsSection,
    "projects": ProjectsSection,
    "awards": AwardsSection,
}


def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """Return the full text of a PDF as markdown via PyMuPDF."""
    try:
        from app.resume.pymupdf_rag import to_markdown
        with pymupdf.open(pdf_path) as doc:
            return to_markdown(doc, pages=range(doc.page_count))
    except Exception as exc:
        logger.error("Failed to extract text from %s: %s", pdf_path, exc)
        return None


def _extract_section(resume_text: str, section_name: str) -> Optional[dict]:
    """Call OpenRouter to extract one section from the resume text."""
    pydantic_model = SECTION_MODELS.get(section_name)
    if pydantic_model is None:
        logger.error("Unknown section: %s", section_name)
        return None

    try:
        template_text = _load_template(section_name)
        prompt = _render(template_text, text_content=resume_text)
        system_msg = _render(
            _load_template("system_message"),
            section_name_param=section_name,
        )
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return None

    schema = pydantic_model.model_json_schema()
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": prompt},
    ]

    try:
        data = chat_json(messages, schema, model=FAST_MODEL, temperature=0.1)
        return transform_parsed_data(data)
    except Exception as exc:
        logger.error("LLM extraction failed for section '%s': %s", section_name, exc)
        return None


def extract_json_resume_from_text(resume_text: str) -> Optional[JSONResume]:
    """Extract a full JSONResume from plain text."""
    sections = ["basics", "work", "education", "skills", "projects", "awards"]
    complete: dict = {
        "basics": None, "work": None, "volunteer": None, "education": None,
        "awards": None, "certificates": None, "publications": None, "skills": None,
        "languages": None, "interests": None, "references": None, "projects": None,
        "meta": None,
    }

    for section_name in sections:
        data = _extract_section(resume_text, section_name)
        if data is None:
            logger.warning("Retrying '%s'…", section_name)
            data = _extract_section(resume_text, section_name)
        if data:
            complete.update(data)
        else:
            logger.error("Failed to extract '%s'. Aborting.", section_name)
            return None

    try:
        if complete.get("basics") and isinstance(complete["basics"], dict):
            complete["basics"] = Basics(**complete["basics"])
        return JSONResume(**complete)
    except Exception as exc:
        logger.error("Failed to construct JSONResume: %s", exc)
        return None


def extract_json_resume_from_pdf(pdf_path: str) -> Optional[JSONResume]:
    """Full pipeline: PDF → text → JSONResume."""
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return None
    return extract_json_resume_from_text(text)
