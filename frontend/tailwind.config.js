/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Navy color scale (replaces indigo - more academic/professional)
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

        // PAU Grade Colors
        'grade-a': '#059669',  // Green - Excellent (updated)
        'grade-b': '#2563EB',  // Blue - Good (updated)
        'grade-c': '#D97706',  // Amber - Fair (updated)
        'grade-d': '#DC2626',  // Red - Pass (updated)
        'grade-e': '#991B1B',  // Dark Red - Conditional
        'grade-f': '#000000',  // Black - Fail

        // Status Colors
        'on-track': '#059669',
        'at-risk': '#D97706',
        'critical': '#DC2626',

        // Mood Colors
        'mood-focused': '#8B5CF6',
        'mood-tired': '#6B7280',
        'mood-stressed': '#DC2626',
        'mood-neutral': '#64748B',
        'mood-motivated': '#059669',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
