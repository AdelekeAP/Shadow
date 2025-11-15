import { Link } from 'react-router-dom'

function HomePage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="text-center px-4">
        <h1 className="text-6xl font-bold text-gray-900 mb-4">
          Shadow
        </h1>
        <p className="text-xl text-gray-600 mb-2">
          Goal-Driven Academic Achievement System
        </p>
        <p className="text-md text-gray-500 mb-8">
          For Pan-Atlantic University Students
        </p>

        <div className="space-x-4">
          <Link
            to="/login"
            className="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            Login
          </Link>
          <Link
            to="/register"
            className="inline-block bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold border-2 border-blue-600 hover:bg-blue-50 transition"
          >
            Register
          </Link>
        </div>

        <div className="mt-12 text-gray-500">
          <p className="text-sm">Track your CGPA • Prioritize tasks • Achieve your goals</p>
        </div>
      </div>
    </div>
  )
}

export default HomePage
