# ExamAutoPro - AI-Powered Automated Examination System

ExamAutoPro is a comprehensive AI-based examination evaluation system built with Django. It transforms traditional examination evaluation by eliminating manual checking limitations, providing fast and accurate results, and ensuring exam integrity through AI-powered proctoring and attempt restrictions.

## 🚀 Key Features

### 🛡️ Exam Integrity & Proctoring
- **Restricted Exam Attempts**: Students are restricted to a single attempt (configurable via `allow_multiple_attempts` and `max_attempts` settings).
- **Auto-Termination on Tab Switch**: Real-time monitoring of browser tab changes. If a student leaves the exam tab, the exam is automatically submitted with a "Terminated" status.
- **Interaction Restrictions**: Right-click, copy, and paste are disabled during exams to prevent external assistance.

### 🤖 AI-Powered Evaluation
- **Hybrid Scoring Engine**: Combines **TF-IDF Cosine Similarity** for semantic overlap with **Keyword Coverage** for technical accuracy.
- **OCR Integration**: Process handwritten answer sheets (PDF/Images) using Tesseract OCR.
- **MCQ & Descriptive Support**: Automated evaluation for both Multiple Choice and long-form descriptive answers.

### 📊 Role-Based Dashboards
- **Student Dashboard**: View available exams, track performance, and view AI-evaluated results.
- **Teacher/Admin Dashboard**: Manage exams, questions, and view detailed analytics of student performance.

## 🛠️ Tech Stack
- **Backend**: Django 4.2.7, PostgreSQL
- **Frontend**: Bootstrap 5, JavaScript
- **AI/NLP**: NLTK, Scikit-learn, Tesseract OCR
- **Testing**: Python `unittest` with dependency mocking

## 📋 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Mahi-Sonkar/Major_Project.git
cd Major_Project
```

### 2. Environment Setup
Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r ExamAutoPro/requirements.txt
```

### 3. OCR Configuration
Install Tesseract OCR on your system.
- **Windows**: Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
- Update `TESSERACT_CMD` in `ExamAutoPro/ExamAutoPro/settings.py` if necessary.

### 4. Database Migrations
```bash
cd ExamAutoPro
python manage.py migrate
```

### 5. Start Development Server
```bash
python manage.py runserver
```
The server will be available at `http://127.0.0.1:8000/`.

## 🧪 Verification
You can verify the core exam flow and AI evaluation logic without a full browser setup using the provided verification script:
```bash
python verify_exam_flow.py
```
This script simulates an exam submission and validates the AI evaluation process using mocks for heavy dependencies.

## 🏗️ Project Structure
```
Major_Project/
├── ExamAutoPro/          # Main Django project directory
│   ├── exams/            # Exam management and submission logic
│   ├── evaluation/       # AI scoring and OCR engines
│   ├── proctoring/       # Tab-switch and focus monitoring
│   ├── templates/        # HTML templates for all modules
│   └── manage.py         # Django management script
├── verify_exam_flow.py   # Unit test for exam lifecycle
└── README.md             # Project documentation
```

## 👥 Authors
- **Mahi Sonkar** - [GitHub](https://github.com/Mahi-Sonkar)

---
*Developed as part of a Major Project for automated education evaluation.*
