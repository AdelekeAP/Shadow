import { Link } from 'react-router-dom'

function HomePage() {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-navy-900 via-navy-800 to-[#0c1425] relative overflow-hidden">
      {/* Grid overlay */}
      <div className="absolute inset-0 opacity-[0.03]" style={{
        backgroundImage: 'linear-gradient(rgba(255,255,255,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.15) 1px, transparent 1px)',
        backgroundSize: '48px 48px',
      }} />

      {/* Glow orbs */}
      <div className="absolute top-1/4 left-1/3 w-[500px] h-[500px] rounded-full bg-blue-500/[0.05] blur-[160px]" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] rounded-full bg-emerald-500/[0.04] blur-[140px]" />

      {/* Nav bar */}
      <nav className="relative z-10 flex items-center justify-between px-6 md:px-12 py-6">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
            <span className="text-white font-display text-[15px] font-bold">S</span>
          </div>
          <span className="text-[16px] font-bold text-white/90">Shadow</span>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/login"
            className="px-4 py-2 text-[13px] font-semibold text-white/60 hover:text-white transition-colors"
          >
            Sign in
          </Link>
          <Link
            to="/register"
            className="px-5 py-2.5 bg-white/10 hover:bg-white/15 backdrop-blur-sm text-white text-[13px] font-semibold rounded-xl border border-white/10 transition-all"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <div className="relative z-10 flex-1 flex items-center justify-center px-6">
        <div className="max-w-2xl text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.06] border border-white/[0.08] mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[11px] font-semibold text-white/50 uppercase tracking-wider">
              Built for Pan-Atlantic University
            </span>
          </div>

          <h1 className="font-display text-[3.5rem] md:text-[4.5rem] font-bold text-white leading-[1.05] tracking-tight mb-6">
            Your CGPA,<br />
            <span className="text-white/40">on track.</span>
          </h1>

          <p className="text-[16px] md:text-[18px] text-white/35 leading-relaxed max-w-lg mx-auto mb-10">
            AI-powered academic planning that helps you set targets, prioritize tasks, and achieve the grades you want.
          </p>

          {/* CTA buttons */}
          <div className="flex items-center justify-center gap-4">
            <Link
              to="/register"
              className="group flex items-center gap-2.5 px-7 py-3.5 bg-white text-navy-900 rounded-xl text-[14px] font-bold hover:bg-white/95 transition-all shadow-lg shadow-black/20"
            >
              Start Tracking
              <svg className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </Link>
            <Link
              to="/login"
              className="px-7 py-3.5 border border-white/15 text-white/70 hover:text-white hover:border-white/25 rounded-xl text-[14px] font-semibold transition-all"
            >
              Sign In
            </Link>
          </div>

          {/* Feature pills */}
          <div className="flex items-center justify-center gap-3 mt-14 flex-wrap">
            {[
              { icon: BarChartIcon, label: 'CGPA Predictions' },
              { icon: SparkleIcon, label: 'AI Study Plans' },
              { icon: ClockIcon, label: 'Task Prioritization' },
            ].map(f => (
              <div key={f.label} className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white/[0.04] border border-white/[0.06]">
                <f.icon className="w-3.5 h-3.5 text-white/30" />
                <span className="text-[12px] font-medium text-white/40">{f.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="relative z-10 text-center pb-8">
        <p className="text-[11px] text-white/15 font-medium">Pan-Atlantic University</p>
      </div>
    </div>
  )
}

/* ─── Icon components ─── */
function BarChartIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" /></svg>
}
function SparkleIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" /></svg>
}
function ClockIcon({ className }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
}

export default HomePage
