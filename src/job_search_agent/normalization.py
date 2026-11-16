"""Conservative canonical field and URL normalization."""
from __future__ import annotations

import hashlib
import html
import re
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.hidden += 1
        elif tag in {"p", "br", "li", "div"}:
            self.chunks.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        elif tag in {"p", "li", "div"}:
            self.chunks.append(" ")

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.chunks.append(data)


def normalize_text(value: str | None) -> str:
    """Normalize identity fields, not descriptions."""
    return re.sub(r"\s+", " ", html.unescape(value or "").casefold()).strip()


def clean_description(value: str | None) -> str:
    extractor = _TextExtractor()
    extractor.feed(html.unescape(value or ""))
    text = html.unescape("".join(extractor.chunks))
    return re.sub(r"\s+", " ", text).strip()


def canonical_url(url: str) -> str:
    """Remove known click tracking; preserve requisition/job-ID parameters."""
    parts = urlsplit(url.strip())
    kept = [
        (key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
        and key.lower() not in {"gclid", "fbclid"}
    ]
    return urlunsplit((
        parts.scheme.lower(),
        parts.netloc.lower(),
        parts.path.rstrip("/") or "/",
        urlencode(sorted(kept)),
        "",
    ))


def digest_text(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def listing_external_key(external_id: str | None, url: str) -> str:
    return (
        "id:" + external_id.strip()
        if external_id and external_id.strip()
        else "url:" + digest_text(canonical_url(url))
    )
