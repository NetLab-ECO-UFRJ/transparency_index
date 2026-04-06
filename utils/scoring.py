"""
Scoring utilities for the Social Media Transparency Evaluation.

Implements the two-component methodology score (0–100):

  S_SC = 75 × Σ(w_i × SC_i)    — Special criteria  (75% of total)
  S_OC = 25 × Σ(OC_j) / N_app  — Other criteria    (25% of total)
  Total = S_SC + S_OC

Special criteria (SC): each question carries its own weight w_i from the YAML.
  UGC: 4 criteria, weights [0.30, 0.30, 0.30, 0.10]
  ADS: 3 criteria, weights [0.50, 0.30, 0.20]

Other criteria (OC): all questions carry equal weight — only the answer weight
  OC_j matters (typically 0, 0.5, or 1). N/A answers are excluded from N_app.
"""

from typing import Dict, List, Any, Tuple
from .loader import load_questions, load_answers, load_categories, get_answer_weight, get_answer_label

# Maps question_type to the code prefix used in question codes (e.g. UGC_SC1, AD_OC3)
_CODE_PREFIX = {'ugc': 'UGC', 'ads': 'AD'}


def _validate_question_type(question_type: str) -> str:
    """Return the code prefix for question_type, or raise ValueError."""
    prefix = _CODE_PREFIX.get(question_type)
    if not prefix:
        raise ValueError(f"Invalid question_type '{question_type}'. Must be 'ugc' or 'ads'.")
    return prefix


def _special_codes(questions_dict: Dict[str, Any], question_type: str) -> set:
    """Return the set of SC question codes (e.g. {UGC_SC1, UGC_SC2, UGC_SC3, UGC_SC4})."""
    prefix = _validate_question_type(question_type) + '_SC'
    return {q['code'] for q in questions_dict.values() if q.get('code', '').startswith(prefix)}


def _other_criteria_count(questions_dict: Dict[str, Any], question_type: str) -> int:
    """Return the expected number of OC questions for this question_type."""
    prefix = _validate_question_type(question_type) + '_OC'
    return sum(1 for q in questions_dict.values() if q.get('code', '').startswith(prefix))


def calculate_category_scores(
    questions_dict: Dict[str, Any],
    answers_list: List[Dict[str, str]],
    category: str
) -> Tuple[float, float, List[Dict[str, Any]]]:
    """
    Score all questions in a category.

    Returns (actual_score, max_possible_score, per-question detail list).
    Each question contributes question['weight'] × answer_weight to the score.
    """
    actual_score = 0.0
    max_possible_score = 0.0
    details = []

    for answer_item in answers_list:
        code = answer_item['code']
        selected = answer_item['selected_answer']

        if code not in questions_dict:
            raise ValueError(f"Question code '{code}' not found in questions.yml")

        question = questions_dict[code]

        if question['category'] != category:
            raise ValueError(
                f"Question {code} belongs to category '{question['category']}', "
                f"but was found in '{category}' answers"
            )

        answer_weight = get_answer_weight(question, selected)
        question_score = question['weight'] * answer_weight

        actual_score += question_score
        max_possible_score += question['weight']

        details.append({
            'question_code': code,
            'question_text': question['text'],
            'question_weight': question['weight'],
            'selected_value': selected,
            'selected_label': get_answer_label(question, selected),
            'answer_weight': answer_weight,
            'question_score': question_score,
            'question_max': question['weight'],
            'notes': answer_item.get('notes', ''),
            'category': question['category'],
            'category_label': question['category_label'],
        })

    return actual_score, max_possible_score, details


def calculate_methodology_score(
    answers_data: Dict[str, Any],
    questions_dict: Dict[str, Any],
    question_type: str
) -> Dict[str, Any]:
    """
    Compute the methodology score (0–100) for a single framework (UGC or ADS).

    S_SC = 75 × Σ(w_i × SC_i)   weights and answer values from the questions YAML
    S_OC = 25 × Σ(OC_j) / N_app  answer weights only; N/A excluded from denominator
    Total = S_SC + S_OC
    """
    special_answers = answers_data.get('special-criteria_answers', [])
    expected_sc_codes = _special_codes(questions_dict, question_type)
    expected_oc_count = _other_criteria_count(questions_dict, question_type)

    # --- Special criteria: S_SC = 75 × Σ(w_i × SC_i) ---
    if len(special_answers) != len(expected_sc_codes):
        raise ValueError(
            f"Expected {len(expected_sc_codes)} special criteria for {question_type.upper()}, "
            f"got {len(special_answers)}"
        )

    special_weighted_sum = 0.0
    for item in special_answers:
        code = item['code']
        if code not in questions_dict:
            raise ValueError(f"Question code '{code}' not found")
        if code not in expected_sc_codes:
            raise ValueError(f"'{code}' is not a special criterion for {question_type.upper()}")
        q = questions_dict[code]
        special_weighted_sum += q['weight'] * get_answer_weight(q, item['selected_answer'])

    special_score = 75 * special_weighted_sum

    # --- Other criteria: S_OC = 25 × Σ(OC_j) / N_app ---
    other_sum = 0.0
    other_count = 0
    applicable_count = 0

    for key, category_answers in answers_data.items():
        if key in ('metadata', 'special-criteria_answers') or not key.endswith('_answers'):
            continue
        for item in category_answers:
            code = item['code']
            selected = item['selected_answer']
            if code not in questions_dict:
                raise ValueError(f"Question code '{code}' not found")
            # OC_j is the answer weight only — question weight is intentionally ignored here
            # because the methodology treats all other criteria as equal weight.
            other_sum += get_answer_weight(questions_dict[code], selected)
            other_count += 1
            if selected != 'not_applicable':
                applicable_count += 1

    if other_count != expected_oc_count:
        raise ValueError(
            f"Expected {expected_oc_count} other criteria for {question_type.upper()}, "
            f"got {other_count}"
        )

    # N_app: exclude N/A from denominator; fall back to total if all are N/A
    denominator = applicable_count if applicable_count > 0 else other_count
    other_score = 25 * (other_sum / denominator)

    # A platform is fully not-applicable when every answer is N/A
    # (e.g. Discord for UGC — no API exists, so the entire framework is N/A)
    all_not_applicable = (
        applicable_count == 0
        and all(item['selected_answer'] == 'not_applicable' for item in special_answers)
    )

    return {
        'special_score': special_score,
        'other_score': other_score,
        'total_score': special_score + other_score,
        'total_max': 100.0,
        'is_not_applicable': all_not_applicable,
    }


def calculate_platform_score(
    platform: str = None,
    region: str = None,
    year: str = "2025",
    scope: str = "regional",
    question_type: str = "all",
    answers_dir: str = None,
    answers_file: str = None
) -> Dict[str, Any]:
    """
    Load answers and compute scores for a platform.

    When question_type is 'ugc' or 'ads', applies the two-component methodology
    formula (S_SC + S_OC). When question_type is 'all', returns a simple weighted
    sum across all categories.

    Returns a dict with: metadata, categories, total_score, total_max,
    total_percentage, special_score, other_score, is_not_applicable.
    """
    questions_dict = load_questions(year=year, question_type=question_type)
    categories_list = load_categories(year=year, question_type=question_type)
    answers_data = load_answers(platform, region, year, scope, question_type, answers_dir, answers_file)

    category_results = {}

    for category_info in categories_list:
        name = category_info['name']
        # Answer keys may use hyphens (e.g. "special-criteria_answers") while
        # category names use underscores — try both variants.
        key = f"{name}_answers"
        if key not in answers_data:
            key = key.replace('_', '-', 1)
            if key not in answers_data:
                continue

        score, max_score, details = calculate_category_scores(
            questions_dict, answers_data[key], name
        )

        category_results[name] = {
            'label': category_info['label'],
            'description': category_info['description'],
            'score': score,
            'max': max_score,
            'percentage': (score / max_score * 100) if max_score > 0 else 0,
            'details': details,
        }

    if question_type in ('ugc', 'ads'):
        m = calculate_methodology_score(answers_data, questions_dict, question_type)
        return {
            'metadata': answers_data['metadata'],
            'categories': category_results,
            'total_score': m['total_score'],
            'total_max': m['total_max'],
            'total_percentage': m['total_score'],  # already on 0–100 scale
            'special_score': m['special_score'],
            'other_score': m['other_score'],
            'is_not_applicable': m['is_not_applicable'],
        }

    total_score = sum(cat['score'] for cat in category_results.values())
    total_max = sum(cat['max'] for cat in category_results.values())
    return {
        'metadata': answers_data['metadata'],
        'categories': category_results,
        'total_score': total_score,
        'total_max': total_max,
        'total_percentage': (total_score / total_max * 100) if total_max > 0 else 0,
    }
