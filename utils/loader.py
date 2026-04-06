"""
Data loader utilities for Social Media Evaluation project.

This module provides functions to load and parse YAML configuration files
for questions and platform-specific answers.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any


# Get the project root directory (parent of utils/)
PROJECT_ROOT = Path(__file__).parent.parent


def _resolve_question_file(year: str, question_type: str) -> Path:
    """Resolve question file path for flat and legacy data layouts."""
    filename = f"questions_{question_type}_{year}.yml"
    candidates = [
        PROJECT_ROOT / "data" / filename,
        PROJECT_ROOT / "data" / year / filename,
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def load_questions(year: str = "2025", question_type: str = "all") -> Dict[str, Any]:
    """
    Load questions configuration from separate UGC and ADS files.
    Both files use section-based structure (no 'categories' wrapper).

    Args:
        year: Year of the evaluation (default: '2025')
        question_type: Type of questions to load - 'ugc', 'ads', or 'all' (default: 'all')

    Returns:
        Dictionary with question code as keys and question data as values.
        Each question includes its parent category (section) information.

    Example structure:
        {
            'UGC_01': {
                'category': 'consistency',
                'category_label': 'Consistency',
                'category_description': 'Evaluates how consistently...',
                'text': 'Does the platform...',
                'weight': 2.0,
                'answers': [...]
            }
        }

    Note: Questions use 'title' field in YAML, which is loaded into 'text' field here.
    """
    questions_dict = {}

    # Determine which files to load
    files_to_load = []
    if question_type in ["ugc", "all"]:
        files_to_load.append(_resolve_question_file(year, "ugc"))
    if question_type in ["ads", "all"]:
        files_to_load.append(_resolve_question_file(year, "ads"))

    if not files_to_load:
        raise ValueError(f"Invalid question_type: {question_type}. Must be 'ugc', 'ads', or 'all'")

    # Load each file
    for full_path in files_to_load:
        with open(full_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Section-based structure (consistency, accessibility, special-criteria, etc.)
        for section_name, questions_list in data.items():
            if isinstance(questions_list, list):
                # Convert section name to label (e.g., "special-criteria" or "special_criteria" -> "Special Criteria")
                category_label = section_name.replace('-', ' ').replace('_', ' ').title()

                for question in questions_list:
                    code = question['code']
                    question_text = question.get('title', '')

                    questions_dict[code] = {
                        'category': section_name,
                        'category_label': category_label,
                        'category_description': question.get('description', ''),
                        'code': code,
                        'text': question_text,
                        'weight': question['weight'],
                        'answers': question['answers']
                    }

    return questions_dict


def load_categories(year: str = "2025", question_type: str = "all") -> List[Dict[str, str]]:
    """
    Load categories from separate UGC and ADS question files.

    Args:
        year: Year of the evaluation (default: '2025')
        question_type: Type of questions to load categories from - 'ugc', 'ads', or 'all' (default: 'all')

    Returns:
        List of category dictionaries with name, label, and description.
        Categories are deduplicated by name when loading from multiple files.

    Example:
        [
            {
                'name': 'consistency',
                'label': 'Consistency',
                'description': 'Evaluates how consistently...'
            }
        ]
    """
    categories_dict = {}

    # Determine which files to load
    files_to_load = []
    if question_type in ["ugc", "all"]:
        files_to_load.append(_resolve_question_file(year, "ugc"))
    if question_type in ["ads", "all"]:
        files_to_load.append(_resolve_question_file(year, "ads"))

    if not files_to_load:
        raise ValueError(f"Invalid question_type: {question_type}. Must be 'ugc', 'ads', or 'all'")

    # Load each file and merge categories (deduplicate by name)
    for full_path in files_to_load:
        with open(full_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Section-based structure: extract sections as categories
        for section_name, questions_list in data.items():
            if isinstance(questions_list, list) and questions_list:
                if section_name not in categories_dict:
                    # Convert section name to label (e.g., "special-criteria" or "special_criteria" -> "Special Criteria")
                    category_label = section_name.replace('-', ' ').replace('_', ' ').title()
                    # Use first question's description as category description
                    category_desc = questions_list[0].get('description', '')

                    categories_dict[section_name] = {
                        'name': section_name,
                        'label': category_label,
                        'description': category_desc
                    }

    return list(categories_dict.values())


def load_answers(platform: str = None, region: str = None, year: str = "2025",
                 scope: str = "regional", question_type: str = None,
                 answers_dir: str = None, answers_file: str = None) -> Dict[str, Any]:
    """
    Load platform-specific answers for a given region.

    Args:
        platform: Platform name (e.g., 'reddit', 'facebook') - optional if answers_file is provided
        region: Region code (e.g., 'BR', 'UK', 'EU') or 'GLOBAL' for global scope - optional if answers_file is provided
        year: Year of the evaluation (default: '2025')
        scope: Either 'regional' or 'global' (default: 'regional')
        question_type: Type of answers to load - 'ugc' or 'ads' (optional, for split files)
        answers_dir: Override directory containing answer files (optional, legacy)
        answers_file: Direct path to answer file (e.g., 'data/global/kwai/ugc.yml')
                     If provided, all path auto-discovery is skipped

    Returns:
        Dictionary containing metadata and categorized answers

    Example structure:
        {
            'metadata': {...},
            'consistency_answers': [...],
            'timeliness_answers': [...]
        }
    """
    if answers_file:
        # Use direct file path
        filepath = PROJECT_ROOT / answers_file
    elif answers_dir is None:
        data_roots = [
            PROJECT_ROOT / "data",
            PROJECT_ROOT / "data" / year,
        ]

        if scope == "global":
            # Global structure candidates:
            # - data/global/<platform>/<question_type>.yml
            # - data/global/<platform>/<platform>_<question_type>.yml (legacy)
            # - data/global/<platform>.yml
            if question_type:
                filenames = [
                    f"{question_type.lower()}.yml",
                    f"{platform.lower()}_{question_type.lower()}.yml",
                ]
            else:
                filenames = [f"{platform.lower()}.yml"]

            candidates = []
            for root in data_roots:
                for filename in filenames:
                    candidates.append(root / "global" / platform.lower() / filename)
                    candidates.append(root / "global" / filename)
            filepath = next((p for p in candidates if p.exists()), candidates[0])
        else:
            # Regional structure candidates:
            # - data/regional/<REGION>/<platform>/<question_type>.yml
            # - data/regional/<REGION>/<platform>/<platform>_<region>_<question_type>.yml (legacy)
            if question_type:
                filenames = [
                    f"{question_type.lower()}.yml",
                    f"{platform.lower()}_{region.lower()}_{question_type.lower()}.yml",
                ]
            else:
                filenames = [f"{platform.lower()}_{region.lower()}.yml"]

            candidates = []
            for root in data_roots:
                for filename in filenames:
                    candidates.append(root / "regional" / region.upper() / platform.lower() / filename)
            filepath = next((p for p in candidates if p.exists()), candidates[0])
    else:
        # Legacy path support
        filename = f"{platform.lower()}_{region.lower()}.yml"
        filepath = PROJECT_ROOT / answers_dir / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Answer file not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        answers_data = yaml.safe_load(f)

    return answers_data


def get_answer_weight(question: Dict[str, Any], selected_value: str) -> float:
    """
    Get the weight for a specific answer value within a question.

    Args:
        question: Question dictionary containing answers list
        selected_value: The selected answer value (e.g., 'yes', 'no', 'partial')

    Returns:
        Weight of the selected answer (0.0 to 1.0)

    Raises:
        ValueError: If selected_value not found in question's answers
    """
    if selected_value == 'not_applicable':
        return 0.0

    for answer in question['answers']:
        if answer['value'] == selected_value:
            return answer['weight']

    raise ValueError(
        f"Answer value '{selected_value}' not found in question '{question['code']}'"
    )


def get_answer_label(question: Dict[str, Any], selected_value: str) -> str:
    """
    Get the human-readable label for a specific answer value.

    Args:
        question: Question dictionary containing answers list
        selected_value: The selected answer value

    Returns:
        Label text for the answer
    """
    if selected_value == 'not_applicable':
        return 'Not Applicable'

    for answer in question['answers']:
        if answer['value'] == selected_value:
            return answer['label']

    return selected_value
