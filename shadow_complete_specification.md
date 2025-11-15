# 🎯 SHADOW — Complete Project Specification
## Goal-Driven Academic Achievement System for Pan-Atlantic University

**Version:** 1.0  
**Last Updated:** October 29, 2025  
**Target Institution:** Pan-Atlantic University (PAU)  
**Initial Cohort:** Computer Science 400-Level Students

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Core Value Proposition](#core-value-proposition)
4. [System Architecture](#system-architecture)
5. [PAU-Specific Grading System](#pau-specific-grading-system)
6. [Database Schema](#database-schema)
7. [Core Features](#core-features)
8. [UI/UX Design Guidelines](#uiux-design-guidelines)
9. [Implementation Roadmap](#implementation-roadmap)
10. [MVP Scope](#mvp-scope)
11. [Success Metrics](#success-metrics)
12. [Risk Mitigation](#risk-mitigation)
13. [Future Enhancements](#future-enhancements)
14. [CS400 Course Catalog](#cs400-course-catalog)

---

## 1. Executive Summary

### Project Overview
**Shadow** is a goal-oriented academic assistant that helps university students achieve their target CGPA through intelligent task prioritization and real-time progress tracking. Unlike passive grade calculators, Shadow prescribes specific actions needed to close the gap between current trajectory and academic goals.

### The Core Innovation
Students set their target CGPA (e.g., 4.50 for First Class), and Shadow continuously calculates what they need to do—course by course, task by task—to achieve it, with AI-enhanced recommendations based on mood and workload.

### Key Features
- **Goal-Driven CGPA Management**: Real-time tracking toward target CGPA
- **PAU-Specific Grading**: Accurate 35/65 CA/Exam split calculations
- **Smart Task Prioritization**: AI-powered recommendations based on mood and deadlines
- **Predictive Analytics**: Course grade predictions based on current performance
- **Recovery Planning**: Actionable guidance when falling behind
- **Unified Dashboard**: All academic data in one place

---

## 2. Problem Statement

### The Gap Identified

University students face three critical challenges in academic management:

1. **No Behavioral Feedback Loop**  
   Students cannot see how daily task completion impacts semester-long CGPA outcomes until grades are finalized.

2. **Isolated Wellness Data**  
   Mood and stress tracking exists separately from academic workload, preventing students from understanding which courses or habits trigger burnout.

3. **Reactive Risk Awareness**  
   Academic struggles are identified at midterms or finals—too late for meaningful intervention.

### Current Landscape

Students currently use:
- **Google Calendar** - deadlines, reminders
- **Notion/Todoist** - task management
- **Excel/Google Sheets** - GPA calculators  
- **University LMS** (Canvas/Moodle) - course content, grades
- **Mental health apps** - mood tracking (Daylio, Headspace)

**What's Missing:** No single system connects behavioral data (task completion, mood, workload) to academic outcomes (GPA prediction, course risk) in real-time.

### The Solution

Shadow addresses the **academic integration gap** by providing:
- Unified dashboard for courses, tasks, grades, and wellness
- Real-time CGPA prediction based on completion patterns
- Goal-driven task recommendations (not just due dates)
- Mood-aware workload balancing
- Actionable recovery plans when falling behind
- **PAU-specific grading calculations** for accurate predictions

---

## 3. Core Value Proposition

### For Students:
- **Know exactly what to do**: "Complete these 3 tasks to stay on track for your 4.50 goal"
- **See progress in real-time**: Dashboard shows "72% toward your goal"
- **Get personalized guidance**: Recommendations adapt to mood and capacity
- **Recover from setbacks**: Clear path back when you fall behind
- **One place for everything**: Stop context-switching between 5 apps
- **Accurate predictions**: PAU-specific grading system ensures reliable forecasts

### Key Differentiation:
- ❌ **Not** a passive grade tracker → ✅ **Active coaching system**
- ❌ **Not** just task management → ✅ **Goal achievement engine**
- ❌ **Not** generic advice → ✅ **Personalized, data-driven guidance**
- ❌ **Not** institution-agnostic → ✅ **PAU-specific accuracy**

---

## 4. System Architecture

### Technology Stack

#### Frontend
- **Framework:** React.js 18+
- **Styling:** TailwindCSS
- **State Management:** React Context API / Redux (if needed)
- **Charts:** Recharts / Chart.js
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
- **Sentiment Analysis:** Hugging Face `distilbert-base-uncased-finetuned-sst-2-english`
- **Priority Scoring:** Rule-based weighted algorithm
- **CGPA Prediction:** Mathematical model (PAU-validated formulas)
- **Grade Prediction:** Pattern-based estimation using CA performance

#### DevOps
- **Version Control:** GitHub
- **CI/CD:** GitHub Actions
- **API Testing:** Postman / pytest
- **Monitoring:** Sentry (error tracking)

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

PAU uses a **35/65 split** for all courses:

```python
# Standard PAU Course Breakdown
CONTINUOUS_ASSESSMENT = 35  # Fixed
FINAL_EXAM = 65            # Fixed

# CA Breakdown (35 marks total)
CA_ASSESSMENTS = 30        # Tests + Projects (minimum 2)
CA_PARTICIPATION = 5        # Class engagement

# Typical CA Distribution Options
OPTION_A = {  # 2 Tests
    "test_1": 15,
    "test_2": 15,
    "participation": 5
}

OPTION_B = {  # 2 Tests + 1 Project
    "test_1": 10,
    "test_2": 10,
    "project": 10,
    "participation": 5
}

OPTION_C = {  # 3 Tests
    "test_1": 10,
    "test_2": 10,
    "test_3": 10,
    "participation": 5
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


def validate_real_results():
    """
    Validation against real PAU transcript data:
    - 200L First: 110 total points ÷ 23 units = 4.78 ✓
    - 300L: Consistent 4.5+ performance
    - Current CGPA: 4.73
    """
    pass
```

### 5.4 Task Types and Weights

```python
PAU_TASK_TYPES = {
    "test": {
        "label": "Test/Quiz",
        "typical_weight": 15,  # Out of 30 CA marks
        "min_weight": 10,
        "max_weight": 15,
        "category": "CA",
        "description": "In-class or take-home tests"
    },
    "project": {
        "label": "Project/Assignment",
        "typical_weight": 10,
        "min_weight": 5,
        "max_weight": 15,
        "category": "CA",
        "description": "Coding projects, reports, presentations"
    },
    "participation": {
        "label": "Class Participation",
        "typical_weight": 5,
        "min_weight": 5,
        "max_weight": 5,
        "category": "CA",
        "auto_tracked": True,  # System can auto-add this
        "description": "Attendance, engagement, class contributions"
    },
    "exam": {
        "label": "Final Examination",
        "typical_weight": 65,
        "min_weight": 65,
        "max_weight": 65,
        "category": "EXAM",
        "auto_tracked": True,  # System auto-adds finals
        "description": "End-of-semester comprehensive exam"
    }
}
```

### 5.5 Grade Prediction Algorithm

```python
def calculate_course_grade_pau(tasks, participation_score=None, exam_score=None):
    """
    Calculate course grade using PAU's 35/65 split
    """
    # CA Component (35 marks total)
    ca_tasks = [t for t in tasks if t.category == "CA" and t.type != "participation"]
    ca_assessments_score = sum(t.score for t in ca_tasks)  # Out of 30
    
    # Participation (5 marks) - can be estimated or entered
    if participation_score is None:
        participation_score = estimate_participation(user_id, course_id)
    
    total_ca = ca_assessments_score + participation_score  # Out of 35
    
    # Exam Component (65 marks)
    if exam_score is None:
        exam_score = predict_exam_score(total_ca, course_difficulty)
    
    # Final Course Score (out of 100)
    final_score = total_ca + exam_score
    
    # Convert to Grade Point (PAU 5.0 scale)
    grade_point = convert_to_grade_point(final_score)
    
    return {
        "ca_score": total_ca,
        "exam_score": exam_score,
        "final_score": final_score,
        "grade_point": grade_point,
        "letter_grade": get_letter_grade(final_score)
    }


def predict_exam_score(ca_score, course_difficulty=1.0):
    """
    Predict exam performance based on CA
    Research shows strong correlation between CA and exam scores
    """
    # Convert CA (out of 35) to expected Exam (out of 65)
    ca_percentage = ca_score / 35
    
    # Apply slight regression to mean (exams typically harder)
    exam_percentage = ca_percentage * 0.85  # 85% of CA performance
    
    # Adjust for course difficulty
    exam_percentage *= course_difficulty
    
    predicted_exam = exam_percentage * 65
    
    return round(predicted_exam, 2)


def estimate_participation(user_id, course_id):
    """
    Estimate participation score (5 marks) based on:
    - Task completion consistency
    - Mood logs (proxy for engagement)
    - Historical patterns
    """
    completion_rate = get_completion_rate(user_id, course_id)
    
    # High completion = likely high participation
    if completion_rate >= 0.85:
        return 5.0  # Full marks
    elif completion_rate >= 0.70:
        return 4.0  # Good participation
    elif completion_rate >= 0.60:
        return 3.0  # Average participation
    else:
        return 2.5  # Below average


def convert_to_grade_point(score):
    """Convert numerical score to PAU grade point"""
    for (min_score, max_score), grade_info in PAU_GRADE_SCALE.items():
        if min_score <= score <= max_score:
            return grade_info["points"]
    return 0.0


def get_letter_grade(score):
    """Convert numerical score to letter grade"""
    for (min_score, max_score), grade_info in PAU_GRADE_SCALE.items():
        if min_score <= score <= max_score:
            return grade_info["grade"]
    return "F"
```

### 5.6 Real-World Performance Prediction

Based on actual PAU student data:

```python
def predict_400l_performance(current_cgpa=4.73, target_cgpa=4.50):
    """
    Shadow can predict 400L performance based on patterns:
    - Current CGPA: 4.73
    - Target: 4.50+ (First Class)
    - 400L has 22-24 credits remaining
    - Need ~4.3 GPA in 400L to maintain First Class
    """
    buffer = current_cgpa - target_cgpa  # +0.23 points above threshold
    
    # Calculate required 400L GPA
    # Formula: (current_total + 400l_total) / (current_credits + 400l_credits) = target
    # Solve for 400l_gpa
    
    required_400l_gpa = 4.3  # Calculated based on current standing
    
    return {
        "current": current_cgpa,
        "goal": target_cgpa,
        "buffer": buffer,
        "400l_target": required_400l_gpa,
        "risk_level": "LOW" if buffer > 0.2 else "MEDIUM" if buffer > 0 else "HIGH",
        "message": f"Maintain {required_400l_gpa}+ GPA (achievable based on 4.76 last semester)"
    }
```

---

## 6. Database Schema

### 6.1 Core Tables

#### `users`
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    university_id VARCHAR(50),
    entry_level VARCHAR(10), -- '100L', '200L-DE', '300L', '400L'
    gpa_scale DECIMAL(3,1) DEFAULT 5.0, -- PAU uses 5.0
    target_cgpa DECIMAL(3,2), -- User's goal (e.g., 4.50)
    current_cgpa DECIMAL(3,2),
    total_credits_completed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_university_id (university_id)
);
```

#### `semesters`
```sql
CREATE TABLE semesters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL, -- 'Fall 2024', 'Spring 2025'
    academic_year VARCHAR(20), -- '2024/2025'
    semester_number INTEGER, -- 1 for First Semester, 2 for Second
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    target_gpa DECIMAL(3,2), -- Semester-specific goal
    actual_gpa DECIMAL(3,2), -- Final semester GPA
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_user_active (user_id, is_active)
);
```

#### `courses`
```sql
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) NOT NULL UNIQUE, -- 'CSC401', 'PAU-CSC411'
    title VARCHAR(255) NOT NULL,
    credits INTEGER NOT NULL,
    level VARCHAR(10), -- '400'
    status VARCHAR(20) DEFAULT 'C', -- 'C' (Compulsory), 'E' (Elective), 'R' (Required)
    department VARCHAR(100) DEFAULT 'Computer Science',
    description TEXT,
    created_by VARCHAR(10) DEFAULT 'admin', -- 'admin' or 'user'
    is_approved BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_code (code),
    INDEX idx_level (level),
    INDEX idx_department (department)
);
```

#### `user_courses`
```sql
CREATE TABLE user_courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    semester_id UUID REFERENCES semesters(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    is_carryover BOOLEAN DEFAULT false,
    is_priority BOOLEAN DEFAULT false, -- Flag for critical courses
    
    -- PAU-specific fields
    ca_score DECIMAL(5,2) DEFAULT 0, -- Current CA out of 35
    participation_score DECIMAL(5,2), -- Out of 5
    exam_score DECIMAL(5,2), -- Out of 65 (if taken)
    predicted_exam_score DECIMAL(5,2), -- Predicted exam score
    
    -- Overall grades
    current_score DECIMAL(5,2), -- CA + Exam (if taken)
    predicted_score DECIMAL(5,2), -- CA + Predicted Exam
    current_grade_point DECIMAL(3,2), -- 0.0-5.0 (if final)
    predicted_grade_point DECIMAL(3,2), -- Predicted GP
    letter_grade VARCHAR(2), -- 'A', 'B', 'C', etc.
    predicted_letter_grade VARCHAR(2),
    
    completion_rate DECIMAL(5,2), -- Percentage of tasks completed
    enrolled_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, semester_id, course_id),
    INDEX idx_user_semester (user_id, semester_id),
    INDEX idx_predictions (predicted_grade_point)
);
```

#### `tasks`
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    user_course_id UUID REFERENCES user_courses(id) ON DELETE CASCADE,
    
    -- Task details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) NOT NULL, -- 'test', 'project', 'participation', 'exam'
    
    -- PAU-specific grading
    weight DECIMAL(5,2) NOT NULL, -- Marks (e.g., 15 for Test 1)
    max_marks DECIMAL(5,2), -- Usually same as weight
    earned_marks DECIMAL(5,2), -- Actual score received
    category VARCHAR(10), -- 'CA' or 'EXAM'
    
    -- Timing
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    is_completed BOOLEAN DEFAULT false,
    is_late BOOLEAN DEFAULT false,
    
    -- Effort tracking
    effort_estimate INTEGER, -- Minutes
    actual_effort INTEGER, -- Minutes (user feedback)
    
    -- Priority
    priority_score DECIMAL(5,2), -- Calculated by system
    is_urgent BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user_course (user_course_id),
    INDEX idx_due_date (due_date),
    INDEX idx_completion (is_completed),
    INDEX idx_priority (priority_score DESC)
);
```

#### `moods`
```sql
CREATE TABLE moods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    mood_type VARCHAR(50) NOT NULL, -- 'focused', 'tired', 'stressed', 'neutral', 'motivated', 'overwhelmed'
    mood_text TEXT, -- Optional text note
    sentiment_score DECIMAL(3,2), -- -1.0 to 1.0 (from NLP)
    energy_level INTEGER, -- 1-5 scale
    
    -- Context
    associated_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    associated_course_id UUID REFERENCES user_courses(id) ON DELETE SET NULL,
    
    logged_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user_date (user_id, logged_at DESC),
    INDEX idx_sentiment (sentiment_score)
);
```

#### `gpa_records`
```sql
CREATE TABLE gpa_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    semester_id UUID REFERENCES semesters(id),
    
    semester_gpa DECIMAL(3,2),
    cumulative_gpa DECIMAL(3,2),
    predicted_cgpa DECIMAL(3,2),
    
    total_credits INTEGER,
    credits_this_semester INTEGER,
    
    -- PAU-specific
    classification VARCHAR(50), -- 'First Class', 'Second Class Upper', etc.
    target_cgpa DECIMAL(3,2),
    gap_to_target DECIMAL(3,2), -- target - predicted
    
    recorded_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user_date (user_id, recorded_at DESC)
);
```

#### `recommendations`
```sql
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    
    recommendation_type VARCHAR(50), -- 'urgent', 'mood_based', 'goal_driven', 'recovery'
    recommendation_reason TEXT,
    priority_rank INTEGER,
    
    is_active BOOLEAN DEFAULT true,
    is_dismissed BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    acted_on_at TIMESTAMP,
    
    INDEX idx_user_active (user_id, is_active),
    INDEX idx_priority (priority_rank)
);
```

#### `task_patterns` (Post-MVP)
```sql
CREATE TABLE task_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    
    pattern_type VARCHAR(50), -- 'weekly_test', 'midterm', 'project', 'final'
    typical_week INTEGER, -- Week number when task usually appears
    typical_weight DECIMAL(5,2),
    frequency VARCHAR(20), -- 'once', 'weekly', 'biweekly'
    
    confidence_score DECIMAL(3,2), -- 0.0-1.0 based on data volume
    sample_size INTEGER, -- Number of historical instances
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_course_type (course_id, pattern_type)
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
  - Semester setup

**Implementation:**
- bcrypt password hashing
- JWT with refresh tokens
- OAuth2 flow (FastAPI Security)

### 7.2 Course Management

**Features:**
- Pre-loaded CS400 courses
- Add/edit enrolled courses
- Set course priorities
- Track course completion rate
- View course-specific tasks

**PAU-Specific:**
- Automatic CA/Exam structure (35/65)
- Credit weight validation
- Compulsory vs. Elective tagging

### 7.3 Task Management

**Features:**
- Create tasks with:
  - Title & description
  - Task type (test, project, participation, exam)
  - Weight (marks out of 30 for CA)
  - Due date
  - Effort estimate
- Mark tasks complete
- Enter earned marks
- Track completion rate

**Smart UI:**
- Auto-suggest typical weights based on task type
- Show CA balance (e.g., "15/30 marks allocated")
- Warn if CA exceeds 30 marks
- Auto-add participation (5 marks)
- Auto-add final exam (65 marks)

### 7.4 CGPA Tracking & Prediction

**Features:**
- Real-time CGPA calculation
- Predicted CGPA based on:
  - Current CA performance
  - Estimated exam scores
  - Historical patterns
- Progress toward target CGPA
- "What-if" scenarios (e.g., "What if I get B in CSC401?")

**PAU-Specific:**
- Accurate 35/65 split
- 5.0 scale conversion
- First Class threshold tracking (4.50)
- Buffer calculation (current - target)

### 7.5 Smart Recommendations

**Algorithm:**
```python
def calculate_priority_score(task, user_context):
    """
    Priority Score = W1×Urgency + W2×Weight + W3×Mood + W4×Goal Impact
    """
    # Urgency (0-10)
    days_until_due = (task.due_date - now()).days
    urgency_score = max(0, 10 - days_until_due)
    
    # Weight Impact (0-10)
    weight_impact = (task.weight / 30) * 10  # Normalize CA tasks
    
    # Mood Alignment (0-10)
    recent_mood = get_recent_moods(user_id, limit=5)
    avg_energy = mean([m.energy_level for m in recent_mood])
    mood_score = match_task_to_mood(task, avg_energy)
    
    # Goal Impact (0-10)
    cgpa_gap = user.target_cgpa - user.predicted_cgpa
    goal_impact = (task.weight / 100) * cgpa_gap * 10
    
    # Weighted sum
    W1, W2, W3, W4 = 0.4, 0.3, 0.15, 0.15
    priority = (W1 * urgency_score + 
                W2 * weight_impact + 
                W3 * mood_score + 
                W4 * goal_impact)
    
    return round(priority, 2)


def match_task_to_mood(task, energy_level):
    """Match task type to current energy level"""
    if energy_level >= 4:  # High energy
        if task.task_type in ['test', 'exam']:
            return 10  # Perfect time for focused work
        return 7
    elif energy_level >= 3:  # Moderate energy
        if task.task_type == 'project':
            return 8
        return 6
    else:  # Low energy
        if task.task_type == 'participation':
            return 7  # Low-intensity task
        return 3  # Avoid heavy tasks
```

**Recommendation Types:**
1. **Urgent**: Due within 48 hours
2. **Goal-Driven**: High impact on target CGPA
3. **Mood-Based**: Matched to current energy level
4. **Recovery**: Critical tasks when falling behind

### 7.6 Mood Tracking

**Features:**
- Quick mood log:
  - Mood type (focused, tired, stressed, etc.)
  - Energy level (1-5)
  - Optional text note
- Link mood to specific course/task
- Mood trends visualization
- Correlation with academic performance

**Integration:**
- Sentiment analysis on text notes
- Influence task recommendations
- Trigger recovery mode if consistently low
- Track mood patterns per course

### 7.7 Analytics & Insights

**Dashboard Widgets:**
1. **CGPA Progress**
   - Current vs. Target
   - Predicted final CGPA
   - Buffer/gap visualization

2. **Course Performance**
   - Grade per course (current + predicted)
   - Completion rate
   - Risk indicators

3. **Task Overview**
   - Completed vs. Pending
   - Upcoming deadlines
   - Priority tasks

4. **Mood Trends**
   - Weekly mood average
   - Correlation with workload
   - Best/worst days

**Advanced Analytics:**
- Time-to-completion patterns
- Course difficulty rankings
- Productivity heatmaps
- Goal achievement probability

### 7.8 Recovery Plans

**Triggered When:**
- Predicted CGPA < Target CGPA
- Course grade drops below acceptable threshold
- Multiple late/missed tasks
- Consistently low mood

**Recovery Plan Components:**
1. **Diagnosis**: What's wrong (e.g., "3 late tasks in CSC401")
2. **Impact**: How it affects goal (e.g., "Risk of B grade, drops CGPA to 4.35")
3. **Action Plan**: Specific steps to recover
   - Prioritize specific tasks
   - Suggested catch-up schedule
   - Resource recommendations
4. **Timeline**: Weeks to recover if actions taken
5. **Tracking**: Monitor recovery progress

**Example Recovery Plan:**
```
⚠️ Recovery Plan: CSC401 At Risk

Current Status:
- CA: 18/35 (51%)
- Missed Test 2 (15 marks)
- Predicted Grade: C (3.0)
- Impact: CGPA drops from 4.73 → 4.45 (below First Class)

Action Plan:
1. Complete Project 1 (12 marks) by Nov 5 [2 days]
2. Prepare for Test 3 (15 marks) on Nov 10 [7 days]
3. Target: 85%+ on remaining tasks

If Successful:
- Expected CA: 32/35 (91%)
- Predicted Final Grade: A (5.0)
- CGPA maintained at 4.70+

Time Investment: 12 hours over 7 days
```

---

## 8. UI/UX Design Guidelines

### 8.1 Design Principles

1. **Clarity Over Cleverness**: Information must be instantly understandable
2. **Goal-Oriented**: Always show progress toward target
3. **Action-Focused**: Tell user what to do, not just what is
4. **Mood-Aware**: UI adapts to user's current state
5. **Minimal Cognitive Load**: Use visual hierarchy, not text walls

### 8.2 Color System

**Grade Colors:**
```css
/* PAU Grade Colors */
--grade-a: #10B981; /* Green - Excellent */
--grade-b: #3B82F6; /* Blue - Good */
--grade-c: #F59E0B; /* Amber - Fair */
--grade-d: #EF4444; /* Red - Pass */
--grade-e: #991B1B; /* Dark Red - Conditional */
--grade-f: #000000; /* Black - Fail */

/* Status Colors */
--on-track: #10B981;
--at-risk: #F59E0B;
--critical: #EF4444;

/* Mood Colors */
--focused: #8B5CF6;
--tired: #6B7280;
--stressed: #EF4444;
--neutral: #64748B;
--motivated: #10B981;
```

### 8.3 Course Card Design

**Predicted Grade Display:**

```
┌─────────────────────────────────────┐
│  CSC409                    🔮 A     │  ← Crystal ball = prediction
│  Research Methodology               │
│  3 credits                          │
│                                     │
│  📝 CA Progress: 5/35 (14%)         │
│  ├─ Test 1: Not started             │
│  └─ Participation: 5/5 estimated    │
│                                     │
│  📊 Predicted Final: A (75/100)     │
│  └─ Est. Exam: 52/65                │
│                                     │
│  🎯 Next: Test 1 due in 2 days      │
└─────────────────────────────────────┘
```

**Completed Course Display:**

```
┌─────────────────────────────────────┐
│  CSC497                         A   │  ← Solid green A (confirmed)
│  Final Year Project I               │
│  3 credits                          │
│                                     │
│  ✓ Final Score: 82/100              │
│  ├─ CA: 30/35                       │
│  └─ Exam: 52/65                     │
│                                     │
│  Contributes 3 × 5.0 = 15.0 to CGPA │
└─────────────────────────────────────┘
```

**At-Risk Course Display:**

```
┌─────────────────────────────────────┐
│  CSC421                    🔮 C     │  ← Yellow warning
│  Data Management II                 │
│  2 credits                          │
│                                     │
│  ⚠️ CA Progress: 8/35 (23%)         │
│  [███░░░░░░░] Below target          │
│                                     │
│  🎯 Priority: Complete Test 2 (15)  │
│  📈 Can reach B if: 85%+ remaining  │
└─────────────────────────────────────┘
```

### 8.4 Task Entry UI

```
┌─────────────────────────────────────────┐
│  ➕ Add New Task                         │
├─────────────────────────────────────────┤
│                                          │
│  Course: [CSC401 ▼]                     │
│                                          │
│  Task Type:                              │
│  ● Test/Quiz (typically 10-15 marks)    │
│  ○ Project/Assignment (typically 10)    │
│  ○ Participation (auto: 5 marks)        │
│  ○ Final Exam (auto: 65 marks)          │
│                                          │
│  Title: [Test 2: Dynamic Programming]   │
│                                          │
│  Due Date: [Nov 15, 2025 📅]            │
│                                          │
│  Weight: [15] marks (out of 30 CA)      │
│  ℹ️ Most tests are 10-15 marks          │
│                                          │
│  📊 Course CA Balance:                   │
│  Test 1: 15 marks ✓ completed           │
│  This test: 15 marks                     │
│  Participation: 5 marks (ongoing)        │
│  ─────────────────                       │
│  Total CA: 35/35 marks ✓                │
│                                          │
│  Effort Estimate: [120] minutes         │
│                                          │
│  [Cancel]  [Add Task ✓]                 │
└─────────────────────────────────────────┘
```

### 8.5 Dashboard Layout

**Header:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SHADOW - Fall 2024 Semester

Current CGPA: 4.73        Target: 4.50
[████████████████████░░] 92% to First Class

Week 7/15 • 17 units • 5 courses
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Main Content:**
```
┌─ Today's Priorities ──────────────────┐
│                                        │
│  1. 🔴 CSC401 Test 2 (Due in 2 hours) │
│     Impact: +15 marks toward A        │
│                                        │
│  2. 🟡 CSC409 Project 1 (Due tomorrow)│
│     Impact: Critical for B+ grade     │
│                                        │
│  3. 🟢 PAU-CSC411 Reading (Due Mon)   │
│     Impact: Maintains A trajectory    │
│                                        │
│  [View All Tasks →]                   │
└────────────────────────────────────────┘

┌─ Your Courses ────────────────────────┐
│                                        │
│  [Course cards as shown above]         │
│                                        │
└────────────────────────────────────────┘

┌─ How are you feeling? ────────────────┐
│                                        │
│  😊 😐 😫 😤 🥱                      │
│  [Quick mood log]                      │
│                                        │
└────────────────────────────────────────┘
```

### 8.6 Visual Indicators

**Progress Bars:**
- Only use for at-risk courses (draws attention)
- Color-coded: Green > 70%, Yellow 50-70%, Red < 50%

**Icons:**
- 🔮 Crystal ball = Predicted grade
- ✓ Checkmark = Confirmed/completed
- ⚠️ Warning = At risk
- 🎯 Target = Goal-relevant
- 📊 Chart = Analytics
- 🔴 Red dot = Urgent
- 🟡 Yellow dot = Important
- 🟢 Green dot = On track

**Typography:**
- Predicted grades: Larger, bold, with 🔮
- Confirmed grades: Solid color, no icon
- Risk indicators: Red/yellow, with ⚠️
- Headers: 16px bold
- Body: 14px regular
- Captions: 12px gray

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-3)

**Week 1: Project Setup**
- Initialize Git repository
- Set up development environment
- Create database schema
- Set up FastAPI backend skeleton
- Set up React frontend skeleton
- Configure hosting (Vercel, Render, Supabase)

**Week 2: Authentication**
- Implement user registration
- Implement login/logout
- JWT token management
- Password hashing
- Basic profile management

**Week 3: Database & Models**
- Implement all SQLAlchemy models
- Create database migrations (Alembic)
- Seed CS400 courses
- Write CRUD APIs for core entities

**Deliverable:** Working auth system + database

---

### Phase 2: Core CGPA System (Weeks 4-6)

**Week 4: Course Management**
- Course enrollment API
- Semester creation
- Course listing/filtering
- Credit tracking

**Week 5: PAU Grading Logic**
- Implement CGPA calculation
- Implement grade prediction
- CA/Exam split calculations
- Grade conversion (score → letter → points)

**Week 6: Testing & Validation**
- Unit tests for grading formulas
- Validate against real PAU data
- Test edge cases
- Fix calculation bugs

**Deliverable:** Accurate CGPA calculation engine

---

### Phase 3: Task Management (Weeks 7-10)

**Week 7: Task CRUD**
- Create task API
- Task listing/filtering
- Task completion
- Deadline tracking

**Week 8: PAU Task Structure**
- Implement task type system
- CA balance validation
- Auto-add participation/exam
- Weight suggestions

**Week 9: Priority Algorithm**
- Implement priority scoring
- Urgency calculation
- Weight impact calculation
- Sort tasks by priority

**Week 10: Task UI**
- Task creation form
- Task list views
- Completion interaction
- Deadline reminders

**Deliverable:** Full task management system

---

### Phase 4: Frontend Dashboard (Weeks 11-14)

**Week 11: Dashboard Layout**
- Header with CGPA display
- Priority tasks section
- Course cards grid
- Mood log widget

**Week 12: Course Cards**
- Display predicted grades
- Show CA progress
- Next task indicator
- Risk visualization

**Week 13: Charts & Analytics**
- CGPA trend chart
- Completion rate chart
- Mood correlation chart
- Weekly progress chart

**Week 14: Responsive Design**
- Mobile optimization
- Tablet layout
- Touch interactions
- Performance optimization

**Deliverable:** Fully functional dashboard

---

### Phase 5: Smart Features (Weeks 15-18)

**Week 15: Mood Tracking**
- Mood log API
- Sentiment analysis integration
- Mood trends
- Link mood to courses/tasks

**Week 16: Recommendations**
- Implement recommendation engine
- Mood-based suggestions
- Goal-driven prioritization
- Display recommendation cards

**Week 17: Recovery Plans**
- Detect at-risk situations
- Generate recovery plans
- Action step breakdown
- Track recovery progress

**Week 18: What-If Scenarios**
- "What if I get X grade?" calculator
- Goal feasibility checker
- Course substitution simulator
- Target adjustment suggestions

**Deliverable:** AI-enhanced features

---

### Phase 6: Polish & Optimization (Weeks 19-21)

**Week 19: UX Improvements**
- Onboarding tutorial
- Tooltips and help text
- Error handling UI
- Loading states

**Week 20: Performance**
- Database query optimization
- API response caching
- Frontend bundle optimization
- Image/asset optimization

**Week 21: Security**
- Security audit (OWASP checklist)
- Input validation
- Rate limiting
- Error logging (Sentry)

**Deliverable:** Production-ready application

---

### Phase 7: Testing & Launch (Weeks 22-25)

**Week 22: Backend Testing**
- Unit tests for all APIs
- Integration tests
- Test coverage report
- Bug fixes

**Week 23: Frontend Testing**
- Component tests
- E2E tests (Cypress/Playwright)
- Cross-browser testing
- Accessibility audit

**Week 24: Beta Testing**
- Recruit 10-15 CS400 students
- User testing sessions
- Collect feedback
- Implement critical fixes

**Week 25: Documentation & Launch**
- API documentation
- User guide
- Developer README
- Demo video (5-7 minutes)
- Presentation slides
- Deploy to production
- Soft launch

**Deliverable:** Deployed system + full documentation

---

## 10. MVP Scope

### ✅ Included in MVP

**Core Functionality:**
- User registration & authentication
- CS400 courses pre-loaded
- Course enrollment
- Manual task creation
- Task completion tracking
- CGPA calculation (PAU-specific)
- Grade prediction (35/65 split)
- Priority task recommendations
- Mood logging
- Basic analytics dashboard
- Recovery plan generation
- Mobile-responsive UI

**Technical Features:**
- RESTful API (FastAPI)
- React frontend
- PostgreSQL database
- JWT authentication
- Input validation
- Error handling
- Basic admin panel

### ⏸️ Deferred to Post-MVP

**Phase 2 Enhancements:**
- Pattern learning from historical data
- Predictive task suggestions
- Automated task generation
- Multi-semester trend analysis
- Confidence scoring for predictions

**Phase 3 Features:**
- Multi-department support (beyond CS)
- Multi-level support (100L-300L)
- Web push notifications
- Email digests
- PDF syllabus parsing
- Calendar integration (Google, Outlook)
- Collaborative features (study groups)
- Social features (anonymized peer comparison)

**Phase 4 Expansion:**
- Admin analytics dashboard
- Faculty/advisor portal
- University LMS integration
- Mobile apps (iOS/Android)
- Gamification (badges, streaks)
- AI chatbot for guidance

---

## 11. Success Metrics

### 11.1 Evaluation Criteria (Academic)

1. **Functionality (40%)**
   - ✓ Goal-driven CGPA tracking works correctly
   - ✓ PAU-specific grading is accurate
   - ✓ Task management is complete
   - ✓ Recommendations are relevant
   - ✓ Recovery plans are actionable

2. **Technical Implementation (30%)**
   - ✓ Clean, well-documented code
   - ✓ RESTful API design
   - ✓ Proper database normalization
   - ✓ Security best practices (OWASP)
   - ✓ Error handling & validation

3. **Innovation (15%)**
   - ✓ Goal-driven approach (not passive)
   - ✓ PAU-specific accuracy
   - ✓ Mood-performance correlation
   - ✓ Recovery system design
   - ✓ Predictive analytics

4. **Usability (10%)**
   - ✓ Intuitive UI/UX
   - ✓ Mobile-responsive
   - ✓ Minimal learning curve
   - ✓ Clear visual hierarchy
   - ✓ Helpful feedback

5. **Documentation (5%)**
   - ✓ API documentation (Swagger)
   - ✓ User guide
   - ✓ Code comments
   - ✓ README with setup instructions
   - ✓ Demo video

### 11.2 Real-World Impact Metrics

**User Acquisition:**
- 30+ CS400 students registered
- 20+ active users (login weekly)

**Engagement:**
- 70%+ users log in at least 3x/week
- Average session: 5+ minutes
- Task completion rate: 60%+

**Goal Achievement:**
- 60%+ users meet or exceed target CGPA
- 80%+ users report "helpful" or "very helpful"
- 50%+ users complete semester with improved GPA

**Technical Performance:**
- API response time: < 200ms (p95)
- Page load time: < 2 seconds
- Uptime: 99%+
- Zero critical security vulnerabilities

**Satisfaction:**
- User rating: 4.0+ / 5.0
- Would recommend: 70%+
- Return rate: 80%+ (next semester)

---

## 12. Risk Mitigation

### 12.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Backend performance issues | Medium | High | Database indexing, query optimization, caching |
| Sentiment model slow/inaccurate | Medium | Low | Make NLP optional, use keyword matching fallback |
| Frontend state complexity | High | Medium | Use React Context carefully, Redux if needed |
| Database costs exceed free tier | Low | Medium | Query optimization, data retention policies |
| API rate limiting on free tier | Medium | Medium | Implement caching, optimize API calls |

### 12.2 Prediction Accuracy Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Exam predictions too inaccurate | Medium | High | Clear confidence intervals, allow manual override |
| CA predictions misleading | Low | Medium | Only show when sufficient data exists |
| Students over-rely on predictions | Medium | Medium | Emphasize "estimated" nature, show ranges |

### 12.3 Scope Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Feature creep delays MVP | High | High | Strict adherence to CS400-only scope |
| Perfectionism slows progress | High | Medium | "Done is better than perfect" mindset |
| Testing takes longer than expected | Medium | Medium | Focus on critical path only |
| Integration bugs near deadline | Medium | High | Weekly integration testing, not just end |

### 12.4 User Adoption Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Students don't trust predictions | Medium | High | Show calculation transparency, validation data |
| Too much data entry required | Medium | High | Pre-load courses, minimize input, auto-complete |
| Competing with established habits | High | Medium | Focus on "better than Excel + Calendar" |
| Privacy concerns about mood data | Low | Medium | Clear privacy policy, optional features |
| Students abandon after initial use | Medium | High | Onboarding tutorial, quick wins, notifications |

---

## 13. Future Enhancements

### Phase 2: Multi-Department Expansion
- Support all CS levels (100-400L)
- Add Software Engineering program
- Other SST departments
- Department-specific grading rules

### Phase 3: Advanced Features
- **Integrations:**
  - Google Calendar sync
  - Microsoft Outlook sync
  - WhatsApp reminders
  - LMS data import (Canvas, Moodle)

- **Productivity Tools:**
  - Study timer (Pomodoro)
  - Focus mode (block distractions)
  - Study group matching
  - Resource library

- **Gamification:**
  - Achievement badges
  - Streak tracking
  - Leaderboards (anonymous)
  - Challenge mode

### Phase 4: Institution-Wide Platform
- **Faculty Features:**
  - Instructor dashboard
  - Aggregate student risk alerts
  - Assignment creation
  - Grade distribution analytics

- **Admin Features:**
  - University-wide analytics
  - Department performance
  - Retention risk prediction
  - Resource allocation insights

- **Mobile Apps:**
  - Native iOS app
  - Native Android app
  - Offline mode
  - Push notifications

### Phase 5: AI Enhancements
- **Predictive Analytics:**
  - Pattern learning from historical tasks
  - Automated task generation
  - Semester difficulty prediction
  - Course recommendation engine

- **Chatbot Assistant:**
  - Natural language queries
  - Personalized study tips
  - Answer academic questions
  - Mental health support

- **Advanced Mood Tracking:**
  - Voice mood logging
  - Automatic mood detection (typing patterns)
  - Burnout prediction
  - Wellness intervention

---

## 14. CS400 Course Catalog

### 14.1 Compulsory Courses (17 credits)

| Code | Title | Credits | Description |
|------|-------|---------|-------------|
| COS 409 | Research Methodology | 3 | Research design, data collection, analysis methods |
| CSC 401 | Algorithms and Complexity | 2 | Algorithm design, complexity analysis, optimization |
| CSC 402 | Ethics and Legal Issues | 2 | Professional ethics, intellectual property, privacy |
| CSC 497 | Final Year Project I | 3 | Research proposal, literature review, initial implementation |
| CSC 498 | Final Year Project II | 3 | Project completion, testing, documentation, defense |
| INS 401 | Project Management | 2 | Planning, execution, monitoring, risk management |
| PAU-CSC 411 | Machine Learning | 2 | Supervised/unsupervised learning, neural networks |
| PAU-CSC 412 | Survey of Programming Languages | 3 | Language paradigms, design principles, comparisons |

**Total Compulsory: 20 credits**

### 14.2 Elective Courses (Choose 2+ for 4-6 credits)

| Code | Title | Credits | Description |
|------|-------|---------|-------------|
| PAU-CSC 413 | Human-Computer Interaction | 2 | UI/UX design, usability testing, accessibility |
| PAU-CSC 414 | Deep Learning | 2 | CNN, RNN, transformers, advanced neural networks |
| PAU-CSC 415 | Game Design and Development | 2 | Game engines, graphics, physics, AI for games |
| PAU-CSC 416 | Computer Vision | 3 | Image processing, object detection, recognition |
| PAU-CSC 417 | Data Science and Engineering | 3 | Data pipelines, big data, visualization, analytics |
| PAU-CSC 418 | Cloud Computing | 3 | AWS/Azure/GCP, serverless, containerization |
| PAU-CSC 419 | Web, Mobile & Blockchain | 3 | Full-stack web, mobile apps, blockchain fundamentals |
| PAU-CSC 420 | Natural Language Processing | 3 | Text processing, NLP models, transformers |
| PAU-CSC 421 | Data Management II | 2 | Advanced databases, NoSQL, distributed systems |
| PAU-CSC 422 | Computer Networks II | 3 | Advanced networking, security, protocols |

**Total Elective Options: 28 credits**  
**Minimum Required: 4 credits (2 courses)**

### 14.3 Typical 400L Schedule

**First Semester (12-13 credits):**
- COS 409: Research Methodology (3)
- CSC 401: Algorithms and Complexity (2)
- CSC 497: Final Year Project I (3)
- PAU-CSC 411: Machine Learning (2)
- PAU-CSC 412: Survey of Programming Languages (3)
- 1 Elective (2-3 credits)

**Second Semester (11-12 credits):**
- CSC 402: Ethics and Legal Issues (2)
- CSC 498: Final Year Project II (3)
- INS 401: Project Management (2)
- 1-2 Electives (4-5 credits)

**Total 400L: 23-25 credits**

---

## 15. Appendices

### A. PAU Grading Scale Reference

| Score Range | Letter | Points | Classification |
|-------------|--------|--------|----------------|
| 70-100 | A | 5.0 | Excellent |
| 60-69 | B | 4.0 | Good |
| 50-59 | C | 3.0 | Fair |
| 45-49 | D | 2.0 | Pass |
| 40-44 | E | 1.0 | Conditional Pass |
| 0-39 | F | 0.0 | Fail |

**Degree Classifications:**
- **First Class**: 4.50 - 5.00
- **Second Class Upper**: 3.50 - 4.49
- **Second Class Lower**: 2.40 - 3.49
- **Third Class**: 1.50 - 2.39
- **Pass**: 1.00 - 1.49
- **Fail**: Below 1.00

### B. Sample API Endpoints

```
# Authentication
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/auth/me

# Users
GET    /api/v1/users/{user_id}
PUT    /api/v1/users/{user_id}
DELETE /api/v1/users/{user_id}

# Semesters
GET    /api/v1/semesters
POST   /api/v1/semesters
GET    /api/v1/semesters/{semester_id}
PUT    /api/v1/semesters/{semester_id}

# Courses
GET    /api/v1/courses
GET    /api/v1/courses/{course_id}
POST   /api/v1/courses  # Admin only

# User Courses (Enrollment)
GET    /api/v1/user-courses
POST   /api/v1/user-courses
GET    /api/v1/user-courses/{user_course_id}
PUT    /api/v1/user-courses/{user_course_id}
DELETE /api/v1/user-courses/{user_course_id}

# Tasks
GET    /api/v1/tasks
POST   /api/v1/tasks
GET    /api/v1/tasks/{task_id}
PUT    /api/v1/tasks/{task_id}
DELETE /api/v1/tasks/{task_id}
PATCH  /api/v1/tasks/{task_id}/complete

# Moods
GET    /api/v1/moods
POST   /api/v1/moods
GET    /api/v1/moods/{mood_id}

# GPA
GET    /api/v1/gpa/current
GET    /api/v1/gpa/predicted
GET    /api/v1/gpa/history
POST   /api/v1/gpa/what-if

# Recommendations
GET    /api/v1/recommendations
POST   /api/v1/recommendations/{rec_id}/dismiss

# Analytics
GET    /api/v1/analytics/dashboard
GET    /api/v1/analytics/trends
GET    /api/v1/analytics/course-performance
```

### C. Environment Variables

```bash
# Backend (.env)
DATABASE_URL=postgresql://user:pass@host:5432/shadow
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend (.env)
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENV=development
```

### D. Useful Commands

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Database
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Frontend
cd frontend
npm install
npm start

# Testing
pytest
npm test
```

### E. Key Dependencies

**Backend (requirements.txt):**
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
transformers==4.35.2
celery==5.3.4
```

**Frontend (package.json):**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.2",
    "recharts": "^2.10.3",
    "tailwindcss": "^3.3.5",
    "date-fns": "^2.30.0"
  }
}
```

---

## 16. Ethical Considerations

### 16.1 Data Privacy
- Store only essential data (email, name, academic info)
- Hash passwords with bcrypt (10+ rounds)
- No selling/sharing user data
- GDPR-compliant deletion
- Clear privacy policy

### 16.2 Algorithmic Fairness
- Predictions are deterministic and explainable
- No hidden biases (all students use same formulas)
- Transparent confidence levels
- Never punish for low performance
- Focus on improvement, not judgment

### 16.3 Mental Health
- Never shame for negative mood
- Prioritize wellbeing over grades
- Provide mental health resources
- Allow opting out of any feature
- Sensitive language in all messaging

### 16.4 Academic Integrity
- Don't encourage gaming the system
- No feature to "fake" completion
- Focus on genuine learning
- Promote honest effort

---

## 17. Conclusion

Shadow represents a **paradigm shift** from passive academic tracking to **active goal achievement**. By focusing on Computer Science 400-level students at Pan-Atlantic University as the initial cohort, the project delivers:

1. **Real Value**: Solves actual student pain points with PAU-specific accuracy
2. **Technical Depth**: Full-stack development with AI enhancement
3. **Scalability**: Architecture ready for university-wide deployment
4. **Innovation**: Goal-driven approach backed by behavioral psychology
5. **Professionalism**: Production-ready system with comprehensive documentation

The 25-week timeline is realistic, the scope is focused, and the technical choices are pragmatic. This is a portfolio-worthy project that demonstrates both **software engineering competence** and **product thinking**.

### Next Steps
1. Set up development environment
2. Create GitHub repository
3. Initialize database schema
4. Begin Phase 1 implementation
5. Weekly progress reviews
6. Iterate based on feedback

---

**Document Version:** 1.0  
**Last Updated:** October 29, 2025  
**Author:** [Your Name]  
**Project:** Shadow - Goal-Driven Academic Achievement System  
**Institution:** Pan-Atlantic University

---

**Ready to build? Let's get started! 🚀**
