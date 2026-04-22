from django.urls import path
from . import views

app_name = 'evaluation'

urlpatterns = [
    path('results/', views.QuestionEvaluationResultListView.as_view(), name='evaluation_results'),
    path('evaluate/<int:answer_id>/', views.evaluate_answer, name='evaluate_answer'),
    path('analytics/', views.evaluation_analytics, name='evaluation_analytics'),
    
    # Scoring Ranges
    path('scoring-ranges/', views.ScoringRangeListView.as_view(), name='scoring_range_list'),
    path('scoring-ranges/create/', views.ScoringRangeCreateView.as_view(), name='scoring_range_create'),
    path('scoring-ranges/<int:pk>/update/', views.ScoringRangeUpdateView.as_view(), name='scoring_range_update'),
    path('scoring-ranges/<int:pk>/delete/', views.ScoringRangeDeleteView.as_view(), name='scoring_range_delete'),
]
