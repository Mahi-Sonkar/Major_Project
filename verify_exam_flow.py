import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock heavy dependencies before importing anything that might use them
sys.modules['face_recognition'] = MagicMock()
sys.modules['face_recognition_models'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['spacy'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

import django
from django.test import Client
from django.urls import reverse
from django.utils import timezone

# Setup Django environment
sys.path.append(os.path.join(os.getcwd(), 'ExamAutoPro'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ExamAutoPro.settings')
django.setup()

from django.contrib.auth import get_user_model
from exams.models import Exam, Question, QuestionOption, ExamSubmission, Answer

User = get_user_model()

def run_submission_test():
    print("Starting Exam Submission Flow Test (Mocked AI)...")
    
    # 1. Setup Data
    teacher, _ = User.objects.get_or_create(
        email='teacher_test@example.com',
        defaults={'username': 'teacher_test', 'role': 'teacher', 'is_staff': True}
    )
    teacher.set_password('pass123')
    teacher.save()
    
    student, _ = User.objects.get_or_create(
        email='student_test@example.com',
        defaults={'username': 'student_test', 'role': 'student'}
    )
    student.set_password('pass123')
    student.save()
    
    # Clean up old tests
    Exam.objects.filter(title="Test Exam 5 Logic").delete()
    
    exam = Exam.objects.create(
        title="Test Exam 5 Logic",
        teacher=teacher,
        duration=60,
        total_marks=10,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=1),
        status='published',
        allow_multiple_attempts=True,
        max_attempts=3
    )
    
    q1 = Question.objects.create(
        exam=exam,
        question_text="What is the capital of France?",
        question_type='mcq',
        marks=5,
        order=1
    )
    opt1 = QuestionOption.objects.create(question=q1, option_text="Paris", is_correct=True)
    opt2 = QuestionOption.objects.create(question=q1, option_text="London", is_correct=False)
    
    q2 = Question.objects.create(
        exam=exam,
        question_text="Explain photosynthesis.",
        question_type='short_answer',
        marks=5,
        order=2,
        model_answer="Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods from carbon dioxide and water.",
        keywords="sunlight, carbon dioxide, water, green plants"
    )
    
    print(f"Created Exam ID: {exam.id}")
    
    # 2. Simulate Taking Exam
    client = Client()
    client.login(email='student_test@example.com', password='pass123')
    
    # Start the exam
    response = client.get(reverse('take_exam', args=[exam.id]))
    print(f"Take Exam Status: {response.status_code}")
    
    submission = ExamSubmission.objects.filter(student=student, exam=exam, status='in_progress').first()
    if not submission:
        print("Error: Submission not created!")
        return
    print(f"Active Submission ID: {submission.id}")
    
    # 3. Simulate Submitting Exam
    # We mock the AI evaluation inside the view call
    with patch('exams.views.auto_evaluate_submission') as mock_eval:
        # Mock what auto_evaluate_submission would do
        def side_effect(sub):
            sub.status = 'evaluated'
            sub.total_marks_obtained = 10
            sub.percentage = 100
            sub.save()
            return sub
        mock_eval.side_effect = side_effect
        
        submit_url = reverse('submit_exam', args=[exam.id])
        post_data = {
            f'question_{q1.id}': opt1.id,
            f'question_{q2.id}': "Plants use sunlight to make food from CO2 and water."
        }
        
        print("Submitting exam...")
        response = client.post(submit_url, post_data, follow=True)
        print(f"Submit Exam Status: {response.status_code}")
    
    # 4. Verify Results
    submission.refresh_from_db()
    print(f"Submission Status After Submit: {submission.status}")
    print(f"Total Marks Obtained: {submission.total_marks_obtained}")
    
    if submission.status == 'evaluated' and submission.total_marks_obtained == 10:
        print("\n✅ TEST PASSED: Submission flow logic is working correctly!")
    else:
        print("\n❌ TEST FAILED: Verification failed.")

if __name__ == "__main__":
    run_submission_test()
