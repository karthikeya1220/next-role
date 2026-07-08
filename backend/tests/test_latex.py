"""The LaTeX path has one job: never hand back a document that will not compile.

`tailor` is exercised with a stubbed model rather than a live one — the
interesting cases are the *bad* rewrites, and asking a real model to produce
unbalanced braces on demand is not a test, it is a wish.
"""
import pytest

from app.ai import latex as latex_mod
from app.ai.latex import find_sections, tailor, validate

# A cut-down version of the most common Overleaf resume shape: custom macros in
# the preamble, \section{\textbf{...}} headings, itemize inside each entry.
TEMPLATE = r"""\documentclass[letterpaper,11pt]{article}
\usepackage{titlesec}
\newcommand{\resumeItem}[1]{\item\small{#1}}
\begin{document}
\begin{center}\textbf{\Huge Ada Lovelace}\end{center}

\section{\textbf{Education}}
  \textbf{Analytical University} \hfill 2023 -- 2027

\section{Work Experience}
  \begin{itemize}
    \resumeItem{Built a payments API handling 200 requests per second}
    \resumeItem{Wrote tests}
  \end{itemize}

\section{Personal Projects}
  \begin{itemize}
    \resumeItem{A notes app}
  \end{itemize}

\section{Technical Skills}
  Python, Go

\end{document}
"""


class FakeChunk:
    def __init__(self, title, accomplishment, impact=None, technologies=None):
        self.title = title
        self.accomplishment = accomplishment
        self.impact = impact
        self.technologies = technologies or []


CHUNKS = [
    FakeChunk(
        "Payments API",
        "Built a payments API in Go serving 200 requests per second",
        impact="cut latency to 40ms",
        technologies=["Go", "Postgres"],
    )
]


def test_find_sections_maps_headings_to_what_we_may_rewrite() -> None:
    found = {s.name: s.heading for s in find_sections(TEMPLATE)}
    assert found == {
        "": "Education",  # not ours to touch
        "experience": "Work Experience",
        "projects": "Personal Projects",
        "skills": "Technical Skills",
    }


def test_section_bodies_stop_at_the_next_section() -> None:
    body = {s.name: TEMPLATE[s.start : s.end] for s in find_sections(TEMPLATE)}
    assert "payments API" in body["experience"]
    assert "notes app" not in body["experience"]
    assert "\\end{document}" not in body["skills"]


def test_a_section_stops_before_the_next_one_s_comment_banner() -> None:
    r"""`% ----- PROJECTS -----` introduces the next section. Included in this
    body, the model rewrites it away and the author's file loses the banner."""
    doc = (
        "\\begin{document}\n"
        "\\section{Experience}\n  \\item Built it\n\n"
        "% ---------- PROJECTS ----------\n"
        "\\section{Projects}\n  \\item Shipped it\n"
        "\\end{document}"
    )
    experience = find_sections(doc)[0]
    body = doc[experience.start : experience.end]
    assert "Built it" in body
    assert "%" not in body


def test_headings_survive_wrapping_commands() -> None:
    """\\section{\\textbf{Education}} still reads as "Education"."""
    assert find_sections(TEMPLATE)[0].heading == "Education"


def test_escaped_ampersands_read_as_text() -> None:
    """Real templates write `Skills \\& Competencies`; the badge must not show the escape."""
    doc = r"\begin{document}\section{Skills \& Competencies} Python \end{document}"
    section = find_sections(doc)[0]
    assert (section.heading, section.name) == ("Skills & Competencies", "skills")


@pytest.mark.parametrize(
    ("rewritten", "expected"),
    [
        ("", "the model returned nothing"),
        (r"\resumeItem{Built a payments API", "unbalanced braces"),
        (r"\begin{itemize}\resumeItem{Shipped it}", "structure changed"),
        (r"\begin{itemize}\resumeItem{\textit{Shipped it}}\end{itemize}", "structure changed"),
        (r"\begin{center}\resumeItem{Shipped it}\end{center}", "environments"),
        (r"\begin{itemize}\resumeItem{Served 900 requests per second}\end{itemize}",
         "invented numbers"),
    ],
)
def test_validate_rejects_dangerous_rewrites(rewritten: str, expected: str) -> None:
    original = r"\begin{itemize}\resumeItem{Built a payments API}\end{itemize}"
    assert expected in validate(original, rewritten, CHUNKS)


def test_a_dropped_macro_is_caught_even_though_it_hides_an_environment() -> None:
    r"""The live failure: templates open `itemize` inside `\resumeSubHeadingListStart`,
    so dropping the matching End leaves a document that will not compile while
    every literal \begin/\end still balances."""
    original = r"\resumeSubHeadingListStart\resumeItem{Built it}\resumeSubHeadingListEnd"
    rewritten = r"\resumeSubHeadingListStart\resumeItem{Built the payments API}"
    assert "structure changed" in validate(original, rewritten, CHUNKS)


def test_erasing_a_certificate_is_rejected() -> None:
    """The live failure that every other check waved through: a certification
    line rewritten as an accomplishment, taking the issuer with it."""
    original = r"\item Product Management using Agentic AI -- IIT Patna x Masai"
    rewritten = r"\item Successfully designed product management strategies"
    problem = validate(original, rewritten, CHUNKS, "certifications")
    assert "dropped entries" in problem
    assert "IIT" in problem or "Patna" in problem


def test_a_prose_section_may_drop_a_parenthetical() -> None:
    """Rewording is the point in experience and projects; only list sections are
    frozen. Enforcing it everywhere rejected every rewrite of a real resume."""
    original = r"\item Shipped contract management (Client ID, Contract Code) for the team"
    rewritten = r"\item Shipped a contract management feature for the team"
    assert validate(original, rewritten, CHUNKS, "experience") == ""


def test_a_comment_banner_is_not_a_fact() -> None:
    r"""Templates label sections with `% ----- EXPERIENCE -----`; a model that
    reformats drops the comment, and that is not a lost credential."""
    original = "% ---------- CERTIFICATIONS ----------\n\\item AWS Certified"
    rewritten = r"\item AWS Certified"
    assert validate(original, rewritten, CHUNKS, "certifications") == ""


def test_reordering_a_list_is_allowed() -> None:
    """Skills may be reordered to lead with what the job asks for."""
    original = r"\item Python, SQL, Docker"
    rewritten = r"\item SQL, Python, Docker"
    assert validate(original, rewritten, CHUNKS, "skills") == ""


def test_an_invented_employer_is_rejected() -> None:
    """The other live failure: the model renamed the employer to suit the job."""
    original = r"\resumeSubheading{Software Engineering Intern}{Fintech Startup}"
    rewritten = r"\resumeSubheading{Cloud Engineer}{AWS Partner Ecosystem}"
    assert "invented names" in validate(original, rewritten, CHUNKS)


@pytest.mark.parametrize(
    "rewritten",
    [
        r"\resumeItem{Designed a Go payments API backed by Postgres}",
        # Real rejections seen from the live model: ordinary English words that
        # happen to be capitalised. Flagging these rejected every single section.
        r"\resumeItem{Proficient in building a payments API}",
        r"\resumeItem{Successfully built a payments API}",
        r"\resumeItem{Built a payments API. Improved throughput}",
        # A verb in front of a name the candidate does own. The name checks out,
        # and rejecting this cost a real Certifications section its rewrite.
        r"\resumeItem{Delivered Payments API work}",
    ],
)
def test_ordinary_capitalisation_is_not_an_invention(rewritten: str) -> None:
    """Only proper-noun phrases and acronyms are claims; English is not."""
    original = r"\resumeItem{Built a payments API}"
    assert validate(original, rewritten, CHUNKS) == ""


@pytest.mark.parametrize(
    "rewritten",
    [
        r"\resumeItem{Built a payments API on AWS Lambda}",  # phrase + acronym
        r"\resumeItem{Built a payments API for Acme Financial Group}",
        r"\resumeItem{Built a payments API deployed to GCP}",  # bare acronym
    ],
)
def test_names_the_candidate_cannot_back_up_are_rejected(rewritten: str) -> None:
    original = r"\resumeItem{Built a payments API}"
    assert "invented names" in validate(original, rewritten, CHUNKS)


def test_validate_accepts_a_faithful_rewrite() -> None:
    original = r"\begin{itemize}\resumeItem{Built a payments API}\end{itemize}"
    rewritten = r"\begin{itemize}\resumeItem{Built a Go payments API at 200 rps}\end{itemize}"
    assert validate(original, rewritten, CHUNKS) == ""


def test_numbers_already_in_the_section_are_not_inventions() -> None:
    """Dates and figures the user wrote must survive being repeated back."""
    original = r"\resumeItem{Led a team of 6 from 2024}"
    rewritten = r"\resumeItem{Led 6 engineers from 2024}"
    assert validate(original, rewritten, CHUNKS) == ""


def _tailor_with(monkeypatch, rewrite):
    """Stubs take **kwargs because a failed rewrite is retried with `correction`."""
    monkeypatch.setattr(latex_mod, "rewrite_section", rewrite)
    return tailor(TEMPLATE, CHUNKS, {"required_skills": ["Go"]})


def test_tailor_changes_only_the_sections_it_may(monkeypatch) -> None:
    out, report = _tailor_with(
        monkeypatch,
        lambda name, body, *a, **kw: body.replace("Wrote tests", "Wrote unit tests"),
    )
    preamble = TEMPLATE[: TEMPLATE.index("\\begin{document}")]
    assert out.startswith(preamble), "the preamble must be byte-identical"
    assert "Analytical University" in out, "Education is not ours to rewrite"
    assert "Wrote unit tests" in out
    assert [e["name"] for e in report] == ["experience", "projects", "skills"]
    assert all(e["rewritten"] for e in report)


def test_a_broken_rewrite_keeps_the_original_section(monkeypatch) -> None:
    out, report = _tailor_with(monkeypatch, lambda *a, **kw: r"\resumeItem{oops")
    assert out == TEMPLATE
    assert all(not e["rewritten"] for e in report)
    assert all("brace" in e["reason"] for e in report)


def test_a_rejected_rewrite_is_retried_once_with_the_reason(monkeypatch) -> None:
    """A small model mostly fails by reflowing structure it was told to copy,
    which it can fix when told what it broke."""
    attempts: list[str | None] = []

    def rewrite(name, body, chunks, reqs, correction=None):
        attempts.append(correction)
        # Break it the first time, copy it faithfully on the retry.
        return r"\resumeItem{oops" if correction is None else body

    out, report = _tailor_with(monkeypatch, rewrite)

    assert out == TEMPLATE, "a faithful copy changes nothing"
    assert all(e["rewritten"] for e in report)
    assert attempts.count(None) == 3, "one first attempt per rewritable section"
    assert all("brace" in a for a in attempts if a), "the retry is told what broke"


def test_a_failing_model_call_keeps_the_original_section(monkeypatch) -> None:
    def boom(*a, **kw):
        raise RuntimeError("ollama is down")

    out, report = _tailor_with(monkeypatch, boom)
    assert out == TEMPLATE
    assert report[0]["reason"] == "the model failed: ollama is down"


def test_tailoring_a_document_without_sections_is_a_no_op() -> None:
    plain = "\\documentclass{article}\\begin{document}Hello\\end{document}"
    out, report = tailor(plain, CHUNKS, {})
    assert (out, report) == (plain, [])
