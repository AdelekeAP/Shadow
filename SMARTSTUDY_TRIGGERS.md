# SmartStudy Trigger System

## Overview
The SmartStudy Trigger System automatically recommends the SmartStudy AI learning coach to students based on their academic performance, emotional state, and task management patterns. The system uses 8 intelligent detection criteria with urgency levels to provide timely interventions.

## Architecture

### Backend Components
- **Service**: `backend/app/services/smartstudy_service.py::check_smartstudy_triggers()`
- **API Endpoints**:
  - `/api/v1/smartstudy/triggers` - Full trigger data with all criteria
  - `/api/v1/smartstudy/dashboard-trigger` - Legacy endpoint for primary trigger only

### Frontend Components
- **Banner Component**: `frontend/src/components/SmartStudyTriggerBanner.jsx`
- **Integration**: Displayed on `DashboardPage.jsx`

## Trigger Types & Criteria

### 1. **Overdue Tasks** (High Urgency)
- **Condition**: 2+ overdue assignments
- **Icon**: ⚠️
- **Message**: "You have X overdue tasks. Let SmartStudy help you prioritize and catch up."
- **Suggested Prompt**: "I have X overdue tasks. How should I tackle them?"

### 2. **CGPA Gap** (Medium/High/Critical Urgency)
- **Condition**:
  - Critical: >0.5 gap from target CGPA
  - High: >0.3 gap from target CGPA
  - Medium: >0.1 gap from target CGPA
- **Icon**: 📉
- **Message**: "You're X.XX points below your target CGPA. SmartStudy can help create a personalized plan."
- **Suggested Prompt**: "I'm behind on my CGPA goal. What's the best strategy to improve?"

### 3. **Negative Mood Patterns** (High Urgency)
- **Condition**: 2+ recent moods with anxiety/fear/sadness/stress/overwhelm (last 3 mood logs)
- **Icon**: 😰
- **Message**: "You seem to be feeling stressed lately. SmartStudy can provide personalized support."
- **Suggested Prompt**: "I'm feeling overwhelmed with my workload. Can you help?"

### 4. **Low Energy Levels** (Medium Urgency)
- **Condition**: 2+ recent moods with energy level ≤2 (out of 5)
- **Icon**: 🔋
- **Message**: "Your energy levels have been low. Let SmartStudy suggest optimized study techniques."
- **Suggested Prompt**: "I'm low on energy. How can I study effectively?"

### 5. **Task Overload** (Medium Urgency)
- **Condition**: 8+ pending/incomplete tasks
- **Icon**: 📚
- **Message**: "X pending tasks detected. SmartStudy can help you prioritize based on deadlines and CGPA impact."
- **Suggested Prompt**: "I have X tasks. What should I focus on first?"

### 6. **Low-Performing Courses** (High Urgency)
- **Condition**:
  - Predicted grade is D/E/F, OR
  - CA score <15/35
- **Icon**: 📕
- **Message**: "Struggling in X course(s). Get targeted help for [course names]."
- **Suggested Prompt**: "I'm struggling with [courses]. What should I do?"

### 7. **Late Submission Pattern** (Medium Urgency)
- **Condition**: 3+ late submissions
- **Icon**: ⏰
- **Message**: "X late submissions detected. SmartStudy can help you build better time management habits."
- **Suggested Prompt**: "I keep submitting tasks late. How can I improve my time management?"

### 8. **New User Welcome** (Low Urgency)
- **Condition**:
  - No SmartStudy chat history, AND
  - (3+ incomplete tasks OR any CGPA gap)
- **Icon**: 🎓
- **Message**: "Welcome to SmartStudy! Get AI-powered help with your courses, tasks, and study planning."
- **Suggested Prompt**: "What can SmartStudy help me with?"

## Urgency Levels

### Critical
- **Color**: Red gradient (`from-red-600 to-red-700`)
- **Behavior**: Pulsing animation
- **Badge**: "🔥 Urgent"
- **Use Cases**: CGPA gap >0.5

### High
- **Color**: Orange gradient (`from-orange-600 to-orange-700`)
- **Behavior**: Static
- **Badge**: "⚡ Important"
- **Use Cases**: Overdue tasks, negative moods, low grades

### Medium
- **Color**: Yellow gradient (`from-yellow-500 to-yellow-600`)
- **Behavior**: Static
- **Text Color**: Dark (stone-900)
- **Use Cases**: Low energy, task overload, late patterns

### Low
- **Color**: Blue gradient (`from-blue-500 to-blue-600`)
- **Behavior**: Static
- **Extra Button**: "Maybe later" dismiss option
- **Use Cases**: New user welcome

## User Experience

### Banner Display
1. **Auto-display**: Banner appears automatically on dashboard if any triggers are active
2. **Session-based dismissal**: Users can dismiss for current session (stored in sessionStorage)
3. **Multiple triggers**: If >1 trigger, shows primary + count of additional areas
4. **View all**: Users can click to see all triggered areas

### Interactions
- **Talk to SmartStudy**: Opens SmartStudyChat with suggested prompt pre-filled (TODO)
- **Dismiss (X)**: Hides banner for current session
- **Maybe later**: Available only for low-urgency triggers

### Visual Hierarchy
- **Critical/High**: Prominent with bold colors, pulsing animation
- **Medium**: Visible but less alarming
- **Low**: Gentle blue gradient, easily dismissible

## API Response Format

```json
{
  "should_trigger": true,
  "urgency": "high",
  "trigger_count": 3,
  "primary_trigger": {
    "type": "overdue_tasks",
    "title": "You have 5 overdue tasks",
    "message": "Let SmartStudy help you prioritize and catch up on your 5 overdue assignments.",
    "urgency": "high",
    "icon": "⚠️",
    "suggested_prompt": "I have 5 overdue tasks. How should I tackle them?"
  },
  "triggers": [
    // Array of all active triggers
  ]
}
```

## Implementation Details

### Backend Logic Flow
1. Load student context (courses, tasks, moods, CGPA)
2. Iterate through 8 trigger criteria
3. For each matched criterion, add trigger object to array
4. Track highest urgency level
5. Return consolidated trigger data

### Frontend Logic Flow
1. On dashboard mount, fetch `/api/v1/smartstudy/triggers`
2. Check sessionStorage for dismissal
3. If `should_trigger` is true and not dismissed, render banner
4. Apply urgency-based styling
5. Handle user interactions (dismiss, open chat)

## Future Enhancements

### Phase 2 (Planned)
- [ ] Auto-fill suggested prompt in SmartStudyChat when opened from banner
- [ ] Trigger history tracking (show dismissed triggers in settings)
- [ ] Personalized trigger thresholds (e.g., user sets own CGPA gap threshold)
- [ ] Email/push notifications for critical triggers
- [ ] Success stories after resolving triggers (positive reinforcement)

### Phase 3 (Ideas)
- [ ] Machine learning to optimize trigger thresholds per student
- [ ] A/B testing for trigger messaging effectiveness
- [ ] Integration with calendar for time-based triggers (exam week)
- [ ] Peer comparison triggers (anonymized, opt-in)

## Testing Scenarios

### Test Case 1: Overdue Tasks Trigger
1. Create 2+ tasks with past due dates
2. Mark as incomplete
3. Visit dashboard
4. **Expected**: High urgency orange banner with overdue task count

### Test Case 2: CGPA Gap Trigger
1. Set target CGPA to 4.5
2. Set current CGPA to 3.8 (0.7 gap)
3. Visit dashboard
4. **Expected**: Critical red pulsing banner

### Test Case 3: Negative Mood Trigger
1. Log 2+ moods with "anxiety" or "stress" emotion
2. Visit dashboard
3. **Expected**: High urgency orange banner about stress

### Test Case 4: Multiple Triggers
1. Meet criteria for 3+ triggers
2. Visit dashboard
3. **Expected**: Banner shows primary trigger + "+2 more areas need attention"

### Test Case 5: Dismissal
1. Trigger active on dashboard
2. Click X to dismiss
3. Refresh page (same session)
4. **Expected**: Banner stays hidden
5. Open new browser tab
6. **Expected**: Banner reappears (new session)

## Performance Considerations

- **Database Queries**: Single context load retrieves all necessary data
- **Caching**: Consider adding 5-minute cache for trigger checks (user context unlikely to change frequently)
- **Frontend**: Banner only renders if `should_trigger` is true (no unnecessary DOM)

## Analytics Metrics (Future)

Track the following to measure effectiveness:
- Trigger activation rate by type
- User engagement rate (% who click "Talk to SmartStudy")
- Dismissal rate by urgency level
- Time to resolution (when trigger condition is resolved)
- CGPA improvement correlation with trigger engagement

---

**Last Updated**: 2025-11-26
**Status**: ✅ Implemented and tested
**Next Steps**: Auto-fill suggested prompts in SmartStudyChat
