# 🚀 Shadow - Quick Setup Guide

## ✅ What's Been Set Up

### 1. Project Structure
```
shadow-final-year/
├── backend/          ✅ FastAPI backend (running on port 8001)
├── frontend/         ✅ React frontend (running on port 3001)
├── database/         ✅ PostgreSQL schema
└── README.md         ✅ Project documentation
```

### 2. Database
- **Database Name**: `shadow_db`
- **User**: `postgres`
- **Status**: ✅ Created with all tables
- **Tables**: users, semesters, courses, user_courses, tasks, moods, gpa_records, recommendations

### 3. Backend (Port 8001)
- **Status**: ✅ Running
- **URL**: http://localhost:8001
- **API Docs**: http://localhost:8001/api/docs
- **Health Check**: http://localhost:8001/health
- **Dependencies**: ✅ Installed

### 4. Frontend (Port 3001)
- **Status**: ✅ Running
- **URL**: http://localhost:3001
- **Framework**: React 18 + Vite
- **Styling**: TailwindCSS
- **Dependencies**: ✅ Installed

### 5. GitHub Repository
- **URL**: https://github.com/AdelekeAP/Shadow.git
- **Status**: ✅ Connected

## 🎯 Current Pages

### Frontend Routes
1. **Home** (`/`) - Landing page
2. **Login** (`/login`) - Login form
3. **Register** (`/register`) - Registration form
4. **Dashboard** (`/dashboard`) - Main dashboard (demo data)

## 📝 Next Steps

### Phase 1: Authentication (Next!)
1. Create User model in backend
2. Implement registration endpoint
3. Implement login endpoint with JWT
4. Connect frontend forms to backend APIs
5. Add protected routes

### Phase 2: Core CGPA System
1. Create Course models
2. Seed CS400 courses
3. Implement CGPA calculation
4. Create course enrollment endpoints

### Phase 3: Task Management
1. Create Task models
2. Implement task CRUD APIs
3. Build task creation UI
4. Add PAU-specific grading logic

## 🛠️ Development Commands

### Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

### Frontend
```bash
cd frontend
npm run dev
```

### Database
```bash
# Connect to database
psql -U postgres -d shadow_db

# View tables
\dt

# View schema
\d+ users
```

## 🔗 Important URLs

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/api/docs
- **GitHub Repo**: https://github.com/AdelekeAP/Shadow.git

## 📦 What's Included

### Backend Features
- ✅ FastAPI application structure
- ✅ Database connection (SQLAlchemy)
- ✅ PAU grading utilities (5.0 scale)
- ✅ CORS middleware
- ✅ Environment variables
- ⏳ Authentication (TODO)
- ⏳ API endpoints (TODO)

### Frontend Features
- ✅ React Router setup
- ✅ TailwindCSS configuration
- ✅ Landing page
- ✅ Login/Register forms (UI only)
- ✅ Dashboard skeleton
- ⏳ API integration (TODO)
- ⏳ State management (TODO)

### Database
- ✅ Complete schema (8 tables)
- ✅ Indexes for performance
- ✅ Foreign key relationships
- ✅ Triggers for timestamps
- ⏳ Seed data (TODO)

## 🎓 PAU Grading System (Already Implemented!)

The `backend/app/utils/pau_grading.py` file includes:

### Functions
- `convert_score_to_grade(score)` - Convert 0-100 to A-F
- `calculate_cgpa(courses)` - Calculate CGPA from courses
- `get_classification(cgpa)` - Get degree classification
- `predict_exam_score(ca_score)` - Predict exam based on CA
- `calculate_course_grade()` - Full grade calculation with 35/65 split
- `validate_ca_allocation()` - Ensure CA doesn't exceed 30 marks

## 🔐 Database Credentials

Located in `backend/.env`:
```
DATABASE_URL=postgresql://postgres:Leke2004@localhost:5432/shadow_db
```

## ⚠️ Important Notes

1. **Port 8000 is occupied** - Backend runs on port 8001
2. **Frontend auto-switched to port 3001** - Port 3000 was in use
3. **Virtual environment** - Always activate before running backend
4. **Hot reload enabled** - Both servers watch for file changes

## 🚀 Ready to Continue!

You now have a fully functional development environment. The next logical step is to:

1. **Build the Authentication System** - Let users register and login
2. **Create Database Models** - SQLAlchemy models for all tables
3. **Connect Frontend to Backend** - Make the forms functional

Would you like me to start with the authentication system?
