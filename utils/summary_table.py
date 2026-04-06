"""
Generate summary heatmap tables for transparency assessments.
"""

from pathlib import Path
from typing import Dict, Optional, Union
import yaml
from .scoring import calculate_platform_score
from .quarto_helpers import parse_qmd_frontmatter


def get_score_class(score: float) -> str:
    """
    Determine CSS class based on score range.

    Transparency Scale:
    - Meaningful (81-100): Well-established, openly accessible data infrastructure enabling systematic collection
    - Limited (61-80): Functional access tools with notable limitations (paywalls, restricted scope, etc.)
    - Deficient (41-60): Partial transparency resources with significant gaps preventing reliable research
    - Minimal (21-40): Only minimal data access, most features absent or severely constrained
    - Negligible (1-20): Negligible transparency infrastructure, nearly all criteria unmet
    - Not Available (0): No data access mechanisms despite framework applicability

    Args:
        score: Score value (0-100)

    Returns:
        CSS class name for color coding
    """
    if score == 0:
        return "score-not-available"
    elif score >= 81:
        return "score-ideal"
    elif score >= 61:
        return "score-satisfactory"
    elif score >= 41:
        return "score-regular"
    elif score >= 21:
        return "score-precarious"
    else:
        return "score-irrelevant"


VLOP_PLATFORMS = {
    'facebook', 'instagram', 'linkedin', 'pinterest',
    'snapchat', 'tiktok', 'x', 'youtube',
}

PLATFORM_ICON_OVERRIDES = {
    'kwai': 'kuaishou',
    'linkedin': 'https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/linkedin.svg',
}

SIMPLEICONS_CDN = 'https://cdn.simpleicons.org'


def get_platform_icon(platform_display: str, size: int = 16) -> str:
    """Return an <img> tag for the platform's brand icon via Simple Icons CDN."""
    key = platform_display.lower().split('/')[0].strip()
    override = PLATFORM_ICON_OVERRIDES.get(key)
    if override and override.startswith('http'):
        url = override
    else:
        slug = override or key
        url = f'{SIMPLEICONS_CDN}/{slug}/000000'
    return (
        f'<img src="{url}" '
        f'alt="{platform_display}" width="{size}" height="{size}" '
        f'style="vertical-align: middle; margin-right: 6px;">'
    )


def normalize_platform_name(platform_name: str) -> str:
    """
    Normalize platform directory name to display name.

    Args:
        platform_name: Directory name (lowercase)

    Returns:
        Display name with proper capitalization
    """
    special_cases = {
        'x': 'X',
        'tiktok': 'TikTok',
        'youtube': 'YouTube',
        'linkedin': 'LinkedIn',
        'whatsapp': 'WhatsApp'
    }
    return special_cases.get(platform_name.lower(), platform_name.title())


def scan_assessments(project_root: Path, scope: str) -> Dict[str, Dict[str, Optional[Union[float, str]]]]:
    """
    Scan QMD files and calculate scores based on `sources` frontmatter.

    Reads sources.<scope> dict from each appendix QMD to get
    {region: filepath} mappings, then calculates scores.

    Args:
        project_root: Project root directory
        scope: Either 'ugc' or 'ads'

    Returns:
        Dictionary mapping platform names to region scores:
        {'Meta': {'BR': 45.2, 'EU': 38.7, 'UK': None}, ...}
    """
    appendices_dir = project_root / 'chapters' / 'appendices'
    all_regions = ['BR', 'EU', 'UK']
    results = {}

    if not appendices_dir.exists():
        return results

    score_cache: Dict[str, Optional[float]] = {}

    def calculate_score(filepath: str) -> Optional[float]:
        if filepath in score_cache:
            return score_cache[filepath]
        assessment_file = project_root / filepath
        if not assessment_file.exists():
            score_cache[filepath] = None
            return None
        try:
            result = calculate_platform_score(
                year='2025',
                question_type=scope,
                answers_file=filepath
            )
            val = round(result.get('total_score', 0.0))
        except Exception as e:
            print(f"Warning: Failed to calculate score for {filepath}: {e}")
            val = None
        score_cache[filepath] = val
        return val

    for qmd_file in sorted(appendices_dir.glob('*.qmd')):
        frontmatter = parse_qmd_frontmatter(qmd_file)
        platform_display = frontmatter.get('title') or normalize_platform_name(qmd_file.stem)

        sources = frontmatter.get('sources', {})
        mapping = sources.get(scope, {})
        if not mapping:
            continue

        results[platform_display] = {r: None for r in all_regions}
        for region, filepath in mapping.items():
            if region in all_regions:
                results[platform_display][region] = calculate_score(filepath)

    return results


SCORE_BANDS = [
    (0, 20, '#EA4E54', 'Negligible'),
    (20, 40, '#F28B4C', 'Minimal'),
    (40, 60, '#F3CB00', 'Deficient'),
    (60, 80, '#41B5DF', 'Limited'),
    (80, 100, '#496AB1', 'Meaningful'),
]




def generate_summary_heatmap(
    scope: str,
    include_average_row: bool = True,
    show_values: bool = True
) -> str:
    """
    Generate HTML heatmap table for UGC or Ads assessments.

    Args:
        scope: Either 'ugc' or 'ads'
        include_average_row: If True, adds per-region average row at the bottom
        show_values: If True, shows numeric values inside cells; if False, shows colors only

    Returns:
        HTML string with styled table
    """
    project_root = Path.cwd()

    # Search upward for project root
    while not (project_root / 'utils').exists() and project_root != project_root.parent:
        project_root = project_root.parent

    scores = scan_assessments(project_root, scope)

    html = '''
<style>
.heatmap-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 2px;
    margin: 20px 0;
    font-family: system-ui, -apple-system, sans-serif;
}
.heatmap-table th, .heatmap-table td {
    padding: 10px 12px;
    text-align: center;
    font-weight: 500;
    border-radius: 3px;
}
.heatmap-table th {
    background-color: #f8f9fa;
    font-weight: 600;
}
.heatmap-table td.platform-name {
    text-align: left;
    font-weight: 600;
    background-color: #f8f9fa;
}
.score-ideal { background-color: #496AB1 !important; color: #ffffff !important; font-weight: 600 !important; }
.score-satisfactory { background-color: #41B5DF !important; color: #1A4A5C !important; font-weight: 600 !important; }
.score-regular { background-color: #F3CB00 !important; color: #5C4A00 !important; font-weight: 600 !important; }
.score-precarious { background-color: #F28B4C !important; color: #663A1F !important; font-weight: 600 !important; }
.score-irrelevant { background-color: #EA4E54 !important; color: #ffffff !important; font-weight: 600 !important; }
.score-not-available { background-color: #EDEDED !important; color: #9D9D9C !important; font-weight: 600 !important; border: 1px solid #d0d0d0 !important; }
.score-missing { background-color: #e0e0e0 !important; color: #666 !important; font-style: italic; }
.average-row td {
    background-color: #4a4a4a !important;
    color: #ffffff !important;
    font-weight: 700 !important;
}
.vlop-badge {
    display: inline-block;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.04em;
    padding: 1px 4px;
    border-radius: 3px;
    background-color: #003399;
    color: #ffffff;
    vertical-align: middle;
    margin-left: 5px;
    line-height: 1.4;
}
</style>

<table class="heatmap-table">
    <thead>
        <tr>
            <th>Platform</th>
            <th>Brazil</th>
            <th>EU</th>
            <th>UK</th>
        </tr>
    </thead>
    <tbody>
'''

    # Calculate average score for each platform for sorting
    def calculate_average(regions_dict):
        numeric_scores = [
            score for score in regions_dict.values()
            if score is not None and score != 'N/A' and isinstance(score, (int, float))
        ]
        return sum(numeric_scores) / len(numeric_scores) if numeric_scores else -1

    # Sort platforms by average score (descending)
    sorted_platforms = sorted(scores.items(), key=lambda x: calculate_average(x[1]), reverse=True)

    region_averages = {}
    if include_average_row:
        for region in ['BR', 'EU', 'UK']:
            region_scores = [
                regions.get(region)
                for _, regions in sorted_platforms
                if isinstance(regions.get(region), (int, float))
            ]
            region_averages[region] = (
                round(sum(region_scores) / len(region_scores)) if region_scores else None
            )

    for platform, regions in sorted_platforms:
        html += f'        <tr>\n'
        icon = get_platform_icon(platform)
        vlop_key = platform.lower().split('/')[0].strip()
        vlop_badge = '<span class="vlop-badge" title="Very Large Online Platform (EU DSA)">VLOP</span>' if vlop_key in VLOP_PLATFORMS else ''
        html += f'            <td class="platform-name">{icon}{platform}{vlop_badge}</td>\n'

        for region in ['BR', 'EU', 'UK']:
            score = regions.get(region)

            if score is None:
                display_text = '—' if show_values else '&nbsp;'
                html += f'            <td class="score-missing">{display_text}</td>\n'
            elif score == 'N/A':
                display_text = 'N/A' if show_values else '&nbsp;'
                html += f'            <td class="score-missing">{display_text}</td>\n'
            else:
                css_class = get_score_class(score)
                display_text = f'{score:.0f}' if show_values else '&nbsp;'
                html += f'            <td class="{css_class}">{display_text}</td>\n'

        html += f'        </tr>\n'

    if include_average_row and show_values:
        html += '        <tr class="average-row">\n'
        html += '            <td class="platform-name"><strong>Average</strong></td>\n'
        for region in ['BR', 'EU', 'UK']:
            avg = region_averages.get(region)
            if avg is None:
                display_text = '—' if show_values else '&nbsp;'
                html += f'            <td>{display_text}</td>\n'
            else:
                display_text = f'<strong>{avg:.0f}</strong>' if show_values else '&nbsp;'
                html += f'            <td>{display_text}</td>\n'
        html += '        </tr>\n'

    html += '''    </tbody>
</table>
<p style="font-size: 12px; color: #555; margin-top: 4px;">
  <span class="vlop-badge">VLOP</span>
  &nbsp;Very Large Online Platform designated under the EU Digital Services Act (DSA), subject to enhanced transparency and accountability obligations.
</p>
'''

    return html
