"""
Sorim.AI — Knowledge Ingestion & Chunking  (ai/rag/ingestion.py)

Loads, cleans, and chunks markdown knowledge base articles with YAML front matter.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any


def parse_front_matter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML-style front matter between leading --- delimiters."""
    if not content.startswith("---"):
        return {}, content.strip()

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content.strip()

    front_raw = parts[1].strip()
    body = parts[2].strip()
    metadata: dict[str, Any] = {}

    current_list_key: str | None = None
    for line in front_raw.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("  - ") and current_list_key:
            item = line[4:].strip().strip("\"'")
            metadata.setdefault(current_list_key, []).append(item)
            continue

        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if not val:
                metadata[key] = []
                current_list_key = key
            elif val.startswith("[") and val.endswith("]"):
                items = [x.strip().strip("\"'") for x in val[1:-1].split(",") if x.strip()]
                metadata[key] = items
                current_list_key = None
            else:
                metadata[key] = val.strip("\"'")
                current_list_key = None

    return metadata, body


def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def chunk_markdown(
    body: str,
    *,
    article_id: str,
    title: str,
    category: str,
    source_file: str,
    content_hash: str,
    max_chunk_chars: int = 600,
    chunk_overlap_chars: int = 100,
) -> list[dict[str, Any]]:
    """
    Heading-aware and paragraph-aware chunker.
    Each chunk retains article and section context.
    """
    sections = re.split(r"\n(?=#{1,3}\s)", body)
    raw_chunks: list[str] = []

    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section) <= max_chunk_chars:
            raw_chunks.append(section)
        else:
            paragraphs = section.split("\n\n")
            current = ""
            for p in paragraphs:
                p = p.strip()
                if not p:
                    continue
                if len(current) + len(p) + 2 <= max_chunk_chars:
                    current = f"{current}\n\n{p}".strip()
                else:
                    if current:
                        raw_chunks.append(current)
                    if len(p) > max_chunk_chars:
                        # Character-level split with overlap
                        start = 0
                        while start < len(p):
                            end = start + max_chunk_chars
                            raw_chunks.append(p[start:end])
                            start += (max_chunk_chars - chunk_overlap_chars)
                        current = ""
                    else:
                        current = p
            if current:
                raw_chunks.append(current)

    chunks: list[dict[str, Any]] = []
    for idx, text in enumerate(raw_chunks):
        chunk_id = f"{article_id}::{idx + 1}"
        # Build first 300-char excerpt
        cleaned_text = re.sub(r"\s+", " ", text).strip()
        excerpt = cleaned_text[:300]
        chunks.append({
            "chunk_id": chunk_id,
            "article_id": article_id,
            "chunk_index": idx + 1,
            "title": title,
            "category": category,
            "source_file": source_file,
            "content_hash": content_hash,
            "text": text,
            "excerpt": excerpt,
        })
    return chunks


def load_and_chunk_article(file_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    raw = file_path.read_text(encoding="utf-8")
    content_hash = compute_content_hash(raw)
    front, body = parse_front_matter(raw)

    article_id = front.get("article_id") or file_path.stem
    title = front.get("title") or article_id.replace("-", " ").title()
    category = front.get("category") or "General"
    tags = front.get("tags") or []
    summary = front.get("summary") or (body[:160] + "...")
    automations = front.get("automations") or []

    chunks = chunk_markdown(
        body,
        article_id=article_id,
        title=title,
        category=category,
        source_file=file_path.name,
        content_hash=content_hash,
    )

    metadata = {
        "_id": article_id,
        "article_id": article_id,
        "title": title,
        "category": category,
        "tags": tags,
        "summary": summary,
        "automations": automations,
        "source_file": file_path.name,
        "content_hash": content_hash,
        "chunk_count": len(chunks),
    }

    return metadata, chunks, raw
