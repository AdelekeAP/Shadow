# 🎨 Shadow - Enhanced Design System v2.0

**Version**: 2.0 - Complete Redesign  
**Last Updated**: November 19, 2025  
**Framework**: React + Vite + TailwindCSS  
**Philosophy**: Natural, Minimalistic, Academic Professional

---

## 🎯 Design Philosophy Changes

### What Changed from v1.0

❌ **REMOVED:**
- Indigo/purple gradients (too "AI startup")
- Busy dashboard with too many elements
- Heavy shadows everywhere
- Excessive emoji usage
- Cool gray tones

✅ **NEW APPROACH:**
- Natural color palette (slate blues, warm neutrals)
- Clean, spacious layouts
- Subtle shadows, more white space
- Strategic emoji use (🔮 only)
- Warm, inviting neutrals

---

## 🎨 New Color System - Natural & Academic

### Primary Palette - "Academic Professional"

```css
/* Primary Brand - Deep Academic Blue (replaces indigo) */
--primary-navy: #1E3A8A         /* Primary actions, headers */
--primary-blue: #2563EB         /* Links, accents */
--primary-light: #DBEAFE       /* Subtle backgrounds */

/* Success - Natural Green */
--success-green: #059669        /* A grades, completed tasks */
--success-light: #D1FAE5        /* Success backgrounds */

/* Warning - Warm Amber */
--warning-amber: #D97706        /* B/C grades, warnings */
--warning-light: #FEF3C7        /* Warning backgrounds */

/* Danger - Muted Red */
--danger-red: #DC2626           /* D/F grades, overdue */
--danger-light: #FEE2E2         /* Error backgrounds */

/* Neutral - Warm Grays (not cool grays!) */
--gray-50: #FAFAF9              /* Page background */
--gray-100: #F5F5F4             /* Card backgrounds */
--gray-200: #E7E5E4             /* Borders */
--gray-300: #D6D3D1             /* Dividers */
--gray-400: #A8A29E             /* Disabled text */
--gray-500: #78716C             /* Secondary text */
--gray-600: #57534E             /* Body text */
--gray-700: #44403C             /* Subheadings */
--gray-800: #292524             /* Headings */
--gray-900: #1C1917             /* Primary text */

/* Accent - Subtle Teal (for highlights) */
--accent-teal: #0D9488          /* Special elements */
--accent-light: #CCFBF1         /* Accent backgrounds */
```

### Grade-Specific Colors

```css
/* Crystal Ball Predictions - Color Coded */
--grade-A: #059669              /* Green - Excellent */
--grade-B: #2563EB              /* Blue - Good */
--grade-C: #D97706              /* Amber - Fair */
--grade-D: #DC2626              /* Red - Pass/Fail */

/* Background gradients for course carousel */
--gradient-A: linear-gradient(135deg, #059669 0%, #047857 100%)
--gradient-B: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)
--gradient-C: linear-gradient(135deg, #D97706 0%, #B45309 100%)
--gradient-D: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%)
```

### Why These Colors Work Better

| Old (v1) | New (v2) | Reason |
|----------|----------|--------|
| Indigo #4F46E5 | Navy #1E3A8A | More academic, less "tech startup" |
| Purple accent | Teal accent | Warmer, more natural |
| Cool grays | Warm grays | Less sterile, more inviting |
| Gradient primary | Solid colors | Cleaner, more professional |

---

## ✍️ Enhanced Typography

### Font System - Better Hierarchy

```css
/* Headings - Stronger weights */
--h1: 48px / 800 / -0.02em      /* Page hero */
--h2: 36px / 700 / -0.01em      /* Section titles */
--h3: 24px / 600 / 0            /* Card titles */
--h4: 20px / 600 / 0            /* Subsections */
--h5: 18px / 600 / 0            /* Component headers */

/* Body - Better readability */
--body-xl: 20px / 400 / 0       /* Large body (hero text) */
--body-lg: 18px / 400 / 0       /* Emphasized body */
--body: 16px / 400 / 0          /* Standard text */
--body-sm: 14px / 400 / 0       /* Small text */
--caption: 12px / 500 / 0.02em  /* Labels (medium weight) */

/* Special - Numbers */
--display: 72px / 700 / -0.02em /* CGPA display */
--number-lg: 48px / 700 / -0.01em /* Large stats */
--number-md: 36px / 600 / 0     /* Medium stats */
```

### Line Height - More Breathing Room

```css
--leading-none: 1.0     /* Tight headlines */
--leading-tight: 1.25   /* Subheadings */
--leading-normal: 1.5   /* Body text */
--leading-relaxed: 1.75 /* Comfortable reading */
```

---

## 🎨 Component Design System

### 1. Dashboard - Complete Redesign

#### New Layout Structure

```
┌──────────────────────────────────────────────────────────┐
│  Header: Logo + User Profile (minimal)                   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │  CGPA HERO - Circular Progress Ring (Large)        │ │
│  │                                                     │ │
│  │        ╱───────────╲                               │ │
│  │       │    4.73     │   Current: 4.73              │ │
│  │       │   92% to    │   Target:  4.50              │ │
│  │       │ First Class │   Status: ✓ ON TRACK         │ │
│  │        ╲───────────╱    Buffer: +0.23 points       │ │
│  │                                                     │ │
│  │  [Full Analytics →]                                │ │
│  └────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │  COURSE CAROUSEL - Auto-rotating                   │ │
│  │                                                     │ │
│  │         [● ○ ○ ○ ○ ○ ○]  7 courses                │ │
│  │                                                     │ │
│  │    ┌───────────────────────────────┐               │ │
│  │    │                                │               │ │
│  │    │      CSC 497                   │               │ │
│  │    │  Final Year Project I          │               │ │
│  │    │                                │               │ │
│  │    │        🔮  A                   │               │ │
│  │    │   (Green gradient bg)          │               │ │
│  │    │                                │               │ │
│  │    │  CA: 25/30  •  3 credits      │               │ │
│  │    │                                │               │ │
│  │    │  [+ Add Task] (hover)          │               │ │
│  │    └───────────────────────────────┘               │ │
│  │                                                     │ │
│  │         [← →] Paused on hover                      │ │
│  └────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │  PRIORITY TASKS (3-5 tasks max, not full list)     │ │
│  │                                                     │ │
│  │  🔴 CSC401 Test 2          Due in 2 hours         │ │
│  │     15/30 CA  •  ~2hrs  •  High impact            │ │
│  │                                                     │ │
│  │  🟡 CSC497 Report          Due tomorrow           │ │
│  │     5/30 CA  •  ~1hr  •  Medium                   │ │
│  │                                                     │ │
│  │  [View All Tasks →]                                │ │
│  └────────────────────────────────────────────────────┘ │
│                                                           │
│  [Log Mood] (Floating button - bottom right)            │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

#### CGPA Hero Card Design

```jsx
<div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
  <div className="flex items-center justify-between">
    {/* Left: Circular Progress */}
    <div className="w-64 h-64">
      <CircularProgressbar
        value={92}
        text="4.73"
        styles={buildStyles({
          pathColor: '#059669',
          textColor: '#1C1917',
          trailColor: '#F5F5F4',
          textSize: '20px',
          pathTransition: 'stroke-dashoffset 0.5s ease 0s',
        })}
      />
      <p className="text-center mt-4 text-sm font-medium text-gray-600">
        92% to First Class
      </p>
    </div>
    
    {/* Right: Stats */}
    <div className="flex-1 ml-12 space-y-4">
      <div className="flex items-baseline justify-between">
        <span className="text-gray-600">Current CGPA</span>
        <span className="text-5xl font-bold text-gray-900">4.73</span>
      </div>
      <div className="flex items-baseline justify-between">
        <span className="text-gray-600">Target CGPA</span>
        <span className="text-3xl font-semibold text-navy-800">4.50</span>
      </div>
      <div className="flex items-baseline justify-between">
        <span className="text-gray-600">Status</span>
        <span className="inline-flex items-center gap-2 text-green-700 font-medium">
          <CheckCircle className="w-5 h-5" />
          On Track
        </span>
      </div>
      <div className="flex items-baseline justify-between">
        <span className="text-gray-600">Buffer</span>
        <span className="text-lg font-medium text-green-700">+0.23 points</span>
      </div>
      
      <button className="mt-6 w-full px-4 py-3 bg-navy-800 hover:bg-navy-900 text-white rounded-lg font-medium transition-colors">
        View Full Analytics →
      </button>
    </div>
  </div>
</div>
```

**Design Rationale:**
- ✅ Circular progress is more engaging than bars
- ✅ Large numbers are scannable
- ✅ Stats on right for natural reading flow
- ✅ Clean white card with subtle shadow
- ✅ Single, prominent CTA

---

### 2. Course Carousel - The Hero Feature

#### Design Specifications

```css
.course-carousel-container {
  max-width: 700px;
  margin: 0 auto;
  position: relative;
}

.course-slide {
  height: 400px;
  border-radius: 24px;
  padding: 48px;
  position: relative;
  cursor: pointer;
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Grade-based gradients */
.course-slide.grade-A {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

.course-slide.grade-B {
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
}

.course-slide.grade-C {
  background: linear-gradient(135deg, #D97706 0%, #B45309 100%);
}

.course-slide.grade-D {
  background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%);
}

.course-slide:hover {
  transform: scale(1.02);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

/* Navigation */
.carousel-nav-button {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 12px;
  border-radius: 50%;
  transition: all 0.2s;
}

.carousel-nav-button:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-50%) scale(1.1);
}

/* Dots indicator */
.carousel-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 24px;
}

.carousel-dot {
  width: 8px;
  height: 8px;
  border-radius: 4px;
  background: #D6D3D1;
  transition: all 0.3s;
}

.carousel-dot.active {
  width: 32px;
  background: #1E3A8A;
}
```

#### Content Layout

```jsx
<div className="course-slide grade-A text-white">
  {/* Course Info */}
  <div className="text-center">
    {/* Code & Title */}
    <div className="flex items-center justify-center gap-2 mb-2">
      <BookOpen className="w-6 h-6 opacity-75" />
      <h3 className="text-3xl font-bold">CSC 497</h3>
    </div>
    <p className="text-xl opacity-90 mb-8">Final Year Project I</p>
    
    {/* Grade - THE HERO */}
    <div className="flex items-center justify-center gap-6 my-12">
      <span className="text-8xl drop-shadow-2xl">🔮</span>
      <span className="text-9xl font-black drop-shadow-2xl">A</span>
    </div>
    
    {/* Quick Stats */}
    <div className="flex items-center justify-center gap-8 text-base opacity-90">
      <div className="flex items-center gap-2">
        <FileText className="w-5 h-5" />
        <span>25/30 CA</span>
      </div>
      <div className="w-1 h-1 rounded-full bg-white/50"></div>
      <div className="flex items-center gap-2">
        <Award className="w-5 h-5" />
        <span>3 credits</span>
      </div>
    </div>
    
    {/* Hover CTA */}
    {isPaused && (
      <button className="
        mt-8 px-8 py-4 
        bg-white/20 hover:bg-white/30 
        backdrop-blur-sm
        rounded-xl font-semibold text-lg
        border border-white/30
        transition-all duration-200
        transform hover:scale-105
        shadow-lg
      ">
        <Plus className="w-5 h-5 inline mr-2" />
        Add Task for This Course
      </button>
    )}
  </div>
  
  {/* Navigation Arrows */}
  <button className="carousel-nav-button" style={{left: '24px'}}>
    <ChevronLeft className="w-6 h-6" />
  </button>
  <button className="carousel-nav-button" style={{right: '24px'}}>
    <ChevronRight className="w-6 h-6" />
  </button>
</div>
```

**Carousel Behavior:**
- Auto-rotates every 3 seconds
- Pause on hover
- Click card → Opens task modal with course pre-selected
- Keyboard navigation (← →)
- Smooth slide transitions (0.5s cubic-bezier)

---

### 3. Task Cards - Clean & Functional

#### New Task Card Design

```jsx
<div className="bg-white border border-gray-200 rounded-xl p-5 hover:shadow-md transition-all">
  {/* Header Row */}
  <div className="flex items-start justify-between mb-3">
    {/* Course Badge */}
    <span className="inline-flex items-center px-3 py-1 bg-navy-50 text-navy-700 text-sm font-semibold rounded-lg">
      {courseCode}
    </span>
    
    {/* Status Icon */}
    {isCompleted ? (
      <CheckCircle className="w-6 h-6 text-green-600" />
    ) : isOverdue ? (
      <AlertCircle className="w-6 h-6 text-red-600" />
    ) : (
      <Clock className="w-6 h-6 text-gray-400" />
    )}
  </div>
  
  {/* Task Title */}
  <h4 className="text-lg font-semibold text-gray-900 mb-2">
    {title}
  </h4>
  
  {/* Metadata Row */}
  <div className="flex items-center gap-4 text-sm text-gray-600 mb-4">
    <div className="flex items-center gap-1.5">
      <FileText className="w-4 h-4" />
      <span>{weight}/30 CA</span>
    </div>
    <div className="flex items-center gap-1.5">
      <Clock className="w-4 h-4" />
      <span>~{estimatedTime}</span>
    </div>
    <div className="flex items-center gap-1.5">
      <Flame className="w-4 h-4" />
      <span className="text-orange-600">{difficulty}</span>
    </div>
  </div>
  
  {/* Due Date */}
  <div className="flex items-center gap-2 text-sm">
    <Calendar className="w-4 h-4 text-gray-500" />
    <span className={cn(
      "font-medium",
      isOverdue ? "text-red-600" : 
      isUrgent ? "text-orange-600" : 
      "text-gray-600"
    )}>
      {dueDate}
    </span>
  </div>
  
  {/* Actions (on hover) */}
  <div className="flex gap-2 mt-4 opacity-0 group-hover:opacity-100 transition-opacity">
    <button className="flex-1 px-3 py-2 bg-navy-800 hover:bg-navy-900 text-white rounded-lg text-sm font-medium">
      Mark Complete
    </button>
    <button className="px-3 py-2 border border-gray-300 hover:bg-gray-50 rounded-lg text-sm">
      <Edit2 className="w-4 h-4" />
    </button>
  </div>
</div>
```

**Key Improvements:**
- ✅ Course badge instead of emoji
- ✅ Clear status icons (not emojis)
- ✅ Task difficulty indicator
- ✅ Estimated time prominently shown
- ✅ Actions appear on hover (cleaner)
- ✅ Color-coded due dates

---

### 4. Buttons - Complete System

#### Button Variants

```jsx
/* Primary - Navy */
className="
  px-6 py-3 
  bg-navy-800 hover:bg-navy-900 
  text-white font-medium 
  rounded-lg 
  transition-colors duration-200
  shadow-sm hover:shadow-md
"

/* Secondary - Outline */
className="
  px-6 py-3 
  border-2 border-gray-300 
  hover:border-navy-800 hover:bg-navy-50 
  text-gray-700 hover:text-navy-800 
  font-medium rounded-lg 
  transition-all duration-200
"

/* Success - Green */
className="
  px-6 py-3 
  bg-green-600 hover:bg-green-700 
  text-white font-medium 
  rounded-lg 
  transition-colors duration-200
"

/* Danger - Red */
className="
  px-6 py-3 
  bg-red-600 hover:bg-red-700 
  text-white font-medium 
  rounded-lg 
  transition-colors duration-200
"

/* Ghost - Minimal */
className="
  px-4 py-2 
  hover:bg-gray-100 
  text-gray-700 
  rounded-lg 
  transition-colors duration-200
"
```

**Button Sizes:**
```jsx
// Small
className="px-3 py-1.5 text-sm"

// Medium (default)
className="px-6 py-3 text-base"

// Large
className="px-8 py-4 text-lg"
```

---

### 5. Forms - Better Input Design

#### Text Input

```jsx
<div className="space-y-2">
  <label className="block text-sm font-semibold text-gray-900">
    Task Title
    <span className="text-red-600 ml-1">*</span>
  </label>
  
  <input
    type="text"
    className="
      w-full px-4 py-3
      border-2 border-gray-200
      focus:border-navy-500 focus:ring-4 focus:ring-navy-100
      rounded-lg
      text-gray-900
      transition-all duration-200
      placeholder:text-gray-400
    "
    placeholder="e.g., Weekly Progress Report"
  />
  
  <p className="text-xs text-gray-500">
    Be specific about what needs to be done
  </p>
</div>
```

#### Select Dropdown

```jsx
<div className="space-y-2">
  <label className="block text-sm font-semibold text-gray-900">
    Course
  </label>
  
  <select className="
    w-full px-4 py-3
    border-2 border-gray-200
    focus:border-navy-500 focus:ring-4 focus:ring-navy-100
    rounded-lg
    text-gray-900
    bg-white
    transition-all duration-200
  ">
    <option value="">Select a course...</option>
    <option value="csc497">CSC 497 - Final Year Project I</option>
    <option value="csc401">CSC 401 - Algorithms</option>
  </select>
</div>
```

#### Date Picker

```jsx
<div className="space-y-2">
  <label className="block text-sm font-semibold text-gray-900">
    Due Date
  </label>
  
  <div className="relative">
    <input
      type="date"
      className="
        w-full px-4 py-3 pl-12
        border-2 border-gray-200
        focus:border-navy-500 focus:ring-4 focus:ring-navy-100
        rounded-lg
        text-gray-900
        transition-all duration-200
      "
    />
    <Calendar className="
      absolute left-4 top-1/2 -translate-y-1/2
      w-5 h-5 text-gray-400
      pointer-events-none
    " />
  </div>
</div>
```

---

### 6. Modals - Cleaner Design

#### Modal Structure

```jsx
{/* Overlay */}
<div className="fixed inset-0 bg-gray-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
  
  {/* Modal Container */}
  <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
    
    {/* Header */}
    <div className="flex items-center justify-between px-6 py-5 border-b border-gray-200">
      <h2 className="text-2xl font-bold text-gray-900">
        Add New Task
      </h2>
      <button 
        onClick={onClose}
        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
      >
        <X className="w-6 h-6 text-gray-500" />
      </button>
    </div>
    
    {/* Body - Scrollable */}
    <div className="px-6 py-6 overflow-y-auto max-h-[calc(90vh-140px)]">
      {/* Form content */}
    </div>
    
    {/* Footer */}
    <div className="flex items-center justify-end gap-3 px-6 py-4 bg-gray-50 border-t border-gray-200">
      <button className="px-6 py-2.5 border-2 border-gray-300 hover:bg-gray-100 text-gray-700 rounded-lg font-medium transition-colors">
        Cancel
      </button>
      <button className="px-6 py-2.5 bg-navy-800 hover:bg-navy-900 text-white rounded-lg font-medium transition-colors">
        Create Task
      </button>
    </div>
    
  </div>
</div>
```

**Key Changes:**
- ✅ Lighter overlay (40% vs 50%)
- ✅ Better backdrop blur
- ✅ Cleaner header with border
- ✅ Footer actions on gray background
- ✅ Proper scrolling for long forms

---

## 🎨 Special Components

### 1. Progress Ring Component

```jsx
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';

const CGPAProgressRing = ({ current, target }) => {
  const percentage = Math.min((current / target) * 100, 100);
  const status = current >= target ? 'success' : current >= target - 0.2 ? 'warning' : 'danger';
  
  const colors = {
    success: '#059669',
    warning: '#D97706',
    danger: '#DC2626'
  };
  
  return (
    <div className="relative">
      <CircularProgressbar
        value={percentage}
        text={current.toFixed(2)}
        styles={buildStyles({
          pathColor: colors[status],
          textColor: '#1C1917',
          trailColor: '#F5F5F4',
          textSize: '18px',
          pathTransitionDuration: 0.5,
        })}
        strokeWidth={8}
      />
      
      {/* Center decoration */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="text-center">
          <div className="text-5xl font-bold text-gray-900 mb-1">
            {current.toFixed(2)}
          </div>
          <div className="text-sm text-gray-600">
            of {target}
          </div>
        </div>
      </div>
    </div>
  );
};
```

### 2. Risk Badge Component

```jsx
const CourseRiskBadge = ({ riskLevel, reasons }) => {
  const configs = {
    safe: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-700',
      icon: CheckCircle,
      label: 'On Track'
    },
    watch: {
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      text: 'text-amber-700',
      icon: AlertTriangle,
      label: 'Watch'
    },
    risk: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-700',
      icon: AlertCircle,
      label: 'At Risk'
    }
  };
  
  const config = configs[riskLevel];
  const Icon = config.icon;
  
  return (
    <div className={`
      ${config.bg} ${config.border} ${config.text}
      border-2 rounded-xl p-4
    `}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-5 h-5" />
        <span className="font-semibold">{config.label}</span>
      </div>
      {reasons && reasons.length > 0 && (
        <ul className="text-sm space-y-1 ml-7">
          {reasons.map((reason, i) => (
            <li key={i}>• {reason}</li>
          ))}
        </ul>
      )}
    </div>
  );
};
```

### 3. Semester Timeline Component

```jsx
import { Flag, FileText, Code, BookOpen, Trophy } from 'lucide-react';

const SemesterTimeline = ({ currentWeek, totalWeeks = 17 }) => {
  const milestones = [
    { week: 1, label: 'Start', icon: Flag },
    { week: 5, label: 'Tests', icon: FileText },
    { week: 9, label: 'Projects', icon: Code },
    { week: 13, label: 'Exams', icon: BookOpen },
    { week: 17, label: 'End', icon: Trophy }
  ];
  
  const progress = (currentWeek / totalWeeks) * 100;
  
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">
        Semester Progress
      </h3>
      
      <div className="relative">
        {/* Progress Track */}
        <div className="absolute top-6 left-0 right-0 h-2 bg-gray-200 rounded-full">
          <div 
            className="h-full bg-navy-600 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        
        {/* Milestones */}
        <div className="relative flex justify-between">
          {milestones.map(({ week, label, icon: Icon }) => {
            const isPassed = week <= currentWeek;
            const isCurrent = week === Math.round(currentWeek);
            
            return (
              <div key={week} className="flex flex-col items-center">
                <div className={`
                  w-12 h-12 rounded-full flex items-center justify-center
                  border-4 border-white
                  ${isPassed ? 'bg-navy-600 text-white' : 'bg-gray-200 text-gray-400'}
                  ${isCurrent ? 'ring-4 ring-navy-200 scale-110' : ''}
                  transition-all duration-300
                `}>
                  <Icon className="w-6 h-6" />
                </div>
                <span className={`
                  text-sm font-medium mt-3
                  ${isPassed ? 'text-gray-900' : 'text-gray-500'}
                `}>
                  {label}
                </span>
                <span className="text-xs text-gray-500 mt-1">
                  Week {week}
                </span>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Current Week Display */}
      <div className="mt-6 text-center">
        <span className="text-sm text-gray-600">You are in </span>
        <span className="text-base font-semibold text-navy-800">
          Week {currentWeek} of {totalWeeks}
        </span>
      </div>
    </div>
  );
};
```

---

## 🎨 Spacing System - More Breathing Room

### New Spacing Scale

```css
/* Spacing tokens */
--space-1: 4px      /* Tiny gaps */
--space-2: 8px      /* Small gaps */
--space-3: 12px     /* Default gaps */
--space-4: 16px     /* Card padding start */
--space-5: 20px     /* Comfortable */
--space-6: 24px     /* Section spacing */
--space-8: 32px     /* Large spacing */
--space-10: 40px    /* Extra large */
--space-12: 48px    /* Hero spacing */
--space-16: 64px    /* Page sections */
```

### Application

```jsx
/* Card padding: Increased from p-4 to p-6 */
className="p-6"  /* 24px instead of 16px */

/* Section margins: Increased from mb-4 to mb-8 */
className="mb-8"  /* 32px instead of 16px */

/* Page padding */
className="px-6 py-8 lg:px-8 lg:py-12"

/* Stack spacing */
className="space-y-6"  /* 24px between stacked elements */
```

---

## 🎨 Shadow System - Subtle & Natural

### Shadow Scale

```css
/* Minimal shadows - more natural */
--shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
--shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)

/* Colored shadows for special elements */
--shadow-navy: 0 4px 14px 0 rgba(30, 58, 138, 0.15)
--shadow-green: 0 4px 14px 0 rgba(5, 150, 105, 0.15)
```

### Usage

```jsx
/* Default cards */
className="shadow-sm hover:shadow-md"

/* Modals */
className="shadow-2xl"

/* Floating elements */
className="shadow-lg"

/* Important CTAs */
className="shadow-navy hover:shadow-lg"
```

---

## 🎨 Border Radius System

```css
/* Rounded corners */
--radius-sm: 6px      /* Small elements */
--radius-md: 8px      /* Buttons, inputs */
--radius-lg: 12px     /* Cards */
--radius-xl: 16px     /* Large cards */
--radius-2xl: 24px    /* Modals, hero elements */
--radius-full: 9999px /* Pills, circles */
```

---

## 🎯 Implementation Priority

### Week 1: Core Visual Upgrade (14 hours)

**Day 1-2: Color System Migration**
```bash
# Replace all instances
Find: bg-indigo-600, text-indigo-600, etc.
Replace: bg-navy-800, text-navy-800

Find: from-indigo-600 to-purple-600
Replace: bg-navy-800 (solid color)

# Update gray scale
Find: gray-50 through gray-900 (cool)
Replace: Use warm grays from new system
```

**Day 3-4: Course Carousel**
```bash
npm install react-circular-progressbar
# Implement carousel with new gradients
# Wire up hover-to-pause
# Add click-to-create-task
```

**Day 5: Dashboard Redesign**
```bash
# Implement circular progress ring
# Simplify layout (remove clutter)
# Add semester timeline
```

### Week 2: Polish & Refinement (13 hours)

**Day 1-2: Component Updates**
- Task cards redesign
- Button system standardization
- Form input improvements
- Modal redesign

**Day 3: Risk Indicators**
- Calculate course risk levels
- Add visual warnings
- Implement action prompts

**Day 4: Micro-interactions**
- Task completion animations
- Hover states
- Transitions

**Day 5: Testing**
- Cross-browser testing
- Mobile responsiveness
- Performance optimization

---

## 🎨 Quick Migration Guide

### 1. Update Tailwind Config

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#F0F4FF',
          100: '#E0E9FF',
          200: '#C7D7FE',
          300: '#A5BBFE',
          400: '#8199FC',
          500: '#6172F3',
          600: '#4F46E5',
          700: '#3E38D8',
          800: '#1E3A8A',  // Primary
          900: '#172554',
        },
        // Keep existing green, amber, red
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
}
```

### 2. Create Color Mapping

```jsx
// Old → New mapping
const colorMigration = {
  'indigo-600': 'navy-800',
  'indigo-700': 'navy-900',
  'indigo-500': 'navy-700',
  'indigo-50': 'navy-50',
  'purple-600': 'navy-800',  // Remove purple
  'gray-50': 'stone-50',     // Warm grays
  'gray-100': 'stone-100',
  // etc.
};
```

### 3. Component Checklist

```
Dashboard:
[ ] Replace CGPA progress bar with ring
[ ] Implement course carousel
[ ] Simplify task list (show 3-5 max)
[ ] Add semester timeline
[ ] Update colors to navy/stone

Task Components:
[ ] Redesign task cards
[ ] Add course badges (not purple pills)
[ ] Add difficulty indicators
[ ] Update icons (Lucide)

Forms:
[ ] Update input styles
[ ] Better focus states
[ ] Improved validation display

Modals:
[ ] Lighter overlay (40%)
[ ] Better header/footer
[ ] Updated button styles

Authentication:
[ ] Remove gradient backgrounds
[ ] Cleaner card design
[ ] Better error states
```

---

## 📱 Mobile Responsiveness

### Breakpoint Strategy

```jsx
/* Mobile First */
// Base styles for mobile (< 640px)

/* Tablet */
@media (min-width: 640px) {
  // sm: breakpoint
}

/* Desktop */
@media (min-width: 1024px) {
  // lg: breakpoint
}
```

### Dashboard Mobile Layout

```jsx
<div className="px-4 py-6 space-y-6">
  {/* CGPA Ring - Smaller on mobile */}
  <div className="w-48 h-48 mx-auto lg:w-64 lg:h-64">
    <CircularProgressbar ... />
  </div>
  
  {/* Carousel - Adjust height */}
  <div className="h-[350px] lg:h-[400px]">
    <CourseCarousel ... />
  </div>
  
  {/* Tasks - Full width on mobile */}
  <div className="space-y-3">
    <TaskCard ... />
  </div>
</div>
```

---

## 🎯 Design Checklist

### Before Defense

- [ ] All indigo/purple replaced with navy
- [ ] Course carousel implemented and working
- [ ] Circular progress rings on dashboard
- [ ] Semester timeline visible
- [ ] Task cards redesigned
- [ ] Risk indicators showing
- [ ] Forms updated with new styles
- [ ] Modals redesigned
- [ ] Mobile responsive (test on 375px)
- [ ] Loading states added
- [ ] Error handling improved
- [ ] Emoji usage reduced (🔮 only)
- [ ] Icons from Lucide throughout
- [ ] Consistent spacing (p-6, mb-8)
- [ ] Subtle shadows everywhere
- [ ] Proper focus states
- [ ] Accessibility tested

---

## 🎨 Final Notes

### What Makes This Better

**v1.0 Problems:**
- Looked like every AI app (indigo/purple)
- Too busy, cluttered
- Generic, not academic
- Cool, uninviting grays

**v2.0 Solutions:**
- Natural, professional navy + warm grays
- Clean, spacious layouts
- Academic professional feel
- Warm, inviting neutrals
- Strategic emoji use (🔮 only)
- Circular progress (more engaging)
- Course carousel (unique feature)
- Better information hierarchy

### Design Philosophy

```
Less is more
White space is your friend
One hero per screen
Natural over trendy
Professional over playful
Academic over startup
```

---

**Ready to implement! Start with the color migration, then tackle the carousel.** 🚀
