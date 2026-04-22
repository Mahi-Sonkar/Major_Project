"""
AI Examiner URL Configuration
"""

from django.urls import path
from . import views

app_name = 'ai_examiner'

urlpatterns = [
    # AI Examiner Dashboard
    path('', views.ai_examiner_dashboard.as_view(), name='dashboard'),
    
    # AI Examiner Management
    path('create/', views.create_ai_examiner.as_view(), name='create'),
    path('list/', views.ai_examiner_list.as_view(), name='list'),
    path('<uuid:pk>/', views.ai_examiner_detail.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.edit_ai_examiner.as_view(), name='edit'),
    path('<uuid:pk>/delete/', views.delete_ai_examiner.as_view(), name='delete'),
    
    # Model Answers
    path('<uuid:examiner_id>/model-answers/', views.model_answer_list.as_view(), name='model_answers'),
    path('<uuid:examiner_id>/model-answers/add/', views.add_model_answer.as_view(), name='add_model_answer'),
    path('model-answers/<int:pk>/edit/', views.edit_model_answer.as_view(), name='edit_model_answer'),
    path('model-answers/<int:pk>/delete/', views.delete_model_answer.as_view(), name='delete_model_answer'),
    
    # Student Answer Sheets
    path('<uuid:examiner_id>/upload-sheets/', views.upload_student_sheets.as_view(), name='upload_sheets'),
    path('<uuid:examiner_id>/student-sheets/', views.student_sheets_list.as_view(), name='student_sheets'),
    path('student-sheets/<uuid:pk>/', views.student_sheet_detail.as_view(), name='student_sheet_detail'),
    path('student-sheets/<uuid:pk>/evaluate/', views.evaluate_student_sheet, name='evaluate_sheet'),
    
    # Evaluation Results
    path('student-sheets/<uuid:pk>/results/', views.evaluation_results, name='evaluation_results'),
    path('student-sheets/<uuid:pk>/grade-card/', views.generate_grade_card, name='grade_card'),
    path('student-sheets/<uuid:pk>/grade-card/download/', views.download_grade_card, name='download_grade_card'),
    
    # Batch Operations
    path('<uuid:examiner_id>/batch-evaluate/', views.batch_evaluate, name='batch_evaluate'),
    path('<uuid:examiner_id>/evaluation-summary/', views.evaluation_summary, name='evaluation_summary'),
    
    # API Endpoints
    path('api/ocr-process/', views.api_ocr_process, name='api_ocr_process'),
    path('api/evaluate-answer/', views.api_evaluate_answer, name='api_evaluate_answer'),
]
