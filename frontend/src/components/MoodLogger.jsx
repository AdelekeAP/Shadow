import { useState } from 'react';
import api from '../services/api';

export default function MoodLogger({ onMoodLogged }) {
  const [isOpen, setIsOpen] = useState(false);
  const [formData, setFormData] = useState({
    mood_type: '',
    energy_level: 3,
    note: ''
  });
  const [loading, setLoading] = useState(false);
  const [sentimentFeedback, setSentimentFeedback] = useState(null);

  const moodOptions = [
    { value: 'focused', label: '🎯 Focused', color: 'bg-blue-100 text-blue-800 border-blue-300' },
    { value: 'motivated', label: '💪 Motivated', color: 'bg-green-100 text-green-800 border-green-300' },
    { value: 'calm', label: '😌 Calm', color: 'bg-teal-100 text-teal-800 border-teal-300' },
    { value: 'confident', label: '😎 Confident', color: 'bg-purple-100 text-purple-800 border-purple-300' },
    { value: 'tired', label: '😴 Tired', color: 'bg-gray-100 text-gray-800 border-gray-300' },
    { value: 'stressed', label: '😰 Stressed', color: 'bg-orange-100 text-orange-800 border-orange-300' },
    { value: 'anxious', label: '😟 Anxious', color: 'bg-yellow-100 text-yellow-800 border-yellow-300' },
    { value: 'overwhelmed', label: '😵 Overwhelmed', color: 'bg-red-100 text-red-800 border-red-300' }
  ];

  const energyLevels = [
    { value: 1, label: 'Very Low', emoji: '🪫', color: 'bg-red-500' },
    { value: 2, label: 'Low', emoji: '🔋', color: 'bg-orange-500' },
    { value: 3, label: 'Medium', emoji: '⚡', color: 'bg-yellow-500' },
    { value: 4, label: 'High', emoji: '🔥', color: 'bg-green-500' },
    { value: 5, label: 'Very High', emoji: '⚡⚡', color: 'bg-blue-500' }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.mood_type) {
      alert('Please select a mood');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/api/v1/mood/log-mood', formData);

      if (response.data.success) {
        // Show sentiment feedback if available
        if (response.data.sentiment_analysis) {
          const { label, confidence } = response.data.sentiment_analysis;
          setSentimentFeedback({
            label,
            confidence,
            message: `AI detected ${label.toLowerCase()} sentiment (${Math.round(confidence * 100)}% confidence)`
          });

          // Auto-hide feedback after 5 seconds
          setTimeout(() => setSentimentFeedback(null), 5000);
        }

        // Reset form
        setFormData({ mood_type: '', energy_level: 3, note: '' });
        setIsOpen(false);

        // Notify parent
        if (onMoodLogged) {
          onMoodLogged(response.data.mood_log);
        }

        // Show actionable feedback based on mood
        let actionMsg = '';
        if (formData.energy_level <= 2) {
          actionMsg = '\n\n💡 Low energy detected. We\'ll prioritize easier tasks for you.';
        } else if (formData.mood_type === 'stressed' || formData.mood_type === 'overwhelmed') {
          actionMsg = '\n\n💡 Feeling stressed? We recommend tackling quick wins first.';
        } else if (formData.mood_type === 'focused' || formData.mood_type === 'motivated') {
          actionMsg = '\n\n💪 Great energy! This is a good time for challenging tasks.';
        }

        alert(`Mood logged successfully!${actionMsg}`);
      }
    } catch (error) {
      console.error('Error logging mood:', error);
      alert('Failed to log mood');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-full shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 font-semibold flex items-center gap-2 z-50"
      >
        <span className="text-xl">💭</span>
        <span>Log Mood</span>
      </button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">How are you feeling?</h2>
          <button
            onClick={() => setIsOpen(false)}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Mood Selection */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Select your mood
            </label>
            <div className="grid grid-cols-2 gap-2">
              {moodOptions.map((mood) => (
                <button
                  key={mood.value}
                  type="button"
                  onClick={() => setFormData({ ...formData, mood_type: mood.value })}
                  className={`px-4 py-3 rounded-lg border-2 font-medium transition-all ${
                    formData.mood_type === mood.value
                      ? `${mood.color} border-current shadow-md transform scale-105`
                      : 'bg-white text-gray-700 border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {mood.label}
                </button>
              ))}
            </div>
          </div>

          {/* Energy Level */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Energy level: {energyLevels.find(e => e.value === formData.energy_level)?.emoji} {energyLevels.find(e => e.value === formData.energy_level)?.label}
            </label>
            <div className="flex items-center gap-2">
              {energyLevels.map((level) => (
                <button
                  key={level.value}
                  type="button"
                  onClick={() => setFormData({ ...formData, energy_level: level.value })}
                  className={`flex-1 h-12 rounded-lg transition-all ${
                    formData.energy_level === level.value
                      ? `${level.color} text-white shadow-md transform scale-110`
                      : 'bg-gray-200 hover:bg-gray-300'
                  }`}
                  title={level.label}
                >
                  <span className="text-lg">{level.emoji}</span>
                </button>
              ))}
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1 px-1">
              <span>Very Low</span>
              <span>Very High</span>
            </div>
          </div>

          {/* Optional Note */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Note (optional)
              <span className="ml-2 text-xs font-normal text-indigo-600">✨ AI-powered sentiment analysis</span>
            </label>
            <textarea
              value={formData.note}
              onChange={(e) => setFormData({ ...formData, note: e.target.value })}
              placeholder="What's on your mind? (AI will analyze sentiment)"
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all"
              rows="3"
              maxLength="500"
            />
            <div className="text-xs text-gray-500 text-right mt-1">
              {formData.note.length}/500
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="flex-1 px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !formData.mood_type}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading ? 'Saving...' : 'Log Mood'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
