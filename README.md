# 🎯 Shadow - Goal-Driven Academic Achievement System

A comprehensive academic management platform designed specifically for Pan-Atlantic University students to achieve their target CGPA through intelligent task prioritization and real-time progress tracking.

## 🌟 Features

- **Goal-Driven CGPA Management**: Real-time tracking toward target CGPA
- **PAU-Specific Grading**: Accurate 35/65 CA/Exam split calculations
- **Smart Task Prioritization**: AI-powered recommendations based on mood and deadlines
- **Predictive Analytics**: Course grade predictions based on current performance
- **Recovery Planning**: Actionable guidance when falling behind
- **Unified Dashboard**: All academic data in one place

## 🏗️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy
- **Authentication**: JWT with bcrypt

### Frontend
- **Framework**: React 18 + Vite
- **Styling**: TailwindCSS
- **Routing**: React Router v6
- **Charts**: Recharts

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

5. Update `.env` with your PostgreSQL credentials:
```
DATABASE_URL=postgresql://username:password@localhost:5432/shadow_db
SECRET_KEY=your-secret-key-here
```

6. Create database:
```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE shadow_db;
\q
```

7. Run database schema:
```bash
psql -U postgres -d shadow_db -f ../database/schema.sql
```

8. Start backend server:
```bash
uvicorn app.main:app --reload
```

Backend will run at: http://localhost:8000
API Docs: http://localhost:8000/api/docs

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

Frontend will run at: http://localhost:3000

## 📁 Project Structure

```
shadow-final-year/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── models/         # SQLAlchemy models
│   │   ├── routes/         # API endpoints
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── utils/          # Helper functions
│   │   ├── database.py     # DB connection
│   │   └── main.py         # FastAPI app entry
│   ├── requirements.txt
│   └── .env
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/       # API calls
│   │   ├── styles/
│   │   └── App.jsx
│   └── package.json
├── database/               # SQL scripts
│   ├── schema.sql
│   ├── migrations/
│   └── seeds/
└── README.md
```

## 🎓 PAU Grading System

Shadow uses PAU's official 5.0 grading scale:

| Score | Grade | Points | Description |
|-------|-------|--------|-------------|
| 70-100 | A | 5.0 | Excellent |
| 60-69 | B | 4.0 | Good |
| 50-59 | C | 3.0 | Fair |
| 45-49 | D | 2.0 | Pass |
| 40-44 | E | 1.0 | Conditional Pass |
| 0-39 | F | 0.0 | Fail |

**Degree Classifications:**
- First Class: 4.50 - 5.00
- Second Class Upper: 3.50 - 4.49
- Second Class Lower: 2.40 - 3.49
- Third Class: 1.50 - 2.39

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `GET /api/v1/auth/me` - Get current user

### Courses
- `GET /api/v1/courses` - List all courses
- `POST /api/v1/user-courses` - Enroll in course
- `GET /api/v1/user-courses` - Get enrolled courses

### Tasks
- `GET /api/v1/tasks` - List tasks
- `POST /api/v1/tasks` - Create task
- `PATCH /api/v1/tasks/{id}/complete` - Mark complete

### GPA
- `GET /api/v1/gpa/current` - Current CGPA
- `GET /api/v1/gpa/predicted` - Predicted CGPA
- `POST /api/v1/gpa/what-if` - What-if scenarios

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📝 Development Roadmap

- [x] Project setup and structure
- [x] Database schema design
- [x] Backend skeleton with FastAPI
- [x] Frontend skeleton with React
- [x] Authentication system (JWT + HttpOnly cookies)
- [x] Course management with semester tracking
- [x] Task management with PAU grading
- [x] CGPA calculation engine with what-if analysis
- [x] Dashboard UI with CGPA ring, stats, tasks
- [x] Mood tracking with sentiment analysis
- [x] Smart recommendations
- [x] SmartStudy AI (GPT-4 chat, study plans, quizzes)
- [x] Learning styles (Visual, Audio, Reading, Kinesthetic)
- [x] ElevenLabs podcast generation
- [x] Study cards, practice exercises, concept diagrams
- [x] Library (peer-to-peer resource sharing)
- [x] Effectiveness analytics
- [x] Production CI/CD pipeline
- [x] E2E test suite (20 deployment readiness tests)

## 👥 Authors

**Paul Adeleke Aladenusi**
Computer Science 400L
Pan-Atlantic University

## 📄 License

This project is part of a Final Year Project at Pan-Atlantic University.

## 🙏 Acknowledgments

- Pan-Atlantic University
- Department of Computer Science
- Project Supervisor: Mr Charles Igah

---

**Built with ❤️ for PAU students**
