"""Planner-domain utilities (AES shared kernel).

Pure helpers shared across planner capabilities and the agent orchestrator.
"""

from __future__ import annotations

import re


def slugify_title(title: str) -> str:
    """Return a conservative branch-name slug derived from a PR title."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)[:50].rstrip("-")
    slug = slug.removesuffix(".lock")
    return slug or "unnamed"