# 🗺️ Shadow Development Roadmap

## ✅ **Phase 1: Foundation (COMPLETED)**
- [x] Project structure setup
- [x] Backend with FastAPI
- [x] Frontend with React + TailwindCSS
- [x] PostgreSQL database with complete schema
- [x] **Authentication system (Register & Login)**
- [x] JWT token management
- [x] Password hashing with bcrypt
- [x] User model and database

**Status**: DONE ✅ (Users can now register and login!)

---

## 🎯 **Phase 2: Course Management** (NEXT - Start Here!)

This is the foundation for everything else. Users need courses before they can add tasks.

### Step 2.1: Backend - Course System
**Priority**: HIGH | **Estimated Time**: 2-3 hours

**Tasks:**
1. ✅ Create SQLAlchemy models for:
   - `Course` (already in database)
   - `UserCourse` (enrollment relationship)

2. Create Pydantic schemas:
   - `CourseResponse` - Course data
   - `UserCourseCreate` - Enroll in course
   - `UserCourseResponse` - Enrollment data with grades

3. Create API endpoints:
   - `GET /api/v1/courses` - List all CS400 courses
   - `POST /api/v1/user-courses` - Enroll in a course
   - `GET /api/v1/user-courses` - Get user's enrolled courses
   - `DELETE /api/v1/user-courses/{id}` - Unenroll from course

4. Seed CS400 courses into database

**Why This First?**
- Courses are required before tasks can be added
- Simple CRUD operations - good warm-up
- Immediate visual progress in the UI

---

### Step 2.2: Frontend - Course Selection UI
**Priority**: HIGH | **Estimated Time**: 2 hours

**Tasks:**
1. Create `CoursesPage.jsx` - Browse and enroll in courses
2. Create `CourseCard` component - Display course info
3. Add course enrollment modal
4. Update Dashboard to show enrolled courses

**Visual Goal:**
```
┌─ Available CS400 Courses ────────────┐
│                                       │
│  [CSC401] Algorithms & Complexity     │
│  2 credits • Compulsory               │
│  [+ Enroll]                           │
│                                       │
│  [COS409] Research Methodology        │
│  3 credits • Compulsory               │
│  [+ Enroll]                           │
│                                       │
└───────────────────────────────────────┘
```

**Deliverable**: Users can browse CS400 courses and enroll in them.

---

## 📝 **Phase 3: Task Management** (AFTER COURSES)

Once users have courses, they can add tasks to track their CA scores.

### Step 3.1: Backend - Task System
**Priority**: HIGH | **Estimated Time**: 3-4 hours

**Tasks:**
1. Create Pydantic schemas:
   - `TaskCreate` - Create new task
   - `TaskUpdate` - Update task
   - `TaskResponse` - Task data

2. Create API endpoints:
   - `POST /api/v1/tasks` - Create task
   - `GET /api/v1/tasks` - List user's tasks
   - `PATCH /api/v1/tasks/{id}` - Update task (mark complete, add score)
   - `DELETE /api/v1/tasks/{id}` - Delete task

3. Implement PAU grading logic:
   - Validate CA doesn't exceed 30 marks
   - Auto-calculate predicted grades
   - Track completion rate

**Why This Second?**
- Tasks are tied to courses
- This is the core of CGPA prediction
- Users can start tracking their work

---

### Step 3.2: Frontend - Task Management UI
**Priority**: HIGH | **Estimated Time**: 3 hours

**Tasks:**
1. Create `AddTaskModal` component
2. Create `TaskList` component
3. Add task completion toggle
4. Show CA progress per course

**Visual Goal:**
```
┌─ CSC401: Algorithms & Complexity ────┐
│                                       │
│  CA Progress: 15/35 (43%)             │
│  [███░░░░░░░]                         │
│                                       │
│  Tasks:                               │
│  ✓ Test 1 (15/15) - Completed        │
│  ☐ Project 1 (12 marks) - Due Nov 5  │
│  ☐ Participation (5 marks) - Ongoing │
│                                       │
│  [+ Add Task]                         │
└───────────────────────────────────────┘
```

**Deliverable**: Users can add tasks, mark them complete, and see CA progress.

---

## 🎓 **Phase 4: CGPA Calculation Engine** (CORE FEATURE)

This is what makes Shadow special - accurate PAU-specific CGPA prediction.

### Step 4.1: Backend - CGPA Calculator
**Priority**: HIGH | **Estimated Time**: 2-3 hours

**Tasks:**
1. Create `services/cgpa_service.py`:
   - `calculate_current_cgpa()` - Based on completed courses
   - `predict_semester_gpa()` - Based on current CA + predicted exam
   - `predict_final_cgpa()` - Include predicted semester GPA
   - `calculate_target_gap()` - Distance to target CGPA

2. Create API endpoints:
   - `GET /api/v1/gpa/current` - Current CGPA
   - `GET /api/v1/gpa/predicted` - Predicted CGPA
   - `POST /api/v1/gpa/what-if` - "What if I get X grade?" scenarios

3. Use PAU grading utilities (already built!)

**Why This Third?**
- Requires courses and tasks to be in place
- This is the "brain" of Shadow
- Enables predictive features

---

### Step 4.2: Frontend - CGPA Dashboard
**Priority**: HIGH | **Estimated Time**: 2 hours

**Tasks:**
1. Update Dashboard with real CGPA data
2. Create CGPA progress bar
3. Show predicted vs target CGPA
4. Add visual indicators (on track / at risk)

**Visual Goal:**
```
┌─ Your CGPA Overview ──────────────────┐
│                                       │
│  Current CGPA: 4.73                   │
│  Target CGPA:  4.50 (First Class)     │
│  [████████████████████░░] 92%         │
│                                       │
│  Predicted Semester GPA: 4.65         │
│  Predicted Final CGPA: 4.68           │
│                                       │
│  Status: ✅ On Track                  │
│  Buffer: +0.18 above target           │
└───────────────────────────────────────┘
```

**Deliverable**: Users see their CGPA in real-time with predictions.

---

## 📊 **Phase 5: Enhanced Dashboard** (POLISH)

Make the dashboard visually appealing and informative.

### Step 5.1: Dashboard Components
**Priority**: MEDIUM | **Estimated Time**: 3-4 hours

**Tasks:**
1. Create `CGPAChart` - Line graph showing CGPA trend
2. Create `PriorityTasks` widget - Top 3 urgent tasks
3. Create `CoursePerformance` widget - Grade breakdown
4. Add semester selector

**Deliverable**: Professional-looking dashboard with charts and insights.

---

## 🎯 **Phase 6: Smart Features** (AI-ENHANCED)

### Step 6.1: Priority Recommendation System
**Priority**: MEDIUM | **Estimated Time**: 2-3 hours

**Tasks:**
1. Implement priority scoring algorithm (already in spec!)
2. Create recommendation engine
3. Show "Today's Priorities" on dashboard
4. Color-code tasks by priority

---

### Step 6.2: Mood Tracking
**Priority**: LOW | **Estimated Time**: 2 hours

**Tasks:**
1. Create mood logging API
2. Add mood log widget to dashboard
3. Track mood correlation with performance

---

### Step 6.3: Recovery Plans
**Priority**: LOW | **Estimated Time**: 3 hours

**Tasks:**
1. Detect at-risk courses
2. Generate recovery action plans
3. Show recovery timeline

---

## 🚀 **Recommended Build Order**

### **Week 1-2: Core Features**
1. ✅ Authentication (DONE!)
2. **Course Management** ← START HERE
3. **Task Management**
4. **CGPA Calculation**

### **Week 3-4: Polish & Enhancement**
5. Enhanced Dashboard
6. Priority Recommendations
7. Mood Tracking (optional)

---

## 📝 **What to Build RIGHT NOW**

I recommend we start with **Phase 2: Course Management**. Here's why:

### **Next Immediate Steps:**

1. **Seed CS400 Courses** (10 minutes)
   - Add all 18 CS400 courses to database
   - This gives users real data to work with

2. **Course Enrollment API** (1-2 hours)
   - Let users enroll in courses
   - Simple CRUD operations

3. **Course Selection UI** (1-2 hours)
   - Beautiful course cards
   - Enroll/unenroll buttons
   - Show enrolled courses on dashboard

**Result**: Users can register → login → enroll in courses → see them on dashboard!

---

## ❓ **Your Choice - What Do You Want to Build Next?**

**Option A**: Follow the roadmap (Course Management)
- Most logical progression
- Builds foundation for everything else
- Immediate visual progress

**Option B**: Jump to something specific
- CGPA calculation if you want to see the "magic"
- Dashboard polish if you want it to look great
- Task system if you want core functionality

**Option C**: I choose for you
- I'll build Course Management system end-to-end
- You'll see how to connect all the pieces
- Then you can replicate for other features

**What would you like to focus on?** 🤔
