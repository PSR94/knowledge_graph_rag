import re
from typing import Iterable
from typing import List


def normalize_identifier(value: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return base.strip("-") or "item"


def split_text(text: str, max_chars: int, overlap: int) -> List[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    if len(cleaned) <= max_chars:
        return [cleaned]

    chunks = []
    start = 0
    text_length = len(cleaned)
    while start < text_length:
        stop = min(text_length, start + max_chars)
        if stop < text_length:
            boundary = cleaned.rfind(" ", start, stop)
            if boundary > start + max_chars // 2:
                stop = boundary
        chunk = cleaned[start:stop].strip()
        if chunk:
            chunks.append(chunk)
        if stop >= text_length:
            break
        start = max(0, stop - overlap)
    return chunks


def extract_query_terms(query: str) -> List[str]:
    words = re.findall(r"[a-zA-Z0-9_]+", query.lower())
    unique = []
    for word in words:
        if len(word) < 3:
            continue
        if word not in unique:
            unique.append(word)
    return unique[:6]


def unique_preserving_order(values: Iterable[str]) -> List[str]:
    ordered = []
    for value in values:
        if value not in ordered:
            ordered.append(value)
    return ordered
