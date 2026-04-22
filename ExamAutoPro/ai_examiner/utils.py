"""
AI Examiner Utility Functions
"""

import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from django.utils import timezone
from .models import StudentAnswerSheet, HandwrittenAnswer, ModelAnswer


def generate_grade_card_pdf(student_sheet):
    """Generate PDF grade card for student evaluation"""
    
    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    # Build content
    content = []
    
    # Title
    content.append(Paragraph("AI EXAMINER - GRADE CARD", title_style))
    content.append(Spacer(1, 20))
    
    # Student Information
    content.append(Paragraph("Student Information", heading_style))
    
    student_data = [
        ['Student Name:', student_sheet.student_name],
        ['Student ID:', student_sheet.student_id or 'N/A'],
        ['Exam Title:', student_sheet.ai_examiner.title],
        ['Evaluation Date:', student_sheet.evaluated_at.strftime('%B %d, %Y') if student_sheet.evaluated_at else 'N/A'],
        ['Status:', student_sheet.status.title()]
    ]
    
    student_table = Table(student_data, colWidths=[2*inch, 4*inch])
    student_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    content.append(student_table)
    content.append(Spacer(1, 20))
    
    # Results Summary
    content.append(Paragraph("Results Summary", heading_style))
    
    # Calculate grade
    grade = calculate_grade(student_sheet.percentage)
    
    results_data = [
        ['Total Marks Obtained:', f"{student_sheet.total_marks_obtained}"],
        ['Total Maximum Marks:', f"{student_sheet.total_max_marks}"],
        ['Percentage:', f"{student_sheet.percentage:.1f}%"],
        ['Grade:', grade]
    ]
    
    results_table = Table(results_data, colWidths=[2*inch, 4*inch])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    content.append(results_table)
    content.append(Spacer(1, 20))
    
    # Detailed Results
    content.append(Paragraph("Detailed Results", heading_style))
    
    # Get handwritten answers
    answers = HandwrittenAnswer.objects.filter(student_sheet=student_sheet).order_by('question_number')
    
    if answers.exists():
        detailed_data = [['Q.No.', 'Marks Obtained', 'Max Marks', 'Status', 'Feedback']]
        
        for answer in answers:
            status = 'Correct' if answer.is_correct else 'Incorrect'
            feedback = (answer.feedback[:50] + '...') if len(answer.feedback) > 50 else answer.feedback
            
            detailed_data.append([
                str(answer.question_number),
                str(answer.marks_obtained),
                str(answer.max_marks),
                status,
                feedback
            ])
        
        detailed_table = Table(detailed_data, colWidths=[0.8*inch, 1.2*inch, 1.2*inch, 1.2*inch, 2.6*inch])
        detailed_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (2, -1), 'CENTER'),
            ('ALIGN', (3, 1), (-1, -1), 'LEFT')
        ]))
        
        content.append(detailed_table)
    else:
        content.append(Paragraph("No detailed results available.", styles['Normal']))
    
    # Footer
    content.append(Spacer(1, 30))
    content.append(Paragraph("Generated by AI Examiner - Powered by EasyOCR & Google Gemini AI", styles['Normal']))
    content.append(Paragraph(f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    
    # Build PDF
    doc.build(content)
    
    # Get PDF content
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content


def calculate_grade(percentage):
    """Calculate grade based on percentage"""
    if percentage >= 95:
        return 'A+ (Outstanding)'
    elif percentage >= 90:
        return 'A (Excellent)'
    elif percentage >= 85:
        return 'A- (Very Good)'
    elif percentage >= 80:
        return 'B+ (Good)'
    elif percentage >= 75:
        return 'B (Good)'
    elif percentage >= 70:
        return 'B- (Satisfactory)'
    elif percentage >= 65:
        return 'C+ (Satisfactory)'
    elif percentage >= 60:
        return 'C (Satisfactory)'
    elif percentage >= 55:
        return 'C- (Pass)'
    elif percentage >= 50:
        return 'D (Pass)'
    else:
        return 'F (Fail)'


def get_performance_analysis(student_sheet):
    """Get performance analysis for student"""
    answers = HandwrittenAnswer.objects.filter(student_sheet=student_sheet)
    
    if not answers.exists():
        return {
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }
    
    total_answers = answers.count()
    correct_answers = answers.filter(is_correct=True).count()
    accuracy = (correct_answers / total_answers * 100) if total_answers > 0 else 0
    
    # Analyze performance
    strengths = []
    weaknesses = []
    recommendations = []
    
    if accuracy >= 80:
        strengths.append("Excellent overall performance")
    elif accuracy >= 60:
        strengths.append("Good understanding of key concepts")
    else:
        weaknesses.append("Needs improvement in overall performance")
    
    # Analyze individual question performance
    high_score_answers = answers.filter(marks_obtained__gte=lambda x: x.max_marks * 0.8)
    low_score_answers = answers.filter(marks_obtained__lt=lambda x: x.max_marks * 0.5)
    
    if high_score_answers.count() > total_answers * 0.7:
        strengths.append("Strong performance in most questions")
    
    if low_score_answers.count() > total_answers * 0.3:
        weaknesses.append("Struggles with certain question types")
        recommendations.append("Focus on understanding fundamental concepts")
    
    # Generate recommendations based on feedback
    feedback_keywords = []
    for answer in answers:
        if answer.feedback:
            feedback_keywords.extend(answer.feedback.lower().split())
    
    common_issues = ['method', 'concept', 'calculation', 'explanation', 'formula']
    for issue in common_issues:
        if issue in feedback_keywords:
            recommendations.append(f"Review {issue}ology and related concepts")
    
    return {
        'strengths': strengths,
        'weaknesses': weaknesses,
        'recommendations': recommendations,
        'accuracy': accuracy
    }


def format_evaluation_data(evaluation_data):
    """Format evaluation data for display"""
    if not evaluation_data:
        return {}
    
    formatted = {}
    
    # Extract key fields
    key_fields = ['marks_obtained', 'is_correct', 'feedback', 'confidence_score', 
                  'strengths', 'improvements', 'evaluation_summary']
    
    for field in key_fields:
        if field in evaluation_data:
            formatted[field] = evaluation_data[field]
    
    # Format lists
    list_fields = ['strengths', 'improvements']
    for field in list_fields:
        if field in formatted and isinstance(formatted[field], list):
            formatted[field] = ', '.join(formatted[field])
    
    return formatted


def validate_file_upload(file):
    """Validate uploaded file for AI Examiner"""
    if not file:
        return False, "No file provided"
    
    # Check file size (50MB limit)
    if file.size > 50 * 1024 * 1024:
        return False, "File size must be less than 50MB"
    
    # Check file extension
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    file_extension = file.name.lower().split('.')[-1]
    
    if f'.{file_extension}' not in allowed_extensions:
        return False, f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
    
    return True, "File is valid"


def get_ai_examiner_statistics(ai_examiner):
    """Get comprehensive statistics for AI Examiner session"""
    student_sheets = StudentAnswerSheet.objects.filter(ai_examiner=ai_examiner)
    
    total_students = student_sheets.count()
    completed_evaluations = student_sheets.filter(status='completed').count()
    failed_evaluations = student_sheets.filter(status='failed').count()
    
    # Calculate statistics
    if completed_evaluations > 0:
        percentages = [sheet.percentage for sheet in student_sheets.filter(status='completed')]
        avg_percentage = sum(percentages) / len(percentages)
        highest_score = max(percentages)
        lowest_score = min(percentages)
        
        # Grade distribution
        grade_dist = {}
        for sheet in student_sheets.filter(status='completed'):
            grade = calculate_grade(sheet.percentage).split(' ')[0]
            grade_dist[grade] = grade_dist.get(grade, 0) + 1
    else:
        avg_percentage = 0
        highest_score = 0
        lowest_score = 0
        grade_dist = {}
    
    return {
        'total_students': total_students,
        'completed_evaluations': completed_evaluations,
        'failed_evaluations': failed_evaluations,
        'success_rate': (completed_evaluations / total_students * 100) if total_students > 0 else 0,
        'average_percentage': avg_percentage,
        'highest_score': highest_score,
        'lowest_score': lowest_score,
        'grade_distribution': grade_dist
    }
