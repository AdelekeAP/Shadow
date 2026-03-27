# SmartStudy Review Fixes — Design Document

**Date:** 2026-03-07
**Approach:** Single branch, all 9 fixes

## Issues to Fix

### Section 1: Critical Backend Bug Fixes

**1. Add chat input sanitization** (`backend/app/routes/smartstudy/chat.py`)
- Import `sanitize_text` from `app.utils.input_sanitizer`
- Call on `message_data.content` in both `/chat` (line 56) and `/chat/stream` (line 101) endpoints
- Prevents prompt injection and XSS payloads flowing through to GPT

**2. Normalize quiz auth** (`backend/app/routes/smartstudy/quizzes.py`)
- Remove custom `get_user_from_token()` (lines 24-31)
- Replace all `Depends(get_user_from_token)` with standard `Depends(get_current_user)` pattern used in chat.py and study_plans.py

**3. Fix learning style naming** (`backend/app/schemas/auth.py`)
- Line 135: Change `'auditory'` to `'audio'` in the valid set
- Matches smartstudy.py, frontend, and all service code

### Section 2: Dynamic Resource Finder (Serper-powered)

**4. Overhaul resource_finder.py** — Make all resource types use Serper dynamically
- `find_documentation()`: Try Serper first with query like `"{topic} documentation tutorial"`, fall back to hardcoded
- `find_practice_resources()`: Try Serper with `"{topic} practice exercises problems"`, fall back to hardcoded platforms
- `find_interactive_tutorials()`: Try Serper with `"{topic} interactive tutorial learn"`, fall back to hardcoded
- Keep `find_articles()` as-is (already uses Serper via article_search_service)
- Keep `find_github_resources()` as-is (generates dynamic search URLs)
- Hardcoded URLs become fallback-only when Serper is unavailable or returns no results

### Section 3: Document Processor

**5. Handle image-based PDFs explicitly** (`backend/app/services/document_processor.py`)
- Line 44-46: Instead of returning "No text content found" string, raise a clear `ValueError` with user-friendly message
- Caller (study_plan_generator) catches this and returns a proper error to the user
- Add inline comments documenting the content analysis thresholds (0.03 math, 0.03 code, 0.01 visual)

### Section 4: Frontend Fixes

**6. Extract friendlyError to shared utility**
- Create `frontend/src/utils/errors.js` with the consolidated `friendlyError()` function
- Update `SmartStudyPage.jsx` and `StudyPlanDetails.jsx` to import from there
- Use the regex-based version (more robust) from SmartStudyPage as the canonical one

**7. Fix React keys in SmartStudyChat.jsx**
- Line 395: Assign each message a unique ID (counter-based) when added to state, use as key
- Line 376: Use `prompt.prompt` string as key (static list, acceptable)

**8. Add SmartStudy CTA to CGPAPage**
- When calculated CGPA < target CGPA, show a banner with link to `/smartstudy`
- Simple, non-intrusive: "Below your target? Create a study plan to get back on track."
- Uses react-router `useNavigate` to link to SmartStudy page

## Out of Scope (Not fixing)

- ~~Model names (gpt-5.4, gpt-4.1)~~ — These are valid models (GPT-4.1 released April 2025, GPT-5.4 released March 2026)
- Frontend component decomposition (large refactor, not a bug fix)
- Frontend test coverage (separate effort)
- Token counting before GPT calls (post-counting already exists)
