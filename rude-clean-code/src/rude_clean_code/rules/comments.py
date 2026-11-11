"""Comment, TODO marker, and suppression hygiene rules (CC902-CC906)."""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity

from rude_clean_code._scope import (
    is_test_context,
    parse_bool_option,
    parse_min_int,
    parse_str_list_option,
)
from rude_clean_code.rules._comment_analysis import (
    DECORATIVE_RE,
    DEFAULT_REFERENCE_PATTERN,
    DEFAULT_TODO_KEYWORDS,
    DIRECTIVE_RE,
    RATIONALE_WORDS,
    allow_blanket_noqa_check,
    compile_regex,
    expired_marker_dates,
    extract_reason_and_codes,
    following_statement_for_comment,
    is_candidate_code_comment,
    is_standalone_single_line_comment,
    keyword_regex,
    parse_iso_date,
    parses_as_commented_code,
    strip_comment_prefix,
    tokenize_identifiers,
)

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.core.types import FileContext

_NOQA_RE = re.compile(r"#\s*noqa\b(?P<tail>.*)$", re.IGNORECASE)
_TYPE_IGNORE_RE = re.compile(r"#\s*type:\s*ignore(?P<tail>.*)$")


class CommentedOutCode(Rule):
    """CC902: Consecutive comment lines that parse conservatively as Python statements."""

    code: ClassVar[str] = "CC902"
    message: ClassVar[str] = "Commented-out code block reduces codebase clarity"
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.MODULE}

    min_lines: int = 2

    def __init__(self) -> None:
        self.min_lines = 2

    def configure(self, options: dict[str, Any]) -> None:
        """Configure minimum consecutive lines (>= 1) via ``min_lines``."""
        if "min_lines" in options:
            self.min_lines = parse_min_int(
                self.code, "min_lines", options["min_lines"], 1
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag multi-line commented-out Python blocks while sparing prose and directives."""
        comments_by_line = {c.line: c for c in node.find("comment")}
        string_lines = node.ctx.string_lines
        block_start: int | None = None
        block_lines: list[str] = []
        for idx, raw_line in enumerate(node.ctx.text_lines, start=1):
            is_comment = (
                idx in comments_by_line
                and idx not in string_lines
                and is_candidate_code_comment(raw_line)
            )
            if is_comment:
                if block_start is None:
                    block_start = idx
                block_lines.append(raw_line)
                continue
            yield from self._flush_block(comments_by_line, block_start, block_lines)
            block_start = None
            block_lines = []
        yield from self._flush_block(comments_by_line, block_start, block_lines)

    def _flush_block(
        self,
        comments_by_line: dict[int, Node],
        start_line: int | None,
        block_lines: list[str],
    ) -> Iterator[Diagnostic]:
        if start_line is None or len(block_lines) < self.min_lines:
            return
        if not parses_as_commented_code(block_lines):
            return
        yield self.diagnostic(
            comments_by_line[start_line],
            f"Comment block ({len(block_lines)} >= {self.min_lines} lines) parses as "
            "commented-out Python code; remove dead code and rely on version control",
        )


class TodoWithoutReference(Rule):
    """CC903: Marker comment missing reference, past expiry date, or matching forbidden tags."""

    code: ClassVar[str] = "CC903"
    message: ClassVar[str] = (
        "TODO/FIXME marker lacks reference or violates marker policy"
    )
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.COMMENT}

    reference_pattern: str = DEFAULT_REFERENCE_PATTERN
    keywords: tuple[str, ...] = DEFAULT_TODO_KEYWORDS
    expiry_pattern: str | None = None
    reference_date: str | None = None
    forbidden_markers: tuple[str, ...] = ()
    exclude_tests: bool = True

    def __init__(self) -> None:
        self.reference_pattern = DEFAULT_REFERENCE_PATTERN
        self.keywords = DEFAULT_TODO_KEYWORDS
        self.expiry_pattern = None
        self.reference_date = None
        self.forbidden_markers = ()
        self.exclude_tests = True

    def should_check_file(self, context: FileContext) -> bool:
        """Skip test modules unless ``exclude_tests`` is disabled."""
        return not (self.exclude_tests and is_test_context(context))

    def configure(self, options: dict[str, Any]) -> None:
        """Configure ticket regex, keywords, optional expiry checks, and forbidden tags."""
        if "reference_pattern" in options:
            compile_regex(self.code, "reference_pattern", options["reference_pattern"])
            self.reference_pattern = options["reference_pattern"]
        if "keywords" in options:
            self.keywords = parse_str_list_option(
                self.code, "keywords", options["keywords"]
            )
        if "expiry_pattern" in options:
            raw_exp = options["expiry_pattern"]
            if raw_exp is not None:
                compile_regex(self.code, "expiry_pattern", raw_exp)
            self.expiry_pattern = raw_exp
        if "reference_date" in options:
            raw_date = options["reference_date"]
            if raw_date is not None:
                parse_iso_date(self.code, "reference_date", raw_date)
            self.reference_date = raw_date
        if "forbidden_markers" in options:
            self.forbidden_markers = parse_str_list_option(
                self.code, "forbidden_markers", options["forbidden_markers"]
            )
        if "exclude_tests" in options:
            self.exclude_tests = parse_bool_option(
                self.code, "exclude_tests", options["exclude_tests"]
            )

    def _check_expiry(self, node: Node, text: str) -> Diagnostic | None:
        if self.expiry_pattern is None:
            return None
        dates = expired_marker_dates(text, self.expiry_pattern, self.reference_date)
        if dates is None:
            return None
        expiry, today = dates
        return self.diagnostic(
            node,
            f"Dated marker expired on {expiry.isoformat()} (< {today.isoformat()}); "
            "resolve the tracked work or renew the deadline",
        )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag untracked, expired, or forbidden marker comments."""
        text = node.text
        if (forb_re := keyword_regex(self.forbidden_markers)) is not None and (
            fm := forb_re.search(text)
        ) is not None:
            yield self.diagnostic(
                node,
                f"Forbidden marker '{fm.group(0)}' present in comment; remove before merging",
            )
        kw_re = keyword_regex(self.keywords)
        if kw_re is None or (kw_match := kw_re.search(text)) is None:
            return
        if re.compile(self.reference_pattern).search(text) is None:
            yield self.diagnostic(
                node,
                f"Marker '{kw_match.group(0)}' lacks a tracking reference "
                "(overlaps Rude META001); add a ticket ID, URL, or @owner",
            )
        if (exp_diag := self._check_expiry(node, text)) is not None:
            yield exp_diag


class CommentRestatingCode(Rule):
    """CC904: Experimental heuristic flagging comments restating the next statement."""

    code: ClassVar[str] = "CC904"
    message: ClassVar[str] = (
        "Experimental: comment appears to restate identifiers of the next statement"
    )
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.COMMENT}

    max_overlap: float = 0.8

    def __init__(self) -> None:
        self.max_overlap = 0.8

    def configure(self, options: dict[str, Any]) -> None:
        """Configure word-overlap ratio threshold in ``[0.0, 1.0]``."""
        if "max_overlap" in options:
            raw = options["max_overlap"]
            invalid = (
                isinstance(raw, bool)
                or not isinstance(raw, (int, float))
                or not (0.0 <= float(raw) <= 1.0)
            )
            if invalid:
                raise ValueError(
                    f"{self.code} option 'max_overlap' must be a float in [0.0, 1.0]"
                )
            self.max_overlap = float(raw)

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag standalone single-line comments restating the following statement header."""
        text = node.text
        if DIRECTIVE_RE.match(text) or DECORATIVE_RE.match(text):
            return
        if not is_standalone_single_line_comment(node):
            return
        stmt = following_statement_for_comment(node)
        if stmt is None or stmt.line > node.line + 1:
            return
        c_words = set(tokenize_identifiers(strip_comment_prefix(text)))
        if len(c_words) < 2 or (c_words & RATIONALE_WORDS):
            return
        header = stmt.text.splitlines()[0]
        s_words = set(tokenize_identifiers(header))
        if not s_words:
            return
        overlap = len(c_words & s_words) / len(c_words)
        if overlap >= self.max_overlap:
            yield self.diagnostic(
                node,
                f"Experimental: comment token overlap with following statement is "
                f"{overlap:.0%} (>= {self.max_overlap:.0%}); explain why instead of "
                "restating what the code does",
            )


class EmptyTodoComment(Rule):
    """CC905: TODO/FIXME marker comment has no actionable description."""

    code: ClassVar[str] = "CC905"
    message: ClassVar[str] = "TODO/FIXME comment lacks an actionable description"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.COMMENT}

    keywords: tuple[str, ...] = DEFAULT_TODO_KEYWORDS
    min_description_chars: int = 3

    def __init__(self) -> None:
        self.keywords = DEFAULT_TODO_KEYWORDS
        self.min_description_chars = 3

    def configure(self, options: dict[str, Any]) -> None:
        """Configure tracked keywords and minimum non-whitespace description chars."""
        if "keywords" in options:
            self.keywords = parse_str_list_option(
                self.code, "keywords", options["keywords"]
            )
        if "min_description_chars" in options:
            self.min_description_chars = parse_min_int(
                self.code,
                "min_description_chars",
                options["min_description_chars"],
                0,
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag marker comments lacking descriptive text beyond keyword and reference."""
        kw_re = keyword_regex(self.keywords)
        if kw_re is None or kw_re.search(node.text) is None:
            return
        body = strip_comment_prefix(node.text)
        body = kw_re.sub(" ", body, count=1)
        body = re.sub(r"^\s*\([^)]*\)|^\s*\[[^\]]*\]", " ", body)
        body = re.sub(DEFAULT_REFERENCE_PATTERN, " ", body)
        cleaned = re.sub(r"[\s:\-–—]+", "", body)
        if len(cleaned) < self.min_description_chars:
            yield self.diagnostic(
                node,
                f"Marker comment has too little description ({len(cleaned)} < "
                f"{self.min_description_chars} chars); state what must change",
            )


class BlanketOrUnexplainedSuppression(Rule):
    """CC906: Blanket ``# noqa``/``# type: ignore`` or missing ``-- <reason>`` justification."""

    code: ClassVar[str] = "CC906"
    message: ClassVar[str] = "Blanket or unexplained lint/type suppression comment"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.COMMENT}

    require_reason_for: tuple[str, ...] = ()

    def __init__(self) -> None:
        self.require_reason_for = ()

    def configure(self, options: dict[str, Any]) -> None:
        """Configure rule prefixes requiring ``-- <reason>`` justification."""
        if "require_reason_for" in options:
            self.require_reason_for = parse_str_list_option(
                self.code, "require_reason_for", options["require_reason_for"]
            )

    def _needs_reason(self, codes: list[str]) -> bool:
        return bool(self.require_reason_for) and any(
            code_item.startswith(prefix)
            for prefix in self.require_reason_for
            for code_item in codes
        )

    def _check_noqa(self, node: Node, text: str) -> Iterator[Diagnostic]:
        if (match := _NOQA_RE.search(text)) is None:
            return
        tail = match.group("tail")
        if not tail.lstrip().startswith(":"):
            allow_blanket_noqa_check(node.ctx, node.line)
            yield self.diagnostic(
                node,
                "Blanket '# noqa' without explicit rule codes (mirrors Rude META002); "
                "specify exact rule codes after ':'",
            )
            return
        codes_raw, reason = extract_reason_and_codes(tail.lstrip()[1:])
        codes = [tok.strip() for tok in codes_raw.split(",") if tok.strip()]
        if not codes:
            allow_blanket_noqa_check(node.ctx, node.line)
            yield self.diagnostic(
                node,
                "Blanket '# noqa:' without explicit rule codes; list specific codes",
            )
            return
        if self._needs_reason(codes) and not reason:
            yield self.diagnostic(
                node,
                f"Suppression '# noqa: {codes_raw}' lacks a '-- <reason>' explanation",
            )

    def _check_type_ignore(self, node: Node, text: str) -> Iterator[Diagnostic]:
        if (match := _TYPE_IGNORE_RE.search(text)) is None:
            return
        tail = match.group("tail")
        if not tail.lstrip().startswith("["):
            yield self.diagnostic(
                node,
                "Blanket '# type: ignore' without '[code]' (mirrors Rude META003); "
                "specify exact mypy error codes",
            )
            return
        codes_raw, reason = extract_reason_and_codes(tail)
        if "type: ignore" in self.require_reason_for and not reason:
            yield self.diagnostic(
                node,
                f"Suppression '# type: ignore{codes_raw}' lacks a '-- <reason>' explanation",
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag blanket ``# noqa``/``# type: ignore`` and missing ``-- reason`` explanations."""
        text = node.text
        yield from self._check_noqa(node, text)
        yield from self._check_type_ignore(node, text)


COMMENT_RULES: list[type[Rule]] = [
    CommentedOutCode,
    TodoWithoutReference,
    EmptyTodoComment,
    BlanketOrUnexplainedSuppression,
    CommentRestatingCode,
]

__all__ = [
    "COMMENT_RULES",
    "DEFAULT_REFERENCE_PATTERN",
    "DEFAULT_TODO_KEYWORDS",
    "BlanketOrUnexplainedSuppression",
    "CommentRestatingCode",
    "CommentedOutCode",
    "EmptyTodoComment",
    "TodoWithoutReference",
]
