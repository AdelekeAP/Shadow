import { useState, useEffect, useMemo } from 'react'

const STEPS = [
  {
    label: 'Processing document',
    detail: 'Extracting text and structure from your file',
    duration: 4000,
  },
  {
    label: 'Analyzing content',
    detail: 'Identifying key topics, concepts, and learning objectives',
    duration: 5000,
  },
  {
    label: 'Generating study plan',
    detail: 'Building personalized day-by-day activities with AI',
    duration: 25000,
  },
  {
    label: 'Curating resources',
    detail: 'Finding quality videos, articles, and practice materials',
    duration: 15000,
  },
  {
    label: 'Saving your plan',
    detail: 'Finalizing everything — almost there',
    duration: 8000,
  },
]

const TOTAL = STEPS.length

export default function GeneratingOverlay() {
  const [step, setStep] = useState(0)
  const [elapsed, setElapsed] = useState(0)
  const [finished, setFinished] = useState(false)

  // Step progression
  useEffect(() => {
    if (step >= TOTAL - 1) {
      const t = setTimeout(() => setFinished(true), STEPS[step].duration)
      return () => clearTimeout(t)
    }
    const t = setTimeout(() => setStep(s => s + 1), STEPS[step].duration)
    return () => clearTimeout(t)
  }, [step])

  // Elapsed timer
  useEffect(() => {
    const iv = setInterval(() => setElapsed(s => s + 1), 1000)
    return () => clearInterval(iv)
  }, [])

  const progress = finished ? 97 : ((step + 1) / TOTAL) * 100

  // Generate stable particle positions once
  const particles = useMemo(() =>
    Array.from({ length: 14 }, (_, i) => ({
      x: 10 + (i * 37 + 13) % 80,
      y: 8 + (i * 53 + 7) % 84,
      size: 1.5 + (i % 3) * 0.8,
      delay: (i * 0.4) % 3.5,
      dur: 3 + (i % 4) * 1.2,
    }))
  , [])

  const formatTime = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0"
        style={{
          background: 'radial-gradient(ellipse at 50% 30%, rgba(15, 26, 62, 0.88), rgba(8, 12, 30, 0.95))',
          backdropFilter: 'blur(20px) saturate(180%)',
        }}
      />

      {/* Card */}
      <div className="relative w-full max-w-[420px] overflow-hidden" style={{ animation: 'go-card-in 0.5s cubic-bezier(0.16, 1, 0.3, 1)' }}>
        {/* Outer glow */}
        <div
          className="absolute -inset-px rounded-[26px] opacity-60"
          style={{
            background: 'linear-gradient(135deg, rgba(97, 114, 243, 0.3), rgba(16, 185, 129, 0.2), rgba(97, 114, 243, 0.15))',
          }}
        />

        {/* Main card body */}
        <div
          className="relative rounded-[25px] border border-white/[0.06]"
          style={{
            background: 'linear-gradient(165deg, rgba(23, 37, 84, 0.95) 0%, rgba(15, 26, 62, 0.98) 50%, rgba(12, 20, 48, 0.99) 100%)',
            boxShadow: '0 0 80px rgba(97, 114, 243, 0.08), 0 32px 64px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.04)',
          }}
        >
          {/* Floating particles */}
          <div className="absolute inset-0 overflow-hidden rounded-[25px] pointer-events-none">
            {particles.map((p, i) => (
              <div
                key={i}
                className="absolute rounded-full"
                style={{
                  left: `${p.x}%`,
                  top: `${p.y}%`,
                  width: p.size,
                  height: p.size,
                  background: i % 3 === 0
                    ? 'rgba(16, 185, 129, 0.5)'
                    : 'rgba(129, 153, 252, 0.35)',
                  animation: `go-drift ${p.dur}s ease-in-out ${p.delay}s infinite`,
                }}
              />
            ))}
          </div>

          {/* Ambient gradient orbs */}
          <div
            className="absolute top-0 right-0 w-60 h-60 pointer-events-none opacity-30"
            style={{ background: 'radial-gradient(circle at 80% 10%, rgba(97, 114, 243, 0.25), transparent 65%)' }}
          />
          <div
            className="absolute bottom-0 left-0 w-48 h-48 pointer-events-none opacity-20"
            style={{ background: 'radial-gradient(circle at 20% 90%, rgba(16, 185, 129, 0.3), transparent 65%)' }}
          />

          {/* Progress bar — top edge */}
          <div className="relative h-[2px] rounded-t-[25px] overflow-hidden bg-white/[0.04]">
            <div
              className="absolute inset-y-0 left-0 transition-all duration-1000 ease-out"
              style={{
                width: `${progress}%`,
                background: 'linear-gradient(90deg, #6172f3, #10b981)',
              }}
            />
            <div
              className="absolute inset-0"
              style={{
                background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%)',
                backgroundSize: '200% 100%',
                animation: 'go-shimmer 2.4s ease-in-out infinite',
              }}
            />
          </div>

          <div className="px-7 pt-7 pb-6">
            {/* ── Central Orb ── */}
            <div className="flex justify-center mb-6" style={{ animation: 'go-fade-in 0.6s ease-out 0.15s both' }}>
              <div className="relative w-[100px] h-[100px]">
                {/* Outer ring — slow spin */}
                <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" style={{ animation: 'go-spin-slow 12s linear infinite' }}>
                  <circle cx="50" cy="50" r="46" fill="none" stroke="rgba(97, 114, 243, 0.12)" strokeWidth="1" />
                  <circle cx="50" cy="50" r="46" fill="none" stroke="url(#go-ring1)" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="30 259" />
                  <defs>
                    <linearGradient id="go-ring1" x1="0" y1="0" x2="100" y2="100" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#6172f3" stopOpacity="0.7" />
                      <stop offset="1" stopColor="#10b981" stopOpacity="0.5" />
                    </linearGradient>
                  </defs>
                </svg>

                {/* Inner ring — counter spin */}
                <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" style={{ animation: 'go-spin-slow 8s linear infinite reverse' }}>
                  <circle cx="50" cy="50" r="36" fill="none" stroke="rgba(16, 185, 129, 0.1)" strokeWidth="1" />
                  <circle cx="50" cy="50" r="36" fill="none" stroke="url(#go-ring2)" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="20 207" />
                  <defs>
                    <linearGradient id="go-ring2" x1="100" y1="0" x2="0" y2="100" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#10b981" stopOpacity="0.6" />
                      <stop offset="1" stopColor="#6172f3" stopOpacity="0.4" />
                    </linearGradient>
                  </defs>
                </svg>

                {/* Center orb */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="relative">
                    {/* Glow */}
                    <div
                      className="absolute -inset-3 rounded-full"
                      style={{
                        background: 'radial-gradient(circle, rgba(97, 114, 243, 0.2), transparent 70%)',
                        animation: 'go-pulse 2.5s ease-in-out infinite',
                      }}
                    />
                    {/* Core */}
                    <div
                      className="relative w-14 h-14 rounded-2xl flex flex-col items-center justify-center border border-white/[0.08]"
                      style={{
                        background: 'linear-gradient(135deg, rgba(97, 114, 243, 0.15), rgba(16, 185, 129, 0.1))',
                        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.06)',
                      }}
                    >
                      {finished ? (
                        <div className="w-5 h-5 border-2 border-emerald-400/40 border-t-emerald-400 rounded-full animate-spin" />
                      ) : (
                        <>
                          <span className="text-[18px] font-bold text-white/90 tabular-nums leading-none tracking-tight">
                            {step + 1}
                          </span>
                          <span className="text-[8px] font-semibold text-white/30 uppercase tracking-widest mt-0.5">
                            of {TOTAL}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* ── Title ── */}
            <div className="text-center mb-7" style={{ animation: 'go-fade-in 0.5s ease-out 0.25s both' }}>
              <h3 className="font-display text-[20px] font-semibold text-white/95 tracking-tight leading-snug">
                {finished ? 'Finishing Up' : 'Generating Your Plan'}
              </h3>
              <p className="text-[12px] text-white/35 mt-1.5 leading-relaxed">
                {finished
                  ? 'Saving your personalized study plan and resources'
                  : 'AI is building a plan tailored to your learning style'}
              </p>
            </div>

            {/* ── Steps Timeline ── */}
            <div className="space-y-0.5 mb-6">
              {STEPS.map((s, i) => {
                const done = finished ? true : i < step
                const active = !finished && i === step
                const pending = !done && !active

                return (
                  <div
                    key={i}
                    className="relative flex items-start gap-3.5 py-2 px-3 rounded-xl transition-all duration-500"
                    style={{
                      background: active ? 'rgba(97, 114, 243, 0.06)' : 'transparent',
                      animation: `go-fade-in 0.4s ease-out ${0.3 + i * 0.08}s both`,
                    }}
                  >
                    {/* Timeline dot + connector */}
                    <div className="flex flex-col items-center flex-shrink-0 pt-0.5">
                      <div className="relative">
                        {active && (
                          <div
                            className="absolute -inset-1.5 rounded-full"
                            style={{
                              background: 'rgba(16, 185, 129, 0.2)',
                              animation: 'go-pulse 2s ease-in-out infinite',
                            }}
                          />
                        )}
                        <div
                          className={`relative w-2.5 h-2.5 rounded-full transition-all duration-500 ${
                            done
                              ? 'bg-emerald-400 shadow-[0_0_6px_rgba(16,185,129,0.4)]'
                              : active
                                ? 'bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]'
                                : 'bg-white/10'
                          }`}
                        >
                          {done && (
                            <svg className="absolute -inset-[1px] text-navy-900" viewBox="0 0 12 12" fill="none">
                              <path d="M3.5 6.2L5.2 7.8 8.5 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                          )}
                        </div>
                      </div>
                      {/* Connector line */}
                      {i < TOTAL - 1 && (
                        <div
                          className="w-px flex-1 min-h-[12px] mt-1 transition-all duration-500"
                          style={{
                            background: done
                              ? 'linear-gradient(180deg, rgba(16, 185, 129, 0.4), rgba(16, 185, 129, 0.1))'
                              : 'rgba(255, 255, 255, 0.05)',
                          }}
                        />
                      )}
                    </div>

                    {/* Label + detail */}
                    <div className="flex-1 min-w-0 -mt-0.5">
                      <p className={`text-[13px] font-semibold leading-tight transition-colors duration-500 ${
                        done ? 'text-emerald-400/80' : active ? 'text-white/90' : 'text-white/20'
                      }`}>
                        {s.label}
                      </p>
                      {active && (
                        <p className="text-[11px] text-white/30 mt-0.5 leading-relaxed" style={{ animation: 'go-fade-in 0.3s ease-out' }}>
                          {s.detail}
                        </p>
                      )}
                    </div>

                    {/* Status */}
                    <div className="flex-shrink-0 pt-0.5">
                      {done && (
                        <span className="text-[10px] font-semibold text-emerald-400/60">Done</span>
                      )}
                      {active && (
                        <div className="flex items-center gap-1">
                          <div className="w-1 h-1 rounded-full bg-emerald-400" style={{ animation: 'go-pulse 1.5s ease-in-out infinite' }} />
                          <div className="w-1 h-1 rounded-full bg-emerald-400" style={{ animation: 'go-pulse 1.5s ease-in-out 0.3s infinite' }} />
                          <div className="w-1 h-1 rounded-full bg-emerald-400" style={{ animation: 'go-pulse 1.5s ease-in-out 0.6s infinite' }} />
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>

            {/* ── Footer ── */}
            <div
              className="flex items-center justify-between pt-4 border-t border-white/[0.04]"
              style={{ animation: 'go-fade-in 0.5s ease-out 0.6s both' }}
            >
              <div className="flex items-center gap-2">
                <div
                  className="w-1.5 h-1.5 rounded-full bg-emerald-400"
                  style={{ animation: 'go-pulse 2s ease-in-out infinite' }}
                />
                <span className="text-[11px] font-medium text-white/30 tabular-nums">
                  {formatTime(elapsed)} elapsed
                </span>
              </div>
              <span className="text-[10px] font-medium text-white/15 tabular-nums">
                {Math.round(progress)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Scoped keyframes */}
      <style>{`
        @keyframes go-card-in {
          from { opacity: 0; transform: scale(0.96) translateY(12px); }
          to { opacity: 1; transform: scale(1) translateY(0); }
        }
        @keyframes go-fade-in {
          from { opacity: 0; transform: translateY(6px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes go-shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        @keyframes go-spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes go-pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.08); }
        }
        @keyframes go-drift {
          0%, 100% { transform: translate(0, 0); opacity: 0.3; }
          25% { transform: translate(4px, -6px); opacity: 0.6; }
          50% { transform: translate(-2px, -10px); opacity: 0.4; }
          75% { transform: translate(5px, -4px); opacity: 0.7; }
        }
      `}</style>
    </div>
  )
}
