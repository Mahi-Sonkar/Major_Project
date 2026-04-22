"""
Text Evaluation Utilities for ExamAutoPro
Provides normalization, fuzzy matching, and improved evaluation logic
"""

import re
from difflib import SequenceMatcher
from typing import Dict, Tuple, Optional


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison by:
    1. Converting to lowercase
    2. Stripping whitespace
    3. Removing extra spaces
    4. Removing common punctuation
    """
    if not text:
        return ""
    
    # Convert to lowercase and strip
    text = text.lower().strip()
    
    # Remove extra spaces and normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common punctuation (but keep important ones like hyphens in technical terms)
    text = re.sub(r'[.,;:!?()[\]{}"\'`]', '', text)
    
    # Remove leading/trailing spaces again
    text = text.strip()
    
    return text


def exact_match_normalized(text1: str, text2: str) -> bool:
    """
    Check if two texts match exactly after normalization
    """
    return normalize_text(text1) == normalize_text(text2)


def fuzzy_similarity(text1: str, text2: str) -> float:
    """
    Calculate fuzzy similarity between two texts using SequenceMatcher
    Returns a score between 0.0 and 1.0
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalize both texts
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    
    # Calculate similarity
    return SequenceMatcher(None, norm1, norm2).ratio()


def evaluate_text_similarity(student_answer: str, correct_answer: str, 
                          question_type: str = 'descriptive') -> Dict:
    """
    Evaluate text similarity with different strategies based on question type
    
    Args:
        student_answer: Student's submitted answer
        correct_answer: The correct answer
        question_type: Type of question (mcq, short_answer, descriptive, essay)
    
    Returns:
        Dictionary with evaluation results
    """
    if not student_answer or not correct_answer:
        return {
            'score': 0,
            'similarity': 0.0,
            'is_correct': False,
            'feedback': 'No answer provided',
            'evaluation_method': 'none'
        }
    
    # MCQ questions require exact match with normalization
    if question_type == 'mcq':
        is_correct = exact_match_normalized(student_answer, correct_answer)
        return {
            'score': 1.0 if is_correct else 0.0,
            'similarity': 1.0 if is_correct else 0.0,
            'is_correct': is_correct,
            'feedback': 'Correct answer selected' if is_correct else 'Incorrect answer',
            'evaluation_method': 'exact_normalized'
        }
    
    # For descriptive questions, use fuzzy matching
    similarity = fuzzy_similarity(student_answer, correct_answer)
    
    # Determine score and feedback based on similarity
    if similarity >= 0.9:
        score = 1.0
        feedback = 'Excellent answer - matches perfectly'
        is_correct = True
    elif similarity >= 0.7:
        score = 0.8
        feedback = 'Good answer - mostly correct'
        is_correct = True
    elif similarity >= 0.5:
        score = 0.6
        feedback = 'Partially correct - some key points missing'
        is_correct = False
    elif similarity >= 0.3:
        score = 0.3
        feedback = 'Basic understanding but needs improvement'
        is_correct = False
    else:
        score = 0.0
        feedback = 'Incorrect answer - does not match expected response'
        is_correct = False
    
    return {
        'score': score,
        'similarity': similarity,
        'is_correct': is_correct,
        'feedback': feedback,
        'evaluation_method': 'fuzzy_matching'
    }


def evaluate_mcq_option(selected_option_text: str, correct_option_text: str) -> Dict:
    """
    Evaluate MCQ option selection with improved text matching
    
    Args:
        selected_option_text: Text of the selected option
        correct_option_text: Text of the correct option
    
    Returns:
        Dictionary with evaluation results
    """
    return evaluate_text_similarity(selected_option_text, correct_option_text, 'mcq')


def extract_key_concepts(text: str) -> list:
    """
    Extract key concepts from text by splitting on common delimiters
    """
    if not text:
        return []
    
    # Split on commas, semicolons, and common delimiters
    concepts = re.split(r'[,;:|\/\-\n]', text)
    
    # Normalize and clean each concept
    normalized_concepts = []
    for concept in concepts:
        norm = normalize_text(concept)
        if norm and len(norm) > 1:  # Keep meaningful concepts
            normalized_concepts.append(norm)
    
    return normalized_concepts


def keyword_coverage(student_answer: str, keywords: str) -> Dict:
    """
    Check keyword coverage in student answer
    
    Args:
        student_answer: Student's submitted answer
        keywords: Comma-separated keywords to check
    
    Returns:
        Dictionary with keyword coverage results
    """
    if not student_answer or not keywords:
        return {
            'coverage': 0.0,
            'matched_keywords': [],
            'total_keywords': 0,
            'feedback': 'No keywords to check'
        }
    
    # Extract and normalize keywords
    keyword_list = extract_key_concepts(keywords)
    student_concepts = extract_key_concepts(student_answer)
    
    # Find matches
    matched_keywords = []
    for keyword in keyword_list:
        if any(keyword in concept or concept in keyword for concept in student_concepts):
            matched_keywords.append(keyword)
    
    # Calculate coverage
    coverage = len(matched_keywords) / len(keyword_list) if keyword_list else 0.0
    
    return {
        'coverage': coverage,
        'matched_keywords': matched_keywords,
        'total_keywords': len(keyword_list),
        'feedback': f'Covered {len(matched_keywords)}/{len(keyword_list)} key concepts'
    }


def hybrid_evaluation(student_answer: str, correct_answer: str, 
                     keywords: str = "", question_type: str = 'descriptive',
                     max_marks: int = 1) -> Dict:
    """
    Hybrid evaluation combining similarity and keyword coverage
    
    Args:
        student_answer: Student's submitted answer
        correct_answer: The correct answer
        keywords: Comma-separated keywords (optional)
        question_type: Type of question
        max_marks: Maximum marks for the question
    
    Returns:
        Dictionary with comprehensive evaluation results
    """
    # Basic similarity evaluation
    similarity_result = evaluate_text_similarity(student_answer, correct_answer, question_type)
    
    # Keyword coverage evaluation (if keywords provided)
    keyword_result = keyword_coverage(student_answer, keywords) if keywords else {
        'coverage': 0.0,
        'matched_keywords': [],
        'total_keywords': 0,
        'feedback': 'No keywords provided'
    }
    
    # Calculate final score (70% similarity, 30% keywords)
    similarity_weight = 0.7
    keyword_weight = 0.3
    
    if keyword_result['total_keywords'] > 0:
        final_score = (similarity_result['score'] * similarity_weight + 
                      keyword_result['coverage'] * keyword_weight)
    else:
        final_score = similarity_result['score']
    
    # Convert to marks
    marks_obtained = int(final_score * max_marks)
    
    # Generate comprehensive feedback
    feedback_parts = [similarity_result['feedback']]
    if keyword_result['total_keywords'] > 0:
        feedback_parts.append(keyword_result['feedback'])
    
    return {
        'score': final_score,
        'marks_obtained': marks_obtained,
        'similarity': similarity_result['similarity'],
        'is_correct': similarity_result['is_correct'],
        'feedback': ' | '.join(feedback_parts),
        'evaluation_method': 'hybrid',
        'keyword_coverage': keyword_result,
        'similarity_result': similarity_result
    }
