from django.contrib import admin
from .models import AnswerEvaluationResult, QuestionEvaluationResult, GraceMarksRule, EvaluationLog, ScoringRange

@admin.register(ScoringRange)
class ScoringRangeAdmin(admin.ModelAdmin):
    list_display = ['name', 'min_similarity', 'max_similarity', 'marks_percentage', 'exam', 'is_active']
    list_filter = ['is_active', 'exam']
    search_fields = ['name', 'description']

@admin.register(AnswerEvaluationResult)
class AnswerEvaluationResultAdmin(admin.ModelAdmin):
    list_display = ['question_paper', 'obtained_marks', 'total_marks', 'percentage', 'created_at']
    list_filter = ['created_at']
    search_fields = ['question_paper__title']
    readonly_fields = ['created_at']


@admin.register(QuestionEvaluationResult)
class QuestionEvaluationResultAdmin(admin.ModelAdmin):
    list_display = ['answer', 'final_score', 'similarity_score', 'confidence_score', 'evaluation_time']
    list_filter = ['evaluation_time']
    readonly_fields = ['evaluation_time']
@admin.register(GraceMarksRule)
class GraceMarksRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'condition_type', 'condition_value', 'grace_marks', 'is_active']
    list_filter = ['condition_type', 'is_active']
    search_fields = ['name', 'description']

@admin.register(EvaluationLog)
class EvaluationLogAdmin(admin.ModelAdmin):
    list_display = ['answer', 'action', 'timestamp', 'user']
    list_filter = ['timestamp']
    search_fields = ['answer__question__question_text', 'details']
    readonly_fields = ['timestamp']
