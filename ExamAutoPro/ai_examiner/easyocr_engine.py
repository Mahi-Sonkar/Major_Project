"""
EasyOCR Engine for Handwritten Text Recognition
"""

import os
import time
import logging
from PIL import Image
import cv2
import numpy as np
from pdf2image import convert_from_path
from django.conf import settings
from django.core.files.base import ContentFile
import easyocr
import io

logger = logging.getLogger(__name__)


class EasyOCREngine:
    """Advanced OCR Engine using EasyOCR for handwritten text recognition"""
    
    def __init__(self):
        self.reader = None
        self.supported_languages = ['en']  # English for handwritten text
        self.confidence_threshold = 0.5
        
    def initialize_reader(self):
        """Initialize EasyOCR reader if not already initialized"""
        if self.reader is None:
            try:
                self.reader = easyocr.Reader(self.supported_languages, gpu=False)
                logger.info("EasyOCR reader initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR reader: {str(e)}")
                raise
    
    def process_image(self, image_path):
        """Process a single image file with EasyOCR"""
        try:
            self.initialize_reader()
            
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            # Preprocessing for better OCR results
            processed_image = self._preprocess_image(image)
            
            # Perform OCR
            results = self.reader.readtext(processed_image)
            
            # Extract and process text
            extracted_text = self._extract_text(results)
            confidence = self._calculate_confidence(results)
            
            return {
                'success': True,
                'text': extracted_text,
                'confidence': confidence,
                'raw_results': results,
                'processing_time': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'confidence': 0.0
            }
    
    def process_pdf(self, pdf_path):
        """Process PDF file by converting to images and performing OCR"""
        try:
            self.initialize_reader()
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            
            all_text = []
            all_confidences = []
            all_results = []
            
            for page_num, image in enumerate(images):
                # Convert PIL image to numpy array
                image_array = np.array(image)
                
                # Preprocessing
                processed_image = self._preprocess_image(image_array)
                
                # Perform OCR
                results = self.reader.readtext(processed_image)
                
                # Extract text and confidence
                page_text = self._extract_text(results)
                page_confidence = self._calculate_confidence(results)
                
                all_text.append(f"Page {page_num + 1}:\n{page_text}")
                all_confidences.append(page_confidence)
                all_results.extend(results)
            
            # Combine all text
            combined_text = "\n\n".join(all_text)
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            
            return {
                'success': True,
                'text': combined_text,
                'confidence': avg_confidence,
                'pages_processed': len(images),
                'raw_results': all_results,
                'processing_time': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'confidence': 0.0
            }
    
    def process_file(self, file_path):
        """Process file (image or PDF) with EasyOCR"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension in ['.pdf']:
            return self.process_pdf(file_path)
        elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            return self.process_image(file_path)
        else:
            return {
                'success': False,
                'error': f'Unsupported file format: {file_extension}',
                'text': '',
                'confidence': 0.0
            }
    
    def _preprocess_image(self, image):
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply threshold to get better contrast
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.medianBlur(binary, 3)
        
        # Enhance contrast
        enhanced = cv2.convertScaleAbs(denoised, alpha=1.2, beta=10)
        
        return enhanced
    
    def _extract_text(self, results):
        """Extract and clean text from EasyOCR results"""
        text_parts = []
        
        for (bbox, text, confidence) in results:
            # Filter by confidence threshold
            if confidence >= self.confidence_threshold:
                # Clean text
                cleaned_text = text.strip()
                if cleaned_text:
                    text_parts.append(cleaned_text)
        
        return ' '.join(text_parts)
    
    def _calculate_confidence(self, results):
        """Calculate average confidence from OCR results"""
        if not results:
            return 0.0
        
        confidences = [confidence for (_, _, confidence) in results 
                      if confidence >= self.confidence_threshold]
        
        if not confidences:
            return 0.0
        
        return sum(confidences) / len(confidences)
    
    def extract_question_answers(self, text, question_numbers):
        """Extract individual question answers from OCR text"""
        try:
            # Split text by question numbers
            answers = {}
            
            # Sort question numbers to ensure proper ordering
            sorted_questions = sorted(question_numbers)
            
            for i, q_num in enumerate(sorted_questions):
                # Create pattern for question number
                pattern = rf"(?:Q\.?|Question\s*{q_num}|{q_num}\.)\s*(.*?)(?=Q\.?|Question\s*{sorted_questions[i+1]}|$)" if i < len(sorted_questions) - 1 else rf"(?:Q\.?|Question\s*{q_num}|{q_num}\.)\s*(.*)"
                
                import re
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                
                if match:
                    answer_text = match.group(1).strip()
                    # Clean up the answer text
                    answer_text = re.sub(r'\s+', ' ', answer_text)
                    answer_text = answer_text.replace('\n', ' ')
                    answers[q_num] = answer_text
                else:
                    # Fallback: look for question number followed by text
                    fallback_pattern = rf"{q_num}[\.\)]\s*(.*?)(?=\d+[\.\)]|$)"
                    fallback_match = re.search(fallback_pattern, text, re.DOTALL)
                    if fallback_match:
                        answers[q_num] = fallback_match.group(1).strip()
                    else:
                        answers[q_num] = ""
            
            return answers
            
        except Exception as e:
            logger.error(f"Error extracting question answers: {str(e)}")
            return {q_num: "" for q_num in question_numbers}


class HandwrittenProcessor:
    """High-level processor for handwritten answer sheets"""
    
    def __init__(self):
        self.ocr_engine = EasyOCREngine()
    
    def process_student_sheet(self, student_sheet, model_answers):
        """Process entire student answer sheet"""
        try:
            # Process the student file
            file_path = student_sheet.answer_file.path
            ocr_result = self.ocr_engine.process_file(file_path)
            
            if not ocr_result['success']:
                return {
                    'success': False,
                    'error': ocr_result['error']
                }
            
            # Extract individual question answers
            question_numbers = [qa.question_number for qa in model_answers]
            extracted_answers = self.ocr_engine.extract_question_answers(
                ocr_result['text'], 
                question_numbers
            )
            
            return {
                'success': True,
                'full_text': ocr_result['text'],
                'confidence': ocr_result['confidence'],
                'answers': extracted_answers,
                'processing_time': ocr_result['processing_time']
            }
            
        except Exception as e:
            logger.error(f"Error processing student sheet: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_model_answer(self, model_answer):
        """Process model answer file"""
        try:
            file_path = model_answer.answer_file.path
            ocr_result = self.ocr_engine.process_file(file_path)
            
            if ocr_result['success']:
                # Update model answer with transcribed text
                model_answer.transcribed_text = ocr_result['text']
                model_answer.save()
            
            return ocr_result
            
        except Exception as e:
            logger.error(f"Error processing model answer: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
