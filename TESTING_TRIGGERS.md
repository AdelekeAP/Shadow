# 🧪 Testing SmartStudy Trigger System

## ✅ Servers Running

**Backend**: http://localhost:8000
**Frontend**: http://localhost:3000

---

## 📍 Where to Test

### Open in your browser:
```
http://localhost:3000
```

1. **Login** with your test account
2. Go to the **Dashboard** (should load automatically)
3. Look for the **SmartStudy Trigger Banner** at the top of the dashboard (below the welcome message)

---

## 🎯 Test Scenarios

### Scenario 1: Test the Trigger Detection

**Option A: Direct API Test**
Open this URL in your browser (while logged in):
```
http://localhost:8000/api/v1/smartstudy/triggers
```

This will show you the raw JSON response with all active triggers.

**Option B: View on Dashboard**
Just visit http://localhost:3000 and the banner will appear automatically if any triggers are active.

---

### Scenario 2: Create Trigger Conditions

To see different triggers, you need to create the conditions:

#### 🟧 Trigger: Overdue Tasks (High Priority - Orange)
1. Go to Dashboard
2. Click **"+ Add Task"**
3. Create a task with:
   - Due date: **Yesterday** (or any past date)
   - Leave it **uncompleted**
4. Create another overdue task (need 2+ for trigger)
5. Refresh dashboard
6. **Expected**: Orange banner saying "You have 2 overdue tasks"

#### 🟥 Trigger: CGPA Gap (Critical - Red Pulsing)
1. Go to **CGPA Analytics** page
2. Check if your current CGPA is significantly below target (>0.5 gap)
3. If not, you can modify in database OR just test other triggers
4. **Expected**: Red pulsing banner saying "You're X.XX points below target"

#### 🟧 Trigger: Negative Mood (High Priority - Orange)
1. Click on the **Mood Logger** (usually in header or dashboard)
2. Log a mood with:
   - Emotion: **Anxiety** or **Stress**
   - Energy: Any level
3. Log another negative mood
4. Refresh dashboard
5. **Expected**: Orange banner saying "You seem to be feeling stressed lately"

#### 🟨 Trigger: Task Overload (Medium Priority - Yellow)
1. Create **8+ incomplete tasks**
2. Refresh dashboard
3. **Expected**: Yellow banner saying "X pending tasks detected"

#### 🟨 Trigger: Low Energy (Medium Priority - Yellow)
1. Log 2+ moods with **Energy Level = 1 or 2** (out of 5)
2. Refresh dashboard
3. **Expected**: Yellow banner saying "Your energy levels have been low"

---

## 🎨 What to Look For

### Banner Appearance
The banner should appear **between the dashboard header and CGPA overview card**.

### Urgency Styling
- **🟥 Critical**: Red gradient, pulsing animation, "🔥 Urgent" badge
- **🟧 High**: Orange gradient, "⚡ Important" badge
- **🟨 Medium**: Yellow gradient, black text
- **🟦 Low**: Blue gradient

### Interactions to Test

1. **Talk to SmartStudy Button**
   - Click the main action button
   - SmartStudy chat should open
   - (TODO: Suggested prompt should pre-fill)

2. **Dismiss (X) Button**
   - Click the X in top-right of banner
   - Banner should disappear
   - Refresh page → Banner should **stay hidden** (same session)
   - Open new browser tab → Banner should **reappear** (new session)

3. **View All Triggers** (if multiple)
   - If 2+ triggers are active, you'll see "+X more areas need attention"
   - Click "View all"
   - Should show alert with all trigger titles
   - (TODO: Make this a nicer modal in future)

---

## 🔍 Debugging

### If Banner Doesn't Appear

1. **Check Console**
   - Open browser DevTools (F12)
   - Go to Console tab
   - Look for errors from `SmartStudyTriggerBanner.jsx`

2. **Check API Response**
   - Open browser DevTools
   - Go to Network tab
   - Look for `/api/v1/smartstudy/triggers`
   - Check if `should_trigger: true` in response

3. **Check Session Storage**
   - DevTools → Application tab → Session Storage
   - Look for `smartstudy_dismissed`
   - If it exists, delete it to show banner again

### If Triggers Aren't Detecting

Open terminal and test the backend directly:

```bash
# Test trigger detection for a specific user
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/smartstudy/triggers
```

---

## 📊 Expected Behavior Summary

| Trigger Type | Condition | Urgency | Color | Animation |
|--------------|-----------|---------|-------|-----------|
| Overdue Tasks | 2+ overdue | High | Orange | Static |
| CGPA Gap (>0.5) | 0.5+ gap | Critical | Red | Pulsing |
| CGPA Gap (>0.3) | 0.3-0.5 gap | High | Orange | Static |
| CGPA Gap (>0.1) | 0.1-0.3 gap | Medium | Yellow | Static |
| Negative Mood | 2+ stressed moods | High | Orange | Static |
| Low Energy | 2+ low energy moods | Medium | Yellow | Static |
| Task Overload | 8+ pending tasks | Medium | Yellow | Static |
| Low Grades | D/E/F or CA <15 | High | Orange | Static |
| Late Pattern | 3+ late submissions | Medium | Yellow | Static |
| New User | No chat history + tasks | Low | Blue | Static |

---

## 🐛 Known Issues / TODOs

1. **Suggested Prompt Auto-Fill**: Currently doesn't pre-fill the chat input when you click "Talk to SmartStudy" from banner
   - **Fix**: Pass `suggestedPrompt` to `SmartStudyChat` component

2. **View All Modal**: Currently uses browser `alert()` - should be a nice modal

3. **Token Display in Chat**: Currently shows tokens used - you mentioned hiding this (design preference)

---

## ✅ Quick Test Checklist

- [ ] Backend running (http://localhost:8000)
- [ ] Frontend running (http://localhost:3000)
- [ ] Can login successfully
- [ ] Dashboard loads
- [ ] Create 2 overdue tasks
- [ ] Banner appears with correct styling
- [ ] "Talk to SmartStudy" button works
- [ ] Dismiss (X) works and persists in session
- [ ] Banner reappears in new tab
- [ ] Multiple triggers show "+X more" indicator

---

## 🎉 Success Criteria

The trigger system is working if:
1. ✅ Banner appears when conditions are met
2. ✅ Urgency levels show correct colors/animations
3. ✅ Dismissal works (session-based)
4. ✅ Clicking action button opens SmartStudy chat
5. ✅ Multiple triggers aggregate correctly

---

**Ready to test!** Open http://localhost:3000 in your browser and try creating some overdue tasks! 🚀
