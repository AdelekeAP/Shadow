import { useState, useEffect } from 'react'

/**
 * Animated circular progress ring showing CGPA progress toward target
 * Uses SVG stroke-dashoffset animation
 */
export default function CGPAProgressRing({ currentCGPA = 0, targetCGPA = 5.0, maxScale = 5.0, size = 160 }) {
  const [animatedOffset, setAnimatedOffset] = useState(null)

  const strokeWidth = 10
  const viewBox = 120
  const radius = 50
  const circumference = 2 * Math.PI * radius

  const percentage = targetCGPA > 0 ? Math.min((currentCGPA / targetCGPA) * 100, 100) : 0
  const targetOffset = circumference - (percentage * circumference / 100)

  const getColor = () => {
    if (percentage >= 90) return { stroke: '#059669', bg: '#d1fae5', text: '#065f46' }  // emerald
    if (percentage >= 75) return { stroke: '#d97706', bg: '#fef3c7', text: '#92400e' }  // amber
    return { stroke: '#dc2626', bg: '#fee2e2', text: '#991b1b' }                         // red
  }

  const colors = getColor()

  useEffect(() => {
    setAnimatedOffset(circumference)
    const timer = requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        setAnimatedOffset(targetOffset)
      })
    })
    return () => cancelAnimationFrame(timer)
  }, [circumference, targetOffset])

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg
        viewBox={`0 0 ${viewBox} ${viewBox}`}
        className="transform -rotate-90"
        style={{ width: size, height: size }}
        data-testid="cgpa-ring-svg"
      >
        {/* Background circle */}
        <circle
          cx={viewBox / 2}
          cy={viewBox / 2}
          r={radius}
          fill="none"
          stroke="#e5e7ee"
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={viewBox / 2}
          cy={viewBox / 2}
          r={radius}
          fill="none"
          stroke={colors.stroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={animatedOffset !== null ? animatedOffset : circumference}
          style={{
            transition: 'stroke-dashoffset 1.2s ease-out',
          }}
          data-testid="cgpa-ring-progress"
        />
      </svg>
      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center" data-testid="cgpa-ring-text">
        <span className="text-2xl font-bold font-mono" style={{ color: colors.stroke }}>
          {currentCGPA.toFixed(2)}
        </span>
        <span className="text-xs text-surface-400">/ {maxScale.toFixed(1)}</span>
      </div>
    </div>
  )
}
