"""Tailor the user's own LaTeX resume instead of replacing it.

Someone who already has an Overleaf resume does not want ours. So we take their
document verbatim, rewrite the wording inside four sections, and hand the whole
thing back — same preamble, same macros, same layout, same fonts.

The design is defensive because a LaTeX document is code: one unbalanced brace
and it does not compile, and the user finds out in Overleaf rather than here.

* **Only section bodies are touched.** `tailor()` splices rewritten bodies back
  into the original string, so the preamble is byte-identical by construction —
  there is nothing to check because there is nothing that can change it.
* **One LLM call per section**, never one call for the document. Small models
  answer the easy part of a big schema and drop the hard part (the lesson from
  Sprint 4), and a single bad call would otherwise poison the whole file.
* **`validate()` is the safety net, not the prompt.** A rewritten body that
  fails any check is discarded and the original body is kept. A resume that is
  slightly less tailored beats one that will not compile.
"""
import re
from typing import NamedTuple

from app.ai.generate_resume import _numbers
from app.ai.llm import generate_text
from app.db.models import KBChunk

# Headings vary by template, so match them loosely. Order matters: the first
# keyword found in the heading wins, and "Technical Skills" must not be read as
# an experience section just because some template calls it "Skills & Experience".
_HEADING_MAP = (
    ("experience", ("experience", "employment", "internship", "work history")),
    ("projects", ("project",)),
    ("certifications", ("certification", "certificate", "licens", "course")),
    ("skills", ("skill", "technolog")),
)

REWRITABLE = tuple(name for name, _ in _HEADING_MAP)

# Sections whose entries are the content: losing one loses a real credential or
# a real keyword. Experience and projects are prose, where rewording is the job.
_LIST_SECTIONS = ("skills", "certifications")

_SECTION_RE = re.compile(r"\\section\*?\s*\{")
_COMMAND_RE = re.compile(r"\\([a-zA-Z]+)")


class Section(NamedTuple):
    """One `\\section{...}` and the span of its body in the original document."""

    name: str  # one of REWRITABLE, or "" when the heading maps to nothing we touch
    heading: str  # as written, e.g. "Work Experience"
    start: int  # index of the first character after the heading
    end: int  # index just past the last character of the body


def find_sections(latex: str) -> list[Section]:
    """Every section in the document, each body running to the next one."""
    sections: list[Section] = []
    document_end = latex.find("\\end{document}")
    if document_end == -1:
        document_end = len(latex)

    starts = [
        (m.start(), m.end() - 1) for m in _SECTION_RE.finditer(latex) if m.start() < document_end
    ]
    for index, (command_start, brace_start) in enumerate(starts):
        brace_end = _matching_brace(latex, brace_start)
        if brace_end is None:
            continue  # malformed \section{ with no closing brace: skip, don't guess
        body_end = starts[index + 1][0] if index + 1 < len(starts) else document_end
        body_end = _trim_trailing_notes(latex, brace_end + 1, body_end)
        heading = _heading_text(latex[brace_start + 1 : brace_end])
        sections.append(
            Section(_canonical(heading), heading, brace_end + 1, max(brace_end + 1, body_end))
        )
    return sections


def tailor(latex: str, chunks: list[KBChunk], requirements: dict) -> tuple[str, list[dict]]:
    """Rewrite what we may, keep what we must. Returns (document, per-section report).

    Splicing runs back-to-front so earlier spans keep their indices.
    """
    sections = find_sections(latex)
    report: list[dict] = []
    out = latex

    for section in reversed(sections):
        if section.name not in REWRITABLE:
            continue
        original = latex[section.start : section.end]
        entry = {"name": section.name, "heading": section.heading, "rewritten": False}

        try:
            candidate = rewrite_section(section.name, original, chunks, requirements)
            problem = validate(original, candidate, chunks, section.name)
            if problem:
                # One retry, told exactly what it broke. A small model usually
                # fails by reflowing structure it was asked to copy, and that is
                # the kind of mistake it can fix when the mistake is named.
                candidate = rewrite_section(
                    section.name, original, chunks, requirements, correction=problem
                )
                problem = validate(original, candidate, chunks, section.name)
        except Exception as e:  # noqa: BLE001 - one dead section must not lose the rest
            entry["reason"] = f"the model failed: {e}"
            report.append(entry)
            continue

        if problem:
            entry["reason"] = problem
        else:
            out = out[: section.start] + candidate + out[section.end :]
            entry["rewritten"] = True
        report.append(entry)

    report.reverse()  # back to document order
    return out, report


_SYSTEM = r"""You are a resume editor working on ONE section of a LaTeX resume. You are not writing a document and you are not writing LaTeX — you are replacing English sentences inside LaTeX that already exists.

WHAT YOU RETURN
Return the section body only: the exact LaTeX you were given, character for character, except for the human-readable sentences inside it. Same length, same shape, same order.

THE STRUCTURE IS NOT YOURS TO TOUCH
- Copy every \command exactly: same names, same count, same order, same braces.
- Copy every \begin{...} and its \end{...}, including macros like \resumeItemListStart and \resumeSubHeadingListEnd. A missing one means the resume does not compile.
- Never add, delete, merge, split or reorder an entry or a bullet. Three bullets in, three bullets out.
- Never add a package, macro, section or environment. Never add markdown.

FACTS ARE NOT YOURS TO TOUCH
- Employers, job titles, institutions, product names, locations, dates and links are facts. Copy them exactly, even if a different one would suit the job better.
- Never state a number, percentage, duration or scale that is not already in this section or in the accomplishments below.
- Never claim a technology the accomplishments do not show. If the job wants Kubernetes and the candidate has never used it, the section stays as it is.

WHAT YOU ACTUALLY CHANGE
- Rewrite each bullet so it leads with what was built or achieved, in strong past tense, one sentence.
- Where the accomplishments genuinely support it, use the target job's own words for the same thing: if they wrote "REST services" and the job says "RESTful APIs", say "RESTful APIs". This is vocabulary matching, not claim making.
- Put the detail the job asks about first within each bullet. Same fact, better order.
- If a bullet cannot be improved truthfully, return it unchanged. That is a valid answer.

Output raw LaTeX. No markdown fences, no explanation, no commentary."""

# What "rewrite" means depends entirely on the section. Told only to improve the
# wording, a model turned "Oracle Cloud Infrastructure 2025 AI Foundations
# Associate" into "Successfully designed and implemented cloud strategies" — a
# certificate rewritten as a claim, which is both false and a lost credential.
_SECTION_RULES = {
    "experience": (
        "This section is bullets about work the candidate did. Rewrite the "
        "sentences. Keep every employer, title and date exactly as written."
    ),
    "projects": (
        "This section is bullets about things the candidate built. Rewrite the "
        "sentences. Keep every project name and technology exactly as written."
    ),
    "skills": (
        "This section is a LIST of skills, not prose. Never turn an entry into a "
        "sentence — a screener reads this as keywords. You may reorder items so "
        "the ones this job asks for come first, and you may relabel a group to "
        "the job's wording. Never drop a skill and never add one."
    ),
    "certifications": (
        "These are the names of real certificates and who issued them. They are "
        "not achievements to describe. Change nothing except, at most, the order "
        "— most relevant to this job first. Returning this section byte-identical "
        "is the expected answer."
    ),
}


def rewrite_section(
    name: str,
    body: str,
    chunks: list[KBChunk],
    requirements: dict,
    correction: str | None = None,
) -> str:
    """One focused call: this section's body in, a reworded body out.

    Every chunk goes in, not a top-k slice: the model is choosing which of the
    candidate's real accomplishments backs each existing bullet, and it cannot
    choose one it was never shown.
    """
    required = list(requirements.get("required_skills", []))
    preferred = list(requirements.get("preferred_skills", []))
    responsibilities = list(requirements.get("responsibilities", []))[:6]

    facts = "\n".join(
        f"[{i}] {c.title}"
        + (f" — {c.company}" if c.company else "")
        + (f" ({c.date_range})" if c.date_range else "")
        + f"\n    {c.accomplishment}"
        + (f"\n    Impact: {c.impact}" if c.impact else "")
        + (f"\n    Technologies: {', '.join(c.technologies)}" if c.technologies else "")
        for i, c in enumerate(chunks, start=1)
    )
    prompt = (
        f"THIS SECTION: {_SECTION_RULES.get(name, '')}\n\n"
        "TARGET JOB\n"
        f"Required skills: {', '.join(required) or 'not specified'}\n"
        f"Preferred skills: {', '.join(preferred) or 'not specified'}\n"
        + (f"Responsibilities: {'; '.join(responsibilities)}\n" if responsibilities else "")
        + "\nUse these words only where the accomplishments below already justify them.\n\n"
        f"THE CANDIDATE'S COMPLETE VERIFIED RECORD ({len(chunks)} accomplishments; "
        "the only facts that exist):\n"
        f"{facts}\n\n"
        + (
            f"YOUR PREVIOUS ATTEMPT WAS REJECTED: {correction}.\n"
            "Fix exactly that and change nothing else. When in doubt, return a "
            "line completely unchanged.\n\n"
            if correction
            else ""
        )
        + f"THE {name.upper()} SECTION TO REWRITE — return it with the same LaTeX and "
        f"better sentences:\n{body}"
    )
    return _strip_fences(generate_text(_SYSTEM, prompt, timeout=None, max_tokens=3000))


def validate(
    original: str, rewritten: str, chunks: list[KBChunk], section: str = ""
) -> str:
    """Why this rewrite must be thrown away, or "" if it is safe to use.

    Every check answers one of two questions: could this break the document, or
    could it put something on the page the candidate cannot back up? Both were
    learned from watching a real model: it dropped a `\\resumeSubHeadingListEnd`
    (leaving an `itemize` open inside a macro, where a `\\begin`/`\\end` count
    never sees it) and it renamed an employer to one that fits the job better.
    """
    if not rewritten.strip():
        return "the model returned nothing"

    if _brace_depth(rewritten) != 0:
        return "unbalanced braces"

    # Same commands, same count, same order. Anything else is a structural edit,
    # and structure is not the model's to change — only the words between it are.
    if _command_sequence(rewritten) != _command_sequence(original):
        return "the LaTeX structure changed (commands added, dropped or reordered)"

    if _environments(rewritten) != _environments(original):
        return "\\begin/\\end environments do not match the original"

    known_numbers = set(_numbers(original)) | set(_facts_numbers(chunks))
    invented = [n for n in _numbers(rewritten) if n not in known_numbers]
    if invented:
        return "invented numbers: " + ", ".join(sorted(set(invented))[:5])

    unsupported = _unsupported_names(rewritten, _vocabulary(original, chunks))
    if unsupported:
        return "invented names: " + ", ".join(sorted(set(unsupported))[:5])

    # In a list section the entries ARE the facts, so losing one is the failure:
    # "Product Management using Agentic AI -- IIT Patna x Masai" came back as
    # "Successfully designed product management strategies" — nothing invented,
    # every other check satisfied, and the certificate gone.
    #
    # Prose sections are exempt. There, rewording is the whole point, and a
    # rephrased bullet that drops a parenthetical is an editorial call the user
    # reviews — not a lost credential.
    if section in _LIST_SECTIONS:
        dropped = _dropped_names(original, rewritten)
        if dropped:
            return "dropped entries the original listed: " + ", ".join(sorted(dropped)[:5])

    return ""


def _trim_trailing_notes(latex: str, start: int, end: int) -> int:
    r"""Pull the section body back off the blank lines and `% ----- NEXT -----`
    banner that sit between it and the following section.

    Those belong to the next heading, not this body. Sending them to the model
    only gives it something of the author's to lose — and it did lose them.
    """
    lines = latex[start:end].split("\n")
    while lines and (not lines[-1].strip() or lines[-1].lstrip().startswith("%")):
        lines.pop()
    return start + len("\n".join(lines))


def _matching_brace(text: str, open_index: int) -> int | None:
    """Index of the `}` closing the `{` at open_index, honouring nesting."""
    depth = 0
    for i in range(open_index, len(text)):
        if text[i] == "{" and not _escaped(text, i):
            depth += 1
        elif text[i] == "}" and not _escaped(text, i):
            depth -= 1
            if depth == 0:
                return i
    return None


def _escaped(text: str, index: int) -> bool:
    r"""True for a literal `\{`, which is a character rather than a group."""
    backslashes = 0
    while index - 1 - backslashes >= 0 and text[index - 1 - backslashes] == "\\":
        backslashes += 1
    return backslashes % 2 == 1


def _brace_depth(text: str) -> int:
    depth = 0
    for i, char in enumerate(text):
        if char in "{}" and not _escaped(text, i):
            depth += 1 if char == "{" else -1
        if depth < 0:
            return depth  # a `}` before its `{` — broken however it ends up
    return depth


def _environments(text: str) -> dict[str, int]:
    """Counts of `\\begin{x}` minus nothing — `\\end{x}` is counted separately so
    a rewrite that drops one of a pair is caught."""
    counts: dict[str, int] = {}
    for kind, name in re.findall(r"\\(begin|end)\s*\{([^}]*)\}", text):
        key = f"{kind}:{name}"
        counts[key] = counts.get(key, 0) + 1
    return counts


def _command_sequence(text: str) -> list[str]:
    return _COMMAND_RE.findall(text)


def _facts_numbers(chunks: list[KBChunk]) -> list[str]:
    return [n for c in chunks for n in _numbers(_chunk_text(c))]


def _vocabulary(original: str, chunks: list[KBChunk]) -> set[str]:
    """Every word the candidate can already point at: this section, plus the KB.

    The job's own skill list is deliberately NOT in here. Letting the model reach
    for a JD keyword the candidate has never used is exactly the keyword-stuffing
    the rest of the product refuses to do.
    """
    blob = original + " " + " ".join(_chunk_text(c) for c in chunks)
    return {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z+#.]*", blob)}


# A name the candidate cannot back up looks like one of two things, and neither
# is ordinary prose: a run of capitalised words ("AWS Partner Ecosystem", "Cloud
# Engineer") or an acronym ("AWS", "GCP"). Single capitalised words are NOT
# checked — "Designed", "Proficient" and "Successfully" are English, and flagging
# them rejected every rewrite while catching nothing.
# No "." inside a word here, or "API. Improved throughput" reads as one phrase
# spanning the full stop between two sentences.
_PROPER_PHRASE = re.compile(r"\b[A-Z][a-zA-Z+#]*(?:\s+[A-Z][a-zA-Z+#]*)+")
_ACRONYM = re.compile(r"\b[A-Z]{2,}(?:[+#]|\b)")


def _unsupported_names(text: str, vocabulary: set[str]) -> list[str]:
    """Employers, products and technologies that appear from nowhere.

    This is the check that catches a model renaming an employer to suit the job —
    the failure a brace count and a number check both sail straight past.
    """
    candidates = _PROPER_PHRASE.findall(text) + _ACRONYM.findall(text)
    unsupported = []
    for candidate in candidates:
        words = [w for w in re.split(r"\s+", candidate) if len(w) >= 3]
        missing = [w for w in words if not _known(w.lower(), vocabulary)]
        # In a phrase, a single unknown word at the front is a sentence starting
        # with a capital in front of a name the candidate does own — "Earned
        # Oracle Cloud Infrastructure". The name is what matters, and it checks
        # out. A lone unknown acronym has no such excuse.
        forgivable = len(words) > 1 and missing == words[:1]
        if missing and not forgivable:
            unsupported.append(candidate.strip())
    return unsupported


def _dropped_names(original: str, rewritten: str) -> set[str]:
    """Names the original stated that the rewrite no longer mentions.

    Only the same proper phrases and acronyms the addition check looks at: an
    employer, an institution, a certificate, a technology.
    """
    source = _without_comments(original)
    present = {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z+#]*", rewritten)}
    dropped = set()
    for name in _PROPER_PHRASE.findall(source) + _ACRONYM.findall(source):
        for word in re.split(r"\s+", name):
            if len(word) >= 3 and word.lower() not in present:
                dropped.add(name.strip())
    return dropped


def _without_comments(latex: str) -> str:
    r"""Drop `% ...` lines. Templates label their sections with comment banners
    (`% ----- EXPERIENCE -----`), and a model that reformats naturally drops
    them. Those are notes to the author, not facts about the candidate."""
    return re.sub(r"(?<!\\)%.*", "", latex)


def _known(word: str, vocabulary: set[str]) -> bool:
    """Tolerant match, so "Postgres" in the KB covers "PostgreSQL" on the page."""
    stem = word[:5]
    return any(known == word or known.startswith(stem) or word.startswith(known[:5])
               for known in vocabulary if len(known) >= 3)


def _chunk_text(chunk: KBChunk) -> str:
    return (
        f"{chunk.title} {chunk.accomplishment} {chunk.impact or ''} "
        f"{' '.join(chunk.technologies or [])}"
    )


def _heading_text(raw: str) -> str:
    r"""`\textbf{Work Experience}` -> "Work Experience"."""
    text = re.sub(r"\\[a-zA-Z]+\s*", " ", raw)  # drop \textbf, \scshape, ...
    text = re.sub(r"\\(.)", r"\1", text)  # unescape \& so it reads as "Skills & Competencies"
    text = re.sub(r"[{}]", " ", text)
    return re.sub(r"\s+", " ", text).strip() or raw


def _canonical(heading: str) -> str:
    lowered = heading.lower()
    for name, keywords in _HEADING_MAP:
        if any(word in lowered for word in keywords):
            return name
    return ""


def _strip_fences(text: str) -> str:
    """Models wrap code in ``` even when told not to."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z]*\n?", "", stripped)
        stripped = re.sub(r"\n?```$", "", stripped)
    return stripped
