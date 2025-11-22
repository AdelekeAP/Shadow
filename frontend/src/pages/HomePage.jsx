import { Link } from 'react-router-dom'

function HomePage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-stone-50">
      <div className="text-center px-4">
        <h1 className="text-6xl font-bold text-stone-900 mb-4">
          Shadow
        </h1>
        <p className="text-xl text-stone-600 mb-2">
          Goal-Driven Academic Achievement System
        </p>
        <p className="text-md text-stone-500 mb-8">
          For Pan-Atlantic University Students
        </p>

        <div className="space-x-4">
          <Link
            to="/login"
            className="inline-block bg-navy-800 text-white px-8 py-3 rounded-lg font-semibold hover:bg-navy-900 transition-colors"
          >
            Login
          </Link>
          <Link
            to="/register"
            className="inline-block bg-white text-navy-800 px-8 py-3 rounded-lg font-semibold border-2 border-stone-300 hover:border-navy-800 hover:bg-navy-50 transition-all"
          >
            Register
          </Link>
        </div>

        <div className="mt-12 text-stone-500">
          <p className="text-sm">Track your CGPA • Prioritize tasks • Achieve your goals</p>
        </div>
      </div>
    </div>
  )
}

export default HomePage
