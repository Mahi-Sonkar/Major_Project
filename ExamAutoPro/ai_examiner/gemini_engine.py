"""
Google Gemini AI Engine for Intelligent Answer Evaluation
"""

import os
import time
import json
import logging
import google.generativeai as genai
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class GeminiAIEngine:
    """Google Gemini AI engine for evaluating handwritten answers"""
    
    def __init__(self):
        self.api_key = self._get_api_key()
        self.model = None
        self._initialize_model()
    
    def _get_api_key(self):
        """Get Gemini API key from settings or environment"""
        api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.environ.get('GEMINI_API_KEY')
        
        if not api_key:
            raise ImproperlyConfigured(
                "GEMINI_API_KEY not found. Please set GEMINI_API_KEY in settings or environment variables."
            )
        
        return api_key
    
    def _initialize_model(self):
        """Initialize Gemini model"""
        try:
            genai.configure(api_key=self.api_key)
            # Use Gemini Pro for text evaluation
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini AI model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise
    
    def evaluate_answer(self, student_answer, model_answer, question_text, max_marks):
        """Evaluate student answer against model answer using Gemini AI"""
        try:
            # Create evaluation prompt
            prompt = self._create_evaluation_prompt(
                student_answer, 
                model_answer, 
                question_text, 
                max_marks
            )
            
            # Generate response
            start_time = time.time()
            response = self.model.generate_content(prompt)
            processing_time = time.time() - start_time
            
            # Parse response
            evaluation_result = self._parse_gemini_response(response.text, max_marks)
            evaluation_result['processing_time'] = processing_time
            
            return {
                'success': True,
                'result': evaluation_result,
                'raw_response': response.text
            }
            
        except Exception as e:
            logger.error(f"Error in Gemini evaluation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'result': None
            }
    
    def _create_evaluation_prompt(self, student_answer, model_answer, question_text, max_marks):
        """Create comprehensive evaluation prompt for Gemini"""
        prompt = f"""
You are an expert educational evaluator. Please evaluate the following student answer against the model answer.

QUESTION: {question_text}
MAX MARKS: {max_marks}

MODEL ANSWER:
{model_answer}

STUDENT ANSWER:
{student_answer}

Please evaluate the student's answer and provide:

1. Marks obtained (out of {max_marks})
2. Detailed feedback explaining the evaluation
3. Key strengths in the answer
4. Areas for improvement
5. Confidence score (0-1) indicating how certain you are about the evaluation

Format your response as JSON:
{{
    "marks_obtained": <integer>,
    "feedback": "<detailed feedback>",
    "strengths": ["<strength1>", "<strength2>", ...],
    "improvements": ["<improvement1>", "<improvement2>", ...],
    "confidence_score": <float between 0 and 1>,
    "evaluation_summary": "<brief summary>"
}}

Be fair but thorough in your evaluation. Consider:
- Correctness of content
- Understanding of concepts
- Completeness of answer
- Clarity and organization
- Relevance to the question
"""
        return prompt
    
    def _parse_gemini_response(self, response_text, max_marks):
        """Parse Gemini response and extract evaluation data"""
        try:
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != 0:
                json_str = response_text[json_start:json_end]
                evaluation_data = json.loads(json_str)
            else:
                # Fallback parsing if JSON extraction fails
                evaluation_data = self._fallback_parse(response_text, max_marks)
            
            # Validate and sanitize data
            evaluation_data['marks_obtained'] = max(0, min(max_marks, evaluation_data.get('marks_obtained', 0)))
            evaluation_data['confidence_score'] = max(0, min(1, evaluation_data.get('confidence_score', 0.5)))
            
            # Determine if answer is correct (60% threshold)
            evaluation_data['is_correct'] = evaluation_data['marks_obtained'] >= (max_marks * 0.6)
            
            return evaluation_data
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            # Return default evaluation
            return {
                'marks_obtained': 0,
                'feedback': 'Error parsing AI evaluation. Please review manually.',
                'strengths': [],
                'improvements': ['Unable to process automatically'],
                'confidence_score': 0.0,
                'evaluation_summary': 'Evaluation failed',
                'is_correct': False,
                'parse_error': str(e)
            }
    
    def _fallback_parse(self, response_text, max_marks):
        """Fallback parsing method when JSON extraction fails"""
        import re
        
        # Extract marks using regex
        marks_match = re.search(r'(?i)marks?\s*(?:obtained|score)?\s*[:\-]?\s*(\d+)', response_text)
        marks_obtained = int(marks_match.group(1)) if marks_match else 0
        
        # Extract confidence
        confidence_match = re.search(r'(?i)confidence\s*[:\-]?\s*([0-9]*\.?[0-9]+)', response_text)
        confidence_score = float(confidence_match.group(1)) if confidence_match else 0.5
        
        # Extract feedback (everything after marks until next section)
        feedback_match = re.search(r'(?i)feedback\s*[:\-]?\s*(.+?)(?=strengths|improvements|$)', response_text, re.DOTALL)
        feedback = feedback_match.group(1).strip() if feedback_match else response_text[:200]
        
        return {
            'marks_obtained': min(max_marks, max(0, marks_obtained)),
            'feedback': feedback,
            'strengths': [],
            'improvements': [],
            'confidence_score': min(1, max(0, confidence_score)),
            'evaluation_summary': feedback[:100] + '...' if len(feedback) > 100 else feedback
        }
    
    def batch_evaluate_answers(self, answers_data):
        """Evaluate multiple answers in batch for efficiency"""
        results = []
        
        for answer_data in answers_data:
            result = self.evaluate_answer(
                answer_data['student_answer'],
                answer_data['model_answer'],
                answer_data['question_text'],
                answer_data['max_marks']
            )
            results.append({
                'question_number': answer_data['question_number'],
                'evaluation': result
            })
        
        return results
    
    def get_evaluation_statistics(self, evaluation_results):
        """Calculate statistics for a batch of evaluations"""
        if not evaluation_results:
            return {}
        
        total_marks = sum(r['result']['marks_obtained'] for r in evaluation_results if r['success'])
        max_possible_marks = sum(r['max_marks'] for r in evaluation_results if r['success'])
        avg_confidence = sum(r['result']['confidence_score'] for r in evaluation_results if r['success']) / len(evaluation_results) if evaluation_results else 0
        
        return {
            'total_marks_obtained': total_marks,
            'max_possible_marks': max_possible_marks,
            'percentage': (total_marks / max_possible_marks * 100) if max_possible_marks > 0 else 0,
            'average_confidence': avg_confidence,
            'evaluations_completed': len([r for r in evaluation_results if r['success']]),
            'evaluations_failed': len([r for r in evaluation_results if not r['success']])
        }


class GeminiPromptTemplates:
    """Pre-defined prompt templates for different evaluation scenarios"""
    
    @staticmethod
    def get_maths_prompt(student_answer, model_answer, question_text, max_marks):
        """Specialized prompt for mathematics evaluation"""
        return f"""
You are a mathematics expert evaluator. Evaluate the following mathematical solution.

QUESTION: {question_text}
MAX MARKS: {max_marks}

MODEL ANSWER:
{model_answer}

STUDENT ANSWER:
{student_answer}

Focus on:
- Correctness of the final answer
- Proper methodology and steps shown
- Mathematical accuracy
- Clarity of mathematical notation

Provide evaluation as JSON:
{{
    "marks_obtained": <integer>,
    "feedback": "<detailed mathematical feedback>",
    "methodology_correct": <boolean>,
    "final_answer_correct": <boolean>,
    "steps_shown": <boolean>,
    "confidence_score": <float>,
    "evaluation_summary": "<summary>"
}}
"""
    
    @staticmethod
    def get_essay_prompt(student_answer, model_answer, question_text, max_marks):
        """Specialized prompt for essay evaluation"""
        return f"""
You are an expert English literature and writing evaluator. Evaluate the following essay.

QUESTION: {question_text}
MAX MARKS: {max_marks}

MODEL ANSWER:
{model_answer}

STUDENT ANSWER:
{student_answer}

Focus on:
- Content relevance and depth
- Structure and organization
- Language and grammar
- Critical thinking and analysis
- Originality and creativity

Provide evaluation as JSON:
{{
    "marks_obtained": <integer>,
    "feedback": "<detailed writing feedback>",
    "content_score": <float 0-1>,
    "structure_score": <float 0-1>,
    "language_score": <float 0-1>,
    "confidence_score": <float>,
    "evaluation_summary": "<summary>"
}}
"""
    
    @staticmethod
    def get_science_prompt(student_answer, model_answer, question_text, max_marks):
        """Specialized prompt for science evaluation"""
        return f"""
You are a science expert evaluator. Evaluate the following science answer.

QUESTION: {question_text}
MAX MARKS: {max_marks}

MODEL ANSWER:
{model_answer}

STUDENT ANSWER:
{student_answer}

Focus on:
- Scientific accuracy
- Understanding of concepts
- Use of scientific terminology
- Logical reasoning
- Experimental methodology (if applicable)

Provide evaluation as JSON:
{{
    "marks_obtained": <integer>,
    "feedback": "<detailed science feedback>",
    "conceptual_understanding": <float 0-1>,
    "scientific_accuracy": <float 0-1>,
    "terminology_usage": <float 0-1>,
    "confidence_score": <float>,
    "evaluation_summary": "<summary>"
}}
"""
