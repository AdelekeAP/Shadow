# 🎯 SHADOW V2.0 — Complete Project Specification
## Goal-Driven Academic Achievement System with AI Learning Intervention

**Version:** 2.0 **[UPDATED]**  
**Last Updated:** November 2025  
**Target Institution:** Pan-Atlantic University (PAU)  
**Initial Cohort:** Computer Science 400-Level Students  
**Major Enhancement:** SmartStudy AI Learning Intervention System

---

## 📋 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Core Value Proposition](#3-core-value-proposition)
4. [System Architecture](#4-system-architecture)
5. [PAU-Specific Grading System](#5-pau-specific-grading-system)
6. [Database Schema](#6-database-schema)
7. [Core Features](#7-core-features)
   - 7.1 Authentication & Onboarding
   - 7.2 Course Management
   - 7.3 Task Management
   - 7.4 CGPA Tracking & Prediction
   - 7.5 Smart Recommendations
   - 7.6 Mood Tracking
   - 7.7 Analytics & Insights
   - 7.8 Recovery Plans
   - **7.9 SmartStudy - AI Learning Intervention [NEW]**
8. [UI/UX Design Guidelines](#8-uiux-design-guidelines)
9. [Implementation Roadmap](#9-implementation-roadmap)
10. [MVP Scope](#10-mvp-scope)
11. [Success Metrics](#11-success-metrics)
12. [Risk Mitigation](#12-risk-mitigation)
13. [Future Enhancements](#13-future-enhancements)
14. [CS400 Course Catalog](#14-cs400-course-catalog)

---

## 1. Executive Summary

### Project Overview
**Shadow** is a goal-oriented academic assistant that helps university students achieve their target CGPA through intelligent task prioritization, real-time progress tracking, and **AI-powered learning intervention**. Unlike passive grade calculators, Shadow prescribes specific actions needed to close the gap between current trajectory and academic goals, and **actively helps students learn better through personalized AI guidance**.

### The Core Innovation
Students set their target CGPA (e.g., 4.50 for First Class), and Shadow continuously calculates what they need to do—course by course, task by task—to achieve it. **With SmartStudy**, when students struggle or want to learn better, they receive personalized AI tutoring, custom study plans, and curated learning resources that adapt to their performance data, mood, and learning style.

### Key Features
- **Goal-Driven CGPA Management**: Real-time tracking toward target CGPA
- **PAU-Specific Grading**: Accurate 35/65 CA/Exam split calculations
- **Smart Task Prioritization**: AI-powered recommendations based on mood and deadlines
- **Predictive Analytics**: Course grade predictions based on current performance
- **🆕 SmartStudy AI Tutor**: Interactive chat with context-aware AI assistance
- **🆕 Personalized Study Plans**: Automated learning intervention with effectiveness tracking
- **🆕 Intelligent Content Curation**: Multi-source quality-scored educational resources
- **Recovery Planning**: Actionable guidance when falling behind
- **Unified Dashboard**: All academic data in one place

### What's New in V2.0

**SmartStudy** transforms Shadow from a **diagnostic tool** into a **treatment system**:

| Shadow v1.0 | Shadow v2.0 with SmartStudy |
|-------------|---------------------------|
| "You're failing CSC401" | "You're struggling with Binary Trees. Here's a 10-day personalized plan" |
| Shows you're behind | Shows you HOW to catch up |
| Tracks performance | Improves performance through AI intervention |
| Passive data display | Active learning assistance |

---

## 2. Problem Statement

### The Gap Identified

University students face **four** critical challenges in academic management:

1. **No Behavioral Feedback Loop**  
   Students cannot see how daily task completion impacts semester-long CGPA outcomes until grades are finalized.

2. **Isolated Wellness Data**  
   Mood and stress tracking exists separately from academic workload, preventing students from understanding which courses or habits trigger burnout.

3. **Reactive Risk Awareness**  
   Academic struggles are identified at midterms or finals—too late for meaningful intervention.

4. **🆕 Disconnected Learning Resources**  
   Students use pauarchive, YouTube, ChatGPT separately—none are personalized to their performance data or learning needs.

### Current Landscape

Students currently use:
- **Google Calendar** - deadlines, reminders
- **Notion/Todoist** - task management
- **Excel/Google Sheets** - GPA calculators  
- **University LMS** (Canvas/Moodle) - course content, grades
- **Mental health apps** - mood tracking (Daylio, Headspace)
- **🆕 ChatGPT** - explains concepts, no academic context
- **🆕 YouTube/Khan Academy** - generic videos, not personalized
- **🆕 pauarchive** - static materials, no guidance

**What's Missing:** 
1. No single system connects behavioral data to academic outcomes
2. **🆕 No system that knows WHY students struggle and HOW to help them improve**
3. **🆕 No personalized learning intervention based on actual performance data**

### The Solution

Shadow addresses the **academic integration gap** by providing:
- Unified dashboard for courses, tasks, grades, and wellness
- Real-time CGPA prediction based on completion patterns
- Goal-driven task recommendations (not just due dates)
- Mood-aware workload balancing
- Actionable recovery plans when falling behind
- PAU-specific grading calculations for accurate predictions
- **🆕 AI-powered learning intervention that diagnoses struggles and prescribes personalized study plans**
- **🆕 Context-aware AI tutor that knows student's academic history**
- **🆕 Effectiveness tracking that proves interventions actually work**

---

## 3. Core Value Proposition

### For Students:
- **Know exactly what to do**: "Complete these 3 tasks to stay on track for your 4.50 goal"
- **See progress in real-time**: Dashboard shows "72% toward your goal"
- **Get personalized guidance**: Recommendations adapt to mood and capacity
- **Recover from setbacks**: Clear path back when you fall behind
- **One place for everything**: Stop context-switching between 5 apps
- **Accurate predictions**: PAU-specific grading system ensures reliable forecasts
- **🆕 Get instant help**: Chat with AI tutor that knows your academic history
- **🆕 Learn effectively**: Personalized study plans based on your learning style
- **🆕 Track improvement**: See if interventions actually improve your grades

### Key Differentiation:

| Compared To | Shadow v2.0 Advantage |
|-------------|----------------------|
| **Google Calendar** | Not just deadlines → Goal-driven prioritization + AI learning help |
| **pauarchive** | Not just content → Personalized resources based on YOUR struggles |
| **ChatGPT** | Not generic → Knows YOUR courses, grades, learning style |
| **YouTube** | Not random videos → Quality-scored, curated for YOUR needs |
| **Human Tutors** | Scales infinitely, available 24/7, learns what works for YOU |

**Core Innovation**: Performance Detection → AI Diagnosis → Personalized Learning → Effectiveness Measurement

---

## 4. System Architecture

### Technology Stack

#### Frontend
- **Framework:** React.js 18+
- **Styling:** TailwindCSS with custom navy/stone color palette
- **State Management:** React Context API
- **Charts:** Victory.js (for CGPA analytics)
- **Hosting:** Vercel

#### Backend
- **Framework:** FastAPI (Python 3.11+)
- **API Documentation:** Auto-generated (Swagger/OpenAPI)
- **Task Queue:** Celery (for notifications)
- **Hosting:** Render / Railway

#### Database
- **Primary DB:** PostgreSQL 15+
- **Hosting:** Supabase / Neon (free tier)
- **ORM:** SQLAlchemy

#### AI/ML Components

**Current (v1.0):**
- **Sentiment Analysis:** Hugging Face `distilbert-base-uncased-finetuned-sst-2-english` (binary POSITIVE/NEGATIVE)
- **Priority Scoring:** Rule-based weighted algorithm
- **CGPA Prediction:** Mathematical model (PAU-validated formulas)
- **Grade Prediction:** Pattern-based estimation using CA performance

**🆕 New (v2.0 - SmartStudy):**
- **LLM Integration:** OpenAI GPT-4 for personalized tutoring and study plan generation
- **Emotion Detection (UPGRADED):** Hugging Face `j-hartmann/emotion-english-distilroberta-base` for 7-emotion classification
  - Emotions: joy, sadness, anxiety, fear, anger, disgust, surprise
  - More nuanced mood understanding for adaptive study recommendations
  - Server-side processing (no per-request API costs)
- **Content Curation:** Multi-source quality scoring (YouTube API + Reddit API + student feedback)
- **Effectiveness Tracking:** Before/after grade comparison algorithms
- **Adaptive Learning:** Reinforcement learning for recommendation optimization

#### DevOps
- **Version Control:** GitHub
- **CI/CD:** GitHub Actions
- **API Testing:** Postman / pytest
- **Monitoring:** Sentry (error tracking)

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  FRONTEND (React + Vite)                 │
│  • Dashboard  • Courses  • Tasks  • CGPA  • SmartStudy  │
└───────────────────────┬─────────────────────────────────┘
                        │ REST API
┌───────────────────────┴─────────────────────────────────┐
│                   BACKEND (FastAPI)                      │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │    Core      │  │  SmartStudy  │  │  Analytics   │ │
│  │   Services   │  │  AI Engine   │  │   Service    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────┐
│            DATABASE (PostgreSQL)                         │
│  • Users  • Courses  • Tasks  • Moods  • Study Plans    │
└──────────────────────────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────┐
│              EXTERNAL SERVICES                           │
│  • OpenAI GPT-4  • YouTube API  • Reddit API            │
└──────────────────────────────────────────────────────────┘
```

---

## 5. PAU-Specific Grading System

### 5.1 Grade Point Scale

PAU uses a **5.0 scale** with the following conversion:

```python
PAU_GRADE_SCALE = {
    (70, 100): {"grade": "A", "points": 5.0, "description": "Excellent"},
    (60, 69):  {"grade": "B", "points": 4.0, "description": "Good"},
    (50, 59):  {"grade": "C", "points": 3.0, "description": "Fair"},
    (45, 49):  {"grade": "D", "points": 2.0, "description": "Pass"},
    (40, 44):  {"grade": "E", "points": 1.0, "description": "Conditional Pass"},
    (0, 39):   {"grade": "F", "points": 0.0, "description": "Fail"}
}

# Classification Thresholds
FIRST_CLASS = 4.50
SECOND_CLASS_UPPER = 3.50
SECOND_CLASS_LOWER = 2.40
THIRD_CLASS = 1.50
```

### 5.2 Course Assessment Structure

**IMPORTANT UPDATE**: CA is **30 marks** (not 35), with 5 participation marks at lecturer's discretion.

PAU uses a **30+5/65 structure** for all courses:

```python
# Standard PAU Course Breakdown (UPDATED)
CA_ASSESSMENTS = 30        # Tests + Projects - student-tracked
CA_PARTICIPATION = 5        # Lecturer discretion - NOT tracked in tasks
TOTAL_CA = 35              # CA + Participation
FINAL_EXAM = 65            # Fixed

# Validation Rule
MAX_CA_TASKS = 30  # Students can only allocate up to 30 marks total

# Typical CA Distribution Options
OPTION_A = {  # 2 Tests
    "test_1": 15,
    "test_2": 15,
    # participation: 5 (not tracked)
}

OPTION_B = {  # 2 Tests + 1 Project
    "test_1": 10,
    "test_2": 10,
    "project": 10,
    # participation: 5 (not tracked)
}

OPTION_C = {  # 3 Tests
    "test_1": 10,
    "test_2": 10,
    "test_3": 10,
    # participation: 5 (not tracked)
}
```

### 5.3 CGPA Calculation

```python
def calculate_cgpa_pau(courses):
    """
    Official PAU CGPA formula
    CGPA = Σ(Grade Points × Credits) / Σ(Credits)
    """
    total_grade_points = sum(
        course.grade_point * course.credits 
        for course in courses
    )
    total_credits = sum(course.credits for course in courses)
    
    cgpa = total_grade_points / total_credits
    return round(cgpa, 2)
```

### 5.4 Grade Prediction with SmartStudy

```python
def calculate_predicted_grade_with_smartstudy(user_course, tasks, study_plans):
    """
    Enhanced prediction considering SmartStudy interventions
    """
    from datetime import datetime
    
    # Completed CA tasks
    completed_ca = sum(
        task.earned_marks for task in tasks 
        if task.is_completed and task.category == 'CA'
    )
    
    # Pending tasks with penalties
    now = datetime.utcnow()
    pending_tasks = [
        task for task in tasks 
        if not task.is_completed and task.category == 'CA'
    ]
    
    pending_ca = 0
    for task in pending_tasks:
        # NEW: Check if student has active study plan for this topic
        has_study_plan = any(
            plan.topic in task.topic and plan.is_active 
            for plan in study_plans
        )
        
        if has_study_plan:
            # Better performance expected with SmartStudy help
            performance_boost = 0.1  # 10% improvement
        else:
            performance_boost = 0
        
        if task.due_date and task.due_date < now:
            # Overdue: 70% + boost
            pending_ca += task.weight * (0.70 + performance_boost)
        else:
            # Not yet due: 80% + boost
            pending_ca += task.weight * (0.80 + performance_boost)
    
    # Total CA (add participation estimate)
    total_ca = completed_ca + pending_ca + 5  # +5 for participation
    
    # Predict exam using 85% retention model
    ca_percentage = total_ca / 35
    predicted_exam = (ca_percentage * 0.85) * 65
    
    # NEW: SmartStudy effectiveness boost
    if any(plan.is_active for plan in study_plans):
        # Students using SmartStudy perform 5% better on average
        predicted_exam *= 1.05
    
    predicted_score = total_ca + predicted_exam
    
    return {
        'completed_ca': completed_ca,
        'pending_ca': pending_ca,
        'total_ca': total_ca,
        'predicted_exam': predicted_exam,
        'predicted_score': min(predicted_score, 100),  # Cap at 100
        'predicted_grade': score_to_grade(predicted_score),
        'predicted_points': grade_to_points(score_to_grade(predicted_score)),
        'smartstudy_boost': has_study_plan
    }
```

---

## 6. Database Schema

### 6.1 Core Tables (Existing)

#### `users`
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    university_id VARCHAR(50),
    entry_level VARCHAR(10),
    gpa_scale DECIMAL(3,1) DEFAULT 5.0,
    target_cgpa DECIMAL(3,2),
    current_cgpa DECIMAL(3,2),
    total_credits_completed INTEGER DEFAULT 0,
    learning_style VARCHAR(50),  -- NEW: 'visual', 'auditory', 'reading', 'kinesthetic'
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    INDEX idx_email (email)
);
```

#### `courses`
```sql
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    credits INTEGER NOT NULL,
    level VARCHAR(10),
    status VARCHAR(20) DEFAULT 'C',
    department VARCHAR(100) DEFAULT 'Computer Science',
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_code (code),
    INDEX idx_level (level)
);
```

#### `user_courses`
```sql
CREATE TABLE user_courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    semester_id UUID REFERENCES semesters(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    
    -- PAU-specific fields
    ca_score DECIMAL(5,2) DEFAULT 0,
    participation_score DECIMAL(5,2) DEFAULT 5,  -- Estimated
    exam_score DECIMAL(5,2),
    predicted_exam_score DECIMAL(5,2),
    
    current_score DECIMAL(5,2),
    predicted_score DECIMAL(5,2),
    current_grade_point DECIMAL(3,2),
    predicted_grade_point DECIMAL(3,2),
    letter_grade VARCHAR(2),
    predicted_letter_grade VARCHAR(2),
    
    completion_rate DECIMAL(5,2),
    enrolled_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, semester_id, course_id),
    INDEX idx_user_semester (user_id, semester_id)
);
```

#### `tasks`
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    user_course_id UUID REFERENCES user_courses(id) ON DELETE CASCADE,
    
    title VARCHAR(255) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) NOT NULL,
    topic VARCHAR(255),  -- NEW: For SmartStudy targeting
    
    -- PAU-specific grading
    weight DECIMAL(5,2) NOT NULL,
    max_marks DECIMAL(5,2),
    earned_marks DECIMAL(5,2),
    category VARCHAR(10),  -- 'CA' or 'EXAM'
    
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    is_completed BOOLEAN DEFAULT FALSE,
    is_late BOOLEAN DEFAULT FALSE,
    
    effort_estimate INTEGER,
    actual_effort INTEGER,
    
    priority_score DECIMAL(5,2),
    is_urgent BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user_course (user_course_id),
    INDEX idx_due_date (due_date),
    INDEX idx_topic (topic)  -- NEW: For SmartStudy queries
);
```

#### `moods`
```sql
CREATE TABLE moods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    mood_type VARCHAR(50) NOT NULL,
    mood_text TEXT,
    sentiment_score DECIMAL(3,2),
    energy_level INTEGER,
    
    associated_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    associated_course_id UUID REFERENCES user_courses(id) ON DELETE SET NULL,
    
    logged_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user_date (user_id, logged_at DESC)
);
```

### 6.2 SmartStudy Tables (NEW)

#### `chat_conversations`
```sql
CREATE TABLE chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),  -- Auto-generated from first message
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user_recent (user_id, updated_at DESC)
);
```

#### `chat_messages`
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES chat_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    tokens_used INTEGER,
    model_used VARCHAR(50) DEFAULT 'gpt-4',
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_conversation (conversation_id, created_at)
);
```

#### `study_plans`
```sql
CREATE TABLE study_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id),
    topic VARCHAR(255) NOT NULL,
    
    -- Trigger information
    trigger_type VARCHAR(50),  -- 'reactive', 'proactive', 'preventive', 'exploratory'
    trigger_task_id UUID REFERENCES tasks(id),
    trigger_score DECIMAL(5,2),  -- Score that triggered intervention (if reactive)
    
    -- Plan content
    plan_data JSONB NOT NULL,  -- GPT-4 generated plan structure
    duration_days INTEGER,
    start_date DATE,
    end_date DATE,
    
    -- Progress tracking
    completion_percentage DECIMAL(5,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Effectiveness
    before_score DECIMAL(5,2),  -- Baseline performance
    after_score DECIMAL(5,2),  -- Performance after intervention
    effectiveness_score DECIMAL(5,2),  -- Calculated improvement
    
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    INDEX idx_user_active (user_id, is_active),
    INDEX idx_topic (topic)
);
```

#### `study_plan_resources`
```sql
CREATE TABLE study_plan_resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    study_plan_id UUID REFERENCES study_plans(id) ON DELETE CASCADE,
    
    resource_type VARCHAR(50) NOT NULL,  -- 'youtube_video', 'reddit_post', 'ai_explanation', 'pauarchive_link'
    resource_url TEXT,
    resource_title TEXT,
    resource_description TEXT,
    quality_score DECIMAL(5,2),  -- CrowdCurate quality score
    
    -- Engagement tracking
    clicked BOOLEAN DEFAULT FALSE,
    clicked_at TIMESTAMP,
    completed BOOLEAN DEFAULT FALSE,
    helpful_rating INTEGER,  -- 1-5 stars
    
    day_number INTEGER,  -- Which day in the plan
    order_in_day INTEGER,  -- Order within day
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_plan_day (study_plan_id, day_number)
);
```

#### `uploaded_documents` (Optional Feature)
```sql
CREATE TABLE uploaded_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id),
    conversation_id UUID REFERENCES chat_conversations(id),
    
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_type VARCHAR(50),
    file_size INTEGER,
    
    -- AI Analysis
    analyzed BOOLEAN DEFAULT FALSE,
    analyzed_topics JSONB,  -- GPT-4 Vision extracted topics
    analysis_confidence VARCHAR(20),  -- 'high', 'medium', 'low'
    
    uploaded_at TIMESTAMP DEFAULT NOW(),
    analyzed_at TIMESTAMP,
    
    INDEX idx_user_uploads (user_id, uploaded_at DESC)
);
```

#### `intervention_outcomes`
```sql
CREATE TABLE intervention_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    study_plan_id UUID REFERENCES study_plans(id),
    
    -- Performance metrics
    before_score DECIMAL(5,2),
    after_score DECIMAL(5,2),
    grade_improvement DECIMAL(5,2),
    
    -- Learning metrics
    days_to_improvement INTEGER,
    completion_rate DECIMAL(5,2),
    resource_engagement_rate DECIMAL(5,2),
    
    -- Context
    intervention_type VARCHAR(50),  -- 'chat_only', 'study_plan', 'both'
    student_mood_during VARCHAR(50),
    
    measured_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_effectiveness (user_id, grade_improvement DESC)
);
```

#### `content_quality_scores` (Curation Cache)
```sql
CREATE TABLE content_quality_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    content_type VARCHAR(50),  -- 'youtube_video', 'reddit_post'
    content_id VARCHAR(255) UNIQUE,  -- External ID
    content_url TEXT,
    content_title TEXT,
    topic VARCHAR(255),
    
    -- Quality signals
    engagement_score DECIMAL(5,2),  -- Likes, views, comments
    sentiment_score DECIMAL(5,2),  -- Comment sentiment
    community_score DECIMAL(5,2),  -- Reddit upvotes
    student_rating DECIMAL(5,2),  -- Shadow user ratings
    
    -- Composite score
    quality_score DECIMAL(5,2),  -- 0-100 final score
    
    last_updated TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_topic_quality (topic, quality_score DESC)
);
```

---

## 7. Core Features

### 7.1 Authentication & Onboarding

**Features:**
- Email/password registration
- Secure login with JWT tokens
- Profile setup wizard:
  - Entry level (100L-400L)
  - Target CGPA selection
  - Current CGPA (if applicable)
  - **🆕 Learning style assessment** (1 question: Visual/Audio/Reading/Kinesthetic)

### 7.2 Course Management

**Features:**
- Pre-loaded CS400 courses
- Add/edit enrolled courses
- Set course priorities
- Track course completion rate
- View course-specific tasks
- **🆕 "Get Help" button triggers SmartStudy for struggling courses**

### 7.3 Task Management

**Features:**
- Create tasks with:
  - Title & description
  - Task type (test, project, assignment, exam)
  - **🆕 Topic field (optional, helps SmartStudy target help)**
  - Weight (marks out of 30 for CA)
  - Due date
  - Effort estimate
- Mark tasks complete
- Enter earned marks
- **🆕 Auto-prompt SmartStudy intervention on low scores**

### 7.4 CGPA Tracking & Prediction

**Features:**
- Real-time CGPA calculation
- Predicted CGPA based on current performance
- Progress toward target CGPA
- "What-if" scenarios
- **🆕 SmartStudy boost indicator (shows if AI help is improving predictions)**

### 7.5 Smart Recommendations

**Algorithm Enhanced with SmartStudy:**
```python
def calculate_priority_score_v2(task, user_context, smartstudy_data):
    """
    Priority Score = W1×Urgency + W2×Weight + W3×Mood + W4×Goal + W5×SmartStudy
    """
    # Original factors
    urgency_score = max(0, 10 - days_until_due)
    weight_impact = (task.weight / 30) * 10
    mood_score = match_task_to_mood(task, user_context.recent_mood)
    goal_impact = (task.weight / 100) * cgpa_gap * 10
    
    # NEW: SmartStudy factor
    if task.topic and has_active_study_plan(task.topic):
        smartstudy_boost = 2  # Slightly boost tasks with active study plans
    else:
        smartstudy_boost = 0
    
    # Weighted sum
    W1, W2, W3, W4, W5 = 0.35, 0.30, 0.15, 0.15, 0.05
    priority = (W1 * urgency_score + 
                W2 * weight_impact + 
                W3 * mood_score + 
                W4 * goal_impact +
                W5 * smartstudy_boost)
    
    return round(priority, 2)
```

### 7.6 Mood Tracking with Advanced Emotion Detection

**Features:**
- Quick mood log with energy level
- **🆕 7-emotion detection** (joy, sadness, anxiety, fear, anger, disgust, surprise)
- Mood trends visualization
- **🆕 Mood influences SmartStudy study plan intensity**
- **🆕 Stressed/anxious moods trigger lighter study sessions**

#### Emotion Detection Implementation

**Model**: `j-hartmann/emotion-english-distilroberta-base`

```python
# backend/app/services/emotion_analysis.py
from transformers import pipeline
import torch

class EmotionAnalyzer:
    def __init__(self):
        # Use GPU if available (MPS for Mac, CUDA for others)
        device = 0 if torch.cuda.is_available() else -1
        if torch.backends.mps.is_available():
            device = "mps"
        
        self.classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            device=device,
            top_k=None  # Return all emotion scores
        )
    
    def analyze_mood(self, text):
        """
        Detect emotions from mood text
        Returns: {
            'primary_emotion': 'joy',
            'confidence': 0.89,
            'all_emotions': {
                'joy': 0.89,
                'anxiety': 0.05,
                'sadness': 0.03,
                ...
            }
        }
        """
        if not text or len(text.strip()) < 3:
            return None
        
        # Get predictions
        results = self.classifier(text)[0]  # Returns list of all emotions
        
        # Parse results
        emotions = {}
        for result in results:
            emotions[result['label']] = round(result['score'], 3)
        
        # Find primary emotion
        primary = max(emotions.items(), key=lambda x: x[1])
        
        return {
            'primary_emotion': primary[0],
            'confidence': primary[1],
            'all_emotions': emotions
        }

# Initialize globally
emotion_analyzer = EmotionAnalyzer()
```

**API Integration:**
```python
# backend/app/routes/mood.py
@router.post("/log-mood")
async def log_mood(
    mood_data: MoodLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log mood with advanced emotion detection
    """
    # Analyze emotion if text provided
    emotion_analysis = None
    if mood_data.mood_text:
        emotion_analysis = emotion_analyzer.analyze_mood(mood_data.mood_text)
    
    # Create mood log
    mood = MoodLog(
        user_id=current_user.id,
        mood_type=mood_data.mood_type,
        mood_text=mood_data.mood_text,
        energy_level=mood_data.energy_level,
        
        # NEW: Store emotion data
        primary_emotion=emotion_analysis['primary_emotion'] if emotion_analysis else None,
        emotion_confidence=emotion_analysis['confidence'] if emotion_analysis else None,
        emotion_scores=emotion_analysis['all_emotions'] if emotion_analysis else None,  # JSONB
        
        logged_at=datetime.utcnow()
    )
    
    db.add(mood)
    db.commit()
    
    return {
        "mood": mood,
        "emotion_analysis": emotion_analysis,
        "smartstudy_recommendation": get_mood_based_recommendation(emotion_analysis)
    }

def get_mood_based_recommendation(emotion_analysis):
    """
    SmartStudy recommendations based on detected emotion
    """
    if not emotion_analysis:
        return None
    
    emotion = emotion_analysis['primary_emotion']
    confidence = emotion_analysis['confidence']
    
    recommendations = {
        'joy': {
            'intensity': 'normal',
            'session_length': 30,
            'message': "Great energy! Perfect time for focused study."
        },
        'anxiety': {
            'intensity': 'light',
            'session_length': 15,
            'message': "You seem anxious. Let's do a short, easy session to build confidence."
        },
        'sadness': {
            'intensity': 'light',
            'session_length': 10,
            'message': "Take it easy today. Small progress is still progress."
        },
        'fear': {
            'intensity': 'supportive',
            'session_length': 20,
            'message': "Let's tackle this together. Start with something familiar."
        },
        'anger': {
            'intensity': 'productive',
            'session_length': 25,
            'message': "Channel that energy into productive learning!"
        },
        'surprise': {
            'intensity': 'normal',
            'session_length': 30,
            'message': "Ready to learn something new?"
        },
        'disgust': {
            'intensity': 'break',
            'session_length': 0,
            'message': "Maybe take a break and come back later?"
        }
    }
    
    return recommendations.get(emotion, recommendations['joy'])
```

**Database Schema Update:**
```sql
-- Add emotion fields to moods table
ALTER TABLE moods ADD COLUMN primary_emotion VARCHAR(50);
ALTER TABLE moods ADD COLUMN emotion_confidence DECIMAL(3,3);
ALTER TABLE moods ADD COLUMN emotion_scores JSONB;

-- Example emotion_scores JSONB:
{
  "joy": 0.892,
  "anxiety": 0.045,
  "sadness": 0.032,
  "fear": 0.018,
  "anger": 0.008,
  "disgust": 0.003,
  "surprise": 0.002
}
```

**Frontend Integration:**
```jsx
// After mood logged
{emotionAnalysis && (
  <div className="mt-4 p-4 bg-teal-50 border border-teal-200 rounded-lg">
    <h4 className="font-semibold text-teal-900 mb-2">
      AI Detected: {emotionAnalysis.primary_emotion} 
      ({Math.round(emotionAnalysis.confidence * 100)}% confidence)
    </h4>
    <p className="text-sm text-teal-800">
      {emotionAnalysis.smartstudy_recommendation.message}
    </p>
    {emotionAnalysis.smartstudy_recommendation.session_length > 0 && (
      <button className="mt-3 px-4 py-2 bg-teal-600 text-white rounded-lg text-sm">
        Start {emotionAnalysis.smartstudy_recommendation.session_length}-min session
      </button>
    )}
  </div>
)}
```

**SmartStudy Integration:**
```python
def adjust_study_plan_for_mood(study_plan_id, current_emotion):
    """
    Dynamically adjust study plan based on current emotional state
    """
    plan = get_study_plan(study_plan_id)
    current_day = get_current_day_tasks(plan)
    
    if current_emotion in ['anxiety', 'fear', 'sadness']:
        # Reduce difficulty and duration
        for task in current_day['tasks']:
            task['duration'] = min(task['duration'], 15)
            task['difficulty'] = 'easy'
            task['supportive_message'] = True
    
    elif current_emotion == 'joy':
        # Can handle normal or challenging tasks
        pass
    
    elif current_emotion == 'anger':
        # Redirect to productive practice problems
        current_day['tasks'] = [
            t for t in current_day['tasks'] 
            if t['type'] == 'practice'
        ]
    
    return current_day
```

### 7.7 Analytics & Insights

**Dashboard Widgets:**
1. CGPA Progress
2. Course Performance
3. Task Overview
4. Mood Trends
5. **🆕 SmartStudy Effectiveness (grade improvements from interventions)**

### 7.8 Recovery Plans

**Triggered When:**
- Predicted CGPA < Target
- Course grade drops below threshold
- Multiple late/missed tasks
- **🆕 SmartStudy auto-generates recovery study plans**

---

## 7.9 SmartStudy - AI Learning Intervention System 🆕

### Overview

**SmartStudy** is an AI-powered learning intervention system that transforms Shadow from a passive tracker into an active learning assistant. It provides two modes of interaction:

1. **Interactive Chat Mode**: Student-initiated Q&A with context-aware AI
2. **Automated Intervention Mode**: System-initiated help when struggles detected

### 7.9.1 Interactive AI Chat

#### Core Functionality

Students can ask questions and receive personalized responses that incorporate their full academic context.

**What Makes It Different from ChatGPT:**

| Feature | ChatGPT | SmartStudy Chat |
|---------|---------|-----------------|
| Context | None | Full academic history |
| Personalization | Generic | Tailored to learning style |
| Resource linking | None | Curated videos, materials |
| Effectiveness tracking | None | Measures grade improvement |
| Conversation memory | Limited | Persistent across sessions |
| Action escalation | None | Can trigger study plans |

#### Example Interactions

**Scenario 1: Concept Explanation**
```
Student: "I don't understand recursion"

SmartStudy: "I see you recently scored 45% on your CSC401 Binary Trees 
assessment. Based on your test answers, you understand the concept but 
struggle with implementation, specifically base cases.

Since you're a visual learner, let me explain with animations...

[Personalized explanation with diagrams]

Would you like me to:
1. Generate practice problems at your level
2. Create a 7-day recursion mastery plan
3. Find the highest-rated tutorial videos
4. Connect this to your upcoming CSC403 assignment"
```

**Scenario 2: Study Strategy**
```
Student: "I have a CSC401 test next week, how should I prepare?"

SmartStudy: "Based on your performance:
• Binary Trees: 45% last time - HIGH PRIORITY
• Graph Algorithms: Not yet tested - MEDIUM PRIORITY
• Sorting: 85% - You're strong here

Your study patterns show you're most productive at 9 PM for 30-minute 
sessions. Here's a 7-day plan:

[Customized daily breakdown]

You're currently feeling stressed (3/5 energy). Want me to create 
lighter sessions for the next 2 days?"
```

#### Implementation

**Backend: Context-Aware Responses**
```python
def generate_chat_response(user_message, user_id, conversation_id):
    """
    Generate AI response with full student context
    """
    # Load comprehensive context
    student = get_user(user_id)
    courses = get_enrolled_courses(user_id)
    recent_tasks = get_recent_tasks(user_id, limit=10)
    recent_mood = get_recent_mood(user_id)
    active_plans = get_active_study_plans(user_id)
    
    # Build rich system prompt
    system_prompt = f"""
    You are SmartStudy, an AI academic tutor for {student.full_name}, 
    a PAU Computer Science student.
    
    STUDENT PROFILE:
    - Current CGPA: {student.current_cgpa} (Target: {student.target_cgpa})
    - Learning Style: {student.learning_style}
    - Entry Level: {student.entry_level}
    
    ENROLLED COURSES (Current Semester):
    {format_courses_context(courses)}
    
    RECENT PERFORMANCE:
    {format_recent_performance(recent_tasks)}
    
    CURRENT MOOD: {recent_mood.mood_type} (Energy: {recent_mood.energy_level}/5)
    
    ACTIVE INTERVENTIONS:
    {format_active_plans(active_plans)}
    
    INSTRUCTIONS:
    - Reference their specific performance when relevant
    - Suggest concrete actions (study plans, resources)
    - Match tone to their mood (supportive if stressed, energetic if motivated)
    - Use PAU's course codes and terminology
    - Always offer to escalate to full study plan if deep help needed
    """
    
    # Call GPT-4
    from openai import OpenAI
    client = OpenAI()
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    ai_response = response.choices[0].message.content
    
    # Save conversation
    save_message(conversation_id, "user", user_message)
    save_message(conversation_id, "assistant", ai_response)
    
    # Track for effectiveness
    log_chat_interaction(user_id, user_message, ai_response)
    
    return ai_response
```

**Frontend: Chat Interface**
```jsx
// SmartStudyChat.jsx
import { useState, useEffect, useRef } from 'react';

export default function SmartStudyChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  
  const sendMessage = async () => {
    if (!input.trim()) return;
    
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: input }]);
    setInput('');
    setLoading(true);
    
    try {
      const response = await fetch('/api/v1/smartstudy/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input })
      });
      
      const data = await response.json();
      
      // Add AI response
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        actions: data.suggested_actions  // Links to resources, study plans
      }]);
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  return (
    <div className="h-screen flex flex-col bg-stone-50">
      {/* Header */}
      <div className="bg-navy-800 text-white p-4">
        <h2 className="text-xl font-bold">💬 SmartStudy AI Tutor</h2>
        <p className="text-sm opacity-90">
          Ask me anything about your courses - I know your academic history
        </p>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <SuggestedPrompts onSelect={setInput} />
        )}
        
        {messages.map((msg, i) => (
          <Message key={i} role={msg.role} content={msg.content} actions={msg.actions} />
        ))}
        
        {loading && <LoadingDots />}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <div className="border-t border-stone-200 p-4 bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask me anything..."
            className="flex-1 px-4 py-3 border-2 border-stone-200 rounded-lg focus:border-navy-500"
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="px-6 py-3 bg-navy-800 text-white rounded-lg hover:bg-navy-900 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 7.9.2 Automated Study Plan Generation

#### When It Triggers

**Reactive (After Struggling):**
```python
def check_intervention_triggers(task_completion_event):
    """
    Auto-trigger SmartStudy when student struggles
    """
    if task_completion_event.score_percentage < 60:
        prompt_smartstudy_intervention(
            user_id=task_completion_event.user_id,
            trigger_type='reactive',
            task=task_completion_event.task,
            score=task_completion_event.score
        )
```

**Proactive (Student Request):**
- Student clicks "Get Study Plan" button
- Student asks in chat: "Help me prepare for X"
- Student navigates to SmartStudy Hub

**Preventive (Upcoming Assessment):**
- 7 days before major test (auto-suggest preparation)
- When course predicted grade drops near threshold

#### Study Plan Structure

```json
{
  "plan_id": "uuid",
  "topic": "Binary Trees and Recursion",
  "course": "CSC401",
  "duration_days": 10,
  "daily_sessions": [
    {
      "day": 1,
      "title": "Understanding the Concept",
      "duration_minutes": 20,
      "tasks": [
        {
          "type": "video",
          "title": "Binary Trees Explained Visually",
          "url": "youtube.com/watch?v=...",
          "quality_score": 94,
          "duration": "12 min",
          "why": "Top-rated visual explanation for your learning style"
        },
        {
          "type": "ai_explanation",
          "content": "Custom GPT-4 explanation using PAU terminology",
          "why": "Tailored to your specific confusion from test"
        },
        {
          "type": "practice",
          "problems": [
            "Implement a BST insert function",
            "Write tree traversal algorithms"
          ],
          "difficulty": "beginner"
        }
      ],
      "checkpoint": "Can you explain BST insertion in your own words?"
    },
    {
      "day": 2,
      "title": "Implementation Practice",
      "duration_minutes": 30,
      "mood_adaptive": true  // Adjust if student stressed
    }
    // ... days 3-10
  ],
  "success_criteria": {
    "target_score": 75,  // Aim for B on next assessment
    "confidence_level": "high"
  }
}
```

#### Plan Generation Code

```python
def generate_study_plan(user_id, topic, course_id, trigger_context):
    """
    Generate personalized study plan using GPT-4
    """
    # Load context
    student = get_user(user_id)
    course = get_course(course_id)
    learning_history = get_learning_history(user_id, topic)
    
    # Build GPT-4 prompt
    prompt = f"""
    Create a personalized study plan for a student struggling with {topic}.
    
    STUDENT CONTEXT:
    - Learning Style: {student.learning_style}
    - Current Performance: {trigger_context.score}% on recent assessment
    - Available Study Time: {estimate_available_time(student)} mins/day
    - Current Mood: {student.recent_mood.mood_type}
    - Course: {course.code} - {course.title}
    
    LEARNING HISTORY:
    - Previous topics mastered: {learning_history.strong_topics}
    - Consistent struggles: {learning_history.weak_areas}
    - Best learning approaches: {learning_history.effective_methods}
    
    TARGET: Improve from {trigger_context.score}% to 75%+ on next assessment
    
    Generate a {calculate_optimal_duration(student)} day study plan with:
    - Daily sessions (15-45 mins based on mood/capacity)
    - Mix of videos, reading, practice problems
    - Checkpoints to verify understanding
    - Adaptive difficulty (start easy, increase gradually)
    
    Format as JSON with this structure: [provide schema]
    """
    
    # Call GPT-4
    from openai import OpenAI
    client = OpenAI()
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2000
    )
    
    # Parse JSON plan
    import json
    plan_data = json.loads(response.choices[0].message.content)
    
    # Enhance with curated resources
    for day in plan_data['daily_sessions']:
        for task in day['tasks']:
            if task['type'] == 'video':
                # Find best YouTube video
                task['url'] = crowdcurate_find_video(topic, min_quality=75)
            elif task['type'] == 'reading':
                # Check pauarchive
                task['url'] = search_pauarchive(course.code, topic)
    
    # Save to database
    study_plan = save_study_plan(
        user_id=user_id,
        course_id=course_id,
        topic=topic,
        plan_data=plan_data,
        trigger_score=trigger_context.score
    )
    
    return study_plan
```

### 7.9.3 Content Curation System (CrowdCurate)

#### Multi-Source Quality Scoring

```python
def crowdcurate_score_video(video_id, topic):
    """
    Calculate quality score from multiple signals
    """
    # YouTube engagement
    youtube_data = get_youtube_stats(video_id)
    engagement_score = calculate_engagement(
        views=youtube_data.views,
        likes=youtube_data.likes,
        comments_count=youtube_data.comments_count,
        like_ratio=youtube_data.likes / max(youtube_data.dislikes, 1)
    )
    
    # Comment sentiment
    comments = get_youtube_comments(video_id, limit=50)
    positive_keywords = [
        "finally understood", "best explanation", "cleared my doubt",
        "made it so easy", "perfect tutorial", "saved my grade"
    ]
    sentiment_score = analyze_comment_sentiment(comments, positive_keywords)
    
    # Reddit community score
    reddit_mentions = search_reddit(f"{topic} tutorial video", subreddits=[
        'learnprogramming', 'computerscience', 'programming'
    ])
    community_score = sum(post.upvotes for post in reddit_mentions if video_id in post.url)
    
    # Shadow user ratings
    shadow_ratings = get_user_ratings(video_id)
    student_score = mean(shadow_ratings) if shadow_ratings else 50
    
    # Weighted composite
    quality_score = (
        0.30 * engagement_score +
        0.25 * sentiment_score +
        0.20 * community_score +
        0.25 * student_score
    )
    
    # Cache result
    cache_quality_score(video_id, topic, quality_score)
    
    return round(quality_score, 2)
```

#### YouTube API Integration

```python
from googleapiclient.discovery import build

def search_youtube_videos(topic, max_results=10):
    """
    Search YouTube for educational videos on topic
    """
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # Search query
    search_response = youtube.search().list(
        q=f"{topic} tutorial explanation",
        part='id,snippet',
        maxResults=max_results,
        type='video',
        videoDuration='medium',  # 4-20 minutes
        relevanceLanguage='en',
        order='relevance'
    ).execute()
    
    # Get detailed stats
    video_ids = [item['id']['videoId'] for item in search_response['items']]
    stats_response = youtube.videos().list(
        part='statistics,contentDetails',
        id=','.join(video_ids)
    ).execute()
    
    # Score and rank
    scored_videos = []
    for video, stats in zip(search_response['items'], stats_response['items']):
        quality_score = crowdcurate_score_video(video['id']['videoId'], topic)
        
        if quality_score >= 70:  # Only high-quality videos
            scored_videos.append({
                'video_id': video['id']['videoId'],
                'title': video['snippet']['title'],
                'url': f"https://youtube.com/watch?v={video['id']['videoId']}",
                'quality_score': quality_score,
                'views': int(stats['statistics']['viewCount']),
                'likes': int(stats['statistics'].get('likeCount', 0))
            })
    
    # Sort by quality
    return sorted(scored_videos, key=lambda x: x['quality_score'], reverse=True)
```

#### Reddit Integration

```python
import praw

def search_reddit_recommendations(topic, min_upvotes=10):
    """
    Find community-recommended resources from Reddit
    """
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent='SmartStudy/1.0'
    )
    
    subreddits = [
        'learnprogramming',
        'computerscience',
        'programming',
        'cscareerquestions'
    ]
    
    recommendations = []
    
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        
        # Search posts
        for post in subreddit.search(topic, limit=20, sort='relevance'):
            if post.score >= min_upvotes:
                # Extract resources from post
                resources = extract_resources_from_post(post)
                
                for resource in resources:
                    recommendations.append({
                        'type': resource['type'],
                        'url': resource['url'],
                        'title': post.title,
                        'upvotes': post.score,
                        'subreddit': subreddit_name,
                        'community_score': calculate_reddit_score(post)
                    })
    
    return sorted(recommendations, key=lambda x: x['community_score'], reverse=True)
```

### 7.9.4 Effectiveness Tracking

#### Measuring Impact

```python
def track_intervention_effectiveness(study_plan_id):
    """
    Measure if SmartStudy intervention actually improved grades
    """
    study_plan = get_study_plan(study_plan_id)
    user_id = study_plan.user_id
    topic = study_plan.topic
    
    # Before score (what triggered intervention)
    before_score = study_plan.trigger_score
    
    # Find next assessment on same topic
    next_task = find_next_assessment(
        user_id=user_id,
        topic=topic,
        after_date=study_plan.created_at
    )
    
    if next_task and next_task.is_completed:
        # After score
        after_score = (next_task.earned_marks / next_task.weight) * 100
        
        # Calculate improvement
        improvement = after_score - before_score
        improvement_percentage = (improvement / before_score) * 100
        
        # Categorize effectiveness
        if improvement >= 20:
            effectiveness = "highly_effective"
        elif improvement >= 10:
            effectiveness = "effective"
        elif improvement >= 0:
            effectiveness = "neutral"
        else:
            effectiveness = "ineffective"
        
        # Update study plan
        update_study_plan_effectiveness(
            study_plan_id=study_plan_id,
            after_score=after_score,
            improvement=improvement,
            effectiveness=effectiveness
        )
        
        # Log outcome
        log_intervention_outcome(
            user_id=user_id,
            study_plan_id=study_plan_id,
            before_score=before_score,
            after_score=after_score,
            grade_improvement=improvement,
            days_to_improvement=(next_task.completed_at - study_plan.created_at).days,
            completion_rate=study_plan.completion_percentage
        )
        
        # Adaptive learning: What worked?
        if effectiveness in ["effective", "highly_effective"]:
            learn_from_success(study_plan_id)
        
        return {
            "improved": improvement > 0,
            "improvement": improvement,
            "effectiveness": effectiveness
        }
    
    return None  # Not yet measured
```

#### Learning from Data

```python
def learn_from_success(study_plan_id):
    """
    Identify what worked in this intervention for future improvements
    """
    study_plan = get_study_plan(study_plan_id)
    user = get_user(study_plan.user_id)
    
    # What resources did they actually use?
    used_resources = get_used_resources(study_plan_id, clicked=True, completed=True)
    
    # Update user learning profile
    for resource in used_resources:
        if resource.helpful_rating >= 4:
            # This type of resource works well for this user
            update_learning_preferences(
                user_id=user.id,
                learning_style=user.learning_style,
                effective_resource_type=resource.resource_type,
                effective_format=resource.format,
                topic_category=study_plan.topic_category
            )
    
    # Update global effectiveness data
    update_global_effectiveness_stats(
        topic=study_plan.topic,
        learning_style=user.learning_style,
        approach=study_plan.approach,
        success=True
    )
```

### 7.9.5 Smart Intervention System

#### Notification Strategy

```python
def send_smart_reminder(study_plan_id, day_number):
    """
    Send context-aware study reminders
    """
    study_plan = get_study_plan(study_plan_id)
    user = get_user(study_plan.user_id)
    
    # Check current mood and workload
    recent_mood = get_recent_mood(user.id)
    other_deadlines = count_upcoming_deadlines(user.id, days=2)
    
    # Adaptive messaging
    if recent_mood.mood_type in ['stressed', 'overwhelmed']:
        message = f"Hi {user.first_name}! You seem stressed. Want to do just 10 minutes of {study_plan.topic} today? Small steps count! 💪"
        adjust_session_duration(study_plan_id, day_number, duration_minutes=10)
    
    elif recent_mood.energy_level >= 4:
        message = f"Great energy today! Perfect time for {study_plan.topic}. Ready for today's 30-min session? 🚀"
    
    elif other_deadlines >= 3:
        message = f"Busy week! Quick 15-min {study_plan.topic} session to keep momentum? 📚"
        adjust_session_duration(study_plan_id, day_number, duration_minutes=15)
    
    else:
        day_plan = study_plan.plan_data['daily_sessions'][day_number - 1]
        message = f"Day {day_number} of your {study_plan.topic} plan: {day_plan['title']} ({day_plan['duration_minutes']} min) 📖"
    
    # Send notification
    send_notification(
        user_id=user.id,
        title="SmartStudy Reminder",
        message=message,
        action_url=f"/smartstudy/plans/{study_plan_id}/day/{day_number}"
    )
```

#### Escalation Logic

```python
def check_escalation_needed(study_plan_id):
    """
    Detect if student needs additional help
    """
    study_plan = get_study_plan(study_plan_id)
    
    # Check engagement
    if study_plan.completion_percentage < 30 and days_since_start(study_plan) > 3:
        # Not engaging with plan
        suggest_alternative_approach(study_plan_id)
    
    # Check comprehension
    checkpoint_results = get_checkpoint_results(study_plan_id)
    if checkpoint_results.correct_percentage < 50:
        # Not understanding material
        offer_simpler_explanation(study_plan_id)
    
    # Check mood correlation
    mood_during_study = get_moods_during_plan(study_plan_id)
    if all(m.mood_type in ['stressed', 'frustrated'] for m in mood_during_study):
        # Plan is too hard or fast
        suggest_plan_adjustment(study_plan_id, slower=True, easier=True)
```

### 7.9.6 File Upload & Analysis (Optional Feature)

```python
def analyze_uploaded_document(file_path, user_id, task_id=None):
    """
    Use GPT-4 Vision to extract topics from uploaded test/slides
    """
    from openai import OpenAI
    import base64
    
    # Read and encode file
    with open(file_path, 'rb') as f:
        file_content = f.read()
    base64_file = base64.b64encode(file_content).decode('utf-8')
    
    # Determine media type
    file_ext = file_path.split('.')[-1].lower()
    media_types = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png'
    }
    media_type = media_types.get(file_ext, 'application/pdf')
    
    # Get course context if available
    if task_id:
        task = get_task(task_id)
        course = task.course
        context = f"{course.code} - {course.title}"
    else:
        user = get_user(user_id)
        courses = get_enrolled_courses(user_id)
        context = f"Student courses: {', '.join(c.code for c in courses)}"
    
    # Call GPT-4 Vision
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "system",
                "content": f"You are analyzing an academic document. Context: {context}"
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What topics does this document cover? List them with percentage coverage if possible. Format as JSON: {\"topics\": [{\"name\": \"...\", \"coverage\": 40}]}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{base64_file}"
                        }
                    }
                ]
            }
        ],
        max_tokens=500
    )
    
    # Parse response
    import json
    analysis = json.loads(response.choices[0].message.content)
    
    # Save to database
    save_document_analysis(
        user_id=user_id,
        task_id=task_id,
        file_path=file_path,
        analyzed_topics=analysis,
        confidence="high"
    )
    
    return analysis
```

### 7.9.7 Integration Points with Shadow

**Dashboard Integration:**
```jsx
// In DashboardPage.jsx
<div className="grid grid-cols-1 gap-6">
  {/* Existing CGPA card */}
  <CGPACard />
  
  {/* NEW: SmartStudy prompt if struggling */}
  {hasStrugglingCourses && (
    <SmartStudyPrompt>
      <h3>📚 Need Help?</h3>
      <p>You're struggling with {strugglingCourses.length} courses.</p>
      <Button onClick={() => navigate('/smartstudy')}>
        Get Personalized Study Plans
      </Button>
    </SmartStudyPrompt>
  )}
  
  {/* Existing task list */}
  <TaskList />
</div>
```

**Task Completion Integration:**
```jsx
// In TaskCompletionModal.jsx
{scorePercentage < 60 && (
  <SmartStudyIntervention>
    <AlertCircle className="w-5 h-5 text-amber-600" />
    <div>
      <h4>Need help with {task.topic}?</h4>
      <p>SmartStudy can create a personalized plan to improve.</p>
    </div>
    <Button onClick={() => triggerSmartStudy(task)}>
      Get Study Plan
    </Button>
  </SmartStudyIntervention>
)}
```

**Course Page Integration:**
```jsx
// In CoursePage.jsx
<CourseCard course={course}>
  {/* Existing course info */}
  
  {/* NEW: SmartStudy access */}
  {predictedGrade < 'B' && (
    <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
      <p className="text-sm text-amber-900">
        At risk of {predictedGrade}. Want to improve?
      </p>
      <Button 
        size="sm"
        onClick={() => openSmartStudy(course.id)}
        className="mt-2"
      >
        Get Help from SmartStudy
      </Button>
    </div>
  )}
</CourseCard>
```

### 7.9.8 Cost Management

```python
# Cost tracking and budgeting
MONTHLY_BUDGET = 30000  # ₦30,000 (~$20)

def track_api_costs(user_id, api_call_type, tokens_used):
    """
    Monitor and cap API spending
    """
    # Calculate cost
    costs = {
        'gpt4_chat': 0.03 / 1000,  # $0.03 per 1K tokens
        'gpt4_completion': 0.06 / 1000,  # $0.06 per 1K tokens
        'gpt4_vision': 0.01 / 1000  # $0.01 per 1K tokens
    }
    
    cost_usd = tokens_used * costs.get(api_call_type, 0.03)
    cost_ngn = cost_usd * 1600  # Exchange rate
    
    # Log cost
    log_api_usage(
        user_id=user_id,
        api_type=api_call_type,
        tokens=tokens_used,
        cost=cost_ngn
    )
    
    # Check budget
    monthly_spend = get_monthly_spend()
    if monthly_spend >= MONTHLY_BUDGET:
        # Switch to cached/template responses
        return "budget_exceeded"
    
    return "ok"

def get_cached_response(topic, user_context):
    """
    Use pre-generated responses when budget tight
    """
    # Check if we have a cached plan for this topic
    cached = get_cached_study_plan(topic, user_context.learning_style)
    
    if cached:
        # Personalize cached plan
        return customize_cached_plan(cached, user_context)
    
    return None
```

---

## 8. UI/UX Design Guidelines

### 8.1 Color System - Navy/Stone Professional

```css
/* Primary Brand - Deep Navy */
--navy-50: #F0F4FF;
--navy-100: #E0E9FF;
--navy-500: #6172F3;
--navy-800: #1E3A8A;  /* Primary actions */
--navy-900: #172554;  /* Hover states */

/* Neutral - Warm Stone */
--stone-50: #FAFAF9;   /* Page background */
--stone-100: #F5F5F4;  /* Card backgrounds */
--stone-200: #E7E5E4;  /* Borders */
--stone-600: #57534E;  /* Body text */
--stone-900: #1C1917;  /* Headings */

/* Status Colors */
--green-600: #059669;  /* Success/A grades */
--amber-600: #D97706;  /* Warning/C grades */
--red-600: #DC2626;    /* Danger/F grades */
--teal-600: #0D9488;   /* SmartStudy accent */
```

### 8.2 Component Patterns

**SmartStudy Button (Primary CTA):**
```jsx
<button className="
  px-6 py-3
  bg-teal-600 hover:bg-teal-700
  text-white font-medium
  rounded-lg
  shadow-sm hover:shadow-md
  transition-all duration-200
  flex items-center gap-2
">
  <Sparkles className="w-5 h-5" />
  Get Study Plan
</button>
```

**Intervention Alert:**
```jsx
<div className="
  p-4
  bg-amber-50 border-l-4 border-amber-500
  rounded-lg
">
  <div className="flex items-start gap-3">
    <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
    <div>
      <h4 className="font-semibold text-amber-900">Need Help?</h4>
      <p className="text-sm text-amber-800">
        You scored 45% on Binary Trees. SmartStudy can create a personalized recovery plan.
      </p>
      <Button className="mt-2" size="sm">Get Help Now</Button>
    </div>
  </div>
</div>
```

### 8.3 SmartStudy Hub Layout

```
┌──────────────────────────────────────────────────────┐
│  SmartStudy AI Learning Assistant                   │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │  💬 Chat    │  │ 📚 Plans    │  │ 📊 Progress  │ │
│  └─────────────┘  └─────────────┘  └──────────────┘ │
│                                                      │
│  [Active Tab Content]                                │
│                                                      │
│  Chat Tab:                                           │
│  ┌────────────────────────────────────────────────┐ │
│  │  Conversation with context-aware AI            │ │
│  │  • Full academic history loaded                │ │
│  │  • Suggested prompts for new conversations     │ │
│  │  • Action buttons (generate plan, find videos) │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  Plans Tab:                                          │
│  ┌────────────────────────────────────────────────┐ │
│  │  Active Study Plans                            │ │
│  │  • Binary Trees Recovery (Day 3/10 - 60%)     │ │
│  │  • CSC401 Exam Prep (Day 1/7 - 15%)           │ │
│  │                                                 │ │
│  │  Completed Plans                               │ │
│  │  • Recursion Mastery ✓ (+25% improvement)     │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  Progress Tab:                                       │
│  ┌────────────────────────────────────────────────┐ │
│  │  Effectiveness Metrics                         │ │
│  │  • Average improvement: +18%                   │ │
│  │  • Plans completed: 3/4 (75%)                  │ │
│  │  • Study streak: 7 days 🔥                     │ │
│  │  [Grade improvement chart]                     │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 9. Implementation Roadmap

### Phase 0: Current Status (Completed)
- ✅ Authentication system
- ✅ Course management
- ✅ Task management with CA tracking
- ✅ CGPA calculation & analytics
- ✅ Mood logging with sentiment analysis
- ✅ Priority recommendations
- ✅ UI redesign (navy/stone palette)

### Phase 1: SmartStudy Foundation (Month 1 - December 2025)

**Week 1: Database & Core Setup**
- [ ] Add `topic` field to tasks table
- [ ] Create SmartStudy database tables
- [ ] Set up OpenAI API integration
- [ ] Implement basic chat message storage

**Week 2: Interactive Chat**
- [ ] Build chat UI component
- [ ] Implement conversation management
- [ ] Create context loader (Shadow data → GPT-4)
- [ ] Deploy chat interface

**Week 3: Context-Aware Responses**
- [ ] Build system prompt generator
- [ ] Enhance with student performance data
- [ ] Add suggested prompts
- [ ] Test response quality

**Week 4: Integration & Testing**
- [ ] Integrate chat into Shadow dashboard
- [ ] Add "Ask SmartStudy" buttons throughout app
- [ ] User testing with 5-10 students
- [ ] Bug fixes and refinements

**Deliverable**: Students can chat with AI tutor that knows their academic history

---

### Phase 2: Automated Study Plans (Month 2 - January 2026)

**Week 5: Detection System**
- [ ] Build performance monitoring
- [ ] Create intervention triggers
- [ ] Implement auto-prompts in UI

**Week 6: Plan Generation**
- [ ] Build GPT-4 study plan generator
- [ ] Create plan storage system
- [ ] Design plan display UI
- [ ] Implement daily breakdowns

**Week 7: Content Curation**
- [ ] YouTube API integration
- [ ] Reddit API integration
- [ ] Build quality scoring algorithm
- [ ] pauarchive linking (when available)

**Week 8: Polish & Testing**
- [ ] Study plan dashboard
- [ ] Resource engagement tracking
- [ ] Test end-to-end flow
- [ ] Deploy to beta users

**Deliverable**: Automated intervention with personalized study plans

---

### Phase 3: Intelligence & Tracking (Month 3 - February 2026)

**Week 9: Smart Notifications**
- [ ] Mood-aware reminder system
- [ ] Escalation logic (adjust difficulty)
- [ ] Email/push notification integration

**Week 10: Effectiveness Tracking**
- [ ] Before/after score comparison
- [ ] Improvement metrics dashboard
- [ ] Learning preferences identification

**Week 11: Adaptive Learning**
- [ ] Success pattern recognition
- [ ] Recommendation optimization
- [ ] User preference learning

**Week 12: System Polish**
- [ ] Performance optimization
- [ ] Mobile responsiveness
- [ ] Error handling improvements
- [ ] Documentation

**Deliverable**: Complete SmartStudy system with measurable impact

---

### Phase 4: Beta Testing & Refinement (Months 4-6 - March-June 2026)

**Month 4 (March): Initial Deployment**
- [ ] Deploy to 20-30 PAU students
- [ ] Monitor usage patterns
- [ ] Collect initial feedback
- [ ] Quick bug fixes

**Month 5 (April): Data Collection**
- [ ] Track effectiveness metrics
- [ ] Analyze grade improvements
- [ ] Study resource engagement
- [ ] Mood correlation analysis

**Month 6 (May-June): Optimization & Defense Prep**
- [ ] Refine algorithms based on data
- [ ] Optimize cost (caching strategies)
- [ ] Prepare defense materials
- [ ] Document research findings

**Deliverable**: Defense-ready system with real user data

---

### Defense (July 2026)
- Complete system demonstration
- 3-4 months of effectiveness data
- User testimonials
- Research findings
- Technical documentation

---

## 10. MVP Scope

### ✅ Included in MVP (Shadow v1.0 - COMPLETED)

**Core Functionality:**
- User registration & authentication ✅
- CS400 courses pre-loaded ✅
- Course enrollment ✅
- Manual task creation ✅
- Task completion tracking ✅
- CGPA calculation (PAU-specific) ✅
- Grade prediction (35/65 split) ✅
- Priority task recommendations ✅
- Mood logging ✅
- Basic analytics dashboard ✅
- Mobile-responsive UI ✅

### 🆕 Included in v2.0 MVP (SmartStudy Core)

**SmartStudy Foundation:**
- [ ] Interactive AI chat with academic context
- [ ] Automated study plan generation
- [ ] YouTube/Reddit content curation
- [ ] Basic effectiveness tracking
- [ ] Integration throughout Shadow UI

**What's Sufficient for Defense:**
- Chat interface working with context
- At least 10 successful study plans generated
- Initial effectiveness data (3+ months)
- User testimonials (5+ students)

### ⏸️ Deferred to Post-MVP

**Phase 2 Enhancements:**
- File upload & GPT-4 Vision analysis
- Advanced adaptive learning algorithms
- Pattern learning from historical data
- Automated task generation predictions

**Phase 3 Features:**
- Multi-department support (beyond CS)
- Web push notifications
- PDF study guide generation
- NotebookLM integration
- Gamification (badges, streaks)

---

## 11. Success Metrics

### 11.1 Academic Performance (Primary)

**Target**: 70% of students using SmartStudy improve grades by +1.0 letter grade

**Measurement**:
- Before score: Assessment that triggered intervention
- After score: Next similar assessment
- Calculate: (After - Before) / Before * 100

**Success Criteria**:
- ✅ 70%+ show improvement
- ✅ Average improvement: +15-20%
- ✅ 50%+ reach target grade

### 11.2 Learning Speed

**Target**: 50% faster mastery compared to baseline

**Measurement**:
- Days from struggle detection to proficiency demonstration
- Baseline: ~6 weeks (without intervention)
- Target: ~3 weeks (with SmartStudy)

### 11.3 Knowledge Retention

**Target**: 75%+ retention after 2 weeks

**Measurement**:
- Follow-up quiz 2 weeks after study plan completion
- Compare to immediate post-plan performance
- Target: <25% degradation

### 11.4 Stress Reduction

**Target**: 40% decrease in "stressed" mood logs

**Measurement**:
- Count "stressed"/"overwhelmed" moods before intervention
- Count during and after intervention period
- Calculate reduction percentage

### 11.5 Engagement Metrics

**Target**:
- 70%+ study plan completion rate
- 3+ logins per week
- 4.0+ user satisfaction rating
- 60%+ would recommend

### 11.6 Cost Efficiency

**Target**: Stay within ₦30,000/month budget

**Measurement**:
- Track all API calls and costs
- Monitor tokens used per interaction
- Optimize with caching

### 11.7 Research Value

**Defense Presentation**:
- Grade improvement data (with statistical significance)
- Learning style effectiveness analysis
- Resource type effectiveness comparison
- Mood correlation insights
- Publication-ready findings

---

## 12. Risk Mitigation

### 12.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| GPT-4 costs exceed budget | Medium | High | Monthly cap, caching, template fallbacks |
| LLM generates bad advice | Medium | High | Confidence thresholds, student ratings, effectiveness tracking |
| YouTube API rate limits | Low | Medium | Caching, request batching, alternative sources |
| Database performance issues | Low | Medium | Indexing, query optimization, connection pooling |

### 12.2 User Adoption Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Low student engagement | Medium | High | Multiple entry points, proactive prompts, quick wins |
| Over-reliance on AI | Medium | Medium | Promote learning, not just answers, scaffold approach |
| Privacy concerns | Low | Medium | Clear data policy, opt-in features, transparency |
| Trust in AI advice | Medium | High | Show effectiveness data, allow feedback, human-like tone |

### 12.3 Academic Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Predictions inaccurate | Low | High | Conservative estimates, confidence levels, validation |
| Study plans too generic | Medium | Medium | Heavy personalization, effectiveness tracking |
| Content quality issues | Low | Medium | Multi-source validation, quality thresholds, ratings |

---

## 13. Future Enhancements

### Post-v2.0 Features

**Phase 3: Advanced Intelligence**
- Deep learning for pattern recognition
- Automatic task generation from syllabus
- Cross-semester knowledge gap analysis
- Peer learning recommendations

**Phase 4: Extended Reach**
- Support all PAU majors (Medicine, Law, Engineering)
- Multi-university deployment
- Mobile apps (iOS/Android)
- Offline mode capability

**Phase 5: Advanced Features**
- Voice-based chat (audio Q&A)
- AR study aids (visual learning)
- Collaborative study groups
- Faculty analytics dashboard

---

## 14. CS400 Course Catalog

[... Keep existing CS400 course catalog unchanged ...]

---

## Appendices

### A. API Endpoints (Updated with SmartStudy)

**SmartStudy Endpoints:**
```
# Chat
POST   /api/v1/smartstudy/chat
GET    /api/v1/smartstudy/conversations
GET    /api/v1/smartstudy/conversations/{id}

# Study Plans
POST   /api/v1/smartstudy/plans/generate
GET    /api/v1/smartstudy/plans
GET    /api/v1/smartstudy/plans/{id}
PATCH  /api/v1/smartstudy/plans/{id}/progress
POST   /api/v1/smartstudy/plans/{id}/rate

# Content
GET    /api/v1/smartstudy/resources/search
POST   /api/v1/smartstudy/resources/rate
GET    /api/v1/smartstudy/effectiveness/dashboard

# File Upload (Optional)
POST   /api/v1/smartstudy/upload
GET    /api/v1/smartstudy/upload/{id}/analysis
```

### B. Environment Variables (Updated)

```bash
# SmartStudy APIs
OPENAI_API_KEY=sk-...
YOUTUBE_API_KEY=...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...

# Limits
SMARTSTUDY_MONTHLY_BUDGET=30000
SMARTSTUDY_MAX_TOKENS_PER_REQUEST=2000
```

### C. Cost Projections (Detailed)

**Per Student Per Semester:**
- Chat interactions: 50 messages × ₦50 = ₦2,500
- Study plans: 3 plans × ₦200 = ₦600
- Total: ~₦3,100 per student

**For 30 Students:**
- Total cost: ₦93,000 per semester
- Monthly: ₦15,500

**Cost Reduction Strategies:**
- Caching common responses: -30% cost
- Template-based plans: -20% cost
- Efficient prompting: -10% cost
- **Projected actual cost: ₦40,000-₦50,000/semester**

---

### D. Key Dependencies & Setup

**Backend (requirements.txt):**
```txt
# Core Framework
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# AI/ML - SmartStudy (NEW)
openai==1.3.5                           # GPT-4 API for chat & study plans
transformers==4.35.2                    # HuggingFace models
torch==2.1.0                            # PyTorch for emotion detection
sentencepiece==0.1.99                  # Tokenizer support

# Content Curation (NEW)
google-api-python-client==2.108.0      # YouTube Data API
praw==7.7.1                            # Reddit API (PRAW)

# Background Tasks
celery==5.3.4
redis==5.0.1

# Monitoring
sentry-sdk==1.38.0
```

**AI Model Setup:**
```bash
# Emotion detection model downloads automatically on first use
# Model: j-hartmann/emotion-english-distilroberta-base
# Size: ~500MB (cached in ~/.cache/huggingface/)

# To pre-download (optional):
python -c "from transformers import pipeline; pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base')"

# Verify installation:
python -c "from transformers import pipeline; clf = pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base'); print(clf('I am so happy today!'))"
# Expected output: [{'label': 'joy', 'score': 0.98...}]
```

**Frontend (package.json):**
```json
{
  "name": "shadow-frontend",
  "version": "2.0.0",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.2",
    "victory": "^36.7.0",
    "tailwindcss": "^3.3.5",
    "date-fns": "^2.30.0",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0"
  }
}
```

**Installation Commands:**
```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Download emotion model (first time only)
python -c "from transformers import pipeline; pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base')"

# Frontend setup
cd ../frontend
npm install

# Environment variables
cp .env.example .env
# Edit .env with your API keys
```

**API Keys Required:**
```bash
# .env file
OPENAI_API_KEY=sk-...                  # Get from platform.openai.com
YOUTUBE_API_KEY=AIza...                # Get from console.cloud.google.com
REDDIT_CLIENT_ID=...                   # Get from reddit.com/prefs/apps
REDDIT_CLIENT_SECRET=...
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key-here
```

---

## Version History

**v1.0** (October 2025): Initial Shadow specification  
**v2.0** (November 2025): SmartStudy AI Learning Intervention added

---

**This specification is ready for Claude Code implementation. Begin with Phase 1 (SmartStudy Foundation) using existing Shadow v1.0 as the base.**

---

**END OF SPECIFICATION**
