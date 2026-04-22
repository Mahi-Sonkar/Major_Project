"""
AI Examiner Evaluation Engine - Combines EasyOCR and Gemini AI
"""

import time
import logging
from django.db import transaction
from django.utils import timezone
from .easyocr_engine import HandwrittenProcessor
from .gemini_engine import GeminiAIEngine, GeminiPromptTemplates

logger = logging.getLogger(__name__)


class AIExaminerEngine:
    """Main AI Examiner engine for handwritten answer evaluation"""
    
    def __init__(self):
        self.ocr_processor = HandwrittenProcessor()
        self.gemini_engine = GeminiAIEngine()
    
    def evaluate_student_sheet(self, student_sheet, model_answers):
        """Complete evaluation workflow for a student answer sheet"""
        try:
            logger.info(f"Starting evaluation for student sheet: {student_sheet.id}")
            start_time = time.time()
            
            # Update status to processing
            student_sheet.status = 'processing'
            student_sheet.save()
            
            # Step 1: OCR Processing
            logger.info("Step 1: Processing OCR for student sheet")
            ocr_result = self.ocr_processor.process_student_sheet(student_sheet, model_answers)
            
            if not ocr_result['success']:
                student_sheet.status = 'failed'
                student_sheet.save()
                return {
                    'success': False,
                    'error': f"OCR Processing failed: {ocr_result['error']}"
                }
            
            # Update status to OCR completed
            student_sheet.status = 'ocr_completed'
            student_sheet.save()
            
            # Step 2: Individual Answer Evaluation
            logger.info("Step 2: Evaluating individual answers with Gemini AI")
            evaluation_results = []
            total_marks = 0
            total_max_marks = 0
            
            for model_answer in model_answers:
                question_num = model_answer.question_number
                student_answer_text = ocr_result['answers'].get(question_num, "")
                
                if student_answer_text:
                    # Evaluate with Gemini AI
                    evaluation_result = self._evaluate_single_answer(
                        student_answer_text,
                        model_answer,
                        student_sheet
                    )
                    
                    if evaluation_result['success']:
                        evaluation_results.append(evaluation_result)
                        total_marks += evaluation_result['result']['marks_obtained']
                        total_max_marks += model_answer.max_marks
                    else:
                        logger.error(f"Evaluation failed for question {question_num}: {evaluation_result['error']}")
                        # Create failed evaluation record
                        self._create_failed_evaluation(student_sheet, model_answer, evaluation_result['error'])
                else:
                    # No answer provided for this question
                    self._create_no_answer_evaluation(student_sheet, model_answer)
                    total_max_marks += model_answer.max_marks
            
            # Step 3: Calculate final results
            logger.info("Step 3: Calculating final results")
            percentage = (total_marks / total_max_marks * 100) if total_max_marks > 0 else 0
            
            # Update student sheet with results
            student_sheet.total_marks_obtained = total_marks
            student_sheet.total_max_marks = total_max_marks
            student_sheet.percentage = percentage
            student_sheet.status = 'completed'
            student_sheet.evaluated_at = timezone.now()
            student_sheet.save()
            
            # Step 4: Create evaluation history record
            self._create_evaluation_history(student_sheet, len(model_answers), total_marks, total_max_marks, percentage)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Evaluation completed for {student_sheet.student_name}: {total_marks}/{total_max_marks} ({percentage:.1f}%)")
            
            return {
                'success': True,
                'student_sheet': student_sheet,
                'evaluation_results': evaluation_results,
                'total_marks': total_marks,
                'total_max_marks': total_max_marks,
                'percentage': percentage,
                'processing_time': processing_time,
                'ocr_confidence': ocr_result['confidence']
            }
            
        except Exception as e:
            logger.error(f"Error in evaluation workflow: {str(e)}")
            student_sheet.status = 'failed'
            student_sheet.save()
            return {
                'success': False,
                'error': f"Evaluation workflow failed: {str(e)}"
            }
    
    def _evaluate_single_answer(self, student_answer_text, model_answer, student_sheet):
        """Evaluate a single answer using Gemini AI"""
        try:
            # Create or get handwritten answer record
            from .models import HandwrittenAnswer, EvaluationSession
            
            handwritten_answer, created = HandwrittenAnswer.objects.get_or_create(
                student_sheet=student_sheet,
                question_number=model_answer.question_number,
                defaults={
                    'original_text': student_answer_text,
                    'cleaned_text': student_answer_text,
                    'max_marks': model_answer.max_marks
                }
            )
            
            if not created:
                # Update existing answer
                handwritten_answer.original_text = student_answer_text
                handwritten_answer.cleaned_text = student_answer_text
                handwritten_answer.max_marks = model_answer.max_marks
                handwritten_answer.save()
            
            # Create evaluation session
            evaluation_session = EvaluationSession.objects.create(
                handwritten_answer=handwritten_answer,
                model_answer=model_answer,
                status='processing'
            )
            
            # Evaluate with Gemini AI
            gemini_result = self.gemini_engine.evaluate_answer(
                student_answer_text,
                model_answer.transcribed_text or model_answer.question_text,  # Fallback to question text
                model_answer.question_text,
                model_answer.max_marks
            )
            
            if gemini_result['success']:
                # Update handwritten answer with results
                result_data = gemini_result['result']
                handwritten_answer.marks_obtained = result_data['marks_obtained']
                handwritten_answer.is_correct = result_data['is_correct']
                handwritten_answer.feedback = result_data['feedback']
                handwritten_answer.evaluation_data = result_data
                handwritten_answer.save()
                
                # Update evaluation session
                evaluation_session.status = 'completed'
                evaluation_session.gemini_response = gemini_result['raw_response']
                evaluation_session.processing_time = result_data['processing_time']
                evaluation_session.completed_at = timezone.now()
                evaluation_session.save()
                
                return {
                    'success': True,
                    'question_number': model_answer.question_number,
                    'result': result_data,
                    'handwritten_answer': handwritten_answer
                }
            else:
                # Evaluation failed
                evaluation_session.status = 'failed'
                evaluation_session.gemini_response = gemini_result.get('error', 'Unknown error')
                evaluation_session.save()
                
                return {
                    'success': False,
                    'question_number': model_answer.question_number,
                    'error': gemini_result['error']
                }
                
        except Exception as e:
            logger.error(f"Error evaluating single answer: {str(e)}")
            return {
                'success': False,
                'question_number': model_answer.question_number,
                'error': str(e)
            }
    
    def _create_failed_evaluation(self, student_sheet, model_answer, error_message):
        """Create a failed evaluation record"""
        from .models import HandwrittenAnswer, EvaluationSession
        
        handwritten_answer, created = HandwrittenAnswer.objects.get_or_create(
            student_sheet=student_sheet,
            question_number=model_answer.question_number,
            defaults={
                'original_text': 'Evaluation failed',
                'cleaned_text': 'Evaluation failed',
                'max_marks': model_answer.max_marks,
                'marks_obtained': 0,
                'is_correct': False,
                'feedback': f'Evaluation failed: {error_message}'
            }
        )
        
        EvaluationSession.objects.create(
            handwritten_answer=handwritten_answer,
            model_answer=model_answer,
            status='failed',
            gemini_response=error_message
        )
    
    def _create_no_answer_evaluation(self, student_sheet, model_answer):
        """Create evaluation record for unanswered question"""
        from .models import HandwrittenAnswer, EvaluationSession
        
        handwritten_answer, created = HandwrittenAnswer.objects.get_or_create(
            student_sheet=student_sheet,
            question_number=model_answer.question_number,
            defaults={
                'original_text': 'No answer provided',
                'cleaned_text': 'No answer provided',
                'max_marks': model_answer.max_marks,
                'marks_obtained': 0,
                'is_correct': False,
                'feedback': 'No answer provided for this question'
            }
        )
        
        EvaluationSession.objects.create(
            handwritten_answer=handwritten_answer,
            model_answer=model_answer,
            status='completed',
            gemini_response='No answer provided'
        )
    
    def _create_evaluation_history(self, student_sheet, total_questions, total_marks, total_max_marks, percentage):
        """Create evaluation history record"""
        from .models import EvaluationHistory
        
        # Calculate grade based on percentage
        grade = self._calculate_grade(percentage)
        
        EvaluationHistory.objects.create(
            ai_examiner=student_sheet.ai_examiner,
            student_sheet=student_sheet,
            total_questions=total_questions,
            total_marks=total_max_marks,
            total_obtained=total_marks,
            percentage=percentage,
            grade=grade
        )
    
    def _calculate_grade(self, percentage):
        """Calculate grade based on percentage"""
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B'
        elif percentage >= 60:
            return 'C'
        elif percentage >= 50:
            return 'D'
        else:
            return 'F'
    
    def batch_evaluate_sheets(self, student_sheets, model_answers):
        """Evaluate multiple student sheets in batch"""
        results = []
        
        for student_sheet in student_sheets:
            result = self.evaluate_student_sheet(student_sheet, model_answers)
            results.append({
                'student_sheet': student_sheet,
                'result': result
            })
        
        return results
    
    def get_evaluation_summary(self, ai_examiner):
        """Get summary of all evaluations for an AI Examiner session"""
        from .models import StudentAnswerSheet, EvaluationHistory
        
        student_sheets = StudentAnswerSheet.objects.filter(ai_examiner=ai_examiner)
        evaluation_history = EvaluationHistory.objects.filter(ai_examiner=ai_examiner)
        
        total_students = student_sheets.count()
        completed_evaluations = student_sheets.filter(status='completed').count()
        failed_evaluations = student_sheets.filter(status='failed').count()
        
        # Calculate statistics
        if completed_evaluations > 0:
            avg_percentage = sum(sheet.percentage for sheet in student_sheets.filter(status='completed')) / completed_evaluations
            highest_score = student_sheets.filter(status='completed').order_by('-percentage').first()
            lowest_score = student_sheets.filter(status='completed').order_by('percentage').first()
        else:
            avg_percentage = 0
            highest_score = None
            lowest_score = None
        
        return {
            'total_students': total_students,
            'completed_evaluations': completed_evaluations,
            'failed_evaluations': failed_evaluations,
            'success_rate': (completed_evaluations / total_students * 100) if total_students > 0 else 0,
            'average_percentage': avg_percentage,
            'highest_score': highest_score.percentage if highest_score else 0,
            'lowest_score': lowest_score.percentage if lowest_score else 0,
            'top_student': highest_score.student_name if highest_score else None
        }
