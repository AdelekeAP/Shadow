# 🎨 SmartStudy Frontend - Testing Guide

## ✅ What's Been Implemented

### Frontend Components Created:
1. **SmartStudyChat.jsx** - Full-featured AI chat interface
   - Navy/stone design system matching existing UI
   - Suggested prompts loading from backend
   - Message history with user/AI styling
   - Auto-scroll to new messages
   - Loading states with animated dots
   - New conversation functionality
   - Token usage display

2. **Dashboard Integration** - Trigger banner and modal
   - Smart trigger detection on page load
   - Animated banner with navy gradient
   - Dismissable trigger alert
   - Modal chat integration

### API Service Functions:
All 7 SmartStudy API functions added to `frontend/src/services/api.js`:
- `sendSmartStudyMessage(content, conversationId)`
- `getSmartStudyConversations(limit)`
- `getSmartStudyConversation(conversationId)`
- `deleteSmartStudyConversation(conversationId)`
- `getSmartStudySuggestedPrompts()`
- `getSmartStudyDashboardTrigger()`
- `getSmartStudyContext()`

---

## 🚀 How to Test

### Step 1: Start the Backend

```bash
cd /Users/useruser/Documents/shadow-final-year/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
✅ OpenAI client initialized successfully
```

**If emotion detection fails** (network issues):
```
❌ Failed to load emotion analysis model
```
This is OK - the backend still works! Emotion detection will retry automatically when internet is available.

### Step 2: Start the Frontend

```bash
cd /Users/useruser/Documents/shadow-final-year/frontend
npm run dev
```

**Expected output:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
```

### Step 3: Login & Navigate to Dashboard

1. Open browser: `http://localhost:3000`
2. Login with your test credentials
3. You should see the Dashboard

---

## 🧪 Testing Checklist

### Test 1: Dashboard Trigger Banner
**Goal:** Verify SmartStudy trigger banner appears for struggling students

**Steps:**
1. Navigate to Dashboard
2. Check if trigger banner appears below the main heading

**Expected Behavior:**
- If you have low CGPA, overdue tasks, or recent negative moods → Banner shows
- Banner has navy gradient background with robot icon 🤖
- Shows reason badge (e.g., "Low CGPA", "Overdue Tasks")
- "Chat with SmartStudy" button is visible
- Dismiss (X) button works

**What to look for:**
- Navy gradient: `from-navy-600 to-navy-700`
- Amber reason badge
- White button with navy text
- Smooth `animate-scale-in` entrance
- Banner disappears when dismissed

### Test 2: Open SmartStudy Chat
**Goal:** Verify chat modal opens and loads properly

**Steps:**
1. Click "💬 Chat with SmartStudy" button (from banner or anywhere)
2. Modal should appear

**Expected Behavior:**
- Modal covers entire screen with backdrop blur
- Navy header with "SmartStudy AI" title
- Robot icon 🤖 in header
- Welcome message with 🎓 emoji
- Suggested prompts load automatically (grid of 2 columns on desktop)
- Input box at bottom with "Send" button

**What to look for:**
- Backdrop: `bg-stone-900/40 backdrop-blur-sm`
- Header: `bg-gradient-to-r from-navy-800 to-navy-700`
- Rounded corners: `rounded-2xl`
- Suggested prompts have icons and categories

### Test 3: Send Your First Message
**Goal:** Test actual GPT-4 chat interaction

**Steps:**
1. Type a message like "Help me understand algorithms"
2. Click "Send"
3. Wait for response

**Expected Behavior:**
- User message appears on the right in navy bubble
- Loading indicator shows (3 bouncing dots)
- AI response appears on the left in white bubble with border
- AI message has 🤖 icon and "SmartStudy AI" label
- Token count shows at bottom of AI message
- Auto-scrolls to new messages

**What to look for:**
- User bubble: `bg-navy-600 text-white`
- AI bubble: `bg-white text-stone-800 border-2 border-stone-200`
- Loading dots: 3 navy dots bouncing with staggered delays
- Response should reference your actual courses/tasks if you have any

### Test 4: Try Suggested Prompts
**Goal:** Test pre-built prompt interactions

**Steps:**
1. Open fresh chat (or click "✨ New Chat")
2. Click one of the suggested prompt cards

**Expected Behavior:**
- Prompt text automatically sent as your message
- Suggested prompts disappear after first message
- AI responds with contextual answer based on YOUR data

**What to look for:**
- Prompt cards have hover effects: `hover:border-navy-400 hover:bg-navy-50`
- Icons scale on hover: `group-hover:scale-110`
- Response is personalized (mentions your courses, CGPA, etc.)

### Test 5: New Conversation
**Goal:** Test conversation reset functionality

**Steps:**
1. Send a few messages
2. Click "✨ New Chat" button in header
3. Observe reset

**Expected Behavior:**
- All messages clear
- Welcome screen returns
- Suggested prompts reload
- New conversation ID generated on next message

### Test 6: Close and Reopen
**Goal:** Test modal state persistence

**Steps:**
1. Send some messages
2. Click X to close modal
3. Reopen chat (from trigger banner or button)

**Expected Behavior:**
- Modal closes smoothly
- **Current behavior:** Messages are lost (conversation isn't stored in state)
- **Future enhancement:** Could implement conversation persistence

### Test 7: API Error Handling
**Goal:** Test graceful error handling

**Steps:**
1. Stop the backend server
2. Try to send a message

**Expected Behavior:**
- Loading indicator shows
- Error message appears in red bubble:
  - "Sorry, I encountered an error. Please try again."
  - Red border and background

**What to look for:**
- Error bubble: `bg-red-100 text-red-800 border-2 border-red-300`
- No crash - UI remains functional

### Test 8: Responsive Design
**Goal:** Test mobile/tablet layouts

**Steps:**
1. Resize browser to mobile width (< 768px)
2. Open SmartStudy chat

**Expected Behavior:**
- Modal adapts to screen size
- Suggested prompts stack in single column
- Messages remain readable
- Input box stays accessible

---

## 🎯 Advanced Testing Scenarios

### Scenario 1: Student Struggling with CGPA
**Setup:** Have current_cgpa < target_cgpa
**Expected:**
- Trigger banner shows with "Low CGPA" reason
- Suggested prompts include CGPA-related advice
- AI responses are empathetic and goal-focused

### Scenario 2: Student with Overdue Tasks
**Setup:** Have tasks with deadline_date < today and is_completed = false
**Expected:**
- Trigger shows with "Overdue Tasks" reason
- Suggested prompts include task prioritization
- AI helps prioritize by CGPA impact

### Scenario 3: Student with Negative Mood
**Setup:** Log a "stressed" or "anxious" mood
**Expected:**
- Trigger shows with "Mood Check" reason
- AI responds with shorter, reassuring messages
- Suggested prompts include motivation/wellness

### Scenario 4: All Clear Student
**Setup:** Good CGPA, no overdue tasks, positive mood
**Expected:**
- No trigger banner shows
- Can still manually open chat
- AI gives proactive improvement suggestions

---

## 🐛 Common Issues & Solutions

### Issue 1: "Access token not found" error
**Cause:** Not logged in or token expired
**Fix:** Login again

### Issue 2: Suggested prompts not loading
**Cause:** Backend API not running or no enrolled courses
**Check:**
- Backend running at http://localhost:8000
- User has enrolled courses in database
- Check browser console for API errors

### Issue 3: GPT-4 responses very slow
**Cause:** Normal - GPT-4 can take 5-10 seconds
**Note:** This is expected behavior, not a bug

### Issue 4: Trigger banner doesn't show
**Cause:** Student is doing well (no struggles detected)
**Fix:** This is correct behavior! Trigger only shows when help is needed
**To test:** Manually set current_cgpa < target_cgpa in database

### Issue 5: Network error when loading emotion model
**Cause:** No internet or HuggingFace unreachable
**Fix:** Backend still works! Just run with internet connection once to download model

---

## 🎨 Design System Verification

### Colors Used:
- **Navy Scale:** navy-50 through navy-900 (primary brand)
- **Stone Scale:** stone-50 through stone-900 (neutrals)
- **Amber:** For alerts/warnings (trigger badge)
- **Emerald:** For success states
- **Red:** For errors

### UI Patterns:
- **Rounded Corners:** `rounded-2xl` (16px) for all major cards/modals
- **Backdrop:** `bg-stone-900/40 backdrop-blur-sm` for overlays
- **Shadows:** `shadow-lg`, `shadow-xl` for depth
- **Animations:** `animate-scale-in`, `animate-bounce` for micro-interactions
- **Transitions:** `transition-all duration-200` for smooth hover states

### Typography:
- **Headings:** `font-bold` with navy-800 or white
- **Body:** `text-stone-600` or `text-stone-700`
- **Small text:** `text-sm` or `text-xs` for secondary info

---

## 📊 Success Metrics

Your implementation is successful if:

1. ✅ Chat modal opens without errors
2. ✅ Suggested prompts load from backend
3. ✅ Messages send and receive responses
4. ✅ AI responses reference your actual data (courses, CGPA, tasks)
5. ✅ Trigger banner shows for struggling students
6. ✅ UI matches navy/stone design system
7. ✅ No console errors (except emotion model download if offline)
8. ✅ Responsive design works on mobile

---

## 🚀 Next Steps After Testing

Once basic functionality works:

1. **Add Conversation History** - Load previous conversations in sidebar
2. **Add Voice Input** - Integrate Whisper API for voice messages
3. **Add File Upload** - Let students upload notes/assignments for AI analysis
4. **Add Study Plans** - Display generated study plans in dashboard
5. **Add Intervention Tracking** - Show effectiveness of AI recommendations

---

## 💡 Pro Testing Tips

1. **Use Browser DevTools:**
   - Open Network tab to see API calls
   - Check Console for React warnings
   - Use React DevTools to inspect component state

2. **Test with Real Data:**
   - Create courses with real topics
   - Add tasks with actual deadlines
   - Log genuine moods
   - This makes AI responses more relevant

3. **Test Edge Cases:**
   - Send empty messages (should be blocked)
   - Send very long messages (500+ words)
   - Rapid-fire multiple messages
   - Close modal while message is sending

4. **Monitor API Costs:**
   - Check OpenAI dashboard after testing
   - Each chat turn costs ~$0.03-0.05
   - Context loading adds ~500-800 tokens per request

---

**Your SmartStudy v2.0 frontend is now complete and ready for testing!** 🎓✨

Let me know if you encounter any issues during testing.
