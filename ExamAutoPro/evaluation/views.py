from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db import models
from django.db.models import Q, Avg, Count
from django.urls import reverse_lazy
from .models import AnswerEvaluationResult, QuestionEvaluationResult, GraceMarksRule, EvaluationLog, OCREvaluation, NLPEvaluation, ScoringRange
from .forms import ScoringRangeForm
from .engines import OCREngine, NLPEngine, GraceMarksEngine
from core.enhanced_evaluation_engine import EnhancedEvaluationEngine
from core.advanced_nlp_evaluation import AdvancedNLPEvaluation, AdvancedOCREvaluation
from exams.models import Answer, ExamSubmission
import json
import logging

logger = logging.getLogger(__name__)

class ScoringRangeListView(LoginRequiredMixin, ListView):
    model = ScoringRange
    template_name = 'evaluation/scoring_range_list.html'
    context_object_name = 'rules'
    
    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return ScoringRange.objects.filter(created_by=self.request.user)
        elif self.request.user.is_admin_user:
            return ScoringRange.objects.all()
        return ScoringRange.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # Calculate statistics for template
        context['total_ranges'] = queryset.count()
        context['active_ranges'] = queryset.filter(is_active=True).count()
        context['user_ranges'] = queryset.count()
        
        return context

class ScoringRangeCreateView(LoginRequiredMixin, CreateView):
    model = ScoringRange
    form_class = ScoringRangeForm
    template_name = 'evaluation/scoring_range_form.html'
    success_url = reverse_lazy('evaluation:scoring_range_list')
    
    def get_initial(self):
        initial = super().get_initial()
        pdf_id = self.request.GET.get('pdf')
        if pdf_id:
            initial['pdf_document'] = pdf_id
        return initial
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        
        # Handle paper image upload and create automatic PDF analysis
        paper_image = form.cleaned_data.get('paper_image')
        if paper_image:
            try:
                # Create PDF document from uploaded image
                from pdf_analysis.models import PDFDocument
                import uuid
                
                # Create a new PDF document entry with the image as the file
                pdf_document = PDFDocument.objects.create(
                    title=f"Paper Image - {form.instance.name}",
                    pdf_file=paper_image,  # Store the image as the file for now
                    uploaded_by=self.request.user,
                    document_type='exam_paper',
                    analysis_status='pending'
                )
                
                # Link the scoring range to the created PDF document
                form.instance.pdf_document = pdf_document
                
                messages.info(self.request, "Paper image uploaded successfully! PDF analysis will be processed automatically.")
                
            except Exception as e:
                messages.warning(self.request, f"Paper image uploaded but PDF analysis creation failed: {str(e)}")
        
        messages.success(self.request, "Scoring range created successfully!")
        return super().form_valid(form)

class ScoringRangeUpdateView(LoginRequiredMixin, UpdateView):
    model = ScoringRange
    form_class = ScoringRangeForm
    template_name = 'evaluation/scoring_range_form.html'
    success_url = reverse_lazy('evaluation:scoring_range_list')
    
    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return ScoringRange.objects.filter(created_by=self.request.user)
        elif self.request.user.is_admin_user:
            return ScoringRange.objects.all()
        return ScoringRange.objects.none()
    
    def form_valid(self, form):
        messages.success(self.request, "Scoring range updated successfully!")
        return super().form_valid(form)

class ScoringRangeDeleteView(LoginRequiredMixin, DeleteView):
    model = ScoringRange
    template_name = 'evaluation/scoring_range_confirm_delete.html'
    success_url = reverse_lazy('evaluation:scoring_range_list')
    
    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return ScoringRange.objects.filter(created_by=self.request.user)
        elif self.request.user.is_admin_user:
            return ScoringRange.objects.all()
        return ScoringRange.objects.none()
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Scoring range deleted successfully!")
        return super().delete(request, *args, **kwargs)

class QuestionEvaluationResultListView(LoginRequiredMixin, ListView):
    model = QuestionEvaluationResult
    template_name = 'evaluation/evaluation_result_list.html'
    context_object_name = 'results'
    paginate_by = 20
    
    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return QuestionEvaluationResult.objects.filter(
                answer__exam_submission__exam__teacher=self.request.user
            )
        elif self.request.user.role == 'student':
            return QuestionEvaluationResult.objects.filter(
                answer__exam_submission__student=self.request.user
            )
        elif self.request.user.is_admin_user:
            return QuestionEvaluationResult.objects.all()
        return QuestionEvaluationResult.objects.none()

@login_required
def evaluate_answer(request, answer_id):
    """Evaluate a single answer"""
    answer = get_object_or_404(Answer, id=answer_id)
    
    # Check permissions
    if request.user.role == 'student' and answer.exam_submission.student != request.user:
        return redirect('dashboard')
    
    if request.user.role == 'teacher' and answer.exam_submission.exam.teacher != request.user:
        return redirect('dashboard')
    
    try:
        # Get evaluation result or create new one
        result, created = QuestionEvaluationResult.objects.get_or_create(answer=answer)
        
        if created or not result.final_score:
            # Run evaluation
            ocr_engine = OCREngine()
            nlp_engine = NLPEngine()
            grace_engine = GraceMarksEngine()
            
            # OCR processing if needed
            if answer.uploaded_file:
                ocr_result = ocr_engine.process_answer(answer)
                # Text is already updated in answer.answer_text by process_answer
            
            # NLP evaluation
            if answer.answer_text:
                nlp_result = nlp_engine.evaluate_answer(answer)
                result.similarity_score = nlp_result.get('similarity', 0.0)
                result.keyword_match_score = nlp_result.get('keyword_score', 0.0)
                result.confidence_score = nlp_result.get('confidence', 0.0)
                result.initial_score = float(nlp_result.get('base_score', 0.0))
            
            # Apply grace marks
            grace_result = grace_engine.apply_grace_marks(answer, nlp_result)
            result.grace_marks_applied = grace_result.get('grace_marks', 0)
            result.final_score = float(nlp_result.get('score', 0.0))
            result.feedback = grace_result.get('feedback', '')
            
            # Update Answer model as well
            answer.marks_obtained = int(result.final_score)
            answer.evaluated_by_ai = True
            answer.confidence_score = result.confidence_score
            answer.feedback = result.feedback
            answer.save()
            
            result.save()
        
        return render(request, 'evaluation/evaluation_result_detail.html', {
            'result': result,
            'answer': answer
        })
        
    except Exception as e:
        logger.error(f"Error evaluating answer {answer_id}: {str(e)}")
        messages.error(request, "Error occurred during evaluation.")
        return redirect('evaluation:evaluation_results')

@login_required
def evaluation_analytics(request):
    """Evaluation analytics dashboard"""
    if not request.user.role in ['teacher', 'admin']:
        return redirect('dashboard')
    
    # Get evaluation statistics
    if request.user.role == 'teacher':
        results = QuestionEvaluationResult.objects.filter(
            answer__exam_submission__exam__teacher=request.user
        )
    else:
        results = QuestionEvaluationResult.objects.all()
    
    # Calculate statistics
    total_evaluations = results.count()
    avg_score = results.aggregate(avg_score=Avg('final_score'))['avg_score'] or 0
    avg_similarity = results.aggregate(avg_sim=Avg('similarity_score'))['avg_sim'] or 0
    avg_confidence = results.aggregate(avg_conf=Avg('confidence_score'))['avg_conf'] or 0
    
    # Score distribution
    score_ranges = {
        '0-20': results.filter(final_score__lte=20).count(),
        '21-40': results.filter(final_score__gt=20, final_score__lte=40).count(),
        '41-60': results.filter(final_score__gt=40, final_score__lte=60).count(),
        '61-80': results.filter(final_score__gt=60, final_score__lte=80).count(),
        '81-100': results.filter(final_score__gt=80).count(),
    }
    
    context = {
        'total_evaluations': total_evaluations,
        'avg_score': round(avg_score, 2),
        'avg_similarity': round(avg_similarity, 2),
        'avg_confidence': round(avg_confidence, 2),
        'score_ranges': score_ranges,
    }
    
    return render(request, 'evaluation/evaluation_analytics.html', context)
