"""
Quarto helper utilities for generating platform evaluation reports.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def parse_qmd_frontmatter(qmd_path: Path) -> dict:
    """Extract YAML frontmatter from a QMD file."""
    content = qmd_path.read_text()
    if content.startswith('---'):
        end = content.find('---', 3)
        if end != -1:
            return yaml.safe_load(content[3:end]) or {}
    return {}


def get_platform_sources(
    platform_slug: str,
    question_type: str,
    project_root: Path,
) -> Dict[str, str]:
    """Read `sources.<question_type>` from a platform's appendix QMD frontmatter.

    Returns {region_code: filepath} dict. Raises FileNotFoundError for missing
    YAML files so callers surface clear errors.
    """
    qmd_path = project_root / "chapters" / "appendices" / f"{platform_slug}.qmd"
    if not qmd_path.exists():
        return {}

    frontmatter = parse_qmd_frontmatter(qmd_path)
    sources = frontmatter.get("sources", {})
    mapping = sources.get(question_type, {})
    if not mapping:
        return {}

    result: Dict[str, str] = {}
    for region, filepath in mapping.items():
        full_path = project_root / filepath
        if not full_path.exists():
            raise FileNotFoundError(
                f"Source file not found: {filepath} "
                f"(platform={platform_slug}, region={region}, type={question_type})"
            )
        result[region] = filepath
    return result


def get_answer_icon(answer: str) -> str:
    """Get icon for answer value based on answer text."""
    answer_lower = answer.lower() if answer else ""
    if answer_lower.startswith("yes") or answer_lower == "full" or answer_lower.startswith("free"):
        return "✅"
    elif answer_lower.startswith("partial"):
        return "⚠️"
    elif answer_lower == "not_applicable" or answer_lower == "not applicable":
        return "➖"
    elif answer_lower == "no" or answer_lower == "no or not applicable":
        return "❌"
    return ""


