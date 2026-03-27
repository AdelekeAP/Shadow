# Shadow Production Readiness Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden Shadow from "features complete" (91/100) to production-ready by fixing all 8 blockers, 15 high-priority issues, and key improvements — organized in 6 iterative phases that each produce a shippable, testable checkpoint.

**Architecture:** Fix-in-place across the existing FastAPI backend and React frontend. No new services or major refactors. Each phase targets one domain, builds on the previous, and ends with a passing test suite + commit.

**Tech Stack:** Python 3.13 / FastAPI / SQLAlchemy / Alembic / React 18 / Vite 5 / Docker Compose / GitHub Actions

---

## Phase Overview

| Phase | Domain | Issues Fixed | Est. Time | Checkpoint |
|-------|--------|-------------|-----------|------------|
| 1 | **Critical Security** | B3, B4, B5, H4, H6 | 30 min | JWT forge impossible, admin-only course creation |
| 2 | **Runtime Crash Fixes** | B1, B2, B7 | 45 min | Dashboard loads, SmartStudy triggers work, AI doesn't freeze |
| 3 | **Error Handling & Resilience** | H11, H12, H3, H10 | 45 min | Consistent error responses, all routes protected |
| 4 | **Performance & Data** | H9, H10, H5 | 45 min | No N+1 queries, no over-fetching, 2GB lighter Docker image |
| 5 | **Infrastructure & Deploy** | B6, H6, H7, H8, H12 | 60 min | Migrations run at startup, CI deploys, versions match |
| 6 | **Testing Gaps** | H13, H14, H15 | 90 min | Auth security flows tested, semesters tested, E2E in CI |

**Total estimated: ~5 hours of focused work**

---

## Chunk 1: Critical Security Fixes

### Task 1.1: Hardcode JWT Algorithm

**Files:**
- Modify: `backend/app/utils/auth.py:25`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_utils/test_auth.py — add to existing file
def test_algorithm_is_not_configurable(monkeypatch):
    """JWT algorithm must be hardcoded, never from env"""
    monkeypatch.setenv("ALGORITHM", "none")
    # Re-import to pick up env change
    import importlib
    from app.utils import auth
    importlib.reload(auth)
    assert auth.ALGORITHM == "HS256", "Algorithm must not be configurable via env"
    # Clean up
    monkeypatch.delenv("ALGORITHM", raising=False)
    importlib.reload(auth)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_utils/test_auth.py::test_algorithm_is_not_configurable -v`
Expected: FAIL (current code reads from env)

- [ ] **Step 3: Fix — hardcode the algorithm**

In `backend/app/utils/auth.py`, replace line 25:
```python
# OLD:
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# NEW:
ALGORITHM = "HS256"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_utils/test_auth.py::test_algorithm_is_not_configurable -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/utils/auth.py backend/tests/test_utils/test_auth.py
git commit -m "fix(security): hardcode JWT algorithm to HS256 — remove env var override"
```

---

### Task 1.2: Remove Fallback Secret Key

**Files:**
- Modify: `backend/app/utils/auth.py:20-24`

- [ ] **Step 1: Fix — always require SECRET_KEY**

In `backend/app/utils/auth.py`, replace lines 20-24:
```python
# OLD:
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if os.getenv("ENVIRONMENT") == "production":
        raise RuntimeError("SECRET_KEY must be set in production")
    SECRET_KEY = "dev-only-insecure-key-change-in-production"

# NEW:
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    import warnings
    warnings.warn("SECRET_KEY not set — using random key (sessions won't persist across restarts)")
    import secrets
    SECRET_KEY = secrets.token_urlsafe(32)
```

This is safer than a hardcoded fallback: dev still works (no crashes), but no attacker can guess the key. Sessions just don't survive restarts in dev, which is acceptable.

- [ ] **Step 2: Run existing auth tests**

Run: `cd backend && python -m pytest tests/test_utils/test_auth.py -v`
Expected: ALL PASS (tests set their own SECRET_KEY via conftest)

- [ ] **Step 3: Commit**

```bash
git add backend/app/utils/auth.py
git commit -m "fix(security): replace hardcoded fallback SECRET_KEY with random generation"
```

---

### Task 1.3: Set ENVIRONMENT in docker-compose

**Files:**
- Modify: `docker-compose.yml:52-60`

- [ ] **Step 1: Add ENVIRONMENT and fix Postgres password**

In `docker-compose.yml`, in the `backend.environment` block, add `ENVIRONMENT=production`. Also fix the Postgres password default:

```yaml
# In the postgres service, change:
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
# To:
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}

# In the backend service environment, add:
- ENVIRONMENT=production
```

- [ ] **Step 2: Verify compose config parses**

Run: `docker compose config --quiet 2>&1 || echo "Config error"`
Expected: Error about missing POSTGRES_PASSWORD (which proves the guard works). Set it and re-run:
Run: `POSTGRES_PASSWORD=test SECRET_KEY=test docker compose config --quiet && echo "OK"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "fix(infra): enforce ENVIRONMENT=production and require POSTGRES_PASSWORD in docker-compose"
```

---

### Task 1.4: Admin Guard on create_course

**Files:**
- Modify: `backend/app/routes/courses.py:109`

- [ ] **Step 1: Write the failing test**

```python
# In backend/tests/test_api/test_course_routes.py — add:
def test_create_course_requires_admin(client, auth_headers):
    """Regular users should not be able to create courses"""
    response = client.post("/api/v1/courses/", json={
        "code": "TST101",
        "title": "Test Course",
        "credits": 3,
        "level": 100
    }, headers=auth_headers)
    # Should be forbidden for non-admin users
    assert response.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_api/test_course_routes.py::test_create_course_requires_admin -v`
Expected: FAIL (returns 200/201 instead of 403)

- [ ] **Step 3: Add admin check to create_course**

In `backend/app/routes/courses.py`, add at the top of `create_course` function body (after the docstring):

```python
    # Only admins can create courses in the catalog
    admin_emails = set(
        e.strip().lower()
        for e in os.getenv("ADMIN_EMAILS", "").split(",")
        if e.strip()
    )
    if current_user.email.lower() not in admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create courses"
        )
```

Add `import os` at the top of the file if not already present.

- [ ] **Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_api/test_course_routes.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/courses.py backend/tests/test_api/test_course_routes.py
git commit -m "fix(security): require admin privileges for course creation"
```

---

## Chunk 2: Runtime Crash Fixes

### Task 2.1: Fix DashboardPage Auth Bypass

**Files:**
- Modify: `frontend/src/pages/DashboardPage.jsx:1-15, 127-131`

- [ ] **Step 1: Replace api auth imports with useAuth hook**

In `frontend/src/pages/DashboardPage.jsx`:

Replace the imports line:
```javascript
// OLD:
import { getCurrentUser, isAuthenticated, logout, getEnrolledCourses, getTasks, getTaskStats, updateEnrollment, resendVerification } from '../services/api'

// NEW:
import { getEnrolledCourses, getTasks, getTaskStats, updateEnrollment, resendVerification } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
```

Inside the component function, add near the top (after `const navigate = useNavigate()`):
```javascript
const { user, logout } = useAuth()
```

Remove the local `user` state:
```javascript
// DELETE this line:
const [user, setUser] = useState(null)
```

Replace the auth useEffect:
```javascript
// OLD:
useEffect(() => {
    if (!isAuthenticated()) { navigate('/login'); return }
    setUser(getCurrentUser())
    loadAll()
}, [navigate])

// NEW:
useEffect(() => {
    loadAll()
}, [])
```

The `ProtectedRoute` wrapper in `App.jsx` already handles the auth redirect — no need to duplicate it.

- [ ] **Step 2: Apply the same fix to ProfilePage.jsx**

In `frontend/src/pages/ProfilePage.jsx`, apply the same pattern:
- Remove `isAuthenticated`, `getCurrentUser`, `logout` from api imports
- Add `import { useAuth } from '../contexts/AuthContext'`
- Use `const { user, logout } = useAuth()` inside the component
- Remove local user state and manual auth check

- [ ] **Step 3: Run frontend tests**

Run: `cd frontend && npm run test:run`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/DashboardPage.jsx frontend/src/pages/ProfilePage.jsx
git commit -m "fix: use AuthContext instead of localStorage for DashboardPage and ProfilePage auth"
```

---

### Task 2.2: Fix Naive datetime.now() Across Backend

**Files:**
- Modify: `backend/app/services/smartstudy_service.py` (lines 87, 108, 326, 435, 476)
- Modify: `backend/app/services/study_plan_generator.py` (lines 586-587, 1150)
- Modify: `backend/app/routes/smartstudy/study_plans.py` (lines 630, 636, 755, 894, 1053)

- [ ] **Step 1: Find all instances**

Run: `cd backend && grep -rn "datetime\.now()" app/ --include="*.py" | grep -v "timezone"`
This will show every `datetime.now()` that does NOT already pass `timezone.utc`.

- [ ] **Step 2: Replace all instances**

In every file found, replace `datetime.now()` with `datetime.now(timezone.utc)`.

Ensure `from datetime import datetime, timezone` is imported at the top of each modified file.

Do NOT touch files that already use `datetime.now(timezone.utc)` (like `auth.py`, `tasks.py`).

- [ ] **Step 3: Run backend tests**

Run: `cd backend && python -m pytest -x -q`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/smartstudy_service.py backend/app/services/study_plan_generator.py backend/app/routes/smartstudy/study_plans.py
git commit -m "fix: replace naive datetime.now() with timezone-aware datetime.now(timezone.utc)"
```

---

### Task 2.3: Fix Blocking time.sleep() in Async OpenAI Client

**Files:**
- Modify: `backend/app/services/openai_client.py:260-271`

- [ ] **Step 1: Make call_with_retry async-safe**

In `backend/app/services/openai_client.py`, replace the `time.sleep(delay)` line:

```python
# OLD:
time.sleep(delay)

# NEW:
import asyncio
try:
    loop = asyncio.get_running_loop()
    await asyncio.sleep(delay)
except RuntimeError:
    # No running loop (called from sync context)
    time.sleep(delay)
```

However, since `call_with_retry` is a sync function called via `asyncio.to_thread` or directly, a simpler fix is to ensure it's always run in a thread (which it should be since OpenAI SDK calls are sync). Check if `call_with_retry` is ever awaited directly.

If it's always called via `asyncio.to_thread`, then `time.sleep` is fine (it only blocks the thread, not the event loop). Verify by searching:

Run: `cd backend && grep -rn "call_with_retry" app/ --include="*.py"`

If it's called directly from async handlers without `to_thread`, wrap the call sites. If it's already threaded, document this and move on.

- [ ] **Step 2: Run tests**

Run: `cd backend && python -m pytest tests/test_services/test_smartstudy_service.py -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/openai_client.py
git commit -m "fix(perf): ensure OpenAI retry sleep doesn't block the async event loop"
```

---

## Chunk 3: Error Handling & Resilience

### Task 3.1: Add RequestValidationError Handler

**Files:**
- Modify: `backend/app/main.py` (near line 270)

- [ ] **Step 1: Add the handler**

In `backend/app/main.py`, before the global `Exception` handler, add:

```python
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = []
    for e in exc.errors():
        loc = " -> ".join(str(l) for l in e["loc"] if l != "body")
        errors.append(f"{loc}: {e['msg']}" if loc else e["msg"])
    return JSONResponse(
        status_code=422,
        content={"detail": "; ".join(errors)}
    )
```

- [ ] **Step 2: Run backend tests**

Run: `cd backend && python -m pytest -x -q`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/main.py
git commit -m "fix(error): add RequestValidationError handler — return human-readable 422 errors"
```

---

### Task 3.2: Add try/except to Unprotected Route Handlers

**Files:**
- Modify: `backend/app/routes/tasks.py` (get_task_statistics, get_tasks_by_course)
- Modify: `backend/app/routes/courses.py` (get_all_courses, get_my_courses)

- [ ] **Step 1: Wrap get_task_statistics**

In `backend/app/routes/tasks.py`, add a module-level logger at the top:
```python
import logging
logger = logging.getLogger(__name__)
```

Wrap the body of `get_task_statistics` in try/except:
```python
async def get_task_statistics(...):
    """..."""
    try:
        # ... existing body ...
    except Exception as e:
        logger.error(f"Error in get_task_statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve task statistics")
```

Apply the same pattern to `get_tasks_by_course`.

- [ ] **Step 2: Add logger and try/except to courses.py**

In `backend/app/routes/courses.py`, add module-level logger and wrap `get_all_courses` and `get_my_courses` in the same pattern.

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_api/test_task_routes.py tests/test_api/test_course_routes.py -v`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/routes/tasks.py backend/app/routes/courses.py
git commit -m "fix(error): add try/except and logging to unprotected route handlers"
```

---

### Task 3.3: Fix Error Shape Consistency

**Files:**
- Modify: `backend/app/routes/smartstudy/chat.py:65-72`

- [ ] **Step 1: Flatten the AI error detail to a string**

In `backend/app/routes/smartstudy/chat.py`, where the AI error is raised:
```python
# OLD:
raise HTTPException(status_code=500, detail={"message": ..., "error_type": ...})

# NEW:
raise HTTPException(status_code=500, detail=result.get("error", "AI service temporarily unavailable"))
```

- [ ] **Step 2: Fix delete_conversation IntegrityError message**

In the same file, fix the `delete_conversation` IntegrityError handler:
```python
# OLD:
detail="Resource already exists"

# NEW:
detail="Cannot delete this conversation because it has dependent records"
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_api/test_smartstudy_routes.py -v`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/routes/smartstudy/chat.py
git commit -m "fix(error): flatten AI error detail to string, fix delete conversation error message"
```

---

## Chunk 4: Performance & Dependencies

### Task 4.1: Fix N+1 Query in get_tasks_by_course

**Files:**
- Modify: `backend/app/routes/tasks.py` (get_tasks_by_course, lines 418-425)

- [ ] **Step 1: Replace per-course loop with batch query**

Replace the loop in `get_tasks_by_course`:
```python
# OLD:
for uc in user_courses:
    tasks = db.query(Task).filter(
        Task.user_course_id == uc.id,
        Task.category == "CA"
    ).all()
    # ...per-course processing...

# NEW:
uc_ids = [uc.id for uc in user_courses]
all_ca_tasks = db.query(Task).filter(
    Task.user_course_id.in_(uc_ids),
    Task.category == "CA"
).all()

# Group tasks by user_course_id
from collections import defaultdict
tasks_by_course = defaultdict(list)
for t in all_ca_tasks:
    tasks_by_course[t.user_course_id].append(t)

summaries = []
for uc in user_courses:
    tasks = tasks_by_course.get(uc.id, [])
    # ...rest of processing unchanged...
```

- [ ] **Step 2: Extract CA/EXAM recalculation helper**

Create a helper function in `tasks.py` to replace the 3x duplicated CA/EXAM recalc:
```python
def recalculate_course_scores(user_course, db):
    """Recalculate CA and EXAM scores for a user course from completed tasks."""
    ca_tasks = db.query(Task).filter(
        Task.user_course_id == user_course.id,
        Task.category == "CA",
        Task.is_completed == True,
        Task.earned_marks.isnot(None)
    ).all()
    user_course.ca_score = sum(float(t.earned_marks) for t in ca_tasks)

    exam_tasks = db.query(Task).filter(
        Task.user_course_id == user_course.id,
        Task.category == "EXAM",
        Task.is_completed == True,
        Task.earned_marks.isnot(None)
    ).all()
    user_course.exam_score = sum(float(t.earned_marks) for t in exam_tasks)

    all_count = db.query(func.count(Task.id)).filter(Task.user_course_id == user_course.id).scalar() or 0
    completed_count = db.query(func.count(Task.id)).filter(
        Task.user_course_id == user_course.id, Task.is_completed == True
    ).scalar() or 0
    user_course.completion_rate = (completed_count / all_count * 100) if all_count > 0 else 0
```

Replace the duplicated blocks in `create_task`, `update_task`, and `mark_task_complete` with calls to `recalculate_course_scores(user_course, db)`.

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_api/test_task_routes.py -v`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/routes/tasks.py
git commit -m "perf: fix N+1 query in get_tasks_by_course, extract recalculate_course_scores helper"
```

---

### Task 4.2: Exclude extracted_text from Library Browse

**Files:**
- Modify: `backend/app/services/library_service.py` (browse_library, ~line 460)

- [ ] **Step 1: Use deferred loading for extracted_text**

In `library_service.py`, modify the browse query to defer the heavy column:
```python
from sqlalchemy.orm import defer

# In browse_library, change the query to:
query = db.query(LibraryDocument).options(
    defer(LibraryDocument.extracted_text),
    joinedload(LibraryDocument.course),
    joinedload(LibraryDocument.uploader)
)
```

Also add `joinedload(LibraryDocument.uploader)` to `get_user_contributions` if missing.

- [ ] **Step 2: Run tests**

Run: `cd backend && python -m pytest tests/test_services/test_library_service.py tests/test_api/test_library_routes.py -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/library_service.py
git commit -m "perf: defer extracted_text from library browse queries, fix missing joinedload"
```

---

### Task 4.3: Remove Unused torch/transformers or Gate Properly

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/services/emotion_analysis.py` (if removing)

- [ ] **Step 1: Check if emotion_analysis is wired into any route**

Run: `cd backend && grep -rn "emotion_analysis\|analyze_emotion" app/routes/ app/services/ --include="*.py" | grep -v "emotion_analysis.py"`

If no route imports it, the service is dead code.

- [ ] **Step 2: Decision point**

**Option A (recommended):** Keep `sentiment_analysis.py` (which uses transformers) but make the model load lazy and add `DISABLE_ML_MODELS` guard. Remove `emotion_analysis.py` since it's unused.

**Option B:** Remove both ML services and use OpenAI for sentiment (eliminates torch entirely). This saves 2-3 GB in Docker image size.

For now, go with **Option A** — the model is already guarded by `DISABLE_ML_MODELS` in production CI, just ensure it's documented.

- [ ] **Step 3: Remove dead ad-hoc test scripts**

```bash
rm backend/test_sentiment.py backend/test_youtube_integration.py
```

- [ ] **Step 4: Run tests**

Run: `cd backend && python -m pytest -x -q`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/app/services/emotion_analysis.py
git rm backend/test_sentiment.py backend/test_youtube_integration.py
git commit -m "chore: remove unused ad-hoc test scripts, document ML model loading"
```

---

## Chunk 5: Infrastructure & Deployment

### Task 5.1: Add Alembic Migration to Container Startup

**Files:**
- Create: `backend/entrypoint.sh`
- Modify: `backend/Dockerfile`

- [ ] **Step 1: Create entrypoint script**

Create `backend/entrypoint.sh`:
```bash
#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting application server..."
exec "$@"
```

- [ ] **Step 2: Update Dockerfile to use entrypoint**

In `backend/Dockerfile`, before the CMD line, add:
```dockerfile
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

The existing CMD remains: `CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]`

- [ ] **Step 3: Commit**

```bash
git add backend/entrypoint.sh backend/Dockerfile
git commit -m "fix(infra): run alembic migrations at container startup via entrypoint"
```

---

### Task 5.2: Fix CI Python Version and Add Migration Test

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Update Python version to match Dockerfile**

In `.github/workflows/ci.yml`, change:
```yaml
# OLD:
python-version: "3.11"

# NEW:
python-version: "3.13"
```

- [ ] **Step 2: Add pip caching**

In the backend-tests job, update the setup-python step:
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.13"
    cache: pip
    cache-dependency-path: backend/requirements.txt
```

- [ ] **Step 3: Fix frontend healthcheck in docker-compose**

In `docker-compose.yml`, fix the frontend healthcheck:
```yaml
# OLD:
test: ["CMD", "curl", "-f", "http://localhost:80/", "||", "exit", "1"]

# NEW:
test: ["CMD-SHELL", "curl -f http://localhost:80/ || exit 1"]
```

- [ ] **Step 4: Add missing env vars to docker-compose backend**

Add `env_file: .env` to the backend service in docker-compose.yml, or add the missing variables:
```yaml
- SERPER_API_KEY=${SERPER_API_KEY:-}
- ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY:-}
- SENTRY_DSN=${SENTRY_DSN:-}
- ADMIN_EMAILS=${ADMIN_EMAILS:-}
```

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml docker-compose.yml
git commit -m "fix(infra): align CI Python to 3.13, add pip cache, fix healthcheck, pass env vars"
```

---

### Task 5.3: Untrack frontend/.env

**Files:**
- Modify: `.gitignore`
- Create: `frontend/.env.example`

- [ ] **Step 1: Create frontend/.env.example**

```
VITE_API_URL=http://localhost:8000
VITE_SENTRY_DSN=
```

- [ ] **Step 2: Add to .gitignore and untrack**

```bash
echo "frontend/.env" >> .gitignore
git rm --cached frontend/.env 2>/dev/null || true
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore frontend/.env.example
git commit -m "fix(security): untrack frontend/.env, add .env.example"
```

---

## Chunk 6: Critical Testing Gaps

### Task 6.1: Test Auth Security Flows

**Files:**
- Modify: `backend/tests/test_api/test_auth_routes.py`

- [ ] **Step 1: Add logout test**

```python
def test_logout_blacklists_token(client, auth_headers):
    """Logout should blacklist the access token"""
    # First verify we're authenticated
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200

    # Logout
    response = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == 200

    # Token should now be blacklisted
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 401
```

- [ ] **Step 2: Add refresh token test**

```python
def test_refresh_token_rotation(client):
    """Refresh should return new tokens and invalidate old refresh token"""
    # Register and login to get tokens
    client.post("/api/v1/auth/register", json={
        "email": "refresh@test.com", "password": "TestPass123!",
        "full_name": "Test User", "entry_level": "100"
    })
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "refresh@test.com", "password": "TestPass123!"
    })
    refresh_token = login_resp.json().get("refresh_token")
    if not refresh_token:
        return  # Skip if refresh tokens not enabled

    # Use refresh token
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert "refresh_token" in resp.json()

    # Old refresh token should no longer work
    resp2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp2.status_code in [401, 400]
```

- [ ] **Step 3: Add password change test**

```python
def test_change_password_invalidates_sessions(client, auth_headers):
    """Changing password should invalidate existing tokens"""
    response = client.post("/api/v1/auth/change-password", json={
        "current_password": "TestPassword123!",
        "new_password": "NewPassword456!"
    }, headers=auth_headers)
    assert response.status_code == 200

    # Old token should now be invalid (token_version incremented)
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 401
```

- [ ] **Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_api/test_auth_routes.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_api/test_auth_routes.py
git commit -m "test: add auth security tests — logout, refresh rotation, password change invalidation"
```

---

### Task 6.2: Add Semester Route Tests

**Files:**
- Create: `backend/tests/test_api/test_semester_routes.py`

- [ ] **Step 1: Create semester test file with core tests**

```python
"""Tests for semester management routes"""
import pytest


def test_create_semester(client, auth_headers):
    response = client.post("/api/v1/semesters/", json={
        "name": "Fall 2025",
        "year": 2025,
        "semester_number": 1
    }, headers=auth_headers)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["name"] == "Fall 2025"
    return data


def test_list_semesters(client, auth_headers):
    # Create first
    client.post("/api/v1/semesters/", json={
        "name": "Fall 2025", "year": 2025, "semester_number": 1
    }, headers=auth_headers)

    response = client.get("/api/v1/semesters/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_create_duplicate_semester(client, auth_headers):
    """Should not allow duplicate semesters for the same user"""
    semester_data = {"name": "Fall 2025", "year": 2025, "semester_number": 1}
    client.post("/api/v1/semesters/", json=semester_data, headers=auth_headers)
    resp = client.post("/api/v1/semesters/", json=semester_data, headers=auth_headers)
    assert resp.status_code in [400, 409]


def test_semester_isolation(client, auth_headers, second_user_headers):
    """Users should only see their own semesters"""
    client.post("/api/v1/semesters/", json={
        "name": "My Semester", "year": 2025, "semester_number": 1
    }, headers=auth_headers)

    response = client.get("/api/v1/semesters/", headers=second_user_headers)
    names = [s["name"] for s in response.json()]
    assert "My Semester" not in names
```

Note: `second_user_headers` fixture may need to be added to conftest if not present. Check existing conftest for available fixtures and adapt accordingly.

- [ ] **Step 2: Run tests**

Run: `cd backend && python -m pytest tests/test_api/test_semester_routes.py -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_api/test_semester_routes.py
git commit -m "test: add semester route tests — CRUD and user isolation"
```

---

### Task 6.3: Fix E2E Test Credentials

**Files:**
- Modify: `frontend/e2e/*.spec.js` (all 6 files)
- Create: `frontend/e2e/helpers.js`

- [ ] **Step 1: Extract test config to a helper**

Create `frontend/e2e/helpers.js`:
```javascript
export const TEST_EMAIL = process.env.E2E_TEST_EMAIL || 'test@example.com'
export const TEST_PASSWORD = process.env.E2E_TEST_PASSWORD || 'TestPassword123!'

export async function loginAs(page, email = TEST_EMAIL, password = TEST_PASSWORD) {
    await page.goto('/login')
    await page.fill('[name="email"]', email)
    await page.fill('[name="password"]', password)
    await page.click('button[type="submit"]')
    await page.waitForURL('**/dashboard', { timeout: 10000 })
}
```

- [ ] **Step 2: Update all E2E specs to use the helper**

In each of the 6 spec files, replace hardcoded credentials with the imported helper.

- [ ] **Step 3: Add E2E config to playwright.config.js**

Ensure `playwright.config.js` has a `webServer` block (even if commented out for now):
```javascript
// Uncomment when running locally:
// webServer: {
//     command: 'cd ../backend && uvicorn app.main:app --port 8000',
//     port: 8000,
//     timeout: 30000,
// },
```

- [ ] **Step 4: Commit**

```bash
git add frontend/e2e/helpers.js frontend/e2e/*.spec.js frontend/playwright.config.js
git commit -m "test: extract E2E credentials to env vars, remove hardcoded emails from specs"
```

---

## Final Checkpoint

- [ ] **Run full backend test suite**

Run: `cd backend && python -m pytest -v --tb=short`
Expected: ALL PASS

- [ ] **Run full frontend test suite**

Run: `cd frontend && npm run test:run`
Expected: ALL PASS

- [ ] **Run lint**

Run: `cd frontend && npm run lint`
Expected: No errors

- [ ] **Verify Docker builds**

Run: `cd backend && docker build -t shadow-backend-test . && echo "Backend image OK"`
Run: `cd frontend && docker build -t shadow-frontend-test . && echo "Frontend image OK"`

- [ ] **Final commit with all changes verified**

Review `git status` and ensure all changes are committed in their respective phase commits.

---

## Post-Plan: Remaining Improvements (Not Blocking)

These are genuine improvements but can be done after the defense:

| Priority | Issue | Effort |
|----------|-------|--------|
| Medium | Move refresh tokens to HttpOnly cookies | 3-4 hrs |
| Medium | Add virus scanning to study plan upload path | 1 hr |
| Medium | Add file path canonicalization to download endpoint | 30 min |
| Medium | Add CSP header to nginx config | 1 hr |
| Medium | Add HTTPS/TLS to nginx or document LB termination | 1-2 hrs |
| Medium | Add deployment workflow to CI | 2-3 hrs |
| Medium | Switch process-local cache to Redis in smartstudy_service | 1 hr |
| Low | Add `Cache-Control` headers to semi-static endpoints | 30 min |
| Low | Dynamic import SmartStudy sub-components | 1 hr |
| Low | Standardize on one icon library | 2 hrs |
| Low | Add frontend coverage threshold to CI | 15 min |
| Low | Add GIN trigram index for library text search | 30 min |
