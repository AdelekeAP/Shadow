# 🎨 Shadow Color Migration Guide - Indigo → Navy

**Time Required:** 2-3 hours  
**Impact:** Complete visual transformation  
**Risk:** Low (just color changes, no logic affected)

---

## 🎯 Quick Start

This guide will transform Shadow from "generic AI app" (indigo/purple) to "professional academic tool" (navy/warm grays).

---

## 📋 Find & Replace Commands

### Step 1: Primary Colors (Indigo → Navy)

Run these find/replace operations across your entire `frontend/src` directory:

```bash
# Primary buttons and CTAs
Find:    bg-indigo-600
Replace: bg-navy-800

Find:    hover:bg-indigo-700
Replace: hover:bg-navy-900

Find:    bg-indigo-500
Replace: bg-navy-700

# Text colors
Find:    text-indigo-600
Replace: text-navy-800

Find:    text-indigo-700
Replace: text-navy-900

Find:    text-indigo-500
Replace: text-navy-700

# Borders
Find:    border-indigo-600
Replace: border-navy-800

Find:    border-indigo-500
Replace: border-navy-700

# Focus states
Find:    focus:border-indigo-500
Replace: focus:border-navy-500

Find:    focus:ring-indigo-500
Replace: focus:ring-navy-500

Find:    focus:ring-indigo-200
Replace: focus:ring-navy-100
```

### Step 2: Remove Purple (No More Gradients)

```bash
# Replace gradient backgrounds with solid navy
Find:    bg-gradient-to-r from-indigo-600 to-purple-600
Replace: bg-navy-800

Find:    from-indigo-500 to-purple-600
Replace: bg-navy-800

Find:    bg-purple-600
Replace: bg-navy-800

Find:    text-purple-600
Replace: text-navy-800

Find:    border-purple-600
Replace: bg-navy-800
```

### Step 3: Update Grays (Cool → Warm)

```bash
# Background colors (cool gray → warm stone)
Find:    bg-gray-50
Replace: bg-stone-50

Find:    bg-gray-100
Replace: bg-stone-100

Find:    bg-gray-200
Replace: bg-stone-200

# Text colors
Find:    text-gray-600
Replace: text-stone-600

Find:    text-gray-700
Replace: text-stone-700

Find:    text-gray-800
Replace: text-stone-800

Find:    text-gray-900
Replace: text-stone-900

# Borders
Find:    border-gray-200
Replace: border-stone-200

Find:    border-gray-300
Replace: border-stone-300
```

---

## 🎨 Tailwind Config Update

### Add Navy Color to Tailwind

Update `tailwind.config.js`:

```js
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // NEW: Navy color scale
        navy: {
          50: '#F0F4FF',
          100: '#E0E9FF',
          200: '#C7D7FE',
          300: '#A5BBFE',
          400: '#8199FC',
          500: '#6172F3',
          600: '#4F46E5',
          700: '#3E38D8',
          800: '#1E3A8A',  // Primary - use this most
          900: '#172554',  // Darker - for hovers
        },
        // Keep existing colors
        green: {
          50: '#F0FDF4',
          100: '#DCFCE7',
          600: '#059669',
          700: '#047857',
        },
        amber: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          600: '#D97706',
          700: '#B45309',
        },
        red: {
          50: '#FEF2F2',
          100: '#FEE2E2',
          600: '#DC2626',
          700: '#B91C1C',
        },
        // Use Tailwind's stone for warm grays (already available)
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
```

---

## 🔍 Component-by-Component Changes

### 1. LoginPage.jsx / RegisterPage.jsx

**Before:**
```jsx
<div className="min-h-screen bg-gradient-to-br from-indigo-100 to-purple-100">
  <div className="bg-white rounded-2xl shadow-2xl">
    <button className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
      Login
    </button>
  </div>
</div>
```

**After:**
```jsx
<div className="min-h-screen bg-stone-50">
  <div className="bg-white rounded-2xl shadow-lg">
    <button className="bg-navy-800 hover:bg-navy-900 text-white rounded-lg transition-colors">
      Login
    </button>
  </div>
</div>
```

### 2. DashboardPage.jsx

**Before:**
```jsx
<div className="bg-gray-50 min-h-screen">
  <div className="bg-white rounded-lg shadow-md p-4">
    <h2 className="text-2xl font-bold text-indigo-600">Your CGPA</h2>
    <div className="h-2 bg-gray-200 rounded-full">
      <div className="h-2 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-full" />
    </div>
  </div>
</div>
```

**After:**
```jsx
<div className="bg-stone-50 min-h-screen">
  <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-6">
    <h2 className="text-2xl font-bold text-stone-900">Your CGPA</h2>
    {/* Replace with circular progress - see DESIGN_SYSTEM_V2.md */}
    <CircularProgressbar ... />
  </div>
</div>
```

### 3. MoodLogger.jsx

**Before:**
```jsx
<button className="fixed bottom-6 right-6 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-full shadow-lg">
  💭 Log Mood
</button>

<div className="border-2 border-indigo-300 bg-indigo-50">
  Selected mood
</div>
```

**After:**
```jsx
<button className="fixed bottom-6 right-6 bg-navy-800 hover:bg-navy-900 text-white rounded-full shadow-lg transition-colors">
  💭 Log Mood
</button>

<div className="border-2 border-navy-300 bg-navy-50">
  Selected mood
</div>
```

### 4. Buttons Across the App

**Before:**
```jsx
// Primary button
<button className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded">

// Secondary button  
<button className="border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50">

// Ghost button
<button className="text-indigo-600 hover:bg-indigo-50">
```

**After:**
```jsx
// Primary button
<button className="bg-navy-800 hover:bg-navy-900 text-white px-6 py-3 rounded-lg font-medium transition-colors shadow-sm">

// Secondary button
<button className="border-2 border-stone-300 hover:border-navy-800 hover:bg-navy-50 text-stone-700 hover:text-navy-800 px-6 py-3 rounded-lg font-medium transition-all">

// Ghost button
<button className="text-stone-700 hover:bg-stone-100 px-4 py-2 rounded-lg transition-colors">
```

### 5. Form Inputs

**Before:**
```jsx
<input className="
  w-full px-4 py-2 
  border-2 border-gray-300 
  focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200
  rounded
" />
```

**After:**
```jsx
<input className="
  w-full px-4 py-3 
  border-2 border-stone-200 
  focus:border-navy-500 focus:ring-4 focus:ring-navy-100
  rounded-lg
  transition-all duration-200
" />
```

### 6. Cards

**Before:**
```jsx
<div className="bg-white rounded-lg shadow-md border border-gray-200 p-4">
```

**After:**
```jsx
<div className="bg-white rounded-xl shadow-sm border border-stone-200 p-6 hover:shadow-md transition-all">
```

### 7. Modals

**Before:**
```jsx
<div className="fixed inset-0 bg-black/50">
  <div className="bg-white rounded-2xl shadow-2xl p-6">
```

**After:**
```jsx
<div className="fixed inset-0 bg-stone-900/40 backdrop-blur-sm">
  <div className="bg-white rounded-2xl shadow-2xl">
    <div className="px-6 py-5 border-b border-stone-200">
      {/* Header */}
    </div>
    <div className="px-6 py-6">
      {/* Body */}
    </div>
    <div className="px-6 py-4 bg-stone-50 border-t border-stone-200">
      {/* Footer */}
    </div>
  </div>
</div>
```

---

## 🎨 Visual Comparison

### Before (Indigo/Purple)
```
Primary CTA: ████████ (Indigo gradient)
Text:        Dark gray on light gray
Cards:       White with gray borders
Shadows:     Heavy and dark
Overall:     Generic AI startup vibe
```

### After (Navy/Stone)
```
Primary CTA: ████████ (Navy solid)
Text:        Warm gray on warm white
Cards:       White with stone borders
Shadows:     Subtle and natural
Overall:     Professional academic tool
```

---

## 🚀 Quick Test Checklist

After making changes, test these screens:

1. **Login Page**
   - [ ] Background is stone-50 (not indigo gradient)
   - [ ] Button is navy-800 (not indigo gradient)
   - [ ] Inputs have navy focus ring

2. **Dashboard**
   - [ ] Page background is stone-50
   - [ ] Cards have stone borders
   - [ ] Text is stone-900/800/600 (not gray)
   - [ ] Primary actions are navy-800

3. **Buttons**
   - [ ] No purple anywhere
   - [ ] Navy buttons have smooth hover transitions
   - [ ] Secondary buttons have navy-800 hover state

4. **Forms/Modals**
   - [ ] Input focus states are navy (not indigo)
   - [ ] Modal overlay is stone-900/40 (not black/50)
   - [ ] Form labels are stone-900

5. **Overall**
   - [ ] No indigo-600 visible anywhere
   - [ ] No purple-600 visible anywhere
   - [ ] No gradients (except course carousel)
   - [ ] Warm grays throughout (stone, not gray)

---

## 🎯 Expected Results

**Before:** App looks like every AI tool (ChatGPT, Gemini, etc.)  
**After:** App looks like a professional academic management system

**Time Investment:** 2-3 hours  
**Visual Impact:** 🔥🔥🔥 Complete transformation  
**Functionality Impact:** None (just colors)

---

## 💡 Pro Tips

1. **Use VS Code's Find & Replace**
   - `Cmd/Ctrl + Shift + F` to search entire project
   - Use regex if needed: `bg-indigo-\d+`
   - Replace one file at a time to test

2. **Test as You Go**
   - Change one component, test it
   - Don't change everything at once
   - Keep browser open with hot reload

3. **Check Console**
   - Tailwind will warn about unknown classes
   - If you see warnings, you missed the config update

4. **Mobile Test**
   - Colors should look warm on both desktop and mobile
   - Navy should be dark but readable

---

## 🐛 Common Issues

**Issue:** Navy colors not showing  
**Fix:** Did you update `tailwind.config.js` and restart the dev server?

**Issue:** Some indigo still visible  
**Fix:** Search for `indigo` in your codebase - you missed some

**Issue:** Colors look wrong on mobile  
**Fix:** Clear browser cache, check if Tailwind CSS is loading

**Issue:** Buttons look flat  
**Fix:** Add `transition-colors` and proper hover states

---

## 📸 Visual Proof

After changes, your app should feel:
- ✅ Warmer (stone vs gray)
- ✅ More professional (navy vs indigo)
- ✅ More academic (solid vs gradients)
- ✅ More spacious (better padding/margins)
- ✅ More natural (subtle shadows)

---

## 🎯 Next Steps After Color Migration

Once colors are updated:

1. **Implement Course Carousel** (6-8 hours)
   - See DESIGN_SYSTEM_V2.md for full code
   - Use navy gradients for grade backgrounds

2. **Add Circular Progress Rings** (2 hours)
   - `npm install react-circular-progressbar`
   - Replace CGPA progress bar on dashboard

3. **Implement Semester Timeline** (4 hours)
   - Shows current week in semester
   - Visual milestone markers

4. **Update Task Cards** (3 hours)
   - Better layout
   - Course badges
   - Risk indicators

---

**Ready to transform Shadow! Start with Step 1 (Primary Colors) and work through systematically.** 🚀

**Questions?** Refer to DESIGN_SYSTEM_V2.md for detailed component specs.
