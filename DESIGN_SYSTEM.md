# 🎨 Shadow - UI/UX Design System Documentation

**Version**: 1.0
**Last Updated**: November 19, 2025
**Framework**: React + Vite + TailwindCSS

---

## 📋 Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Color System](#color-system)
3. [Typography](#typography)
4. [Component Library](#component-library)
5. [Page Layouts](#page-layouts)
6. [Interactive Elements](#interactive-elements)
7. [User Flows](#user-flows)
8. [Responsive Breakpoints](#responsive-breakpoints)
9. [Animation & Transitions](#animation--transitions)
10. [Accessibility](#accessibility)
11. [Design Patterns](#design-patterns)
12. [Improvement Areas](#improvement-areas)

---

## 🎯 Design Philosophy

### Core Principles

**1. Goal-Oriented & Action-First**
- Every screen shows what the user needs to do next
- Minimize informational clutter, maximize actionable guidance
- CTAs are clear, prominent, and contextual

**2. Academic Professionalism with Warmth**
- Clean, organized layouts reflecting academic rigor
- Warm colors (indigo, purple) to reduce stress
- Emojis used sparingly for quick visual cues

**3. Progressive Disclosure**
- Complex data hidden behind expandable sections
- Dashboard shows overview, details on-demand
- Modals for focused tasks (mood logging, task creation)

**4. Data-Driven Feedback**
- Visual progress indicators (CGPA bars, completion percentages)
- Real-time calculations (grade predictions)
- Contextual alerts based on user state

---

## 🎨 Color System

### Primary Palette

```css
/* Brand Colors */
--primary-indigo: #4F46E5      /* Primary CTA, links */
--primary-purple: #7C3AED       /* Accent, gradients */
--gradient-primary: linear-gradient(to right, #4F46E5, #7C3AED)

/* Background Colors */
--bg-light: #F9FAFB            /* Page background */
--bg-card: #FFFFFF             /* Card backgrounds */
--bg-hover: #F3F4F6            /* Hover states */

/* Text Colors */
--text-primary: #111827        /* Headings, important text */
--text-secondary: #6B7280      /* Body text, descriptions */
--text-muted: #9CA3AF          /* Subtle text, labels */

/* Border Colors */
--border-light: #E5E7EB        /* Dividers, card borders */
--border-medium: #D1D5DB       /* Input borders */
```

### Semantic Colors

```css
/* Status Colors */
--success-green: #10B981       /* Completed tasks, positive feedback */
--warning-yellow: #F59E0B      /* Warnings, approaching deadlines */
--error-red: #EF4444           /* Errors, overdue tasks */
--info-blue: #3B82F6           /* Informational messages */

/* Mood-Specific Colors (from MoodLogger) */
--mood-focused: #3B82F6        /* Blue - focused */
--mood-motivated: #10B981      /* Green - motivated */
--mood-calm: #14B8A6           /* Teal - calm */
--mood-confident: #8B5CF6      /* Purple - confident */
--mood-tired: #6B7280          /* Gray - tired */
--mood-stressed: #F97316       /* Orange - stressed */
--mood-anxious: #EAB308        /* Yellow - anxious */
--mood-overwhelmed: #EF4444    /* Red - overwhelmed */
```

### Energy Level Colors

```css
/* Energy Scale (1-5) */
--energy-1: #EF4444            /* Very Low - red */
--energy-2: #F97316            /* Low - orange */
--energy-3: #EAB308            /* Medium - yellow */
--energy-4: #10B981            /* High - green */
--energy-5: #3B82F6            /* Very High - blue */
```

---

## ✍️ Typography

### Font Family

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

### Type Scale

```css
/* Headings */
--h1: 36px / 700     /* Page titles */
--h2: 30px / 700     /* Section titles */
--h3: 24px / 600     /* Card titles */
--h4: 20px / 600     /* Subsection titles */
--h5: 18px / 600     /* Component headers */

/* Body */
--body-lg: 18px / 400    /* Large body text */
--body: 16px / 400       /* Standard body text */
--body-sm: 14px / 400    /* Small body text */
--caption: 12px / 400    /* Captions, labels */

/* Special */
--mono: 'Courier New', monospace   /* Code, data */
```

### Line Height

```css
--leading-tight: 1.25
--leading-normal: 1.5
--leading-relaxed: 1.75
```

---

## 🧩 Component Library

### 1. **Authentication Pages**

#### LoginPage.jsx
```
Layout: Centered card on gradient background
- Logo/brand area (top)
- Welcome heading
- Email input (with validation styling)
- Password input (with show/hide toggle)
- Primary CTA button (full-width gradient)
- Link to register page
- "Remember me" checkbox
- Forgot password link

Design Details:
- Card: White, rounded-2xl, shadow-2xl, max-w-md
- Inputs: border-2, focus:border-indigo-500, focus:ring-2
- Button: bg-gradient-to-r from-indigo-600 to-purple-600
- Error states: Red border, red text below input
```

#### RegisterPage.jsx
```
Similar to Login with additional fields:
- Full name input
- University ID input
- Entry level select (100L, 200L, etc.)
- Target CGPA input (0.0 - 5.0 range)
- Terms acceptance checkbox
- Password confirmation field

Validation:
- Real-time password strength indicator
- Email format validation
- CGPA range validation (5.0 scale)
- Required field indicators (red asterisk)
```

---

### 2. **Dashboard Components**

#### DashboardPage.jsx

**Layout Structure:**
```
┌──────────────────────────────────────────────────────┐
│ Header: "Welcome, {Name}" + Date                     │
├──────────────────────────────────────────────────────┤
│ CGPA Overview Card (2-column grid)                   │
│  - Current CGPA (large, bold)                        │
│  - Target CGPA (with progress bar)                   │
│  - Gap indicator (+/- from target)                   │
├──────────────────────────────────────────────────────┤
│ Task Statistics (3-column grid)                      │
│  - Total Tasks                                       │
│  - Pending (yellow accent)                           │
│  - Completed (green accent)                          │
├──────────────────────────────────────────────────────┤
│ Priority Recommendations (PriorityRecommendations)   │
│  - Top 5 task cards                                  │
│  - Recommendation type badge                         │
│  - Due date indicator                                │
├──────────────────────────────────────────────────────┤
│ Upcoming Deadlines List                              │
│  - Next 7 days                                       │
│  - Urgency color coding                              │
├──────────────────────────────────────────────────────┤
│ Mood Logger (Floating Button - bottom right)         │
└──────────────────────────────────────────────────────┘
```

**CGPA Overview Card:**
- Background: White
- Border: 1px solid gray-200
- Padding: 6 (1.5rem)
- Shadow: shadow-md on hover
- Current CGPA: 48px font, bold, indigo-600
- Target CGPA: 24px font, semibold, gray-700
- Progress bar: Height 8px, gradient fill, rounded-full
- Gap indicator:
  - Positive: Green badge "↑ 0.5 above target"
  - Negative: Red badge "↓ 0.3 below target"

**Task Statistics Cards:**
- 3-column responsive grid
- Each card: bg-white, p-6, rounded-xl, border
- Icon: 48px emoji or SVG
- Number: 36px, bold, color-coded
- Label: 14px, gray-600
- Hover: shadow-lg, transform scale-105

---

### 3. **MoodLogger Component**

#### Closed State (Floating Button)
```css
Position: fixed, bottom-6, right-6, z-50
Style:
  - bg-gradient-to-r from-indigo-600 to-purple-600
  - text-white, px-6, py-3
  - rounded-full
  - shadow-lg, hover:shadow-xl
  - transform hover:scale-105
  - transition-all duration-200
Icon: 💭 emoji (text-xl)
Text: "Log Mood" (font-semibold)
```

#### Open State (Modal)
```
Full-screen overlay: bg-black/50
Modal card: max-w-md, bg-white, rounded-2xl, shadow-2xl, p-6

Header:
  - Title: "How are you feeling?" (text-2xl, font-bold)
  - Close button: × (text-2xl, text-gray-400, hover:text-gray-600)

Mood Selection Grid (2-column):
  - 8 mood buttons
  - Each: px-4 py-3, rounded-lg, border-2
  - Selected: colored background + border, shadow-md, scale-105
  - Unselected: bg-white, border-gray-200, hover:border-gray-300

Energy Level Slider:
  - 5 button segments (flex-1 each)
  - Height: 48px (h-12)
  - Selected: colored background (red→orange→yellow→green→blue)
  - Unselected: bg-gray-200, hover:bg-gray-300
  - Icon: emoji (🪫, 🔋, ⚡, 🔥, ⚡⚡)
  - Label below: "Very Low" ... "Very High" (text-xs)

Note Textarea:
  - Border: 2px, border-gray-200
  - Focus: border-indigo-500, ring-2, ring-indigo-200
  - Rows: 3
  - Max length: 500 chars
  - Character counter: text-xs, text-gray-500, text-right
  - Placeholder: "What's on your mind? (AI will analyze sentiment)"
  - Header: "Note (optional)" + "✨ AI-powered sentiment analysis" badge

Action Buttons (flex, gap-3):
  - Cancel: border-2, border-gray-300, text-gray-700, hover:bg-gray-50
  - Submit: bg-gradient-primary, text-white, hover:shadow-lg
  - Both: px-6, py-3, rounded-lg, font-semibold
  - Disabled state: opacity-50, cursor-not-allowed
```

**Mood Type Colors:**
- Focused: Blue-100 bg, blue-800 text, blue-300 border
- Motivated: Green-100/800/300
- Calm: Teal-100/800/300
- Confident: Purple-100/800/300
- Tired: Gray-100/800/300
- Stressed: Orange-100/800/300
- Anxious: Yellow-100/800/300
- Overwhelmed: Red-100/800/300

---

### 4. **PriorityRecommendations Component**

#### Container
```css
Background: white
Padding: p-6
Border-radius: rounded-xl
Border: border border-gray-200
Shadow: shadow-sm
```

#### Header Section
```
Title: "Priority Recommendations" (text-2xl, font-bold, gray-900)
Subtitle: "Top 5 tasks based on urgency, CGPA impact, and your mood"
         (text-sm, text-gray-600, mt-1)
```

#### Task Cards (Vertical Stack, gap-4)
```
Each card:
  - Border-left: 4px colored accent (type-based)
  - Background: bg-gray-50
  - Padding: p-4
  - Border-radius: rounded-lg
  - Hover: shadow-md, bg-white

Card Header:
  - Task title (font-semibold, text-gray-900)
  - Course code badge (text-xs, bg-indigo-100, text-indigo-800, px-2 py-1, rounded)

Card Body:
  - Recommendation type badge:
    - Urgent: bg-red-100, text-red-800, "🔴 URGENT"
    - Goal-driven: bg-blue-100, text-blue-800, "🎯 High Impact"
    - Mood-based: bg-purple-100, text-purple-800, "💜 Mood Match"
    - Recovery: bg-orange-100, text-orange-800, "⚠️ Recovery"

  - Due date: text-sm, text-gray-600, "Due: Nov 25, 2025"
  - Recommendation reason: text-sm, text-gray-700, italic
  - Priority score: text-xs, text-gray-500, "Score: 8.5/10"

Card Footer:
  - Action button: text-indigo-600, hover:text-indigo-800, "Mark Complete →"
```

**Border Colors by Type:**
- Urgent: border-red-500
- Goal-driven: border-blue-500
- Mood-based: border-purple-500
- Recovery: border-orange-500

---

### 5. **Course Cards (CourseCard.jsx)**

```
Card Layout:
  - Background: white
  - Padding: p-6
  - Border-radius: rounded-xl
  - Border: border-2, border-gray-200
  - Hover: shadow-lg, border-indigo-300
  - Cursor: pointer

Header:
  - Course code: text-sm, font-bold, text-indigo-600
  - Course title: text-lg, font-semibold, text-gray-900, mt-1

Body:
  - Credits: "3 Credits" (text-sm, text-gray-600)
  - Current grade: Large, bold, color-coded (A: green, B: blue, C: yellow, D: orange, F: red)
  - Grade point: text-sm, gray-600, "GPA: 4.50"

Progress Section:
  - Progress bar container: bg-gray-200, h-2, rounded-full
  - Progress fill: bg-gradient-primary, transition-all
  - Percentage text: text-xs, text-gray-600, "72% complete"

Footer:
  - Task summary: "5 pending tasks" (text-sm, gray-600)
  - View details link: text-indigo-600, hover:underline
```

---

### 6. **Task Management Components**

#### TaskList Component
```
Container: bg-white, rounded-xl, border, shadow-sm

Filter Tabs:
  - All / Pending / Completed
  - Border-bottom: 2px when active (indigo-600)
  - Text: gray-600 inactive, indigo-600 active
  - Padding: pb-2, px-4

Task Items:
  - Border-bottom: border-gray-100 (last child: none)
  - Padding: py-4, px-6
  - Hover: bg-gray-50

Task Item Layout:
  - Checkbox: w-5, h-5, rounded, border-gray-300, checked:bg-indigo-600
  - Title: text-base, font-medium, text-gray-900
  - Course badge: text-xs, bg-gray-100, text-gray-700, px-2, py-1, rounded
  - Due date: text-sm, text-gray-600, with urgency color
  - Weight: text-xs, text-gray-500, "30%"
  - Actions: Edit/Delete icons (text-gray-400, hover:text-gray-600)

Urgency Indicators:
  - Overdue: text-red-600, font-semibold, "⚠️ Overdue"
  - Due soon (< 48h): text-orange-600, "Due in 2 days"
  - Normal: text-gray-600, "Due Nov 30"
```

#### AddTaskModal / EditTaskModal
```
Modal Overlay: fixed, inset-0, bg-black/50, z-50

Modal Container:
  - max-w-lg, bg-white, rounded-2xl, shadow-2xl
  - p-6, m-4 (mobile margins)

Header:
  - Title: "Add New Task" / "Edit Task" (text-2xl, font-bold)
  - Close button: × (top-right)

Form Fields:
  - Label: text-sm, font-semibold, text-gray-700, mb-2
  - Input: w-full, px-4, py-2, border-2, border-gray-200
           focus:border-indigo-500, focus:ring-2, focus:ring-indigo-200
           rounded-lg, transition
  - Select dropdown: Same styling as input
  - Textarea: rows-3 for description

Field Groups:
  - Task Type: Dropdown (CA, Exam, Assignment, Project, Quiz, Participation)
  - Weight: Number input with % suffix
  - Max Marks: Number input
  - Due Date: Date picker input
  - Course: Dropdown of enrolled courses

Validation States:
  - Error: border-red-500, text-red-600 error message below
  - Required: Red asterisk after label
  - Success: border-green-500 (after validation)

Action Buttons:
  - Cancel: bg-gray-200, hover:bg-gray-300, text-gray-700
  - Save: bg-gradient-primary, text-white, hover:shadow-lg
  - Both: px-6, py-3, rounded-lg, font-semibold
```

---

### 7. **CGPA Dashboard (CGPADashboard.jsx)**

```
Grid Layout: 2-column on desktop, 1-column on mobile

Overall Summary Card:
  - Current CGPA: 72px font, bold, gradient text
  - Target CGPA: 36px font, semibold
  - Credits completed: text-lg, gray-600
  - Progress to target: Circular progress indicator

CGPA Breakdown Table:
  - Striped rows: even:bg-gray-50
  - Headers: bg-indigo-50, font-semibold, text-sm
  - Columns: Semester | Credits | GPA | Cumulative CGPA
  - Cell padding: px-6, py-4
  - Border: border-b, border-gray-200

Course Performance Grid:
  - Cards showing per-course predictions
  - Color-coded by grade (A→F)
  - Prediction vs. actual comparison
  - Progress bars for CA completion

Grade Distribution Chart:
  - Bar chart showing grade distribution
  - Color-coded bars (A: green, B: blue, C: yellow, etc.)
  - Hover tooltips with exact counts
```

---

## 📱 Page Layouts

### HomePage.jsx (Landing Page)

```
Hero Section:
  - Full viewport height
  - Gradient background (indigo to purple)
  - Center-aligned content
  - Heading: 48px, bold, white
  - Subtitle: 20px, white/80
  - CTA button: Large, white bg, indigo text, hover:shadow-2xl

Features Section:
  - 3-column grid (responsive)
  - Icon + Title + Description per feature
  - Icons: 64px emojis or SVG
  - Background: white with subtle patterns

How It Works:
  - Numbered steps (1, 2, 3, 4)
  - Visual flow diagram
  - Screenshot mockups
  - Alternating left/right layout

Testimonials:
  - Card carousel
  - Student photos (rounded-full)
  - Quote text
  - Star ratings

CTA Footer:
  - Gradient background
  - "Get Started" button
  - Links to register/login
```

---

## 🎭 Interactive Elements

### Buttons

#### Primary Button (CTA)
```css
bg-gradient-to-r from-indigo-600 to-purple-600
text-white
px-6 py-3
rounded-lg
font-semibold
shadow-md hover:shadow-lg
transform hover:scale-105
transition-all duration-200
```

#### Secondary Button
```css
bg-white
border-2 border-indigo-600
text-indigo-600
px-6 py-3
rounded-lg
font-semibold
hover:bg-indigo-50
transition-colors
```

#### Danger Button
```css
bg-red-600
text-white
px-4 py-2
rounded-lg
hover:bg-red-700
transition-colors
```

#### Icon Button
```css
p-2
rounded-full
text-gray-400
hover:text-gray-600
hover:bg-gray-100
transition-colors
```

### Form Inputs

#### Text Input
```css
w-full
px-4 py-2
border-2 border-gray-200
rounded-lg
focus:border-indigo-500
focus:ring-2 focus:ring-indigo-200
transition-all
placeholder:text-gray-400
```

#### Dropdown Select
```css
appearance-none
w-full
px-4 py-2
border-2 border-gray-200
rounded-lg
bg-white
focus:border-indigo-500
cursor-pointer
```

#### Checkbox
```css
w-5 h-5
rounded
border-gray-300
text-indigo-600
focus:ring-2 focus:ring-indigo-200
cursor-pointer
```

### Badges

#### Status Badge
```css
px-3 py-1
text-xs font-semibold
rounded-full

/* Variants */
.badge-success { bg-green-100 text-green-800 }
.badge-warning { bg-yellow-100 text-yellow-800 }
.badge-error { bg-red-100 text-red-800 }
.badge-info { bg-blue-100 text-blue-800 }
```

---

## 🔄 Animation & Transitions

### Standard Transitions
```css
transition-all duration-200 ease-in-out   /* Default for most interactions */
transition-colors duration-150             /* Color changes only */
transition-transform duration-300          /* Transforms (scale, rotate) */
```

### Hover Effects
```css
/* Cards */
hover:shadow-lg
hover:scale-105
hover:border-indigo-300

/* Buttons */
hover:shadow-xl
active:scale-95

/* Links */
hover:text-indigo-700
hover:underline
```

### Loading States
```css
/* Spinner */
animate-spin (Tailwind default)

/* Pulse effect */
animate-pulse

/* Skeleton screens */
bg-gray-200 animate-pulse rounded
```

### Modal Animations
```css
/* Overlay fade in */
animation: fadeIn 200ms ease-in

/* Modal slide up */
animation: slideUp 300ms ease-out

@keyframes fadeIn {
  from { opacity: 0 }
  to { opacity: 1 }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0 }
  to { transform: translateY(0); opacity: 1 }
}
```

---

## 📐 Responsive Breakpoints

```css
/* Tailwind defaults used throughout */
sm: 640px    /* Mobile landscape, small tablets */
md: 768px    /* Tablets */
lg: 1024px   /* Desktop */
xl: 1280px   /* Large desktop */
2xl: 1536px  /* Extra large screens */
```

### Responsive Patterns Used

```css
/* Grid columns */
grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3

/* Padding adjustments */
p-4 md:p-6 lg:p-8

/* Font sizes */
text-2xl md:text-3xl lg:text-4xl

/* Hidden on mobile */
hidden md:block

/* Show only on mobile */
block md:hidden
```

---

## ♿ Accessibility

### Current Implementation

✅ **Implemented:**
- Semantic HTML (headers, nav, main, section)
- Form labels associated with inputs
- Alt text for images
- Focus states on interactive elements
- Color contrast ratios meet WCAG AA
- Keyboard navigation for modals (Esc to close)

❌ **Missing (Needs Improvement):**
- ARIA labels for icon-only buttons
- Screen reader announcements for dynamic content
- Skip to content link
- Focus trap in modals
- Keyboard shortcuts documentation
- High contrast mode support

---

## 🎨 Design Patterns

### 1. **Card Pattern**
Used for: Courses, tasks, CGPA overview, recommendations

```css
Structure:
  - Container: bg-white, rounded-xl, border, shadow-sm, p-6
  - Header: Title + optional badge/action
  - Body: Content with consistent spacing
  - Footer: CTAs or metadata

States:
  - Default: border-gray-200
  - Hover: shadow-lg, border-indigo-300
  - Active/Selected: border-indigo-600, ring-2
```

### 2. **Modal Pattern**
Used for: Task creation, mood logging, confirmations

```css
Structure:
  - Overlay: fixed inset-0, bg-black/50, z-50
  - Container: max-w-{size}, bg-white, rounded-2xl, shadow-2xl
  - Header: Title + close button
  - Body: Scrollable content
  - Footer: Action buttons (aligned right)

Behavior:
  - Click outside to close
  - Esc key to close
  - Focus trap within modal
  - Prevent body scroll when open
```

### 3. **List Pattern**
Used for: Tasks, upcoming deadlines, mood history

```css
Structure:
  - Container: bg-white, rounded-xl, border
  - Items: border-b (last:border-0), py-4, px-6
  - Item hover: bg-gray-50

Layout:
  - Checkbox/icon (left)
  - Content (flex-1)
  - Metadata (right)
  - Actions (far right)
```

### 4. **Form Pattern**
Used for: Registration, login, task creation

```css
Structure:
  - Field group: mb-4
  - Label: block, text-sm, font-semibold, mb-2
  - Input: w-full, px-4, py-2, border-2, rounded-lg
  - Helper text: text-xs, text-gray-600, mt-1
  - Error text: text-xs, text-red-600, mt-1

Validation:
  - Show errors below input
  - Red border on error
  - Green border on success
  - Disable submit until valid
```

### 5. **Empty State Pattern**
Used for: No tasks, no courses, no mood logs

```css
Structure:
  - Container: text-center, py-12
  - Icon: Large emoji or SVG (text-6xl, text-gray-400)
  - Heading: text-xl, font-semibold, text-gray-900, mt-4
  - Description: text-gray-600, mt-2
  - CTA button: mt-6, primary style

Message Tone:
  - Encouraging, not discouraging
  - Suggest next action
  - Example: "No tasks yet! Create your first task to get started 🎯"
```

---

## 🚨 Improvement Areas

### High Priority

**1. Mobile Responsiveness (CRITICAL MVP)**
- Currently desktop-first, many components break on mobile
- Need:
  - Collapsible navigation menu
  - Stack cards vertically on mobile
  - Adjust modal sizes for small screens
  - Touch-friendly button sizes (min 44px)
  - Test on 375px width (iPhone SE)

**2. Loading States**
- Most API calls lack loading indicators
- Need:
  - Skeleton screens for dashboard
  - Spinner for button actions
  - Progress bars for file uploads
  - Disable buttons during loading

**3. Error Handling UI**
- Currently using alert() boxes (poor UX)
- Need:
  - Toast notification system
  - Inline error messages
  - Error boundary components
  - Network error page

**4. Mood Trends Visualization**
- Backend API exists, no frontend component
- Need:
  - Line chart showing mood over time
  - Energy level trends
  - Sentiment distribution pie chart
  - Mood-to-grade correlation graph

### Medium Priority

**5. Accessibility Improvements**
- Add ARIA labels
- Focus management in modals
- Keyboard navigation indicators
- Screen reader testing

**6. Dark Mode**
- No dark mode support
- Would reduce eye strain for night studying
- Need: CSS variable system for easy toggling

**7. Micro-interactions**
- Add more delightful animations
- Confetti on achievements
- Smooth transitions between pages
- Haptic feedback on mobile

**8. Consistency**
- Some buttons use different padding
- Inconsistent spacing in cards
- Mixed use of shadow-sm vs shadow-md
- Need design tokens/variables

### Low Priority

**9. Data Visualization**
- CGPA trends chart (line graph)
- Task completion velocity
- Course difficulty rankings
- Study time analytics

**10. Advanced Features**
- Drag-and-drop task reordering
- Bulk actions (select multiple tasks)
- Search/filter functionality
- Keyboard shortcuts panel

---

## 📊 Current Component Inventory

### Pages (7)
- HomePage.jsx
- LoginPage.jsx
- RegisterPage.jsx
- DashboardPage.jsx
- CoursesPage.jsx
- CGPAPage.jsx
- (TasksPage.jsx - missing?)

### Components (8)
- MoodLogger.jsx ✅ Complete
- PriorityRecommendations.jsx ✅ Complete
- CGPADashboard.jsx ✅ Complete
- CourseCard.jsx ✅ Complete
- TaskList.jsx ✅ Complete
- AddTaskModal.jsx ✅ Complete
- EditTaskModal.jsx ✅ Complete
- (MoodTrendsWidget.jsx - ❌ Missing)

### Utilities
- api.js (Axios config)
- index.css (Tailwind imports)

---

## 🎯 Design Goals for Next Iteration

1. **Mobile-First Redesign**
   - Start with 375px width
   - Progressive enhancement for larger screens
   - Touch-optimized interactions

2. **Component Library**
   - Extract reusable components (Button, Input, Card)
   - Create Storybook documentation
   - Consistent prop APIs

3. **Design System**
   - Document all design tokens
   - Create Figma design library
   - Enforce with linting

4. **Performance**
   - Lazy load heavy components
   - Optimize images
   - Code splitting

5. **User Testing**
   - Test with actual PAU students
   - A/B test critical flows
   - Iterate based on feedback

---

## 📝 Notes for Designers

### What Works Well
✅ Clear visual hierarchy
✅ Consistent color usage for status (red=urgent, green=complete)
✅ Gradient accents add visual interest without overwhelming
✅ Card-based layouts are scannable
✅ Form validation is immediate and helpful
✅ Mood logger UX is delightful and quick

### Pain Points to Address
❌ Dashboard feels cluttered on mobile
❌ Too many similar shades of gray (reduce palette)
❌ Modal backgrounds too dark (50% opacity → 30%?)
❌ Empty states lack personality
❌ No onboarding flow for first-time users
❌ Charts/graphs need work (basic HTML tables currently)

### Design Inspiration Sources
- Linear (task management UX)
- Notion (clean data tables)
- Duolingo (achievement feedback)
- Apple Health (data visualization)
- Headspace (calm, friendly mood tracking)

---

**End of Design System Documentation**

*For design updates, contact: [Your Name]*
*Figma file: [Link when created]*
*Component demos: [Storybook URL when available]*
