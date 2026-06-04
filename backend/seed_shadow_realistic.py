"""
Shadow Seed Script — 6 Weeks of Realistic Multi-User Activity
==============================================================
Seeds 15 PAU 400-Level CS students with realistic 6-week activity
(April – mid-May 2026) across all Shadow features:

- User accounts (password: Shadow2026!)
- Course enrollments (5 courses each, varying electives)
- Tasks (completed, pending, overdue with realistic earned_marks)
- Mood logs (7-class j-hartmann emotion classification)
- SmartStudy chat conversations and messages
- Study plans (for at-risk + driven students)
- Notifications (deadline reminders, intervention alerts)
- Library uploads + votes (peer resource sharing)

Usage:
    cd backend
    python seed_shadow_realistic.py

Requires: DATABASE_URL env var set, courses already seeded.
"""

import sys
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# ─── Path bootstrap ─────────────────────────────────────────────────────────
# Ensure the script can find the app modules when run from backend/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User
from app.models.course import Course, UserCourse
from app.models.task import Task
from app.models.mood import MoodLog
from app.models.smartstudy import ChatConversation, ChatMessage, StudyPlan, StudyPlanResource
from app.models.notification import Notification
from app.models.library import LibraryDocument, LibraryVote
from app.utils.auth import get_password_hash

# Try to import grade recalc helpers (optional but recommended for realism)
try:
    from app.routes.tasks import recalculate_course_scores, update_course_grades
    HAS_RECALC = True
except ImportError:
    HAS_RECALC = False
    print("⚠️  Grade recalc helpers not importable — setting scores manually")


# ─── Configuration ──────────────────────────────────────────────────────────
TIMELINE_START = datetime(2026, 4, 1, 8, 0, tzinfo=timezone.utc)  # 1 April 2026
TIMELINE_END   = datetime(2026, 5, 15, 23, 0, tzinfo=timezone.utc)  # 15 May 2026
PASSWORD = "Shadow2026!"

# Course code mapping
COURSE_CODES = {
    "ALGO":    "CSC401",        # Algorithms (compulsory)
    "ML":      "PAU-CSC411",    # Machine Learning (compulsory)
    "FYP":     "CSC498",        # Final Year Project II (compulsory, 3 cr)
    "HCI":     "PAU-CSC413",
    "DSE":     "PAU-CSC417",
    "DL":      "PAU-CSC414",
}

# ─── Student profiles ───────────────────────────────────────────────────────
# Activity level controls how engaged each user is with Shadow
# - heavy:    daily logins, many moods, frequent SmartStudy use
# - moderate: 2-3x per week, ~8 moods, some SmartStudy use
# - light:    used it for 1-2 weeks then dropped off
# - tryer:    registered, logged in once or twice, never came back

STUDENTS = [
    {
        "name": "Akpe Omokafe", "email": "omokafe.akpe@pau.edu.ng",
        "matric": "22120613087", "cgpa": 4.12, "target": 4.50,
        "electives": ["DSE", "HCI"], "activity": "moderate",
        "profile": "smart but only recently locked in for year 4",
    },
    {
        "name": "Alex-Ojukwu Nduka", "email": "nduka.alex-ojukwu@pau.edu.ng",
        "matric": "22120613086", "cgpa": 4.30, "target": 4.50,
        "electives": ["DSE", "HCI"], "activity": "heavy",
        "profile": "driven student pushing for First Class",
    },
    {
        "name": "Ashiru Opemipo", "email": "opemipo.ashiru@pau.edu.ng",
        "matric": "22120612954", "cgpa": 4.03, "target": 4.50,
        "electives": ["DSE", "HCI"], "activity": "moderate",
        "profile": "consistent, generally happy student",
    },
    {
        "name": "Edegwa Mishael", "email": "mishael.edegwa@pau.edu.ng",
        "matric": "22120612975", "cgpa": 4.70, "target": 4.80,
        "electives": ["DSE", "HCI"], "activity": "light",
        "profile": "nonchalant, good in exams but weak in CAs",
    },
    {
        "name": "Ilesanmi Oluwatimilehin", "email": "oluwatimilehin.ilesanmi@pau.edu.ng",
        "matric": "22120612996", "cgpa": 3.80, "target": 4.50,
        "electives": ["DSE", "HCI"], "activity": "light",
        "profile": "focused on life goals more than school",
    },
    {
        "name": "Irabor Paula", "email": "paula.irabor@pau.edu.ng",
        "matric": "22120612999", "cgpa": 4.75, "target": 4.80,
        "electives": ["DSE", "DL"], "activity": "heavy",
        "profile": "great smart student",
    },
    {
        "name": "Mbama Therese", "email": "therese.mbama@pau.edu.ng",
        "matric": "22120613013", "cgpa": 4.83, "target": 4.90,
        "electives": ["DSE", "HCI"], "activity": "heavy",
        "profile": "one of the best in CS",
    },
    {
        "name": "Obiekwe Kene", "email": "kene.obiekwe@pau.edu.ng",
        "matric": "22120613021", "cgpa": 4.53, "target": 4.75,
        "electives": ["DSE", "DL"], "activity": "moderate",
        "profile": "strong student, no GSTs this semester",
    },
    {
        "name": "Ofili Tobechukwu", "email": "tobechuwku.ofili@pau.edu.ng",
        "matric": "22120613025", "cgpa": 4.52, "target": 4.80,
        "electives": ["HCI", "DSE"], "activity": "moderate",
        "profile": "strong student similar to Kene",
    },
    {
        "name": "Oloyede Oluwalonimi", "email": "oluwalonimi.oloyede@pau.edu.ng",
        "matric": "22120613037", "cgpa": 3.82, "target": 4.50,
        "electives": ["HCI", "DL"], "activity": "moderate",
        "profile": "decent all-rounder, slow learner but tries",
    },
    {
        "name": "Olukanni Mirireoluwa", "email": "mirireoluwa.olukanni@pau.edu.ng",
        "matric": "22120613038", "cgpa": 4.57, "target": 4.70,
        "electives": ["HCI", "DL"], "activity": "heavy",
        "profile": "artistic, composed, focused learner",
    },
    {
        "name": "Onaeko Oluwafunbi", "email": "oluwafunbi.onaeko@pau.edu.ng",
        "matric": "22120613041", "cgpa": 3.20, "target": 3.50,
        "electives": ["HCI", "DSE"], "activity": "heavy",
        "profile": "driven entrepreneur, focused on real world over school",
    },
    {
        "name": "Somide Oluwademilade", "email": "oluwademilade.somide@pau.edu.ng",
        "matric": "22120613050", "cgpa": 3.60, "target": 4.00,
        "electives": ["HCI", "DSE"], "activity": "heavy",
        "profile": "locked in this semester after a casual past",
    },
    {
        "name": "Abaniwonnda Oladimeji", "email": "oladimeji.abaniwonnda@pau.edu.ng",
        "matric": "22120612795", "cgpa": 4.70, "target": 4.80,
        "electives": ["DSE", "DL"], "activity": "tryer",
        "profile": "fast learner but doesn't take school too seriously",
    },
    {
        "name": "Aladenusi Paul", "email": "paul.aladenusi@pau.edu.ng",
        "matric": "23120111053", "cgpa": 4.75, "target": 4.80,
        "electives": ["HCI", "DSE"], "activity": "heavy",
        "profile": "decent but less focused this year due to work",
    },
]


# ─── Helpers ────────────────────────────────────────────────────────────────

def _as_utc(dt: datetime) -> datetime:
    """Coerce a naive datetime to UTC-aware. The DB columns are TIMESTAMP
    (no tz), so values re-read after a commit come back naive — normalise
    them before arithmetic against tz-aware timeline constants."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def rand_date_between(start: datetime, end: datetime) -> datetime:
    """Random datetime between start and end (tz-safe)."""
    start, end = _as_utc(start), _as_utc(end)
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def display_name(register_name: str) -> str:
    """STUDENTS list names are in PAU register order 'Surname Firstname'
    (e.g. 'Ashiru Opemipo', email opemipo.ashiru). The app derives the
    greeting and initials from full_name.split()[0], so store as
    'Firstname Surname' to surface the real first name."""
    parts = register_name.split()
    if len(parts) == 2:
        return f"{parts[1]} {parts[0]}"
    return register_name


def get_course(db, code: str) -> Course:
    """Look up a course by code; fail loudly if missing."""
    c = db.query(Course).filter(Course.code == code).first()
    if not c:
        raise RuntimeError(f"Course not seeded: {code}. Run seed_courses.py first.")
    return c


def score_with_variance(cgpa: float, max_marks: float, profile_factor: float = 1.0) -> float:
    """Generate a realistic earned_marks score based on CGPA, with variance."""
    # Higher CGPA → higher mean. Multiply by profile_factor for course-specific dips
    base_pct = ((cgpa - 1.0) / 4.0) * profile_factor   # ~0.20 (CGPA 1.0) to ~1.0 (CGPA 5.0)
    base_pct = max(0.30, min(0.98, base_pct))
    variance = random.uniform(-0.12, 0.10)
    pct = max(0.20, min(1.0, base_pct + variance))
    return round(pct * float(max_marks), 1)


# ─── Mood + emotion templates ───────────────────────────────────────────────

MOOD_TEMPLATES = {
    # Each entry: (mood_type, energy, primary_emotion, confidence, note_options)
    "happy_high": ("motivated", 5, "joy", 0.92, [
        "Just finished my ML assignment and I feel great about it",
        "Locked in on algorithms today — feeling confident",
        "Had a productive day, ready to tackle the next test",
        "Things are clicking, finally understanding the material",
    ]),
    "happy_calm": ("calm", 4, "joy", 0.78, [
        "Steady day, no panic, just consistent work",
        "I think I'm finding my rhythm this semester",
        "Decent day at school, nothing crazy",
    ]),
    "focused": ("focused", 4, "neutral", 0.71, [
        "Heads down today, just working through problems",
        "Nothing to report, just grinding through assignments",
        "Just going through the motions but it's fine",
    ]),
    "tired": ("tired", 2, "sadness", 0.68, [
        "Honestly drained today, barely got through class",
        "Long week, need a break",
        "Tired but trying to push through",
    ]),
    "stressed": ("stressed", 2, "fear", 0.85, [
        "Algorithms test is next week and I haven't started studying properly",
        "Way too much on my plate right now",
        "Stressed about the FYP deadlines piling up",
        "Don't know how I'm going to finish everything",
    ]),
    "overwhelmed": ("overwhelmed", 1, "sadness", 0.88, [
        "I feel completely lost and overwhelmed with all these assignments",
        "Too many things due at once, I can't focus",
        "Drowning a bit honestly, need to catch up",
    ]),
    "anxious": ("anxious", 2, "fear", 0.82, [
        "Nervous about tomorrow's presentation",
        "Anxious about my CGPA — not sure I can hit my target",
        "Worried about how this test is going to go",
    ]),
    "confident": ("confident", 4, "joy", 0.86, [
        "I think I aced that test, feeling good",
        "Confident about my FYP progress this week",
        "Project is coming together nicely",
    ]),
}


def mood_pool_for(profile_type: str) -> list:
    """Return weighted list of mood keys based on profile activity/performance."""
    if profile_type == "heavy_struggling":
        return ["stressed"] * 5 + ["overwhelmed"] * 3 + ["anxious"] * 3 + \
               ["tired"] * 2 + ["focused"] * 2 + ["happy_calm"] * 1
    if profile_type == "heavy_top":
        return ["confident"] * 4 + ["happy_high"] * 3 + ["focused"] * 3 + \
               ["happy_calm"] * 3 + ["tired"] * 1
    if profile_type == "heavy_borderline":
        return ["focused"] * 4 + ["stressed"] * 3 + ["confident"] * 2 + \
               ["anxious"] * 2 + ["happy_calm"] * 2 + ["tired"] * 1
    if profile_type == "moderate":
        return ["focused"] * 4 + ["happy_calm"] * 3 + ["stressed"] * 2 + \
               ["tired"] * 2 + ["confident"] * 1
    # light / tryer
    return ["focused"] * 2 + ["happy_calm"] * 2 + ["tired"] * 1


def classify_profile(student: dict) -> str:
    """Classify student into a mood pool category."""
    cgpa = student["cgpa"]
    activity = student["activity"]
    if activity == "heavy" and cgpa < 3.8:
        return "heavy_struggling"
    if activity == "heavy" and cgpa >= 4.6:
        return "heavy_top"
    if activity == "heavy":
        return "heavy_borderline"
    return activity


# ─── Mood count per activity level ──────────────────────────────────────────

MOOD_COUNT = {
    "heavy":    lambda: random.randint(20, 35),
    "moderate": lambda: random.randint(8, 14),
    "light":    lambda: random.randint(3, 6),
    "tryer":    lambda: random.randint(0, 2),
}


# ─── Chat templates (no GPT calls) ──────────────────────────────────────────

CHAT_TEMPLATES = [
    {
        "title": "Help with Recursion in Algorithms",
        "messages": [
            ("user", "I'm really struggling with recursion in CSC401. Can you explain it like I'm a beginner?"),
            ("assistant", "Of course. Recursion is when a function calls itself with a smaller version of the same problem. Think of it like opening a Russian doll: each doll contains a smaller one, and you keep opening until you reach the smallest doll (the base case). Every recursive function needs two parts:\n\n1. **Base case** — when to stop recursing\n2. **Recursive case** — how the function calls itself with a simpler input\n\nA classic example is factorial: n! = n × (n-1)!. The base case is 0! = 1, and the recursive case is multiplying n by the factorial of (n-1).\n\nWould you like to work through a problem together?"),
            ("user", "Yes please, can we do the Fibonacci one?"),
            ("assistant", "Great choice. The Fibonacci sequence is 0, 1, 1, 2, 3, 5, 8, 13... where each number is the sum of the two before it.\n\nIn recursive form:\n```python\ndef fib(n):\n    if n <= 1:        # base case\n        return n\n    return fib(n-1) + fib(n-2)   # recursive case\n```\n\nNote that this naive version is exponentially slow because it recomputes the same subproblems. For your test, also know the iterative O(n) version and the concept of memoization."),
        ],
    },
    {
        "title": "ML Assignment Help",
        "messages": [
            ("user", "What's the difference between supervised and unsupervised learning?"),
            ("assistant", "Great foundational question for your ML course.\n\n**Supervised learning** trains a model on labelled data — every input has a known correct output. The model learns the mapping from inputs to outputs. Examples: predicting house prices (regression), classifying emails as spam or not (classification).\n\n**Unsupervised learning** trains on unlabelled data — the model finds patterns or structure on its own. Examples: customer segmentation (clustering), reducing high-dimensional data to 2D for visualisation (dimensionality reduction).\n\nKey distinction: supervised needs a teacher (the labels); unsupervised has to figure things out by itself."),
            ("user", "Where does reinforcement learning fit?"),
            ("assistant", "Reinforcement learning is a third paradigm. An agent learns by taking actions in an environment and receiving rewards or penalties. There's no fixed training dataset — the agent generates its own experience by interacting with the environment. Used in robotics, game-playing (AlphaGo, OpenAI Five), and recommendation systems."),
        ],
    },
    {
        "title": "I'm stressed about my CGPA",
        "messages": [
            ("user", "I've worked out that I might not be able to hit my First Class target this semester. What should I do?"),
            ("assistant", "First — that realisation is actually useful information, not a failure. Knowing where you actually stand lets you plan smartly rather than chasing an impossible target.\n\nLet's reframe. Three things to consider:\n\n1. **What CGPA is realistically achievable** — even a strong Second Class Upper (3.50+) is a solid result and keeps most graduate school and job opportunities open.\n2. **Where your effort gives maximum return** — focus on the courses where you can still meaningfully move the needle. Tests next week matter more than chasing 5 extra marks on something already weighted low.\n3. **Stress management matters academically** — burning out in the final stretch costs you more grade points than relaxing a target.\n\nWhat are your three biggest upcoming assessments? Let's plan around those."),
        ],
    },
    {
        "title": "How to study for HCI test",
        "messages": [
            ("user", "I have an HCI test next week and I don't know where to start"),
            ("assistant", "HCI tests typically lean on three core areas. Let me walk you through them in order of usual exam weight:\n\n1. **Design principles & heuristics** — Nielsen's 10 heuristics, Norman's design principles (visibility, feedback, constraints, affordance, mapping). Expect short-answer or scenario questions.\n2. **User research methods** — interviews, surveys, usability testing, A/B testing. Know when to use each.\n3. **Prototyping & evaluation** — low vs high fidelity, formative vs summative evaluation, common metrics (task success, time-on-task, SUS score).\n\nStart with Nielsen's heuristics — they're memorisable, frequently tested, and give you something concrete to hang scenario questions on. Want me to generate a quick quiz?"),
        ],
    },
]


# ─── Study plan templates ───────────────────────────────────────────────────

STUDY_PLAN_TEMPLATES = [
    {
        "topic": "Recursion and Dynamic Programming",
        "trigger_type": "reactive",
        "duration_days": 7,
        "plan_data": {
            "overview": "A focused 7-day plan to build recursion intuition and progress into DP fundamentals.",
            "days": [
                {"day": 1, "focus": "Recursion basics", "tasks": ["Watch intro video", "Solve 3 warm-up problems"]},
                {"day": 2, "focus": "Recursion patterns", "tasks": ["Tree traversal exercises", "Backtracking intro"]},
                {"day": 3, "focus": "Memoization", "tasks": ["Fibonacci memoized", "Practice 2 problems"]},
                {"day": 4, "focus": "Tabulation", "tasks": ["Convert recursion to iteration", "Coin change"]},
                {"day": 5, "focus": "Classic DP problems", "tasks": ["Longest common subsequence", "Knapsack"]},
                {"day": 6, "focus": "Practice test", "tasks": ["Past paper section", "Review weak areas"]},
                {"day": 7, "focus": "Final review", "tasks": ["Quick recall sheet", "Light practice"]},
            ],
        },
    },
    {
        "topic": "Machine Learning Fundamentals",
        "trigger_type": "proactive",
        "duration_days": 10,
        "plan_data": {
            "overview": "Pre-test prep for ML covering supervised learning, gradient descent, and evaluation.",
            "days": [
                {"day": 1, "focus": "Linear regression", "tasks": ["Read lecture notes", "Implement from scratch"]},
                {"day": 2, "focus": "Gradient descent", "tasks": ["Visualise convergence", "Tune learning rate"]},
                {"day": 3, "focus": "Logistic regression", "tasks": ["Sigmoid intuition", "Practice problems"]},
                {"day": 4, "focus": "Train/test splits", "tasks": ["Cross-validation"]},
                {"day": 5, "focus": "Evaluation metrics", "tasks": ["Precision, recall, F1, ROC"]},
                {"day": 6, "focus": "Bias-variance", "tasks": ["Overfitting vs underfitting"]},
                {"day": 7, "focus": "Decision trees", "tasks": ["Entropy and information gain"]},
                {"day": 8, "focus": "Ensemble methods", "tasks": ["Random forest, boosting"]},
                {"day": 9, "focus": "Practice test", "tasks": ["Past paper"]},
                {"day": 10, "focus": "Review", "tasks": ["Cheat sheet", "Final recall"]},
            ],
        },
    },
]


# ─── Main seeding logic ─────────────────────────────────────────────────────

def seed():
    db = SessionLocal()
    try:
        # ── 1. Look up courses ─────────────────────────────────────────────
        print("→ Looking up seeded courses...")
        courses = {key: get_course(db, code) for key, code in COURSE_CODES.items()}
        for key, c in courses.items():
            print(f"   ✓ {key}: {c.code} ({c.credits}cr)")

        # ── 2. Create users ────────────────────────────────────────────────
        print(f"\n→ Creating {len(STUDENTS)} users...")
        password_hash = get_password_hash(PASSWORD)
        user_records = []
        for s in STUDENTS:
            # Stagger created_at across the first week of timeline
            created_at = TIMELINE_START + timedelta(days=random.randint(0, 6), hours=random.randint(0, 23))

            # last_login depends on activity level
            if s["activity"] == "heavy":
                last_login = TIMELINE_END - timedelta(days=random.randint(0, 2))
            elif s["activity"] == "moderate":
                last_login = TIMELINE_END - timedelta(days=random.randint(3, 8))
            elif s["activity"] == "light":
                last_login = TIMELINE_START + timedelta(days=random.randint(7, 18))
            else:  # tryer
                last_login = created_at + timedelta(days=random.randint(0, 2))

            # Check for existing user (e.g. preserved real accounts like Paul):
            # refresh profile fields + reuse the row rather than recreating it.
            existing = db.query(User).filter(User.email == s["email"]).first()
            if existing:
                existing.full_name = display_name(s["name"])
                existing.university_id = s["matric"]
                existing.entry_level = "400L"
                existing.gpa_scale = Decimal("5.0")
                existing.target_cgpa = Decimal(str(s["target"]))
                existing.current_cgpa = Decimal(str(s["cgpa"]))
                existing.total_credits_completed = 132
                existing.learning_style = existing.learning_style or random.choice(["visual", "reading", "auditory"])
                existing.last_login = last_login
                existing.is_active = True
                existing.email_verified = True
                db.flush()
                print(f"   ↺ {s['email']} already exists — preserved + profile refreshed")
                user_records.append((existing, s))
                continue

            u = User(
                email=s["email"],
                password_hash=password_hash,
                full_name=display_name(s["name"]),
                university_id=s["matric"],
                entry_level="400L",
                gpa_scale=Decimal("5.0"),
                target_cgpa=Decimal(str(s["target"])),
                current_cgpa=Decimal(str(s["cgpa"])),
                total_credits_completed=132,   # ~7 semesters worth of 400-level by 2nd sem Y4
                learning_style=random.choice(["visual", "reading", "auditory"]),
                created_at=created_at,
                last_login=last_login,
                is_active=True,
                email_verified=True,
            )
            db.add(u)
            db.flush()
            user_records.append((u, s))
            print(f"   ✓ {s['name']} ({s['email']})")

        db.commit()

        # ── 3. Enrollments ─────────────────────────────────────────────────
        print(f"\n→ Enrolling users in 5 courses each...")
        enrollments = {}  # user_id → {course_key: UserCourse}
        for u, s in user_records:
            enrollments[u.id] = {}
            chosen = ["ALGO", "ML", "FYP"] + s["electives"]
            for key in chosen:
                course = courses[key]
                # Check existing
                ex = db.query(UserCourse).filter(
                    UserCourse.user_id == u.id,
                    UserCourse.course_id == course.id,
                ).first()
                if ex:
                    enrollments[u.id][key] = ex
                    continue
                uc = UserCourse(
                    user_id=u.id,
                    course_id=course.id,
                    is_carryover=False,
                    is_priority=False,
                    ca_score=Decimal("0"),
                    participation_score=Decimal("0"),
                    completion_rate=Decimal("0"),
                )
                db.add(uc)
                db.flush()
                enrollments[u.id][key] = uc
        db.commit()
        print(f"   ✓ Created enrollments for {len(user_records)} users")

        # ── 4. Tasks (with realistic CA progression) ───────────────────────
        print(f"\n→ Creating tasks with realistic CA progression...")
        # Per-course assessment plan:
        # - Test 1 (15 marks) → due Week 2 (mid-April)
        # - Assignment (10 marks) → due Week 3 (late April)
        # - Test 2 (10 marks) → due Week 5 (early May)
        # - Final Exam (65 marks) → not yet taken
        assessment_plan = {
            "ALGO": [
                ("Test 1: Sorting Algorithms",     "test",       15, datetime(2026, 4, 14, 14, 0, tzinfo=timezone.utc)),
                ("Assignment 1: Graph Traversal",  "assignment", 10, datetime(2026, 4, 24, 23, 59, tzinfo=timezone.utc)),
                ("Test 2: Dynamic Programming",    "test",       10, datetime(2026, 5,  9, 14, 0, tzinfo=timezone.utc)),
            ],
            "ML": [
                ("Test 1: Linear Models",          "test",       15, datetime(2026, 4, 16, 10, 0, tzinfo=timezone.utc)),
                ("Assignment: Implement Linear Regression", "assignment", 10, datetime(2026, 4, 26, 23, 59, tzinfo=timezone.utc)),
                ("Test 2: Trees and Ensembles",    "test",       10, datetime(2026, 5, 11, 10, 0, tzinfo=timezone.utc)),
            ],
            "FYP": [
                ("Chapter 4 Draft",                "project",    15, datetime(2026, 4, 18, 23, 59, tzinfo=timezone.utc)),
                ("Implementation Demo",            "project",    10, datetime(2026, 4, 30, 23, 59, tzinfo=timezone.utc)),
                ("Final Report Draft",             "project",    10, datetime(2026, 5, 12, 23, 59, tzinfo=timezone.utc)),
            ],
            "HCI": [
                ("Test 1: Heuristics",             "test",       15, datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc)),
                ("Prototype Design Assignment",    "assignment", 10, datetime(2026, 4, 27, 23, 59, tzinfo=timezone.utc)),
                ("Test 2: Evaluation Methods",     "test",       10, datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc)),
            ],
            "DSE": [
                ("Test 1: SQL and Data Pipelines", "test",       15, datetime(2026, 4, 17, 14, 0, tzinfo=timezone.utc)),
                ("Assignment: Build a Pipeline",   "assignment", 10, datetime(2026, 4, 28, 23, 59, tzinfo=timezone.utc)),
                ("Test 2: Distributed Systems",    "test",       10, datetime(2026, 5, 12, 14, 0, tzinfo=timezone.utc)),
            ],
            "DL": [
                ("Test 1: Neural Network Basics",  "test",       15, datetime(2026, 4, 16, 16, 0, tzinfo=timezone.utc)),
                ("Assignment: Build a CNN",        "assignment", 10, datetime(2026, 4, 29, 23, 59, tzinfo=timezone.utc)),
                ("Test 2: Sequence Models",        "test",       10, datetime(2026, 5, 13, 16, 0, tzinfo=timezone.utc)),
            ],
        }

        # Per-student profile factor for each course (to add realism)
        # Struggling students do worse in heavy theory; nonchalant ones do worse in CA generally

        for u, s in user_records:
            cgpa = s["cgpa"]
            # Nonchalant CA factor reduces CA performance for certain students
            nonchalant = "nonchalant" in s["profile"] or "casual" in s["profile"]
            ca_factor = 0.78 if nonchalant else 1.0

            for course_key in ["ALGO", "ML", "FYP"] + s["electives"]:
                uc = enrollments[u.id][course_key]
                # FYP / single-grade: graded once at the end (thesis + defence +
                # supervisor assessment), not during the semester. Seed it as PENDING:
                # no CA tasks and no grade (exam_score stays None). It is excluded from
                # current CGPA and projected from the student's CGPA for the forecast.
                if course_key == "FYP":
                    continue
                if db.query(Task).filter(Task.user_course_id == uc.id).count() > 0:
                    continue  # tasks already seeded for this enrollment (resumable)
                for title, ttype, weight, due in assessment_plan[course_key]:
                    # Has this task happened yet (as of TIMELINE_END)?
                    past_due = due < TIMELINE_END
                    if not past_due:
                        # Pending future task
                        task = Task(
                            user_id=u.id, user_course_id=uc.id,
                            title=title, task_type=ttype,
                            weight=Decimal(str(weight)), max_marks=Decimal(str(weight)),
                            category="CA", due_date=due,
                            is_completed=False, is_late=False,
                            created_at=due - timedelta(days=14),
                        )
                        db.add(task)
                        continue

                    # Task has passed — decide whether student completed it
                    if s["activity"] == "tryer":
                        # Mostly didn't complete anything in Shadow
                        completed = random.random() < 0.25
                    elif s["activity"] == "light" and due > TIMELINE_START + timedelta(days=18):
                        # Light users dropped off after week 2-3
                        completed = random.random() < 0.4
                    else:
                        completed = random.random() < 0.92

                    if completed:
                        earned = score_with_variance(cgpa, weight, ca_factor)
                        # Some students complete late
                        is_late = random.random() < (0.20 if nonchalant else 0.05)
                        if is_late:
                            completed_at = due + timedelta(hours=random.randint(2, 36))
                        else:
                            completed_at = due - timedelta(hours=random.randint(1, 18))
                        task = Task(
                            user_id=u.id, user_course_id=uc.id,
                            title=title, task_type=ttype,
                            weight=Decimal(str(weight)), max_marks=Decimal(str(weight)),
                            earned_marks=Decimal(str(earned)),
                            category="CA", due_date=due,
                            is_completed=True, is_late=is_late,
                            completed_at=completed_at,
                            created_at=due - timedelta(days=14),
                        )
                    else:
                        # Overdue, not completed (rarer)
                        task = Task(
                            user_id=u.id, user_course_id=uc.id,
                            title=title, task_type=ttype,
                            weight=Decimal(str(weight)), max_marks=Decimal(str(weight)),
                            category="CA", due_date=due,
                            is_completed=False, is_late=False,
                            created_at=due - timedelta(days=14),
                        )
                    db.add(task)
            db.flush()
        db.commit()
        print("   ✓ Tasks created")

        # ── 5. Recompute course scores ─────────────────────────────────────
        if HAS_RECALC:
            print("\n→ Running grade recalculation for all enrollments...")
            count = 0
            for u, s in user_records:
                for key, uc in enrollments[u.id].items():
                    if uc.predicted_grade_point is not None:
                        continue  # grades already computed (resumable)
                    try:
                        recalculate_course_scores(uc, db)
                        update_course_grades(uc, db)
                        count += 1
                    except Exception as e:
                        print(f"   ⚠️  Recalc failed for {s['name']}/{key}: {e}")
            print(f"   ✓ Recalculated {count} enrollments")
        else:
            print("\n→ Skipping grade recalc (helpers unavailable)")

        # ── 6. Mood logs ───────────────────────────────────────────────────
        print(f"\n→ Generating mood logs...")
        mood_count_total = 0
        for u, s in user_records:
            if db.query(MoodLog).filter(MoodLog.user_id == u.id).count() > 0:
                continue  # already has moods (real or seeded) — skip (resumable, preserves Paul)
            n = MOOD_COUNT[s["activity"]]()
            if n == 0:
                continue
            pool = mood_pool_for(classify_profile(s))

            # Build mood timestamps based on activity
            if s["activity"] == "heavy":
                # Spread across full timeline
                date_range_end = TIMELINE_END - timedelta(days=2)
            elif s["activity"] == "moderate":
                date_range_end = TIMELINE_END - timedelta(days=5)
            elif s["activity"] == "light":
                date_range_end = TIMELINE_START + timedelta(days=18)
            else:
                date_range_end = TIMELINE_START + timedelta(days=4)

            timestamps = sorted([
                rand_date_between(TIMELINE_START + timedelta(days=1), date_range_end)
                for _ in range(n)
            ])

            for ts in timestamps:
                key = random.choice(pool)
                mood_type, energy, emotion, conf, notes = MOOD_TEMPLATES[key]
                note = random.choice(notes) if random.random() < 0.7 else None

                # Build full emotion_scores distribution
                emotions = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
                scores = {e: round(random.uniform(0.01, 0.08), 3) for e in emotions}
                scores[emotion] = conf
                # Normalise roughly to ~1.0
                total = sum(scores.values())
                scores = {e: round(v / total, 3) for e, v in scores.items()}

                ml = MoodLog(
                    user_id=u.id,
                    mood_type=mood_type,
                    energy_level=energy,
                    note=note,
                    sentiment_score=1 if emotion == "joy" else (-1 if emotion in ["anger", "disgust", "fear", "sadness"] else 0),
                    primary_emotion=emotion if note else None,
                    emotion_confidence=Decimal(str(conf)) if note else None,
                    emotion_scores=scores if note else None,
                    logged_at=ts,
                )
                db.add(ml)
                mood_count_total += 1
            db.commit()  # per-user commit (resumable across connection blips)
        print(f"   ✓ Created {mood_count_total} mood logs")

        # ── 7. SmartStudy chat conversations ───────────────────────────────
        print(f"\n→ Creating SmartStudy chat conversations...")
        chat_count = 0
        for u, s in user_records:
            if db.query(ChatConversation).filter(ChatConversation.user_id == u.id).count() > 0:
                continue  # already has conversations — skip (resumable, preserves Paul)
            # Heavy users: 2-4 conversations; moderate: 1-2; light: 0-1; tryer: 0
            if s["activity"] == "heavy":
                num_chats = random.randint(2, 4)
            elif s["activity"] == "moderate":
                num_chats = random.randint(1, 2)
            elif s["activity"] == "light":
                num_chats = random.randint(0, 1)
            else:
                num_chats = 0

            for _ in range(num_chats):
                template = random.choice(CHAT_TEMPLATES)
                conv_created = rand_date_between(
                    TIMELINE_START + timedelta(days=3), TIMELINE_END - timedelta(days=2)
                )
                conv = ChatConversation(
                    user_id=u.id,
                    title=template["title"],
                    created_at=conv_created,
                    updated_at=conv_created + timedelta(minutes=random.randint(5, 30)),
                )
                db.add(conv)
                db.flush()
                for i, (role, content) in enumerate(template["messages"]):
                    msg = ChatMessage(
                        conversation_id=conv.id,
                        role=role,
                        content=content,
                        tokens_used=random.randint(50, 400) if role == "assistant" else None,
                        model_used="gpt-4-turbo" if role == "assistant" else None,
                        created_at=conv_created + timedelta(seconds=i * 60),
                    )
                    db.add(msg)
                chat_count += 1
            db.commit()  # per-user commit (resumable)
        print(f"   ✓ Created {chat_count} chat conversations")

        # ── 8. Study plans ─────────────────────────────────────────────────
        print(f"\n→ Generating study plans for at-risk/driven students...")
        plan_count = 0
        for u, s in user_records:
            if db.query(StudyPlan).filter(StudyPlan.user_id == u.id).count() > 0:
                continue  # already has study plans — skip (resumable, preserves Paul)
            # Study plans for: struggling + heavy users + borderline cases
            should_have_plan = (
                s["cgpa"] < 4.0 or
                (s["activity"] == "heavy" and s["cgpa"] - s["target"] < -0.10)
            )
            if not should_have_plan:
                continue

            for template in random.sample(STUDY_PLAN_TEMPLATES, k=min(2, len(STUDY_PLAN_TEMPLATES))):
                start_date = (TIMELINE_START + timedelta(days=random.randint(5, 25))).date()
                sp = StudyPlan(
                    user_id=u.id,
                    topic=template["topic"],
                    plan_data=template["plan_data"],
                    trigger_type=template["trigger_type"],
                    duration_days=template["duration_days"],
                    start_date=start_date,
                    end_date=start_date + timedelta(days=template["duration_days"]),
                    completion_percentage=Decimal(str(random.choice([0, 20, 40, 60, 80]))),
                    is_active=True,
                    learning_style_used=u.learning_style,
                    completed_days=[],
                    created_at=datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                )
                db.add(sp)
                plan_count += 1
            db.commit()  # per-user commit (resumable)
        print(f"   ✓ Created {plan_count} study plans")

        # ── 9. Notifications ───────────────────────────────────────────────
        print(f"\n→ Generating notifications...")
        notif_count = 0
        for u, s in user_records:
            if db.query(Notification).filter(Notification.user_id == u.id).count() > 0:
                continue  # already has notifications — skip (resumable, preserves Paul)
            if s["activity"] == "tryer":
                # Just one welcome notif
                n = Notification(
                    user_id=u.id,
                    title="Welcome to Shadow!",
                    message="Get started by adding your courses and CA scores.",
                    notification_type="system",
                    priority="medium",
                    channel="in_app",
                    is_read=False,
                    created_at=u.created_at + timedelta(minutes=5),
                )
                db.add(n)
                db.commit()  # per-user commit (resumable)
                notif_count += 1
                continue

            # Standard notifications across the period
            templates = [
                ("Task reminder: Algorithms Test approaching", "Your CSC401 test is in 3 days. Review your notes!", "task_reminder", "medium"),
                ("Goal update", "You're on track to meet your CGPA target if you maintain current performance.", "goal_progress", "medium"),
                ("SmartStudy suggestion", "Based on your recent mood, a 30-minute focused review session might help.", "smart_study", "low"),
                ("Mood check-in", "How are you feeling today? Log your mood to keep your insights accurate.", "mood_check", "low"),
            ]
            if s["cgpa"] < 4.0:
                templates.append(("CGPA Gap Alert", "Your current trajectory is below your target — let's adjust.", "goal_progress", "high"))

            count_for_user = {"heavy": 8, "moderate": 4, "light": 2, "tryer": 1}[s["activity"]]
            chosen = random.sample(templates, k=min(count_for_user, len(templates)))
            for title, msg, ntype, prio in chosen:
                ts = rand_date_between(u.created_at, TIMELINE_END - timedelta(days=1))
                n = Notification(
                    user_id=u.id,
                    title=title,
                    message=msg,
                    notification_type=ntype,
                    priority=prio,
                    channel="in_app",
                    is_read=random.random() < 0.6,
                    created_at=ts,
                )
                db.add(n)
                notif_count += 1
            db.commit()  # per-user commit (resumable)
        print(f"   ✓ Created {notif_count} notifications")

        # ── 10. Library uploads and votes ──────────────────────────────────
        print(f"\n→ Creating library documents and votes...")
        lib_documents = [
            ("Algorithms Cheat Sheet — Sorting Complexity", "CSC401", "ALGO", "Sorting", "pdf"),
            ("ML Lecture 3 Notes — Linear Regression", "PAU-CSC411", "ML", "Linear Regression", "pdf"),
            ("HCI Nielsen Heuristics Summary", "PAU-CSC413", "HCI", "Nielsen Heuristics", "pdf"),
            ("Data Science SQL Practice Problems", "PAU-CSC417", "DSE", "SQL", "pdf"),
            ("Deep Learning Backpropagation Walkthrough", "PAU-CSC414", "DL", "Backpropagation", "pptx"),
            ("FYP Chapter 3 Template", "CSC498", "FYP", "Thesis Writing", "pdf"),
        ]
        doc_objs = []
        for title, code, course_key, topic, ftype in lib_documents:
            if db.query(LibraryDocument).filter(
                LibraryDocument.topic == topic,
                LibraryDocument.course_id == courses[course_key].id,
            ).first():
                continue  # this library doc already seeded — skip (resumable)
            # Upload by a random heavy user
            uploader = random.choice([u for u, s in user_records if s["activity"] == "heavy"])
            upload_time = rand_date_between(TIMELINE_START + timedelta(days=2), TIMELINE_END - timedelta(days=7))
            doc = LibraryDocument(
                course_id=courses[course_key].id,
                topic=topic,
                file_name=f"{title.replace(' ', '_').replace('—', '-')}.{ftype}",
                file_path=f"/uploads/library/{uuid.uuid4()}.{ftype}",
                file_type=ftype,
                file_size=random.randint(500_000, 5_000_000),
                content_hash=uuid.uuid4().hex,
                uploaded_by=uploader.id,
                uploaded_at=upload_time,
                last_accessed=TIMELINE_END - timedelta(days=random.randint(0, 5)),
                scan_status="clean",
                is_public=True,
                is_verified=True,
                view_count=random.randint(5, 30),
                download_count=random.randint(2, 15),
                helpful_votes=0,
            )
            db.add(doc)
            db.flush()
            doc_objs.append(doc)

        # Votes — give each doc some up-votes from a sample of users
        vote_count = 0
        for doc in doc_objs:
            voters = random.sample(user_records, k=random.randint(3, 8))
            net = 0
            for voter, _ in voters:
                if voter.id == doc.uploaded_by:
                    continue
                value = 1 if random.random() < 0.85 else -1
                vote = LibraryVote(
                    document_id=doc.id,
                    user_id=voter.id,
                    vote_value=value,
                )
                db.add(vote)
                net += value
                vote_count += 1
            doc.helpful_votes = net
        db.commit()
        print(f"   ✓ Created {len(doc_objs)} library docs and {vote_count} votes")

        # ── DONE ───────────────────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("✅ Seeding complete!")
        print("=" * 60)
        print(f"Users:         {len(user_records)}")
        print(f"Password:      {PASSWORD}")
        print(f"Timeline:      {TIMELINE_START.date()} → {TIMELINE_END.date()}")
        print(f"Tasks, moods, chats, study plans, notifications, library docs all populated.")
        print("\nLog in with any of these emails:")
        for u, s in user_records:
            print(f"   • {s['email']}  ({s['activity']:9})  CGPA {s['cgpa']:.2f} → {s['target']:.2f}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Shadow Realistic Seed Script")
    print("=" * 60)
    confirm = input("This will write ~15 users + 6 weeks of activity to the database. Continue? (yes/no): ")
    if confirm.lower().strip() not in ("yes", "y"):
        print("Aborted.")
        sys.exit(0)
    seed()
