# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Shadow is a goal-driven academic achievement system for Pan-Atlantic University (PAU) students. It helps students achieve their target CGPA through intelligent task prioritization, grade prediction, and AI-powered study recommendations.

## Development Commands

### Backend (FastAPI)
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# Backend runs at http://localhost:8000
# API docs at http://localhost:8000/api/docs
```

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
# Frontend runs at http://localhost:3000
```

### Database (PostgreSQL)
```bash
# Create database
psql -U postgres -c "CREATE DATABASE shadow_db;"

# Run schema
psql -U postgres -d shadow_db -f database/schema.sql
```

### Testing
```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

### Linting
```bash
cd frontend && npm run lint
```

## Architecture

### Backend Structure (`backend/app/`)
- **main.py**: FastAPI application entry point, CORS config, router registration
- **database.py**: SQLAlchemy engine, session management, `get_db` dependency
- **models/**: SQLAlchemy ORM models (user, course, task, mood, smartstudy, library)
- **schemas/**: Pydantic validation schemas for request/response
- **routes/**: API endpoint handlers organized by domain (auth, courses, tasks, cgpa, mood, smartstudy, library)
- **services/**: Business logic (smartstudy_service, youtube_service, study_plan_generator, document_processor)
- **utils/**: Helper functions
  - `pau_grading.py`: PAU-specific grading calculations (35/65 CA/Exam split, 5.0 scale)
  - `cgpa_calculator.py`: CGPA computation
  - `priority_calculator.py`: Task priority scoring algorithm
  - `auth.py`: JWT authentication utilities

### Frontend Structure (`frontend/src/`)
- **App.jsx**: React Router configuration
- **pages/**: Page components (Dashboard, Courses, CGPA, Library, Login, Register)
- **components/**: Reusable UI components (CourseCard, TaskList, MoodLogger, SmartStudyChat, StudyPlanView)
- **services/api.js**: Centralized Axios client with auth interceptors for all API calls

### API Structure
All API routes prefixed with `/api/v1/`:
- `/auth/*`: Authentication (register, login)
- `/courses/*`: Course management and enrollment
- `/tasks/*`: Task CRUD and completion tracking
- `/gpa/*`: CGPA calculations and predictions
- `/mood/*`: Mood logging and tracking
- `/smartstudy/*`: AI chat, study plans, resource recommendations
- `/library/*`: Learning resource library

## PAU Grading System

The codebase implements PAU-specific grading logic in `backend/app/utils/pau_grading.py`:

- **5.0 Grade Scale**: A=5.0 (70-100), B=4.0 (60-69), C=3.0 (50-59), D=2.0 (45-49), E=1.0 (40-44), F=0.0 (0-39)
- **Assessment Split**: 35% CA (30 marks assessments + 5 marks participation) / 65% Exam
- **CGPA Formula**: `Σ(Grade Points × Credits) / Σ(Credits)`
- **Classifications**: First Class (4.50+), Second Class Upper (3.50+), Second Class Lower (2.40+), Third Class (1.50+)

## Key Implementation Details

### Authentication
- JWT tokens stored in localStorage (`access_token`)
- Axios interceptors auto-attach Bearer token and handle 401 redirects
- Password hashing with bcrypt

### SmartStudy AI System
- OpenAI integration for chat and study plan generation
- Study plans include curated YouTube videos, articles, and uploaded documents
- Document processing for PDF/PPTX files with text extraction

### Environment Variables
Backend requires `.env` file (see `.env.example`):
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key
- `OPENAI_API_KEY`: For SmartStudy AI features

Frontend uses Vite env:
- `VITE_API_URL`: Backend URL (defaults to http://localhost:8000)
