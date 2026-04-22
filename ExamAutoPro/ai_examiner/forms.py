"""
AI Examiner Forms
"""

from django import forms
from .models import AIExaminer, ModelAnswer, StudentAnswerSheet
from django.conf import settings


class AIExaminerForm(forms.ModelForm):
    """Form for creating AI Examiner sessions"""
    
    class Meta:
        model = AIExaminer
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter exam title...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter exam description...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = 'Exam Title'
        self.fields['description'].label = 'Description (Optional)'


class ModelAnswerForm(forms.ModelForm):
    """Form for uploading model answers"""
    
    class Meta:
        model = ModelAnswer
        fields = ['question_number', 'question_text', 'max_marks', 'answer_file']
        widgets = {
            'question_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Question number'
            }),
            'question_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter the question text...'
            }),
            'max_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Maximum marks'
            }),
            'answer_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.bmp,.tiff'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['question_number'].label = 'Question Number'
        self.fields['question_text'].label = 'Question Text'
        self.fields['max_marks'].label = 'Maximum Marks'
        self.fields['answer_file'].label = 'Model Answer File (PDF/Image)'
    
    def clean_answer_file(self):
        file = self.cleaned_data.get('answer_file')
        
        if file:
            # Check file extension
            file_extension = file.name.lower().split('.')[-1]
            allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'bmp', 'tiff']
            
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(
                    f'Unsupported file format. Allowed formats: {", ".join(allowed_extensions)}'
                )
            
            # Check file size (50MB limit)
            if file.size > 50 * 1024 * 1024:
                raise forms.ValidationError('File size must be less than 50MB.')
        
        return file


class StudentAnswerSheetForm(forms.ModelForm):
    """Form for uploading student answer sheets"""
    
    class Meta:
        model = StudentAnswerSheet
        fields = ['student_name', 'student_id', 'answer_file']
        widgets = {
            'student_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter student name...'
            }),
            'student_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter student ID (optional)...'
            }),
            'answer_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.bmp,.tiff'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student_name'].label = 'Student Name'
        self.fields['student_id'].label = 'Student ID (Optional)'
        self.fields['answer_file'].label = 'Answer Sheet File (PDF/Image)'
    
    def clean_answer_file(self):
        file = self.cleaned_data.get('answer_file')
        
        if file:
            # Check file extension
            file_extension = file.name.lower().split('.')[-1]
            allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'bmp', 'tiff']
            
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(
                    f'Unsupported file format. Allowed formats: {", ".join(allowed_extensions)}'
                )
            
            # Check file size (50MB limit)
            if file.size > 50 * 1024 * 1024:
                raise forms.ValidationError('File size must be less than 50MB.')
        
        return file


class BatchUploadForm(forms.Form):
    """Form for batch uploading student answer sheets"""
    
    zip_file = forms.FileField(
        label='Upload ZIP file containing student answer sheets',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.zip'
        })
    )
    
    def clean_zip_file(self):
        file = self.cleaned_data.get('zip_file')
        
        if file:
            # Check file extension
            if not file.name.lower().endswith('.zip'):
                raise forms.ValidationError('Please upload a ZIP file.')
            
            # Check file size (100MB limit)
            if file.size > 100 * 1024 * 1024:
                raise forms.ValidationError('ZIP file size must be less than 100MB.')
        
        return file


class EvaluationSettingsForm(forms.Form):
    """Form for evaluation settings"""
    
    confidence_threshold = forms.FloatField(
        label='OCR Confidence Threshold',
        min_value=0.0,
        max_value=1.0,
        initial=0.5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 0.1
        })
    )
    
    evaluation_mode = forms.ChoiceField(
        label='Evaluation Mode',
        choices=[
            ('standard', 'Standard Evaluation'),
            ('strict', 'Strict Evaluation'),
            ('lenient', 'Lenient Evaluation')
        ],
        initial='standard',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    auto_grade = forms.BooleanField(
        label='Auto-generate Grade Cards',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['confidence_threshold'].help_text = 'Minimum confidence score for OCR text recognition'
        self.fields['evaluation_mode'].help_text = 'Choose evaluation strictness level'
        self.fields['auto_grade'].help_text = 'Automatically generate grade cards after evaluation'
