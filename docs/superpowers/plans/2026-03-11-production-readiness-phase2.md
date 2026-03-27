# Shadow Production Readiness Phase 2 — Push to 95%

> **For agentic workers:** Use superpowers:subagent-driven-development to implement this plan.

**Goal:** Close the remaining gaps across security, testing, performance, infrastructure, and code quality to reach 95%+ production readiness.

**Architecture:** Fix-in-place, no new services. Prioritized by quickest wins first, then security, then infra.

**Tech Stack:** Python 3.13 / FastAPI / SQLAlchemy / React 18 / Vite 5 / Docker Compose / nginx

---

## Phase Overview

| # | Task | Domain Impact | Est. Time |
|---|------|--------------|-----------|
| A | Remove torch/emotion_analysis dead code | Quality +3, Docker -2GB | 20 min |
| B | Add virus scanning to study plan uploads | Security +3 | 20 min |
| C | Add frontend coverage threshold to CI | Testing +3 | 10 min |
| D | Switch process-local SmartStudy cache to Redis | Perf +4 | 25 min |
| E | Add CSP headers to nginx + fix backend CSP | Security +4 | 20 min |
| F | Add HTTPS/TLS config to nginx | Infra +8 | 20 min |
| G | Add database backup cron to docker-compose | Infra +3 | 10 min |
| H | Add CD workflow to GitHub Actions | Infra +5 | 30 min |
| I | Add frontend component tests (SmartStudy, Quiz, Dashboard) | Testing +10 | 60 min |
| J | Move refresh tokens to HttpOnly cookies | Security +8 | 45 min |

**Total: ~4.5 hours → projected score 95-97%**

---

## Task A: Remove torch/emotion_analysis Dead Code

**Files:**
- Modify: `backend/requirements.txt` — remove `torch`, `transformers`, `scipy`, `hf-xet`, `huggingface-hub`, `safetensors`, `tokenizers`
- Delete: `backend/app/services/emotion_analysis.py`
- Modify: `backend/app/services/sentiment_analysis.py` — keep but ensure DISABLE_ML_MODELS guard works
- Delete: `backend/tests/test_services/test_emotion_analysis.py` (if exists, tests dead code)

Keep `sentiment_analysis.py` since it IS used by `mood.py`, but ensure the ML model is lazy-loaded and guarded.

---

## Task B: Add Virus Scanning to Study Plan Uploads

**Files:**
- Modify: `backend/app/routes/smartstudy/study_plans.py`

In `create_study_plan_with_upload`, after file is read into memory but before processing, add virus scanning call matching the library upload pattern:
```python
from app.services.virus_scan_service import scan_bytes
scan_result = scan_bytes(file_content)
if scan_result and scan_result.get("infected"):
    raise HTTPException(400, detail="File failed security scan")
```

Same pattern used in `library_service.py:contribute_to_library`.

---

## Task C: Add Frontend Coverage Threshold

**Files:**
- Modify: `frontend/vite.config.js` — add coverage thresholds to test config
- Modify: `.github/workflows/ci.yml` — ensure frontend test step uses coverage flag

---

## Task D: Switch SmartStudy Context Cache to Redis

**Files:**
- Modify: `backend/app/services/smartstudy_service.py`

Replace the process-local `_context_cache` dict with calls to the existing `cache_service.py` (`cache_get`/`cache_set`). The Redis cache service already has graceful in-memory fallback, so this works in all environments.

---

## Task E: Add CSP Headers to nginx + Fix Backend CSP

**Files:**
- Modify: `frontend/nginx.conf` — add Content-Security-Policy header
- Modify: `backend/app/middleware/security_headers.py` — expand CSP directives

nginx CSP should allow: self, YouTube iframes, YouTube thumbnails, OpenAI connect, inline styles (Tailwind), blob: for audio.

Backend CSP should add: connect-src, frame-src, img-src, media-src directives.

---

## Task F: Add HTTPS/TLS to nginx

**Files:**
- Modify: `frontend/nginx.conf` — add SSL server block with cert paths, HTTP→HTTPS redirect
- Modify: `docker-compose.yml` — expose port 443, mount cert volume

Use environment variable for cert paths so it works with Let's Encrypt, self-signed, or load balancer termination.

---

## Task G: Add Database Backup Cron

**Files:**
- Create: `backend/scripts/backup-db.sh`
- Modify: `docker-compose.yml` — add pg_dump cron via postgres healthcheck or separate backup service

---

## Task H: Add CD Workflow

**Files:**
- Create: `.github/workflows/deploy.yml`

Triggers on push to main after tests pass. Builds Docker images, pushes to GHCR, optionally SSH deploys.

---

## Task I: Add Frontend Component Tests

**Files:**
- Create: `frontend/src/components/__tests__/SmartStudyChat.test.jsx`
- Create: `frontend/src/components/__tests__/TaskList.test.jsx`
- Create: `frontend/src/components/quiz/__tests__/QuizPlayer.test.jsx`
- Create: `frontend/src/pages/__tests__/DashboardPage.test.jsx`

Focus on: render tests, user interaction, error states, loading states. Mock API calls.

---

## Task J: Move Refresh Tokens to HttpOnly Cookies

**Files:**
- Modify: `backend/app/routes/auth.py` — set refresh token as HttpOnly cookie on login/refresh
- Modify: `backend/app/routes/auth.py` — read refresh token from cookie on /refresh endpoint
- Modify: `frontend/src/services/api.js` — stop storing refresh_token in localStorage
- Modify: `frontend/src/contexts/AuthContext.jsx` — remove refresh_token localStorage handling
