"""
AI Examiner Views for Handwritten Answer Evaluation
"""

import os
import uuid
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db import transaction
from .models import AIExaminer, ModelAnswer, StudentAnswerSheet, HandwrittenAnswer, EvaluationSession, GradeCard, EvaluationHistory
from .evaluation_engine import AIExaminerEngine
from .forms import AIExaminerForm, ModelAnswerForm, StudentAnswerSheetForm
from .utils import generate_grade_card_pdf

# Mixin for teacher-only access
class TeacherRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_teacher:
            messages.error(request, "Access denied. Teacher privileges required.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


class ai_examiner_dashboard(TeacherRequiredMixin, ListView):
    """Main dashboard for AI Examiner"""
    model = AIExaminer
    template_name = 'ai_examiner/dashboard.html'
    context_object_name = 'ai_examiners'
    paginate_by = 10
    
    def get_queryset(self):
        return AIExaminer.objects.filter(teacher=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_examiners'] = self.get_queryset().count()
        context['active_examiners'] = self.get_queryset().filter(status='created').count()
        context['completed_examiners'] = self.get_queryset().filter(status='completed').count()
        return context


class create_ai_examiner(TeacherRequiredMixin, CreateView):
    """Create new AI Examiner session"""
    model = AIExaminer
    form_class = AIExaminerForm
    template_name = 'ai_examiner/create.html'
    success_url = reverse_lazy('ai_examiner:list')
    
    def form_valid(self, form):
        form.instance.teacher = self.request.user
        messages.success(self.request, "AI Examiner session created successfully!")
        return super().form_valid(form)


class ai_examiner_list(TeacherRequiredMixin, ListView):
    """List all AI Examiner sessions"""
    model = AIExaminer
    template_name = 'ai_examiner/list.html'
    context_object_name = 'ai_examiners'
    paginate_by = 15
    
    def get_queryset(self):
        return AIExaminer.objects.filter(teacher=self.request.user).order_by('-created_at')


class ai_examiner_detail(TeacherRequiredMixin, DetailView):
    """Detail view for AI Examiner session"""
    model = AIExaminer
    template_name = 'ai_examiner/detail.html'
    context_object_name = 'ai_examiner'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ai_examiner = self.get_object()
        
        # Get model answers
        context['model_answers'] = ModelAnswer.objects.filter(ai_examiner=ai_examiner)
        
        # Get student sheets
        context['student_sheets'] = StudentAnswerSheet.objects.filter(ai_examiner=ai_examiner)
        
        # Get evaluation summary
        engine = AIExaminerEngine()
        context['evaluation_summary'] = engine.get_evaluation_summary(ai_examiner)
        
        return context


class model_answer_list(TeacherRequiredMixin, DetailView):
    """List and manage model answers for an AI Examiner"""
    model = AIExaminer
    template_name = 'ai_examiner/model_answers.html'
    context_object_name = 'ai_examiner'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_answers'] = ModelAnswer.objects.filter(ai_examiner=self.get_object())
        return context


class add_model_answer(TeacherRequiredMixin, CreateView):
    """Add model answer to AI Examiner"""
    model = ModelAnswer
    form_class = ModelAnswerForm
    template_name = 'ai_examiner/add_model_answer.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ai_examiner'] = get_object_or_404(AIExaminer, id=self.kwargs['examiner_id'])
        return context
    
    def form_valid(self, form):
        ai_examiner = get_object_or_404(AIExaminer, id=self.kwargs['examiner_id'])
        form.instance.ai_examiner = ai_examiner
        
        # Process uploaded file with OCR
        try:
            from .easyocr_engine import HandwrittenProcessor
            processor = HandwrittenProcessor()
            ocr_result = processor.process_model_answer(form.instance)
            
            if ocr_result['success']:
                messages.success(self.request, f"Model answer processed successfully with {ocr_result['confidence']:.2f} confidence")
            else:
                messages.warning(self.request, f"OCR processing failed: {ocr_result['error']}")
        except Exception as e:
            messages.warning(self.request, f"OCR processing encountered an error: {str(e)}")
        
        messages.success(self.request, "Model answer added successfully!")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('ai_examiner:model_answers', kwargs={'examiner_id': self.kwargs['examiner_id']})


class upload_student_sheets(TeacherRequiredMixin, CreateView):
    """Upload student answer sheets for evaluation"""
    model = StudentAnswerSheet
    form_class = StudentAnswerSheetForm
    template_name = 'ai_examiner/upload_sheets.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ai_examiner'] = get_object_or_404(AIExaminer, id=self.kwargs['examiner_id'])
        return context
    
    def form_valid(self, form):
        ai_examiner = get_object_or_404(AIExaminer, id=self.kwargs['examiner_id'])
        form.instance.ai_examiner = ai_examiner
        
        # Generate unique ID for the student sheet
        form.instance.id = uuid.uuid4()
        
        messages.success(self.request, "Student answer sheet uploaded successfully!")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('ai_examiner:student_sheets', kwargs={'examiner_id': self.kwargs['examiner_id']})


class student_sheets_list(TeacherRequiredMixin, DetailView):
    """List all student answer sheets for an AI Examiner"""
    model = AIExaminer
    template_name = 'ai_examiner/student_sheets.html'
    context_object_name = 'ai_examiner'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student_sheets'] = StudentAnswerSheet.objects.filter(ai_examiner=self.get_object())
        return context


class student_sheet_detail(TeacherRequiredMixin, DetailView):
    """Detail view for student answer sheet"""
    model = StudentAnswerSheet
    template_name = 'ai_examiner/student_sheet_detail.html'
    context_object_name = 'student_sheet'
    pk_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_sheet = self.get_object()
        
        # Get handwritten answers
        context['handwritten_answers'] = HandwrittenAnswer.objects.filter(student_sheet=student_sheet)
        
        # Get model answers for comparison
        context['model_answers'] = ModelAnswer.objects.filter(ai_examiner=student_sheet.ai_examiner)
        
        return context


class edit_ai_examiner(TeacherRequiredMixin, UpdateView):
    """Edit AI Examiner session"""
    model = AIExaminer
    form_class = AIExaminerForm
    template_name = 'ai_examiner/edit.html'
    success_url = reverse_lazy('ai_examiner:list')
    
    def form_valid(self, form):
        messages.success(self.request, "AI Examiner session updated successfully!")
        return super().form_valid(form)


class delete_ai_examiner(TeacherRequiredMixin, DeleteView):
    """Delete AI Examiner session"""
    model = AIExaminer
    template_name = 'ai_examiner/confirm_delete.html'
    success_url = reverse_lazy('ai_examiner:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "AI Examiner session deleted successfully!")
        return super().delete(request, *args, **kwargs)


class edit_model_answer(TeacherRequiredMixin, UpdateView):
    """Edit model answer"""
    model = ModelAnswer
    form_class = ModelAnswerForm
    template_name = 'ai_examiner/edit_model_answer.html'
    
    def get_success_url(self):
        return reverse('ai_examiner:model_answers', kwargs={'examiner_id': self.object.ai_examiner.id})


class delete_model_answer(TeacherRequiredMixin, DeleteView):
    """Delete model answer"""
    model = ModelAnswer
    template_name = 'ai_examiner/confirm_delete_model_answer.html'
    
    def get_success_url(self):
        return reverse('ai_examiner:model_answers', kwargs={'examiner_id': self.object.ai_examiner.id})


@login_required
def evaluate_student_sheet(request, pk):
    """Evaluate a single student answer sheet"""
    if not request.user.is_teacher:
        messages.error(request, "Access denied. Teacher privileges required.")
        return redirect('dashboard')
    
    student_sheet = get_object_or_404(StudentAnswerSheet, id=pk)
    model_answers = ModelAnswer.objects.filter(ai_examiner=student_sheet.ai_examiner)
    
    if not model_answers.exists():
        messages.error(request, "No model answers found for this AI Examiner session.")
        return redirect('ai_examiner:student_sheet_detail', pk=pk)
    
    try:
        # Initialize AI Examiner Engine
        engine = AIExaminerEngine()
        
        # Perform evaluation
        result = engine.evaluate_student_sheet(student_sheet, model_answers)
        
        if result['success']:
            messages.success(request, f"Evaluation completed! Score: {result['total_marks']}/{result['total_max_marks']} ({result['percentage']:.1f}%)")
        else:
            messages.error(request, f"Evaluation failed: {result['error']}")
        
    except Exception as e:
        messages.error(request, f"An error occurred during evaluation: {str(e)}")
    
    return redirect('ai_examiner:student_sheet_detail', pk=pk)


@login_required
def batch_evaluate(request, examiner_id):
    """Evaluate all student sheets for an AI Examiner"""
    if not request.user.is_teacher:
        messages.error(request, "Access denied. Teacher privileges required.")
        return redirect('dashboard')
    
    ai_examiner = get_object_or_404(AIExaminer, id=examiner_id)
    model_answers = ModelAnswer.objects.filter(ai_examiner=ai_examiner)
    student_sheets = StudentAnswerSheet.objects.filter(ai_examiner=ai_examiner, status='uploaded')
    
    if not model_answers.exists():
        messages.error(request, "No model answers found for this AI Examiner session.")
        return redirect('ai_examiner:detail', pk=examiner_id)
    
    if not student_sheets.exists():
        messages.error(request, "No student sheets found to evaluate.")
        return redirect('ai_examiner:detail', pk=examiner_id)
    
    try:
        # Initialize AI Examiner Engine
        engine = AIExaminerEngine()
        
        # Perform batch evaluation
        results = engine.batch_evaluate_sheets(student_sheets, model_answers)
        
        successful_evaluations = len([r for r in results if r['result']['success']])
        failed_evaluations = len([r for r in results if not r['result']['success']])
        
        messages.success(request, f"Batch evaluation completed! {successful_evaluations} successful, {failed_evaluations} failed.")
        
    except Exception as e:
        messages.error(request, f"An error occurred during batch evaluation: {str(e)}")
    
    return redirect('ai_examiner:detail', pk=examiner_id)


@login_required
def evaluation_results(request, pk):
    """Show detailed evaluation results for a student sheet"""
    if not request.user.is_teacher:
        messages.error(request, "Access denied. Teacher privileges required.")
        return redirect('dashboard')
    
    student_sheet = get_object_or_404(StudentAnswerSheet, id=pk)
    handwritten_answers = HandwrittenAnswer.objects.filter(student_sheet=student_sheet)
    
    context = {
        'student_sheet': student_sheet,
        'handwritten_answers': handwritten_answers,
        'model_answers': ModelAnswer.objects.filter(ai_examiner=student_sheet.ai_examiner)
    }
    
    return render(request, 'ai_examiner/evaluation_results.html', context)


@login_required
def generate_grade_card(request, pk):
    """Generate grade card for student evaluation"""
    if not request.user.is_teacher:
        messages.error(request, "Access denied. Teacher privileges required.")
        return redirect('dashboard')
    
    student_sheet = get_object_or_404(StudentAnswerSheet, id=pk)
    
    if student_sheet.status != 'completed':
        messages.error(request, "Evaluation must be completed before generating grade card.")
        return redirect('ai_examiner:student_sheet_detail', pk=pk)
    
    try:
        # Generate PDF grade card
        pdf_content = generate_grade_card_pdf(student_sheet)
        
        # Save grade card record
        grade_card, created = GradeCard.objects.get_or_create(
            student_sheet=student_sheet,
            defaults={'pdf_file': ContentFile(pdf_content, f'grade_card_{student_sheet.id}.pdf')}
        )
        
        if not created:
            # Update existing grade card
            grade_card.pdf_file = ContentFile(pdf_content, f'grade_card_{student_sheet.id}.pdf')
            grade_card.save()
        
        messages.success(request, "Grade card generated successfully!")
        
    except Exception as e:
        messages.error(request, f"Error generating grade card: {str(e)}")
    
    return redirect('ai_examiner:evaluation_results', pk=pk)


@login_required
def download_grade_card(request, pk):
    """Download grade card PDF"""
    if not request.user.is_teacher:
        messages.error(request, "Access denied. Teacher privileges required.")
        return redirect('dashboard')
    
    student_sheet = get_object_or_404(StudentAnswerSheet, id=pk)
    
    try:
        grade_card = GradeCard.objects.get(student_sheet=student_sheet)
        
        # Serve the PDF file
        response = HttpResponse(grade_card.pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="grade_card_{student_sheet.student_name}.pdf"'
        return response
        
    except GradeCard.DoesNotExist:
        messages.error(request, "Grade card not found. Please generate it first.")
        return redirect('ai_examiner:evaluation_results', pk=pk)


@login_required
def evaluation_summary(request, examiner_id):
    """Get evaluation summary for an AI Examiner session"""
    if not request.user.is_teacher:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    ai_examiner = get_object_or_404(AIExaminer, id=examiner_id)
    
    try:
        engine = AIExaminerEngine()
        summary = engine.get_evaluation_summary(ai_examiner)
        
        return JsonResponse(summary)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# API Endpoints
@login_required
def api_ocr_process(request):
    """API endpoint for OCR processing"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    if not request.user.is_teacher:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        # Process with EasyOCR
        from .easyocr_engine import HandwrittenProcessor
        processor = HandwrittenProcessor()
        
        # Save file temporarily
        temp_path = default_storage.save(f'temp/{file.name}', file)
        full_path = default_storage.path(temp_path)
        
        # Process OCR
        result = processor.ocr_engine.process_file(full_path)
        
        # Clean up temporary file
        default_storage.delete(temp_path)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_evaluate_answer(request):
    """API endpoint for single answer evaluation"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    if not request.user.is_teacher:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        student_answer = data.get('student_answer', '')
        model_answer = data.get('model_answer', '')
        question_text = data.get('question_text', '')
        max_marks = data.get('max_marks', 10)
        
        if not student_answer or not model_answer:
            return JsonResponse({'error': 'Student answer and model answer are required'}, status=400)
        
        # Evaluate with Gemini AI
        from .gemini_engine import GeminiAIEngine
        gemini_engine = GeminiAIEngine()
        
        result = gemini_engine.evaluate_answer(student_answer, model_answer, question_text, max_marks)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
