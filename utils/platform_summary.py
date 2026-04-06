"""
Generate platform summary pages with score cards and category heatmaps.

Reads source mappings from appendix QMD frontmatter, calculates scores
per region/framework, and outputs HTML for Quarto rendering.
"""

from pathlib import Path
from typing import Dict, Optional

from .scoring import calculate_platform_score
from .quarto_helpers import get_platform_sources
from .summary_table import (
    get_platform_icon,
    normalize_platform_name,
    SCORE_BANDS,
)


def _find_project_root() -> Path:
    project_root = Path.cwd()
    while not (project_root / "utils").exists() and project_root != project_root.parent:
        project_root = project_root.parent
    return project_root


def get_score_band_label(score: float) -> str:
    if score == 0:
        return "Not Available"
    for lo, hi, _, label in SCORE_BANDS:
        if lo <= score < hi:
            return label
    if score >= 100:
        return "Meaningful"
    return "N/A"


def _get_score_band_color(score: float) -> str:
    if score == 0:
        return "#9D9D9C"
    for lo, hi, color, _ in SCORE_BANDS:
        if lo <= score < hi:
            return color
    if score >= 100:
        return "#496AB1"
    return "#9D9D9C"


def _compute_scores_for_sources(
    sources: Dict[str, str], question_type: str, year: str = "2025"
) -> Dict[str, dict]:
    results = {}
    for region, filepath in sources.items():
        try:
            result = calculate_platform_score(
                year=year, question_type=question_type, answers_file=filepath
            )
            results[region] = result
        except Exception as e:
            print(f"<!-- Warning: Failed to calculate {question_type} score for {region}: {e} -->")
    return results


def _generate_score_badge_html(score: float, is_not_applicable: bool = False) -> str:
    if is_not_applicable:
        return '<span style="font-size: 2.2rem; font-weight: 700; color: #999;">N/A</span>'
    color = _get_score_band_color(score)
    return f'<span style="font-size: 2.2rem; font-weight: 700; color: {color};">{score:.0f}</span>'


def _generate_overall_scores_html(
    ugc_scores: Dict[str, dict],
    ads_scores: Dict[str, dict],
    platform_slug: str,
) -> str:
    platform_display = normalize_platform_name(platform_slug)
    icon = get_platform_icon(platform_display, size=24)

    cards = []

    for framework_label, scores in [("User-Generated Content", ugc_scores), ("Advertising", ads_scores)]:
        if not scores:
            badge = _generate_score_badge_html(0, is_not_applicable=True)
            cards.append(
                f'<div style="flex: 1; min-width: 250px; border-radius: 8px; padding: 20px 24px; '
                f'background: #f8f9fa; border: 1px solid #e0e0e0; opacity: 0.5;">'
                f'<div style="margin: 0 0 12px 0; font-size: 1rem; color: #555; font-weight: 600;">{framework_label}</div>'
                f'<div style="margin-bottom: 4px;">{badge}</div>'
                f'<div style="font-size: 0.85rem; font-weight: 600; color: #999;">Not applicable</div>'
                f'</div>'
            )
            continue

        all_na = all(r.get("is_not_applicable", False) for r in scores.values())
        if all_na:
            badge = _generate_score_badge_html(0, is_not_applicable=True)
            cards.append(
                f'<div style="flex: 1; min-width: 250px; border-radius: 8px; padding: 20px 24px; '
                f'background: #f8f9fa; border: 1px solid #e0e0e0; opacity: 0.5;">'
                f'<div style="margin: 0 0 12px 0; font-size: 1rem; color: #555; font-weight: 600;">{framework_label}</div>'
                f'<div style="margin-bottom: 4px;">{badge}</div>'
                f'<div style="font-size: 0.85rem; font-weight: 600; color: #999;">Not applicable</div>'
                f'</div>'
            )
            continue

        region_parts = []
        for region in ["BR", "EU", "UK"]:
            if region in scores:
                r = scores[region]
                if r.get("is_not_applicable", False):
                    region_parts.append(
                        f'<div style="text-align: center; flex: 1;">'
                        f'<div style="font-size: 0.75rem; font-weight: 600; color: #888; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.05em;">{region}</div>'
                        f'<span style="font-size: 2.2rem; font-weight: 700; color: #999;">N/A</span>'
                        f'</div>'
                    )
                else:
                    s = round(r["total_score"])
                    color = _get_score_band_color(s)
                    band = get_score_band_label(s)
                    region_parts.append(
                        f'<div style="text-align: center; flex: 1;">'
                        f'<div style="font-size: 0.75rem; font-weight: 600; color: #888; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.05em;">{region}</div>'
                        f'<span style="font-size: 2.2rem; font-weight: 700; color: {color};">{s}</span>'
                        f'<div style="font-size: 0.75rem; font-weight: 600; color: {color}; margin-top: 2px;">{band}</div>'
                        f'</div>'
                    )

        region_html = "".join(region_parts)
        cards.append(
            f'<div style="flex: 1; min-width: 250px; border-radius: 8px; padding: 20px 24px; '
            f'background: #f8f9fa; border: 1px solid #e0e0e0;">'
            f'<div style="margin: 0 0 16px 0; font-size: 1rem; color: #555; font-weight: 600;">{framework_label}</div>'
            f'<div style="display: flex; gap: 16px;">{region_html}</div>'
            f'</div>'
        )

    cards_html = "".join(cards)
    return f'\n<div style="display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap;">{cards_html}</div>\n'


def generate_platform_summary(platform_slug: str, year: str = "2025"):
    """Generate full platform summary HTML and print it for Quarto `output: asis`."""
    project_root = _find_project_root()

    ugc_sources = get_platform_sources(platform_slug, "ugc", project_root)
    ads_sources = get_platform_sources(platform_slug, "ads", project_root)

    ugc_scores = _compute_scores_for_sources(ugc_sources, "ugc", year) if ugc_sources else {}
    ads_scores = _compute_scores_for_sources(ads_sources, "ads", year) if ads_sources else {}

    print(_generate_overall_scores_html(ugc_scores, ads_scores, platform_slug))

