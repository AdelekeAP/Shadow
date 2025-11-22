import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { VictoryPie, VictoryChart, VictoryLine, VictoryAxis, VictoryTheme, VictoryBar } from 'victory';
import api from '../services/api';

export default function CGPADashboard() {
  const navigate = useNavigate();
  const [cgpaData, setCgpaData] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview'); // overview, analytics, breakdown

  useEffect(() => {
    fetchCGPAData();
  }, []);

  const fetchCGPAData = async () => {
    try {
      setLoading(true);
      const [dashboardRes, analyticsRes] = await Promise.all([
        api.get('/api/v1/cgpa/dashboard'),
        api.get('/api/v1/cgpa/analytics')
      ]);

      setCgpaData(dashboardRes.data.data);
      setAnalytics(analyticsRes.data.analytics);
      setError(null);
    } catch (err) {
      console.error('Error fetching CGPA data:', err);
      setError('Failed to load CGPA data');
    } finally {
      setLoading(false);
    }
  };

  // Helper function to safely format numbers
  const formatNumber = (value, decimals = 2) => {
    if (value === null || value === undefined) return '0.00';
    const num = typeof value === 'number' ? value : parseFloat(value);
    return isNaN(num) ? '0.00' : num.toFixed(decimals);
  };

  const getGPAColor = (gpa) => {
    if (gpa >= 4.5) return 'text-green-600';
    if (gpa >= 3.5) return 'text-navy-800';
    if (gpa >= 2.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getGPABgColor = (gpa) => {
    if (gpa >= 4.5) return 'bg-green-100';
    if (gpa >= 3.5) return 'bg-blue-100';
    if (gpa >= 2.5) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-navy-800"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        {error}
      </div>
    );
  }

  if (!cgpaData) {
    return (
      <div className="bg-stone-50 border border-stone-200 rounded-lg p-4 text-stone-700">
        No CGPA data available yet. Start adding courses and grades!
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Back Button and Tabs */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center text-stone-600 hover:text-stone-900 font-medium transition"
          >
            <span className="mr-2">←</span> Back to Dashboard
          </button>
          <h2 className="text-2xl font-bold text-stone-900">CGPA Dashboard</h2>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              activeTab === 'overview'
                ? 'bg-navy-800 text-white'
                : 'bg-stone-100 text-stone-700 hover:bg-stone-200'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              activeTab === 'analytics'
                ? 'bg-navy-800 text-white'
                : 'bg-stone-100 text-stone-700 hover:bg-stone-200'
            }`}
          >
            Analytics
          </button>
          <button
            onClick={() => setActiveTab('breakdown')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              activeTab === 'breakdown'
                ? 'bg-navy-800 text-white'
                : 'bg-stone-100 text-stone-700 hover:bg-stone-200'
            }`}
          >
            Breakdown
          </button>
        </div>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Current CGPA Card */}
          <div className={`${getGPABgColor(cgpaData.current.cgpa)} rounded-xl p-8 border-2 border-opacity-50`}>
            <div className="flex justify-between items-start">
              <div>
                <p className="text-stone-600 font-medium mb-2">Current CGPA</p>
                <p className={`text-6xl font-bold ${getGPAColor(cgpaData.current.cgpa)}`}>
                  {formatNumber(cgpaData.current.cgpa, 2)}
                </p>
                <p className="text-stone-600 mt-2">
                  {cgpaData.current.total_credits} credits completed
                </p>
              </div>
              <div className="text-right">
                <div className="bg-white rounded-lg p-4 shadow-sm">
                  <p className="text-sm text-stone-600">Classification</p>
                  <p className="text-lg font-bold text-stone-900">
                    {cgpaData.current.cgpa >= 4.5 ? 'First Class' :
                     cgpaData.current.cgpa >= 3.5 ? 'Second Class Upper' :
                     cgpaData.current.cgpa >= 2.5 ? 'Second Class Lower' :
                     cgpaData.current.cgpa >= 1.5 ? 'Third Class' : 'Pass'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Predicted CGPA */}
            <div className="bg-white rounded-lg shadow p-6 border border-stone-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-stone-600 text-sm font-medium">Predicted Final CGPA</p>
                  <p className={`text-3xl font-bold mt-2 ${getGPAColor(cgpaData.predictions.predicted_cgpa)}`}>
                    {formatNumber(cgpaData.predictions.predicted_cgpa, 2)}
                  </p>
                </div>
                <div className="text-2xl">🎯</div>
              </div>
              <p className="text-xs text-stone-500 mt-2">
                Based on current performance trends
              </p>
            </div>

            {/* Total Courses */}
            <div className="bg-white rounded-lg shadow p-6 border border-stone-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-stone-600 text-sm font-medium">Total Courses</p>
                  <p className="text-3xl font-bold mt-2 text-stone-900">
                    {cgpaData.total_courses}
                  </p>
                </div>
                <div className="text-2xl">📚</div>
              </div>
              <p className="text-xs text-stone-500 mt-2">
                {cgpaData.semesters.length} semesters completed
              </p>
            </div>

            {/* Target Analysis */}
            <div className="bg-white rounded-lg shadow p-6 border border-stone-200">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-stone-600 text-xs font-medium mb-1">
                    To reach Target CGPA: {formatNumber(cgpaData.target_analysis.target_cgpa, 2)}
                  </p>
                  <p className="text-stone-700 text-sm font-semibold mb-2">
                    Required Semester GPA:
                  </p>
                  <p className={`text-3xl font-bold ${
                    cgpaData.target_analysis.is_achievable ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatNumber(cgpaData.target_analysis.required_gpa, 2)}
                  </p>
                  <p className={`text-xs mt-1 ${
                    cgpaData.target_analysis.is_achievable ? 'text-green-600' : 'text-red-600'
                  } font-medium`}>
                    {cgpaData.target_analysis.is_achievable
                      ? '(Achievable - Max GPA is 5.0)'
                      : '(Impossible - Max GPA is 5.0)'}
                  </p>
                </div>
                <div className="text-2xl">
                  {cgpaData.target_analysis.is_achievable ? '✅' : '⚠️'}
                </div>
              </div>
              <p className={`text-xs mt-3 px-2 py-1 rounded ${
                cgpaData.target_analysis.is_achievable
                  ? 'bg-green-50 text-green-700'
                  : 'bg-red-50 text-red-700'
              }`}>
                {cgpaData.target_analysis.difficulty}
              </p>
            </div>
          </div>

          {/* Semester Trend Chart */}
          {analytics && analytics.semester_gpa_history && analytics.semester_gpa_history.length > 1 && (
            <div className="bg-white rounded-lg shadow p-6 border border-stone-200">
              <h3 className="text-lg font-semibold mb-4">Semester Performance Trend</h3>
              <div className="h-64">
                <VictoryChart
                  theme={VictoryTheme.material}
                  height={250}
                  padding={{ top: 20, bottom: 40, left: 50, right: 20 }}
                >
                  <VictoryAxis
                    label="Semester"
                    style={{
                      axisLabel: { fontSize: 12, padding: 30 }
                    }}
                  />
                  <VictoryAxis
                    dependentAxis
                    label="GPA"
                    domain={[0, 5.0]}
                    style={{
                      axisLabel: { fontSize: 12, padding: 40 }
                    }}
                  />
                  <VictoryLine
                    data={analytics.semester_gpa_history.map((gpa, index) => ({
                      x: index + 1,
                      y: gpa
                    }))}
                    style={{
                      data: { stroke: '#9333ea', strokeWidth: 3 }
                    }}
                  />
                </VictoryChart>
              </div>
              <div className="flex justify-center mt-4">
                <div className={`px-4 py-2 rounded-full ${
                  analytics.trend === 'Improving' ? 'bg-green-100 text-green-700' :
                  analytics.trend === 'Declining' ? 'bg-red-100 text-red-700' :
                  'bg-stone-100 text-stone-700'
                }`}>
                  Trend: {analytics.trend}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Analytics Tab */}
      {activeTab === 'analytics' && analytics && (
        <div className="space-y-6">
          {/* Performance Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-green-50 rounded-lg p-6 border-2 border-green-200">
              <p className="text-green-700 text-sm font-medium">Best Semester GPA</p>
              <p className="text-4xl font-bold text-green-600 mt-2">
                {formatNumber(analytics.best_semester_gpa, 2)}
              </p>
            </div>
            <div className="bg-blue-50 rounded-lg p-6 border-2 border-blue-200">
              <p className="text-blue-700 text-sm font-medium">Average Semester GPA</p>
              <p className="text-4xl font-bold text-navy-800 mt-2">
                {formatNumber(analytics.average_semester_gpa, 2)}
              </p>
            </div>
            <div className="bg-orange-50 rounded-lg p-6 border-2 border-orange-200">
              <p className="text-orange-700 text-sm font-medium">Worst Semester GPA</p>
              <p className="text-4xl font-bold text-orange-600 mt-2">
                {formatNumber(analytics.worst_semester_gpa, 2)}
              </p>
            </div>
          </div>

          {/* Grade Distribution */}
          {analytics.grade_distribution && Object.keys(analytics.grade_distribution).length > 0 && (
            <div className="bg-white rounded-lg shadow p-6 border border-stone-200">
              <h3 className="text-lg font-semibold mb-4">Grade Distribution</h3>
              <div className="flex flex-col md:flex-row items-center justify-around">
                <div className="w-full md:w-1/2">
                  <VictoryPie
                    data={Object.entries(analytics.grade_distribution).map(([grade, count]) => ({
                      x: grade,
                      y: count,
                      label: `${grade}: ${count}`
                    }))}
                    colorScale={['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#6b7280']}
                    height={300}
                  />
                </div>
                <div className="w-full md:w-1/2 space-y-2">
                  {Object.entries(analytics.grade_distribution)
                    .sort(([, a], [, b]) => b - a)
                    .map(([grade, count]) => (
                      <div key={grade} className="flex justify-between items-center p-3 bg-stone-50 rounded">
                        <span className="font-medium">{grade}</span>
                        <span className="text-stone-600">{count} course{count !== 1 ? 's' : ''}</span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Breakdown Tab */}
      {activeTab === 'breakdown' && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Semester-by-Semester Breakdown</h3>
          {cgpaData.semesters.map((semester, index) => (
            <div key={index} className="bg-white rounded-lg shadow border border-stone-200 overflow-hidden">
              <div className="bg-gradient-to-r from-navy-800 to-navy-700 p-4 text-white">
                <div className="flex justify-between items-center">
                  <h4 className="text-lg font-bold">{semester.name}</h4>
                  <div className="text-right">
                    <p className="text-sm opacity-90">Semester GPA</p>
                    <p className="text-2xl font-bold">
                      {semester.courses && semester.courses.length > 0
                        ? (() => {
                            const totalCredits = semester.courses.reduce((sum, c) => sum + (c.credits || 0), 0);
                            const totalQP = semester.courses.reduce(
                              (sum, c) => sum + ((c.grade_point || 0) * (c.credits || 0)),
                              0
                            );
                            return formatNumber(totalQP / totalCredits, 2);
                          })()
                        : '0.00'}
                    </p>
                  </div>
                </div>
              </div>
              <div className="p-4">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 text-sm font-semibold">Course</th>
                      <th className="text-center py-2 text-sm font-semibold">Credits</th>
                      <th className="text-center py-2 text-sm font-semibold">Score</th>
                      <th className="text-center py-2 text-sm font-semibold">Grade</th>
                      <th className="text-center py-2 text-sm font-semibold">Points</th>
                    </tr>
                  </thead>
                  <tbody>
                    {semester.courses && semester.courses.map((course, idx) => (
                      <tr key={idx} className="border-b hover:bg-stone-50">
                        <td className="py-3">
                          <div>
                            <p className="font-medium text-sm">{course.code}</p>
                            <p className="text-xs text-stone-600">{course.name}</p>
                          </div>
                        </td>
                        <td className="text-center text-sm">{course.credits}</td>
                        <td className="text-center text-sm font-medium">
                          {course.score && typeof course.score === 'number' && course.score > 0
                            ? course.score.toFixed(1)
                            : 'N/A'}
                        </td>
                        <td className="text-center">
                          <span className={`px-2 py-1 rounded text-xs font-bold ${
                            course.grade === 'A' ? 'bg-green-100 text-green-700' :
                            course.grade === 'B' ? 'bg-blue-100 text-blue-700' :
                            course.grade === 'C' ? 'bg-yellow-100 text-yellow-700' :
                            course.grade === 'D' ? 'bg-orange-100 text-orange-700' :
                            'bg-stone-100 text-stone-700'
                          }`}>
                            {course.grade}
                          </span>
                        </td>
                        <td className="text-center text-sm font-medium">
                          {course.grade_point && typeof course.grade_point === 'number'
                            ? course.grade_point.toFixed(1)
                            : '0.0'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="mt-4 flex justify-between items-center bg-stone-50 p-3 rounded">
                  <span className="font-semibold">Total Credits:</span>
                  <span className="font-bold">
                    {semester.courses ? semester.courses.reduce((sum, c) => sum + c.credits, 0) : 0}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
