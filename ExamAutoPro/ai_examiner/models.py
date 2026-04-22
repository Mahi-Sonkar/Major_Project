"""
AI Examiner Models for Handwritten Answer Evaluation
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class AIExaminer(models.Model):
    """AI Examiner model for managing handwritten evaluation sessions"""
    
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.teacher.email}"


class ModelAnswer(models.Model):
    """Model answer uploaded by teacher for evaluation comparison"""
    
    ai_examiner = models.ForeignKey(AIExaminer, on_delete=models.CASCADE, related_name='model_answers')
    question_number = models.IntegerField()
    question_text = models.TextField()
    max_marks = models.IntegerField(default=10)
    answer_file = models.FileField(upload_to='model_answers/', help_text="PDF or Image of model answer")
    transcribed_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['question_number']
        unique_together = ['ai_examiner', 'question_number']
    
    def __str__(self):
        return f"Q{self.question_number}: {self.question_text[:50]}..."


class StudentAnswerSheet(models.Model):
    """Student answer sheet uploaded for evaluation"""
    
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('ocr_completed', 'OCR Completed'),
        ('evaluating', 'Evaluating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ai_examiner = models.ForeignKey(AIExaminer, on_delete=models.CASCADE, related_name='student_sheets')
    student_name = models.CharField(max_length=200)
    student_id = models.CharField(max_length=50, blank=True, null=True)
    answer_file = models.FileField(upload_to='student_answers/', help_text="PDF or Image of student answer sheet")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    total_marks_obtained = models.IntegerField(default=0)
    total_max_marks = models.IntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    evaluated_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['student_name']
    
    def __str__(self):
        return f"{self.student_name} - {self.ai_examiner.title}"


class HandwrittenAnswer(models.Model):
    """Individual handwritten answer extracted from student sheet"""
    
    student_sheet = models.ForeignKey(StudentAnswerSheet, on_delete=models.CASCADE, related_name='answers')
    question_number = models.IntegerField()
    original_text = models.TextField(blank=True, null=True, help_text="Raw OCR text")
    cleaned_text = models.TextField(blank=True, null=True, help_text="Cleaned and processed text")
    confidence_score = models.FloatField(default=0.0, help_text="OCR confidence score")
    marks_obtained = models.IntegerField(default=0)
    max_marks = models.IntegerField(default=10)
    is_correct = models.BooleanField(default=False)
    feedback = models.TextField(blank=True, null=True)
    evaluation_data = models.JSONField(blank=True, null=True, help_text="Detailed AI evaluation data")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['question_number']
        unique_together = ['student_sheet', 'question_number']
    
    def __str__(self):
        return f"Q{self.question_number}: {self.student_sheet.student_name}"


class EvaluationSession(models.Model):
    """Individual evaluation session with Gemini AI"""
    
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    handwritten_answer = models.OneToOneField(HandwrittenAnswer, on_delete=models.CASCADE)
    model_answer = models.ForeignKey(ModelAnswer, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    gemini_response = models.TextField(blank=True, null=True)
    processing_time = models.FloatField(default=0.0, help_text="Processing time in seconds")
    api_cost = models.FloatField(default=0.0, help_text="API cost in credits")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Evaluation: Q{self.handwritten_answer.question_number}"


class GradeCard(models.Model):
    """Generated grade card for student evaluation"""
    
    student_sheet = models.OneToOneField(StudentAnswerSheet, on_delete=models.CASCADE)
    pdf_file = models.FileField(upload_to='grade_cards/', help_text="Generated grade card PDF")
    summary_data = models.JSONField(default=dict, help_text="Summary statistics and scores")
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Grade Card: {self.student_sheet.student_name}"


class EvaluationHistory(models.Model):
    """History of all AI evaluations for tracking and analytics"""
    
    ai_examiner = models.ForeignKey(AIExaminer, on_delete=models.CASCADE, related_name='evaluation_history')
    student_sheet = models.ForeignKey(StudentAnswerSheet, on_delete=models.CASCADE)
    total_questions = models.IntegerField(default=0)
    total_marks = models.IntegerField(default=0)
    total_obtained = models.IntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    grade = models.CharField(max_length=2, blank=True, null=True)
    processing_time = models.FloatField(default=0.0)
    api_cost = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"History: {self.student_sheet.student_name} - {self.percentage:.1f}%"
