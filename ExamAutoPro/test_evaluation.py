#!/usr/bin/env python
"""
Test script for the improved evaluation system
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ExamAutoPro.settings')
django.setup()

from evaluation.utils import normalize_text, exact_match_normalized, fuzzy_similarity, hybrid_evaluation

def test_text_normalization():
    """Test text normalization functions"""
    print('=== Testing Text Normalization ===')
    test_cases = [
        ('Database Management System', 'database management system'),
        ('Database Management System', ' Database Management System '),
        ('Database Management System', 'database management system.'),
        ('DBMS', 'dbms'),
        ('Database Management', 'database management systems')
    ]

    for text1, text2 in test_cases:
        norm1 = normalize_text(text1)
        norm2 = normalize_text(text2)
        exact_match = exact_match_normalized(text1, text2)
        similarity = fuzzy_similarity(text1, text2)
        
        print(f'"{text1}" vs "{text2}"')
        print(f'  Normalized: "{norm1}" vs "{norm2}"')
        print(f'  Exact Match: {exact_match}')
        print(f'  Similarity: {similarity:.3f}')
        print()

def test_hybrid_evaluation():
    """Test hybrid evaluation system"""
    print('=== Testing Hybrid Evaluation ===')
    
    # Test case 1: Exact match
    result = hybrid_evaluation(
        student_answer='Database Management System',
        correct_answer='Database Management System',
        keywords='database, management, system',
        question_type='short_answer',
        max_marks=5
    )
    
    print(f'Test 1 - Exact Match:')
    print(f'  Student: Database Management System')
    print(f'  Correct: Database Management System')
    print(f'  Score: {result["score"]:.3f}')
    print(f'  Marks: {result["marks_obtained"]}/5')
    print(f'  Is Correct: {result["is_correct"]}')
    print(f'  Feedback: {result["feedback"]}')
    print()
    
    # Test case 2: Case difference
    result = hybrid_evaluation(
        student_answer='database management system',
        correct_answer='Database Management System',
        keywords='database, management, system',
        question_type='short_answer',
        max_marks=5
    )
    
    print(f'Test 2 - Case Difference:')
    print(f'  Student: database management system')
    print(f'  Correct: Database Management System')
    print(f'  Score: {result["score"]:.3f}')
    print(f'  Marks: {result["marks_obtained"]}/5')
    print(f'  Is Correct: {result["is_correct"]}')
    print(f'  Feedback: {result["feedback"]}')
    print()
    
    # Test case 3: Partial match
    result = hybrid_evaluation(
        student_answer='Database system',
        correct_answer='Database Management System',
        keywords='database, management, system',
        question_type='short_answer',
        max_marks=5
    )
    
    print(f'Test 3 - Partial Match:')
    print(f'  Student: Database system')
    print(f'  Correct: Database Management System')
    print(f'  Score: {result["score"]:.3f}')
    print(f'  Marks: {result["marks_obtained"]}/5')
    print(f'  Is Correct: {result["is_correct"]}')
    print(f'  Feedback: {result["feedback"]}')
    print()

if __name__ == '__main__':
    test_text_normalization()
    test_hybrid_evaluation()
    print('=== Test Complete ===')
