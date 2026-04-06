"""
Social Media Evaluation utilities package.

Provides data loading and scoring functions for Quarto reports.
"""

from .loader import (
    load_questions,
    load_answers,
    load_categories,
    get_answer_weight,
    get_answer_label
)

from .scoring import calculate_platform_score

from .platform_summary import generate_platform_summary

__all__ = [
    'load_questions',
    'load_answers',
    'load_categories',
    'get_answer_weight',
    'get_answer_label',
    'calculate_platform_score',
    'generate_platform_summary',
]
