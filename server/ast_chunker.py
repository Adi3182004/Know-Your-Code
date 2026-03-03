import os
import re

SUPPORTED_CODE_EXT = (".py", ".js", ".ts", ".jsx")


def _chunk_by_lines(lines, fallback_size=40, overlap=10):
    chunks = []
    start = 0

    while start < len(lines):
        end = start + fallback_size
        chunk_lines = lines[start:end]

        text = "".join(chunk_lines).strip()
        if text:
            chunks.append(
                {
                    "text": text,
                    "start_line": start + 1,
                    "end_line": min(end, len(lines)),
                    "type": "chunk",
                }
            )

        start += fallback_size - overlap

    return chunks


def _python_chunks(lines):
    chunks = []
    pattern = re.compile(r"^\s*(def|class)\s+\w+")

    current_start = None

    for i, line in enumerate(lines):
        if pattern.match(line):
            if current_start is not None:
                chunk_text = "".join(lines[current_start:i]).strip()
                if chunk_text:
                    chunks.append(
                        {
                            "text": chunk_text,
                            "start_line": current_start + 1,
                            "end_line": i,
                            "type": "function_or_class",
                        }
                    )
            current_start = i

    if current_start is not None:
        chunk_text = "".join(lines[current_start:]).strip()
        if chunk_text:
            chunks.append(
                {
                    "text": chunk_text,
                    "start_line": current_start + 1,
                    "end_line": len(lines),
                    "type": "function_or_class",
                }
            )

    return chunks


def _js_chunks(lines):
    chunks = []
    pattern = re.compile(
        r"^\s*(function\s+\w+|\w+\s*=\s*\(?.*\)?\s*=>|class\s+\w+)"
    )

    current_start = None

    for i, line in enumerate(lines):
        if pattern.match(line):
            if current_start is not None:
                chunk_text = "".join(lines[current_start:i]).strip()
                if chunk_text:
                    chunks.append(
                        {
                            "text": chunk_text,
                            "start_line": current_start + 1,
                            "end_line": i,
                            "type": "function_or_class",
                        }
                    )
            current_start = i

    if current_start is not None:
        chunk_text = "".join(lines[current_start:]).strip()
        if chunk_text:
            chunks.append(
                {
                    "text": chunk_text,
                    "start_line": current_start + 1,
                    "end_line": len(lines),
                    "type": "function_or_class",
                }
            )

    return chunks


def ast_chunk_file(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return []

    ext = os.path.splitext(path)[1].lower()

    if ext == ".py":
        chunks = _python_chunks(lines)
    elif ext in (".js", ".ts", ".jsx"):
        chunks = _js_chunks(lines)
    else:
        return _chunk_by_lines(lines)

    if not chunks:
        return _chunk_by_lines(lines)

    return chunks