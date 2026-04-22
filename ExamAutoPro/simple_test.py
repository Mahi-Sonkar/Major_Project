import re
from difflib import SequenceMatcher

def normalize_text(text):
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[.,;:!?()[\]{}\"\'`]', '', text)
    text = text.strip()
    return text

def exact_match_normalized(text1, text2):
    return normalize_text(text1) == normalize_text(text2)

# Test the exact issue mentioned by the user
print("=== Testing Exact Issue ===")
student = "Database Management System"
correct = "Database Management System"

norm_student = normalize_text(student)
norm_correct = normalize_text(correct)
exact_match = exact_match_normalized(student, correct)

print(f"Student Answer: '{student}'")
print(f"Correct Answer: '{correct}'")
print(f"Normalized Student: '{norm_student}'")
print(f"Normalized Correct: '{norm_correct}'")
print(f"Exact Match: {exact_match}")
print()

# Test other problematic cases
test_cases = [
    ("Database Management System", "database management system"),
    ("Database Management System", " Database Management System "),
    ("Database Management System", "database management system."),
]

print("=== Testing Other Cases ===")
for text1, text2 in test_cases:
    match = exact_match_normalized(text1, text2)
    print(f"'{text1}' vs '{text2}' -> Match: {match}")
