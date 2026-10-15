"""Check repository-local Markdown links, anchors, and HTML image sources offline."""

import os
import re
import unicodedata
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {
    ".git",
    ".venv",
    "node_modules",
    "dist",
    "work",
    "outputs",
    "__pycache__",
    ".pytest_cache",
}


def headings(path):
    anchors = set()
    counts = {}
    content = re.sub(r"```.*?```", "", path.read_text(), flags=re.S)
    for heading in re.findall(r"^#{1,6}\s+(.+)$", content, flags=re.M):
        text = re.sub(r"<[^>]*>", "", heading).strip().lower()
        text = "".join(
            c for c in text if c in " -_" or unicodedata.category(c)[0] in {"L", "N"}
        )
        slug = text.replace(" ", "-")
        number = counts.get(slug, 0)
        counts[slug] = number + 1
        anchors.add(slug if not number else f"{slug}-{number}")
    return anchors


def check():
    failures = []
    checked = 0
    documents = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDED]
        documents.extend(Path(base) / name for name in files if name.endswith(".md"))
    for document in documents:
        content = re.sub(r"```.*?```", "", document.read_text(), flags=re.S)
        targets = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", content)
        targets += re.findall(
            r"<(?:img|a)\b[^>]*\b(?:src|href)=[\"']([^\"']+)[\"']", content, flags=re.I
        )
        for target in targets:
            target = unescape(target.strip().strip("<>"))
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc:
                continue
            checked += 1
            resolved = (
                (document.parent / unquote(parsed.path)).resolve()
                if parsed.path
                else document
            )
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                failures.append(
                    f"{document.relative_to(ROOT)}: link escapes repository: {target}"
                )
                continue
            if not resolved.exists():
                failures.append(
                    f"{document.relative_to(ROOT)}: missing target: {target}"
                )
            elif (
                parsed.fragment
                and resolved.suffix == ".md"
                and unquote(parsed.fragment) not in headings(resolved)
            ):
                failures.append(
                    f"{document.relative_to(ROOT)}: missing heading: {target}"
                )
    if failures:
        print("\n".join(failures))
        return 1
    print(
        f"Documentation passed: {len(documents)} Markdown files, {checked} local links/assets."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(check())
