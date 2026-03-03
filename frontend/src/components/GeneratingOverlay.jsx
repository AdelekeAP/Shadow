export default function GeneratingOverlay({ generatingStep }) {
  return (
    <div className="fixed inset-0 z-50 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-sm w-full text-center animate-scale-in">
        {/* Animated ring */}
        <div className="w-16 h-16 mx-auto mb-5 relative">
          <svg className="w-16 h-16 -rotate-90" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="none" stroke="#e5e7ee" strokeWidth="3" />
            <circle cx="32" cy="32" r="28" fill="none" stroke="#1e3a8a" strokeWidth="3"
              strokeDasharray="175.93" strokeDashoffset={175.93 - (generatingStep + 1) / 3 * 175.93}
              strokeLinecap="round" className="transition-all duration-700 ease-out" />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-6 h-6 border-2 border-navy-200 border-t-navy-800 rounded-full animate-spin" />
          </div>
        </div>

        <h3 className="text-[16px] font-display font-bold text-navy-900 mb-4">Generating Study Plan</h3>

        {/* Step indicators */}
        <div className="space-y-2.5">
          {[
            { label: 'Analyzing your topic', icon: 'search' },
            { label: 'Finding resources', icon: 'globe' },
            { label: 'Building your plan', icon: 'sparkle' },
          ].map((step, i) => (
            <div key={i} className={`flex items-center gap-2.5 px-3 py-2 rounded-lg transition-all duration-500 ${
              i === generatingStep ? 'bg-navy-800/[0.04] text-navy-800' :
              i < generatingStep ? 'text-emerald-600' : 'text-surface-300'
            }`}>
              {i < generatingStep ? (
                <svg className="w-4 h-4 text-emerald-500 animate-check-pop" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              ) : i === generatingStep ? (
                <div className="w-4 h-4 border-2 border-navy-200 border-t-navy-700 rounded-full animate-spin" />
              ) : (
                <div className="w-4 h-4 rounded-full border-2 border-surface-200" />
              )}
              <span className="text-[13px] font-medium">{step.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
