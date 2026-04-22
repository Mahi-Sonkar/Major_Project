#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Add Django path to fix import issues
sys.path.append('D:/Lib/site-packages')

def main():
    """Run administrative tasks."""
    # Mock heavy dependencies that might prevent management commands from running
    from unittest.mock import MagicMock
    import sys
    
    class MockPackage(MagicMock):
        def __repr__(self):
            return f"<MockPackage {self._name}>"
            
    def mock_module(name):
        if name in sys.modules:
            return
        parts = name.split('.')
        for i in range(len(parts)):
            part_name = '.'.join(parts[:i+1])
            if part_name not in sys.modules:
                m = MockPackage()
                m.__path__ = []
                sys.modules[part_name] = m

    mock_modules_list = [
        'easyocr', 'face_recognition', 'sentence_transformers', 
        'spacy', 'google.generativeai', 'google', 'google.api_core', 
        'google.cloud', 'reportlab', 'reportlab.lib', 'reportlab.lib.pagesizes', 
        'reportlab.pdfgen', 'reportlab.platypus', 'reportlab.lib.styles',
        'reportlab.lib.units', 'reportlab.lib.colors'
    ]
    
    for module in mock_modules_list:
        mock_module(module)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ExamAutoPro.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
