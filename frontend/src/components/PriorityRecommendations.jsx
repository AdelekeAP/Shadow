import { useState, useEffect } from 'react';
import api from '../services/api';

export default function PriorityRecommendations() {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('all'); // all, urgent, goal, recovery

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/v1/recommendations/priority-tasks?limit=10');

      if (response.data.success) {
        setRecommendations(response.data.recommendations);
      }
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setError('Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  const getRecommendationIcon = (type) => {
    switch(type) {
      case 'urgent':
        return '🔴';
      case 'goal_driven':
        return '🎯';
      case 'mood_based':
        return '😊';
      case 'recovery':
        return '⚠️';
      default:
        return '📝';
    }
  };

  const getRecommendationLabel = (type) => {
    switch(type) {
      case 'urgent':
        return 'Urgent';
      case 'goal_driven':
        return 'Goal-Driven';
      case 'mood_based':
        return 'Mood-Based';
      case 'recovery':
        return 'Recovery';
      default:
        return 'Standard';
    }
  };

  const getRecommendationMessage = (rec) => {
    const dueText = formatDueDate(rec.due_date);

    switch(rec.recommendation_type) {
      case 'urgent':
        if (rec.is_overdue) {
          return `This is overdue! Complete it ASAP to avoid penalties.`;
        }
        // formatDueDate already returns "Due today" or "Due in X days"
        return `${dueText}. Don't delay!`;
      case 'goal_driven':
        return `High impact on your CGPA goal. Worth ${rec.weight} marks.`;
      case 'mood_based':
        return `Well-aligned with your current energy level.`;
      case 'recovery':
        return `Critical for getting back on track with your goals.`;
      default:
        return `Complete this to stay on top of your coursework.`;
    }
  };

  const getPriorityColor = (score) => {
    if (score >= 8) return 'text-red-600 bg-red-50';
    if (score >= 6) return 'text-orange-600 bg-orange-50';
    if (score >= 4) return 'text-yellow-600 bg-yellow-50';
    return 'text-blue-600 bg-blue-50';
  };

  const getPriorityBadge = (score) => {
    if (score >= 8) return '🔥 Critical';
    if (score >= 6) return '⚡ High';
    if (score >= 4) return '📌 Medium';
    return '💡 Low';
  };

  const formatDueDate = (dueDate) => {
    if (!dueDate) return 'No deadline';

    const date = new Date(dueDate);
    const now = new Date();
    const diffTime = date - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) return `Overdue by ${Math.abs(diffDays)} day(s)`;
    if (diffDays === 0) return 'Due today';
    if (diffDays === 1) return 'Due tomorrow';
    if (diffDays <= 7) return `Due in ${diffDays} days`;

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const filteredRecommendations = activeTab === 'all'
    ? recommendations
    : recommendations.filter(rec => rec.recommendation_type === activeTab);

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="flex flex-col items-center justify-center h-64">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
          <div className="text-gray-600 font-medium">Analyzing your tasks...</div>
          <div className="text-gray-400 text-sm mt-1">Calculating priorities</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="flex flex-col items-center justify-center h-64">
          <div className="text-6xl mb-4">⚠️</div>
          <div className="text-red-600 font-semibold text-lg">{error}</div>
          <button
            onClick={fetchRecommendations}
            className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="p-6 bg-gradient-to-r from-blue-50 to-purple-50">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <span className="text-3xl">🎯</span>
            What to Focus On Next
          </h2>
        </div>
        <div className="flex flex-col items-center justify-center h-64 text-gray-500">
          <div className="text-6xl mb-4">🎉</div>
          <p className="text-xl font-bold text-gray-700">All caught up!</p>
          <p className="text-sm mt-2 text-gray-500">No pending tasks at the moment</p>
          <p className="text-xs mt-4 text-gray-400">Great work staying on top of your coursework!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-100">
      {/* Header */}
      <div className="p-8 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 relative overflow-hidden">
        {/* Decorative circles */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white opacity-10 rounded-full -mr-32 -mt-32"></div>
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white opacity-10 rounded-full -ml-24 -mb-24"></div>

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-14 h-14 bg-white rounded-2xl shadow-lg flex items-center justify-center text-3xl transform rotate-3 hover:rotate-6 transition-transform">
              🎯
            </div>
            <h2 className="text-3xl font-extrabold text-white tracking-tight">
              What to Focus On Next
            </h2>
          </div>
          <p className="text-white text-opacity-90 text-sm font-medium ml-1">
            AI-powered recommendations • {recommendations.length} tasks ranked by priority
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 px-6 bg-gray-50">
        <button
          onClick={() => setActiveTab('all')}
          className={`py-4 px-6 font-semibold text-sm border-b-3 transition-all ${
            activeTab === 'all'
              ? 'border-blue-600 text-blue-700 bg-white -mb-px'
              : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <span>All Tasks</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
              activeTab === 'all' ? 'bg-blue-100 text-blue-700' : 'bg-gray-200 text-gray-600'
            }`}>
              {recommendations.length}
            </span>
          </div>
        </button>
        <button
          onClick={() => setActiveTab('urgent')}
          className={`py-4 px-6 font-semibold text-sm border-b-3 transition-all ${
            activeTab === 'urgent'
              ? 'border-red-600 text-red-700 bg-white -mb-px'
              : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <span>🔴</span>
            <span>Urgent</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
              activeTab === 'urgent' ? 'bg-red-100 text-red-700' : 'bg-gray-200 text-gray-600'
            }`}>
              {recommendations.filter(r => r.recommendation_type === 'urgent').length}
            </span>
          </div>
        </button>
        <button
          onClick={() => setActiveTab('goal_driven')}
          className={`py-4 px-6 font-semibold text-sm border-b-3 transition-all ${
            activeTab === 'goal_driven'
              ? 'border-green-600 text-green-700 bg-white -mb-px'
              : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <span>🎯</span>
            <span>Goal Impact</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
              activeTab === 'goal_driven' ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'
            }`}>
              {recommendations.filter(r => r.recommendation_type === 'goal_driven').length}
            </span>
          </div>
        </button>
        <button
          onClick={() => setActiveTab('recovery')}
          className={`py-4 px-6 font-semibold text-sm border-b-3 transition-all ${
            activeTab === 'recovery'
              ? 'border-orange-600 text-orange-700 bg-white -mb-px'
              : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <span>⚠️</span>
            <span>Recovery</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
              activeTab === 'recovery' ? 'bg-orange-100 text-orange-700' : 'bg-gray-200 text-gray-600'
            }`}>
              {recommendations.filter(r => r.recommendation_type === 'recovery').length}
            </span>
          </div>
        </button>
      </div>

      {/* Recommendations List */}
      <div className="p-8 space-y-6 bg-gradient-to-b from-gray-50 to-gray-100">
        {filteredRecommendations.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-lg border-2 border-dashed border-gray-300">
            <div className="text-5xl mb-3">
              {activeTab === 'urgent' ? '✅' : activeTab === 'goal_driven' ? '🎯' : activeTab === 'recovery' ? '💪' : '📝'}
            </div>
            <p className="text-gray-700 font-semibold text-lg">
              No {activeTab !== 'all' ? getRecommendationLabel(activeTab) : ''} tasks right now
            </p>
            <p className="text-gray-500 text-sm mt-2">
              {activeTab === 'urgent' && "You're all caught up with urgent deadlines!"}
              {activeTab === 'goal_driven' && "No high-impact tasks at the moment"}
              {activeTab === 'recovery' && "You're on track with your goals!"}
            </p>
          </div>
        ) : (
          filteredRecommendations.map((rec, index) => (
            <div
              key={rec.task_id}
              className={`relative overflow-hidden rounded-2xl shadow-md hover:shadow-2xl transition-all duration-300 cursor-pointer transform hover:-translate-y-1 bg-white border-2 ${
                rec.is_overdue
                  ? 'border-red-400 bg-gradient-to-br from-red-50 via-white to-white'
                  : rec.priority_score >= 8
                  ? 'border-red-300 bg-gradient-to-br from-red-50 via-orange-50 to-white'
                  : rec.priority_score >= 6
                  ? 'border-orange-300 bg-gradient-to-br from-orange-50 via-yellow-50 to-white'
                  : 'border-blue-200 bg-gradient-to-br from-blue-50 via-indigo-50 to-white'
              }`}
            >
              {/* Priority stripe on the left */}
              <div className={`absolute left-0 top-0 bottom-0 w-2 ${
                rec.is_overdue
                  ? 'bg-gradient-to-b from-red-600 to-red-400'
                  : rec.priority_score >= 8
                  ? 'bg-gradient-to-b from-red-500 to-orange-500'
                  : rec.priority_score >= 6
                  ? 'bg-gradient-to-b from-orange-500 to-yellow-500'
                  : 'bg-gradient-to-b from-blue-500 to-indigo-500'
              }`}></div>

              <div className="p-6 pl-8">
              <div className="flex items-start gap-5">
                {/* Rank Badge - Premium Design */}
                <div className={`flex-shrink-0 w-16 h-16 rounded-2xl flex items-center justify-center font-black text-2xl shadow-xl transform hover:scale-110 transition-transform ${
                  index === 0
                    ? 'bg-gradient-to-br from-yellow-400 via-yellow-500 to-yellow-600 text-white border-4 border-yellow-200'
                    : index === 1
                    ? 'bg-gradient-to-br from-gray-300 via-gray-400 to-gray-500 text-white border-4 border-gray-200'
                    : index === 2
                    ? 'bg-gradient-to-br from-orange-400 via-orange-500 to-orange-600 text-white border-4 border-orange-200'
                    : 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white border-2 border-indigo-300'
                }`}>
                  <span className="drop-shadow-lg">{index + 1}</span>
                </div>

                <div className="flex-1">
                  {/* Priority Badge - Top Right */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <h3 className="font-black text-gray-900 text-xl leading-tight">
                        {rec.title}
                      </h3>
                    </div>
                    <div className={`px-4 py-2 rounded-xl text-xs font-extrabold shadow-md ${getPriorityColor(rec.priority_score)}`}>
                      {getPriorityBadge(rec.priority_score)}
                    </div>
                  </div>

                  {/* Course and Task Type */}
                  <div className="flex items-center gap-3 mb-4">
                    <span className="px-4 py-1.5 bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-sm font-black rounded-full shadow-md">
                      {rec.course_code}
                    </span>
                    <span className="text-sm text-gray-700 font-semibold bg-gray-100 px-3 py-1 rounded-full">
                      {rec.task_type} • {rec.weight} marks
                    </span>
                  </div>

                  {/* Recommendation Message - Clear, Human Language */}
                  <div className={`text-sm font-semibold mb-4 p-4 rounded-xl shadow-sm border-l-4 ${
                    rec.recommendation_type === 'urgent'
                      ? 'bg-gradient-to-r from-red-50 to-red-100 text-red-900 border-red-500'
                      : rec.recommendation_type === 'goal_driven'
                      ? 'bg-gradient-to-r from-green-50 to-green-100 text-green-900 border-green-500'
                      : rec.recommendation_type === 'recovery'
                      ? 'bg-gradient-to-r from-orange-50 to-orange-100 text-orange-900 border-orange-500'
                      : 'bg-gradient-to-r from-blue-50 to-blue-100 text-blue-900 border-blue-500'
                  }`}>
                    <span className="text-xl mr-2">{getRecommendationIcon(rec.recommendation_type)}</span>
                    {getRecommendationMessage(rec)}
                  </div>

                  {/* Visual Priority Bar */}
                  <div className="mb-4 bg-white p-4 rounded-xl shadow-sm">
                    <div className="flex items-center justify-between text-xs font-bold text-gray-700 mb-2">
                      <span>Priority Level</span>
                      <span className="text-base">{Math.round((rec.priority_score / 10) * 100)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden shadow-inner">
                      <div
                        className={`h-4 rounded-full transition-all duration-700 shadow-lg ${
                          rec.priority_score >= 8
                            ? 'bg-gradient-to-r from-red-500 via-red-600 to-red-700'
                            : rec.priority_score >= 6
                            ? 'bg-gradient-to-r from-orange-400 via-orange-500 to-orange-600'
                            : rec.priority_score >= 4
                            ? 'bg-gradient-to-r from-yellow-400 via-yellow-500 to-yellow-600'
                            : 'bg-gradient-to-r from-blue-400 via-blue-500 to-blue-600'
                        }`}
                        style={{ width: `${(rec.priority_score / 10) * 100}%` }}
                      />
                    </div>
                  </div>

                  {/* Due Date - Prominent */}
                  <div className={`text-sm font-bold flex items-center gap-2 px-4 py-2 rounded-lg ${
                    rec.is_overdue
                      ? 'bg-red-100 text-red-700 border border-red-300'
                      : 'bg-gray-100 text-gray-800 border border-gray-300'
                  }`}>
                    <span className="text-lg">📅</span>
                    {formatDueDate(rec.due_date)}
                  </div>
                </div>
              </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
