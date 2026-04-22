"""
AI Examiner Django App Configuration
"""

from django.apps import AppConfig


class AiExaminerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_examiner'
    verbose_name = 'AI Examiner'
    
    def ready(self):
        """
        App initialization
        """
        # Import signals if needed
        # from . import signals
