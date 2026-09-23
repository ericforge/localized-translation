#!/usr/bin/env python3
"""Validate protected tokens and structure between a source and target file.

This is a conservative validator: it assumes URLs, network addresses,
placeholders, HTML tag names and frozen HTML attributes are unchanged.
Approved slug localization or link replacement must be reviewed separately and
recorded in the delivery notes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


URL_RE = re.compile(
    r"(?:https?|ftp)://[^\s<>\"']+|"
    r"(?:mailto:|tel:|app:)[^\s<>\"']+|"
    r"\bwww\.[^\s<>\"']+|"
    r"(?<![@\w.-])(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}(?:/[^\s<>\"']*)?",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
MAC_RE = re.compile(r"\b(?:[0-9A-F]{2}:){5}[0-9A-F]{2}\b", re.IGNORECASE)
IPV4_RE = re.compile(
    r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}"
    r"(?:/\d{1,2})?(?::\d{1,5})?(?![\w.])"
)
IPV6_RE = re.compile(
    r"(?<![\w:])(?:[0-9A-F]{1,4}:){2,7}[0-9A-F]{0,4}(?![\w:])",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(
    r"(?:\{\{\s*[A-Za-z_][\w.-]*\s*\}\}|"
    r"\{\s*[A-Za-z_][\w.-]*\s*\}|"
    r"%\d+\$[sdif]|%[sdif])"
)
ICU_VARIABLE_RE = re.compile(r"\{\s*([A-Za-z_][\w.-]*)\s*,")
HTML_TAG_RE = re.compile(r"<\s*(/?)\s*([A-Za-z][\w:-]*)\b[^>]*>")
FROZEN_HTML_ATTRIBUTES = {"id", "class", "href", "src", "srcset", "style"}


class FrozenHTMLAttributeParser(HTMLParser):
    """Collect attributes whose values are structure or code, not prose."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.attributes: Counter[tuple[str, str, str]] = Counter()

    def _collect(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            name = name.lower()
            if name in FROZEN_HTML_ATTRIBUTES or name.startswith("data-"):
                self.attributes[(tag.lower(), name, value or "")] += 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._collect(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._collect(tag, attrs)


def read_text(path: Path) -> tuple[str, list[str]]:
    raw = path.read_bytes()
    errors: list[str] = []
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append(f"{path}: UTF-8 BOM found")
    try:
        return raw.decode("utf-8"), errors
    except UnicodeDecodeError as exc:
        errors.append(f"{path}: invalid UTF-8: {exc}")
        return raw.decode("utf-8", errors="replace"), errors


def protected_tokens(text: str) -> dict[str, Counter[str]]:
    return {
        "url": Counter(URL_RE.findall(text)),
        "email": Counter(EMAIL_RE.findall(text)),
        "mac": Counter(MAC_RE.findall(text)),
        "ipv4": Counter(IPV4_RE.findall(text)),
        "ipv6": Counter(IPV6_RE.findall(text)),
        "placeholder": Counter(PLACEHOLDER_RE.findall(text)),
        "icu_variable": Counter(ICU_VARIABLE_RE.findall(text)),
    }


def html_tags(text: str) -> Counter[str]:
    return Counter((closing, name.lower()) for closing, name in HTML_TAG_RE.findall(text))


def counter_diff(source: Counter[str], target: Counter[str]) -> dict[str, dict[str, int]]:
    missing = source - target
    extra = target - source
    return {"missing": dict(missing), "extra": dict(extra)}


def frozen_html_attributes(text: str) -> Counter[tuple[str, str, str]]:
    parser = FrozenHTMLAttributeParser()
    parser.feed(text)
    parser.close()
    return parser.attributes


def json_shape(path: Path, text: str) -> tuple[Any | None, str | None]:
    if path.suffix.lower() != ".json":
        return None, None
    try:
        return json.loads(text), None
    except json.JSONDecodeError as exc:
        return None, f"{path}: invalid JSON: {exc}"


def shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: shape(item) for key, item in value.items()}
    if isinstance(value, list):
        return [shape(item) for item in value]
    return type(value).__name__


def validate(source_path: Path, target_path: Path) -> dict[str, Any]:
    source, source_errors = read_text(source_path)
    target, target_errors = read_text(target_path)
    errors = source_errors + target_errors
    checks: dict[str, Any] = {}

    source_tokens = protected_tokens(source)
    target_tokens = protected_tokens(target)
    for kind in source_tokens:
        diff = counter_diff(source_tokens[kind], target_tokens[kind])
        checks[kind] = {"status": "PASS" if not diff["missing"] and not diff["extra"] else "FAIL", **diff}
        if diff["missing"] or diff["extra"]:
            errors.append(f"{kind} tokens differ")

    source_tags = html_tags(source)
    target_tags = html_tags(target)
    tag_diff = counter_diff(source_tags, target_tags)
    checks["html_tags"] = {"status": "PASS" if not tag_diff["missing"] and not tag_diff["extra"] else "FAIL", **tag_diff}
    if tag_diff["missing"] or tag_diff["extra"]:
        errors.append("HTML tag structure differs")

    source_attrs = frozen_html_attributes(source)
    target_attrs = frozen_html_attributes(target)
    attr_diff = counter_diff(source_attrs, target_attrs)
    checks["frozen_html_attributes"] = {
        "status": "PASS" if not attr_diff["missing"] and not attr_diff["extra"] else "FAIL",
        **attr_diff,
    }
    if attr_diff["missing"] or attr_diff["extra"]:
        errors.append("Frozen HTML attribute values differ")

    source_json, source_json_error = json_shape(source_path, source)
    target_json, target_json_error = json_shape(target_path, target)
    if source_json_error:
        errors.append(source_json_error)
    if target_json_error:
        errors.append(target_json_error)
    if source_json is not None and target_json is not None:
        source_shape = shape(source_json)
        target_shape = shape(target_json)
        checks["json_shape"] = {
            "status": "PASS" if source_shape == target_shape else "FAIL",
            "source": source_shape,
            "target": target_shape,
        }
        if source_shape != target_shape:
            errors.append("JSON structure differs")

    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    result = validate(args.source, args.target)
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["status"])
        for error in result["errors"]:
            print(f"- {error}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
