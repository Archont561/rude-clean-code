"""Shared comment, AST-code parsing, marker, and suppression parsing helpers."""

from __future__ import annotations

import ast
import datetime as dt
import re
import textwrap
from typing import TYPE_CHECKING

from rude_clean_code._scope import option_error

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.core.types import FileContext

DEFAULT_TODO_KEYWORDS: tuple[str, ...] = ("TODO", "FIXME", "XXX")
DEFAULT_REFERENCE_PATTERN: str = (
    r"(?:#\d+|[A-Z][A-Z0-9]+-\d+|https?://\S+|@[A-Za-z0-9_.-]+)"
)
DIRECTIVE_RE = re.compile(
    r"^\s*#(?:!|:|.*coding[:=]|"
    r"\s*(?:noqa|type:|fmt:|isort:|pragma:|pyright:|mypy:|ruff:|pylint:|rude:|nosec\b|"
    r"TODO\b|FIXME\b|XXX\b|HACK\b|NOTE\b|WARNING\b|DEPRECATED\b))",
    re.IGNORECASE,
)
DECORATIVE_RE = re.compile(r"^\s*#[\s\-=*_#~/]+$")
RATIONALE_WORDS = frozenset(
    {
        "avoid",
        "because",
        "bug",
        "hack",
        "must",
        "note",
        "prevent",
        "since",
        "warning",
        "why",
        "workaround",
    }
)
_STRONG_AST_STMT = (
    ast.Assign,
    ast.AugAssign,
    ast.Return,
    ast.Raise,
    ast.Import,
    ast.ImportFrom,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.With,
    ast.AsyncWith,
    ast.Assert,
    ast.Delete,
    ast.Match,
    ast.Break,
    ast.Continue,
)
_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "not",
        "of",
        "on",
        "or",
        "the",
        "this",
        "that",
        "to",
        "with",
    }
)
_UNMASKED_ATTR = "_cc906_unmasked_lines"


def strip_comment_prefix(line: str) -> str:
    """Strip the leading ``#`` (and single optional space) from *line*."""
    stripped = line.lstrip()
    if stripped.startswith("# "):
        return stripped[2:]
    return stripped.lstrip("#")


def is_candidate_code_comment(raw_line: str) -> bool:
    """Return whether *raw_line* is a non-directive, non-doctest comment line."""
    stripped = raw_line.strip()
    if not stripped.startswith("#"):
        return False
    if DIRECTIVE_RE.match(stripped) or DECORATIVE_RE.match(stripped):
        return False
    body = strip_comment_prefix(stripped).lstrip()
    return not body.startswith((">>>", "... "))


def _has_strong_python_statement(tree: ast.Module) -> bool:
    for stmt in tree.body:
        if isinstance(stmt, _STRONG_AST_STMT):
            return True
        if isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            return True
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            return True
    return False


def parses_as_commented_code(lines: list[str]) -> bool:
    """Conservatively test whether commented *lines* parse as Python statements."""
    body = textwrap.dedent("\n".join(strip_comment_prefix(line) for line in lines))
    try:
        parsed = ast.parse(body, mode="exec")
    except SyntaxError:
        return False
    return bool(parsed.body) and _has_strong_python_statement(parsed)


def compile_regex(code: str, option_name: str, raw: object) -> re.Pattern[str]:
    """Validate and compile a non-empty rule regex option."""
    if not isinstance(raw, str) or not raw:
        raise ValueError(
            f"{code} option '{option_name}' must be a non-empty regex string"
        )
    try:
        return re.compile(raw)
    except re.error as exc:
        raise ValueError(
            f"{code} option '{option_name}' contains an invalid regex: {exc}"
        ) from exc


def parse_iso_date(code: str, option_name: str, raw: object) -> dt.date:
    """Validate and parse an ISO ``YYYY-MM-DD`` option value."""
    if isinstance(raw, str):
        try:
            return dt.date.fromisoformat(raw)
        except ValueError as exc:
            raise option_error(
                code, option_name, "a valid YYYY-MM-DD date", raw
            ) from exc
    raise option_error(code, option_name, "an ISO YYYY-MM-DD string", raw)


def keyword_regex(keywords: tuple[str, ...]) -> re.Pattern[str] | None:
    """Build a whole-word regex matching any keyword in *keywords*."""
    cleaned = [re.escape(kw) for kw in keywords if kw]
    if not cleaned:
        return None
    return re.compile(r"\b(?:" + "|".join(cleaned) + r")\b")


def extract_reason_and_codes(tail: str) -> tuple[str, str]:
    """Split suppression codes and optional trailing ``-- reason`` text."""
    before_reason, _sep, reason = tail.partition("--")
    code_part = before_reason.split("#", 1)[0].strip()
    return code_part, reason.strip()


def following_statement_for_comment(comment: Node) -> Node | None:
    """Return the first non-comment statement sibling following *comment*."""
    sibling = comment.next_sibling
    while sibling is not None and sibling.type == "comment":
        sibling = sibling.next_sibling
    if sibling is None:
        return None
    if sibling.type == "block":
        return next(
            (child for child in sibling.named_children if child.type != "comment"),
            None,
        )
    return sibling


def tokenize_identifiers(text: str) -> list[str]:
    """Normalize snake_case and camelCase text into non-stopword lowercase tokens."""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text.replace("_", " "))
    tokens: list[str] = []
    for tok in re.findall(r"[A-Za-z][A-Za-z0-9]*", spaced):
        lower = tok.lower()
        if len(lower) > 1 and lower not in _STOP_WORDS:
            tokens.append(lower)
    return tokens


def is_standalone_single_line_comment(node: Node) -> bool:
    """Return whether *node* is an isolated single-line standalone ``#`` comment."""
    lines = node.ctx.text_lines
    idx = node.line - 1
    if not (0 <= idx < len(lines)):
        return False
    if not lines[idx].lstrip().startswith("#"):
        return False
    prev_is_comment = idx > 0 and lines[idx - 1].lstrip().startswith("#")
    next_is_comment = idx + 1 < len(lines) and lines[idx + 1].lstrip().startswith("#")
    return not prev_is_comment and not next_is_comment


def expired_marker_dates(
    text: str, expiry_pattern: str, reference_date: str | None
) -> tuple[dt.date, dt.date] | None:
    """Return ``(expiry, today)`` when *text* carries an expired date marker."""
    match = re.compile(expiry_pattern).search(text)
    if match is None:
        return None
    date_text = match.group(1) if match.lastindex else match.group(0)
    try:
        expiry = dt.date.fromisoformat(date_text.strip())
    except ValueError:
        return None
    today = (
        dt.date.fromisoformat(reference_date)
        if reference_date is not None
        else dt.datetime.now(dt.UTC).date()
    )
    return (expiry, today) if expiry < today else None


def allow_blanket_noqa_check(ctx: FileContext, line: int) -> None:
    """Ensure ``CC906`` can inspect blanket ``# noqa`` lines filtered by Rude core."""
    unmasked = ctx.__dict__.get(_UNMASKED_ATTR)
    if not isinstance(unmasked, set):
        orig_has_noqa = ctx.has_noqa
        unmasked = set()

        def _patched_has_noqa(ln: int, code: str | None = None) -> bool:
            if code == "CC906" and ln in unmasked:
                return False
            return orig_has_noqa(ln, code)

        ctx.__dict__[_UNMASKED_ATTR] = unmasked
        ctx.__dict__["has_noqa"] = _patched_has_noqa
    unmasked.add(line)
