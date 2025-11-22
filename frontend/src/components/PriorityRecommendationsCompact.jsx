import { useState, useEffect } from 'react';
import api from '../services/api';

export default function PriorityRecommendationsCompact({ onTaskClick }) {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/v1/recommendations/priority-tasks?limit=3');

      if (response.data.success) {
        setRecommendations(response.data.recommendations.slice(0, 3)); // Top 3 only
      }
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setError('Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (score) => {
    if (score >= 8) return { bg: 'bg-red-500', text: 'text-red-700', border: 'border-red-500', light: 'bg-red-50' };
    if (score >= 6) return { bg: 'bg-orange-500', text: 'text-orange-700', border: 'border-orange-500', light: 'bg-orange-50' };
    return { bg: 'bg-yellow-500', text: 'text-yellow-700', border: 'border-yellow-500', light: 'bg-yellow-50' };
  };

  const getPriorityLabel = (score) => {
    if (score >= 8) return '🔥 CRITICAL';
    if (score >= 6) return '⚡ HIGH';
    return '💼 MEDIUM';
  };

  const formatDueDate = (dueDate) => {
    if (!dueDate) return null;
    const date = new Date(dueDate);
    const now = new Date();
    const diffTime = date - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) return `Overdue ${Math.abs(diffDays)}d`;
    if (diffDays === 0) return 'Due today';
    if (diffDays === 1) return 'Due tomorrow';
    return `Due in ${diffDays}d`;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-6 bg-stone-200 rounded w-1/3"></div>
          <div className="h-20 bg-stone-100 rounded"></div>
          <div className="h-20 bg-stone-100 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-6">
        <p className="text-red-600 text-sm">{error}</p>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-6">
        <div className="text-center py-8">
          <div className="text-4xl mb-2">🎉</div>
          <p className="text-stone-700 font-semibold">All caught up!</p>
          <p className="text-sm text-stone-500 mt-1">No pending tasks</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-stone-200 overflow-hidden">
      {/* Compact Header */}
      <div className="p-5 bg-gradient-to-r from-navy-800 to-navy-900">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-2xl">
            🎯
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">What to Focus On Next</h2>
            <p className="text-white/70 text-xs">AI-powered • Top {recommendations.length} priorities</p>
          </div>
        </div>
      </div>

      {/* Compact Cards */}
      <div className="p-5 space-y-3">
        {recommendations.map((rec, index) => {
          const colors = getPriorityColor(rec.priority_score);
          const priorityPercent = Math.round((rec.priority_score / 10) * 100);

          return (
            <div
              key={rec.task_id}
              className={`relative bg-white rounded-lg border-l-4 ${colors.border} p-4 hover:shadow-md transition-all ${colors.light}`}
            >
              <div className="flex items-start gap-4">
                {/* Rank Badge - Compact */}
                <div className={`flex-shrink-0 w-10 h-10 rounded-full ${colors.bg} text-white font-bold text-lg flex items-center justify-center shadow-sm`}>
                  {index + 1}
                </div>

                {/* Content - Horizontal Layout */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0 pr-3">
                      <h3 className="text-base font-bold text-stone-900 truncate">{rec.title}</h3>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-navy-100 text-navy-800">
                          {rec.course_code}
                        </span>
                        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-stone-100 text-stone-700">
                          {rec.task_type}
                        </span>
                        <span className="text-xs text-stone-600">{rec.weight} marks</span>
                        {rec.is_overdue && (
                          <span className="text-xs font-semibold text-red-600">
                            • {formatDueDate(rec.due_date)}
                          </span>
                        )}
                        {!rec.is_overdue && rec.due_date && (
                          <span className="text-xs text-stone-500">
                            • {formatDueDate(rec.due_date)}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Priority Badge */}
                    <span className={`flex-shrink-0 px-3 py-1 text-xs font-bold rounded-lg ${colors.light} ${colors.text} border ${colors.border}`}>
                      {getPriorityLabel(rec.priority_score)}
                    </span>
                  </div>

                  {/* Alert Message - Inline */}
                  {rec.is_overdue && (
                    <div className={`flex items-center gap-2 mb-3 p-2 rounded-md ${colors.light} border ${colors.border}`}>
                      <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      <p className="text-xs font-semibold">
                        Overdue! Complete ASAP to avoid penalties.
                      </p>
                    </div>
                  )}

                  {/* Priority Bar & CTA - Inline */}
                  <div className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-stone-600">Priority</span>
                        <span className={`text-sm font-bold ${colors.text}`}>{priorityPercent}%</span>
                      </div>
                      <div className="h-2 bg-stone-200 rounded-full overflow-hidden">
                        <div
                          className={`h-2 rounded-full ${colors.bg} transition-all duration-500`}
                          style={{ width: `${priorityPercent}%` }}
                        />
                      </div>
                    </div>

                    <button
                      onClick={() => onTaskClick?.(rec.task_id)}
                      className={`flex-shrink-0 px-4 py-2 ${colors.bg} hover:opacity-90 text-white text-xs font-medium rounded-lg transition-all`}
                    >
                      {index === 0 ? 'Work On This →' : index === 1 ? 'Start Task →' : 'View Task →'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
