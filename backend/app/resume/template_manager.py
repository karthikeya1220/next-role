"""Jinja template manager — ported from hiring-agent/prompts/template_manager.py.

Now resolves templates relative to this file's location.
"""

from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, Template

_TEMPLATES_DIR = Path(__file__).parent / "prompts" / "templates"


class TemplateManager:
    def __init__(self, template_dir: str | Path = _TEMPLATES_DIR):
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._templates: dict[str, Template] = {}
        self._load_templates()

    def _load_templates(self):
        names = ["basics", "work", "education", "skills", "projects", "awards",
                 "system_message", "github_project_selection"]
        for name in names:
            try:
                self._templates[name] = self.env.get_template(f"{name}.jinja")
            except Exception:
                pass  # Optional templates may be missing

    def render_template(self, section_name: str, **kwargs) -> Optional[str]:
        tmpl = self._templates.get(section_name)
        if not tmpl:
            return None
        try:
            return tmpl.render(**kwargs)
        except Exception as exc:
            return None

    def render_string(self, source: str, **kwargs) -> str:
        return self.env.from_string(source).render(**kwargs)
