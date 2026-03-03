# Shadow - System Architecture

## 1. System Context (C4 Level 1)

High-level view of Shadow and its external dependencies.

```mermaid
graph TB
    Student["PAU Student<br/>(Web Browser)"]

    subgraph Shadow["Shadow System"]
        Frontend["React Frontend<br/>(Vite + TailwindCSS)"]
        Backend["FastAPI Backend<br/>(Python 3.11)"]
        DB[("PostgreSQL<br/>Database")]
    end

    OpenAI["OpenAI GPT-4 API"]
    YouTube["YouTube Data API v3"]
    Reddit["Reddit API"]

    Student -->|HTTPS| Frontend
    Frontend -->|REST API| Backend
    Backend -->|SQLAlchemy ORM| DB
    Backend -->|Chat completions| OpenAI
    Backend -->|Video search| YouTube
    Backend -->|Resource search| Reddit
```

## 2. Container Diagram (C4 Level 2)

Detailed view of frontend pages, backend routes, and services.

```mermaid
graph TB
    subgraph Frontend["React Frontend (Port 3000)"]
        direction TB
        Dashboard["DashboardPage"]
        Courses["CoursesPage"]
        CGPA["CGPAPage"]
        Library["LibraryPage"]
        Login["LoginPage"]
        Register["RegisterPage"]

        subgraph Components["Key Components"]
            SmartStudyChat["SmartStudyChat"]
            StudyPlanView["StudyPlanView"]
            MoodLogger["MoodLogger"]
            TaskList["TaskList"]
            NotifBell["NotificationBell"]
            WhatIf["WhatIfCalculator"]
        end
    end

    subgraph Backend["FastAPI Backend (Port 8000)"]
        direction TB
        subgraph Routes["API Routes (/api/v1)"]
            AuthR["/auth"]
            CourseR["/courses"]
            TaskR["/tasks"]
            CGPAR["/gpa"]
            MoodR["/mood"]
            SmartStudyR["/smartstudy"]
            LibraryR["/library"]
            NotifR["/notifications"]
            AnalyticsR["/analytics"]
        end

        subgraph Middleware["Middleware"]
            RateLimit["Rate Limiter<br/>(slowapi)"]
            ReqLog["Request Logger<br/>(JSON + Request ID)"]
            CORS["CORS"]
        end

        subgraph Services["Business Logic"]
            SSService["SmartStudy Service"]
            SPGen["Study Plan Generator"]
            EmotionSvc["Emotion Analysis"]
            NotifSvc["Notification Service"]
            LibSvc["Library Service"]
            DocProc["Document Processor"]
            YTSvc["YouTube Service"]
            ContentCur["Content Curator"]
        end
    end

    DB[("PostgreSQL<br/>21 Tables")]
    OpenAI["OpenAI GPT-4"]
    YouTube["YouTube API"]
    Reddit["Reddit API"]

    Frontend -->|Axios + JWT| Routes
    Routes --> Services
    Services --> DB
    SSService -->|Chat/Plan generation| OpenAI
    YTSvc -->|Video search| YouTube
    ContentCur -->|Resource discovery| Reddit
```

## 3. SmartStudy Chat Flow (Sequence Diagram)

End-to-end flow when a student sends a message to SmartStudy AI.

```mermaid
sequenceDiagram
    participant S as Student
    participant F as React Frontend
    participant A as FastAPI
    participant SS as SmartStudy Service
    participant GPT as OpenAI GPT-4
    participant DB as PostgreSQL

    S->>F: Types "Help me study Binary Trees"
    F->>A: POST /api/v1/smartstudy/chat<br/>{"content": "Help me study...", "conversation_id": null}
    A->>A: Authenticate (JWT)
    A->>A: Rate limit check (10/min)
    A->>SS: chat_with_smartstudy(db, user_id, message)
    SS->>DB: load_student_context(user_id)
    DB-->>SS: courses, tasks, moods, CGPA, learning style
    SS->>SS: Build context-aware system prompt
    SS->>GPT: ChatCompletion.create(messages=[system_prompt, user_msg])
    GPT-->>SS: AI response with study advice
    SS->>DB: Save/update ChatConversation
    SS->>DB: Save ChatMessage (user + assistant)
    SS-->>A: {response, conversation_id, tokens_used}
    A-->>F: 200 OK (JSON)
    F-->>S: Display AI response in chat UI
```

## 4. Study Plan Generation Flow

```mermaid
sequenceDiagram
    participant S as Student
    participant F as React Frontend
    participant A as FastAPI
    participant SPG as Study Plan Generator
    participant GPT as OpenAI GPT-4
    participant YT as YouTube Service
    participant DB as PostgreSQL

    S->>F: "Generate plan for Binary Trees" + optional file upload
    F->>A: POST /api/v1/smartstudy/study-plans<br/>{"topic": "Binary Trees", "duration_days": 7}
    A->>SPG: generate_study_plan(db, user_id, topic, ...)
    SPG->>DB: Load student context
    SPG->>SPG: calculate_optimal_duration()
    SPG->>GPT: Generate day-by-day plan (JSON)
    GPT-->>SPG: Structured plan data
    SPG->>YT: Search YouTube for educational videos
    YT-->>SPG: Video results with quality scores
    SPG->>DB: Create StudyPlan record
    SPG->>DB: Create StudyPlanResource records
    SPG-->>A: {study_plan_id, topic, plan_data, resources}
    A-->>F: 200 OK
    F-->>S: Display interactive study plan
```

## 5. Data Model (ERD)

All 21 database tables and their relationships.

```mermaid
erDiagram
    users {
        uuid id PK
        string email UK
        string full_name
        string university_id
        string entry_level
        decimal target_cgpa
        decimal current_cgpa
    }

    courses {
        uuid id PK
        string code UK
        string title
        int credits
        string semester
        string level
    }

    user_courses {
        uuid id PK
        uuid user_id FK
        uuid course_id FK
        decimal ca_score
        decimal exam_score
    }

    tasks {
        uuid id PK
        uuid user_id FK
        uuid course_id FK
        string title
        string priority
        datetime due_date
        boolean is_completed
    }

    mood_logs {
        uuid id PK
        uuid user_id FK
        string mood
        int energy_level
        text note
    }

    chat_conversations {
        uuid id PK
        uuid user_id FK
        string title
    }

    chat_messages {
        uuid id PK
        uuid conversation_id FK
        string role
        text content
        int tokens_used
    }

    study_plans {
        uuid id PK
        uuid user_id FK
        uuid course_id FK
        string topic
        json plan_data
        decimal completion_percentage
        boolean is_active
    }

    study_plan_resources {
        uuid id PK
        uuid study_plan_id FK
        string resource_type
        string resource_url
        boolean clicked
        boolean completed
        int helpful_rating
    }

    video_notes {
        uuid id PK
        uuid user_id FK
        uuid resource_id FK
        text content
        int timestamp_seconds
        string note_type
    }

    library_documents {
        uuid id PK
        uuid course_id FK
        uuid uploaded_by FK
        string topic
        string file_name
        string file_type
        int helpful_votes
    }

    library_votes {
        uuid id PK
        uuid user_id FK
        uuid document_id FK
        int vote_value
    }

    notifications {
        uuid id PK
        uuid user_id FK
        string title
        string notification_type
        string priority
        boolean is_read
        boolean is_dismissed
    }

    notification_preferences {
        uuid id PK
        uuid user_id FK
        boolean task_reminders
        boolean mood_check_reminders
        boolean email_enabled
    }

    scheduled_reminders {
        uuid id PK
        uuid user_id FK
        string reminder_type
        datetime scheduled_time
        boolean is_recurring
        boolean is_active
    }

    uploaded_documents {
        uuid id PK
        uuid user_id FK
        string file_name
        boolean analyzed
    }

    intervention_outcomes {
        uuid id PK
        uuid user_id FK
        uuid study_plan_id FK
        decimal before_score
        decimal after_score
        decimal grade_improvement
    }

    content_quality_scores {
        uuid id PK
        string content_type
        string content_id UK
        decimal quality_score
    }

    curated_resources {
        uuid id PK
        string topic
        string resource_type
        decimal quality_score
    }

    content_curation_queries {
        uuid id PK
        string topic
        int result_count
    }

    semesters {
        uuid id PK
        string name
        date start_date
        date end_date
    }

    users ||--o{ user_courses : enrolls
    users ||--o{ tasks : creates
    users ||--o{ mood_logs : logs
    users ||--o{ chat_conversations : has
    users ||--o{ study_plans : generates
    users ||--o{ notifications : receives
    users ||--o{ notification_preferences : configures
    users ||--o{ scheduled_reminders : schedules
    users ||--o{ library_documents : uploads
    users ||--o{ library_votes : casts
    users ||--o{ video_notes : writes
    users ||--o{ uploaded_documents : uploads
    users ||--o{ intervention_outcomes : tracked

    courses ||--o{ user_courses : has
    courses ||--o{ tasks : categorizes
    courses ||--o{ library_documents : contains
    courses ||--o{ study_plans : targets

    chat_conversations ||--o{ chat_messages : contains

    study_plans ||--o{ study_plan_resources : includes
    study_plans ||--o{ intervention_outcomes : measures

    study_plan_resources ||--o{ video_notes : annotated

    library_documents ||--o{ library_votes : receives
```

## 6. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + Vite 5 | UI framework + build tool |
| **Styling** | TailwindCSS 3 | Utility-first CSS |
| **Charts** | Recharts | CGPA visualizations |
| **HTTP Client** | Axios | API communication with JWT interceptors |
| **Backend** | FastAPI 0.120 | Async Python web framework |
| **ORM** | SQLAlchemy 2.0 | Database abstraction |
| **Migrations** | Alembic | Schema version control |
| **Auth** | python-jose + bcrypt | JWT tokens + password hashing |
| **AI** | OpenAI GPT-4 | Chat + study plan generation |
| **NLP** | Transformers (HuggingFace) | 7-emotion detection |
| **Database** | PostgreSQL | Production data store |
| **Rate Limiting** | slowapi | API abuse prevention |
| **Logging** | python-json-logger | Structured JSON logs |
| **Testing** | pytest + Vitest | Backend + frontend testing |
| **Security** | Bandit | Static analysis |
| **CI/CD** | GitHub Actions | Automated testing pipeline |

## 7. PAU Grading System

Shadow implements Pan-Atlantic University's specific grading rules:

| Grade | Points | Score Range |
|-------|--------|-------------|
| A | 5.0 | 70-100 |
| B | 4.0 | 60-69 |
| C | 3.0 | 50-59 |
| D | 2.0 | 45-49 |
| E | 1.0 | 40-44 |
| F | 0.0 | 0-39 |

**Assessment Split:** 35% CA (30 marks assessments + 5 marks participation) / 65% Exam

**CGPA Formula:** `Sum(Grade Points x Credits) / Sum(Credits)`

**Classifications:** First Class (4.50+), Second Class Upper (3.50+), Second Class Lower (2.40+), Third Class (1.50+)
