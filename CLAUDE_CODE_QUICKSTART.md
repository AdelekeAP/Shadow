# 🚀 Claude Code Quick Start - Shadow v2.0 Implementation

**Purpose**: Guide for implementing Shadow v2.0 with SmartStudy using Claude Code  
**Time to First Feature**: ~2 hours for basic chat interface

---

## 📋 Prerequisites Checklist

Before starting with Claude Code, ensure you have:

- [ ] Shadow v1.0 codebase (75% complete)
- [ ] PostgreSQL database running
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] OpenAI API key (get from platform.openai.com)
- [ ] YouTube API key (optional for Phase 2)
- [ ] Reddit API credentials (optional for Phase 2)

---

## 📁 Setup Instructions

### 1. Copy Specification to Your Project

```bash
cd /path/to/shadow-project

# Create docs folder
mkdir -p docs

# Copy the specification
cp SHADOW_SPECIFICATION_V2.md docs/

# Verify it's there
ls -lh docs/
```

### 2. Install New Dependencies

**Backend:**
```bash
cd backend

# Activate your virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Add new dependencies to requirements.txt
cat >> requirements.txt << EOF

# SmartStudy Dependencies
openai==1.3.5
transformers==4.35.2
torch==2.1.0
sentencepiece==0.1.99
google-api-python-client==2.108.0
praw==7.7.1
EOF

# Install
pip install -r requirements.txt

# Download emotion detection model (takes 2-3 minutes)
python -c "from transformers import pipeline; pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base')"
```

**Frontend:**
```bash
cd ../frontend

# Already have most dependencies, just verify
npm install
```

### 3. Add Environment Variables

```bash
# In backend/.env
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
echo "YOUTUBE_API_KEY=your-key-here" >> .env
echo "REDDIT_CLIENT_ID=your-id" >> .env
echo "REDDIT_CLIENT_SECRET=your-secret" >> .env
```

---

## 🤖 Using Claude Code

### Method 1: Step-by-Step Implementation (Recommended)

**Start Claude Code in your project directory:**
```bash
cd /path/to/shadow-project
claude-code
```

**Prompt 1: Phase 1 Week 1 - Database Setup**
```
Read docs/SHADOW_SPECIFICATION_V2.md section 6.2 and implement:
1. Add 'topic' field to tasks table (with migration)
2. Create the 6 new SmartStudy tables: chat_conversations, chat_messages, 
   study_plans, study_plan_resources, uploaded_documents, intervention_outcomes
3. Generate Alembic migration file
4. Test the migration on dev database

Show me the migration file before applying it.
```

**Prompt 2: Emotion Detection Service**
```
Read docs/SHADOW_SPECIFICATION_V2.md section 7.6 and implement the emotion 
detection service:
1. Create backend/app/services/emotion_analysis.py with EmotionAnalyzer class
2. Use model: j-hartmann/emotion-english-distilroberta-base
3. Update the mood logging endpoint to use emotion detection
4. Test with sample mood texts

Show me test results for these moods:
- "I'm feeling great today!"
- "I'm so stressed about this exam"
- "I failed my test and I'm really sad"
```

**Prompt 3: Basic Chat Interface**
```
Read docs/SHADOW_SPECIFICATION_V2.md section 7.9.1 and implement:
1. Create chat API endpoint: POST /api/v1/smartstudy/chat
2. Load student context (courses, tasks, mood) and pass to GPT-4
3. Create frontend component: SmartStudyChat.jsx
4. Add route /smartstudy in App.jsx
5. Test the chat with a sample question

Context: Use my existing Shadow data (courses, tasks, CGPA) to personalize responses.
```

**Prompt 4: Integration into Dashboard**
```
Read docs/SHADOW_SPECIFICATION_V2.md section 7.9.7 and add SmartStudy 
prompts to the dashboard:
1. Show "📚 Need Help?" card when student is struggling (predicted grade < B)
2. Add SmartStudy button to course cards
3. Add "Ask SmartStudy" button next to task completion
4. Link all buttons to /smartstudy chat

Show me before/after screenshots of the dashboard.
```

### Method 2: Feature-Complete Implementation

**Single comprehensive prompt:**
```
Read docs/SHADOW_SPECIFICATION_V2.md and implement Phase 1 Week 1-2:

CONTEXT:
- I have Shadow v1.0 running (auth, courses, tasks, CGPA, moods all working)
- Database: PostgreSQL with SQLAlchemy ORM
- Backend: FastAPI at backend/app/
- Frontend: React + Vite at frontend/src/

IMPLEMENT:
1. Database migrations (add topic field + 6 new tables)
2. Emotion detection service (7-emotion model)
3. Basic SmartStudy chat (GPT-4 integration with context)
4. Chat UI component
5. Dashboard integration (SmartStudy prompts)

REQUIREMENTS:
- Use existing auth middleware
- Match existing code style (navy/stone colors)
- Add comprehensive error handling
- Include API tests

PRIORITY: Get chat working first, then polish.

Start with database migrations. Show me each file before creating it.
```

---

## 🎯 Implementation Phases

### Phase 1: Foundation (Week 1-4)

**Week 1: Database + Emotion Detection**
```bash
# Claude Code prompts:
1. "Implement database migrations from section 6.2"
2. "Create emotion detection service from section 7.6"
3. "Update mood logging endpoint to use emotion detection"
4. "Test emotion detection with 10 sample texts"

# Expected time: 4-6 hours
# Deliverable: Emotion detection working in mood logs
```

**Week 2: Chat Backend**
```bash
# Claude Code prompts:
1. "Create chat API endpoints from section 7.9.1"
2. "Implement context loading (student data → GPT-4)"
3. "Add conversation management (save/load messages)"
4. "Test chat API with Postman/curl"

# Expected time: 6-8 hours
# Deliverable: Chat API returning context-aware responses
```

**Week 3: Chat Frontend**
```bash
# Claude Code prompts:
1. "Create SmartStudyChat.jsx component from section 7.9.1"
2. "Add suggested prompts for new users"
3. "Implement real-time message updates"
4. "Style with navy/stone palette matching existing UI"

# Expected time: 4-6 hours
# Deliverable: Functional chat interface
```

**Week 4: Integration**
```bash
# Claude Code prompts:
1. "Add SmartStudy prompts throughout app (section 7.9.7)"
2. "Create SmartStudy hub page with tabs (Chat/Plans/Progress)"
3. "Test complete user flow: struggle → prompt → chat → help"
4. "Deploy to staging for user testing"

# Expected time: 6-8 hours
# Deliverable: End-to-end SmartStudy chat working
```

---

## 🧪 Testing Checklist

After each implementation step, verify:

**Database:**
- [ ] New tables exist in database
- [ ] Foreign keys are correct
- [ ] Can insert/query test data
- [ ] Migration is reversible

**Emotion Detection:**
- [ ] Model loads successfully (~30 seconds first time)
- [ ] Returns 7 emotions with scores
- [ ] Primary emotion is correct (test with obvious examples)
- [ ] Performance acceptable (<2 seconds per analysis)

**Chat API:**
- [ ] Endpoint returns 200 OK
- [ ] Response includes student context
- [ ] GPT-4 responses are personalized
- [ ] Conversation history persists
- [ ] Error handling works (bad input, API failures)

**Chat UI:**
- [ ] Messages display correctly
- [ ] Input/send works
- [ ] Loading states show during API calls
- [ ] Scrolls to latest message
- [ ] Suggested prompts clickable
- [ ] Mobile responsive

**Integration:**
- [ ] SmartStudy prompts show when appropriate
- [ ] Links navigate to chat correctly
- [ ] Chat pre-fills context when triggered from specific task
- [ ] Styling matches rest of app

---

## 💡 Pro Tips for Claude Code

### 1. **Be Specific About Context**

❌ Bad prompt:
```
"Add SmartStudy to Shadow"
```

✅ Good prompt:
```
"Read docs/SHADOW_SPECIFICATION_V2.md section 7.9.1. I have Shadow v1.0 with 
auth, courses, and tasks working. Add the interactive chat feature with GPT-4. 
Use my existing API client pattern in frontend/src/services/api.js."
```

### 2. **Request Incremental Progress**

❌ Bad approach:
```
"Build entire SmartStudy system"
```

✅ Good approach:
```
"Let's build SmartStudy in stages:
1. First, show me the database migration
2. Then create the emotion detection service
3. Then build the chat API
4. Finally, create the UI component

Show me each piece before moving to the next."
```

### 3. **Reference Existing Code**

```
"Look at my existing MoodLogger.jsx component in frontend/src/components/ 
and create SmartStudyChat.jsx using the same styling patterns (navy/stone 
colors, rounded-xl cards, teal accent for SmartStudy)."
```

### 4. **Ask for Tests**

```
"After implementing the chat API, create test cases for:
- Empty messages
- Very long messages (>1000 chars)
- API key missing
- GPT-4 timeout
- Context loading errors

Use pytest and show me the test file."
```

### 5. **Request Documentation**

```
"After completing the chat feature, generate:
1. API documentation for the SmartStudy endpoints
2. Component usage guide for SmartStudyChat.jsx
3. Deployment notes (env vars, model download)

Add this to docs/smartstudy/ folder."
```

---

## 🐛 Common Issues & Solutions

### Issue 1: Emotion Model Download Fails

**Symptoms**: `OSError: Can't load model...`

**Solution**:
```bash
# Manual download
python -c "
from transformers import AutoTokenizer, AutoModelForSequenceClassification
model = AutoModelForSequenceClassification.from_pretrained('j-hartmann/emotion-english-distilroberta-base')
tokenizer = AutoTokenizer.from_pretrained('j-hartmann/emotion-english-distilroberta-base')
print('Model downloaded successfully!')
"
```

### Issue 2: OpenAI API Key Not Working

**Symptoms**: `openai.error.AuthenticationError`

**Solution**:
```bash
# Verify key is set
echo $OPENAI_API_KEY  # Should show sk-...

# Test key manually
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"Hello"}]}'
```

### Issue 3: Database Migration Fails

**Symptoms**: `alembic.util.exc.CommandError`

**Solution**:
```bash
# Check current migration state
alembic current

# Show pending migrations
alembic history

# If stuck, manually rollback
alembic downgrade -1

# Then retry
alembic upgrade head
```

### Issue 4: Frontend Can't Reach Backend

**Symptoms**: `Network Error` in browser console

**Solution**:
```bash
# Check backend is running
curl http://localhost:8000/api/v1/health

# Check CORS settings in backend/app/main.py
# Should include:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Success Metrics

After implementing Phase 1, you should have:

- ✅ Chat interface accessible at `/smartstudy`
- ✅ GPT-4 responds with personalized context
- ✅ Emotion detection working in mood logs
- ✅ SmartStudy prompts appear when student struggles
- ✅ Conversations persist across sessions
- ✅ Cost tracking implemented (< ₦10,000/month in testing)

**Test with 5 students** and collect feedback on:
1. Response quality (personalization)
2. UI/UX (ease of use)
3. Performance (response time)
4. Bugs found

---

## 📚 Additional Resources

**Documentation:**
- OpenAI API Docs: https://platform.openai.com/docs
- Transformers Library: https://huggingface.co/docs/transformers
- YouTube Data API: https://developers.google.com/youtube/v3

**Monitoring:**
- Track OpenAI costs: https://platform.openai.com/usage
- Monitor API performance: Use backend logs
- User feedback: Add feedback button in chat

**Community:**
- HuggingFace Forums: https://discuss.huggingface.co/
- FastAPI Discord: https://discord.gg/fastapi
- React Discord: https://discord.gg/react

---

## 🎓 Next Steps After Phase 1

Once chat is working:

1. **Phase 2 (Week 5-8)**: Automated study plans
   - Prompt: "Read section 7.9.2 and implement study plan generation"
   
2. **Phase 3 (Week 9-12)**: Content curation & effectiveness
   - Prompt: "Read section 7.9.3 and implement CrowdCurate"
   
3. **Phase 4 (Month 4-6)**: Beta testing & refinement
   - Deploy to 20-30 PAU students
   - Collect effectiveness data
   - Prepare defense materials

---

**Good luck! Claude Code + this spec = Powerful combination 🚀**

**Questions?** Check the full specification in `docs/SHADOW_SPECIFICATION_V2.md`
