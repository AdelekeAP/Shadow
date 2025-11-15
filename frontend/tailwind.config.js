/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // PAU Grade Colors
        'grade-a': '#10B981',  // Green - Excellent
        'grade-b': '#3B82F6',  // Blue - Good
        'grade-c': '#F59E0B',  // Amber - Fair
        'grade-d': '#EF4444',  // Red - Pass
        'grade-e': '#991B1B',  // Dark Red - Conditional
        'grade-f': '#000000',  // Black - Fail

        // Status Colors
        'on-track': '#10B981',
        'at-risk': '#F59E0B',
        'critical': '#EF4444',

        // Mood Colors
        'mood-focused': '#8B5CF6',
        'mood-tired': '#6B7280',
        'mood-stressed': '#EF4444',
        'mood-neutral': '#64748B',
        'mood-motivated': '#10B981',
      }
    },
  },
  plugins: [],
}
