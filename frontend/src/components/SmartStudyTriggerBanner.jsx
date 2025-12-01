import { useState, useEffect } from 'react';
import api from '../services/api';

/**
 * SmartStudy Trigger Banner Component
 * Displays contextual recommendations to use SmartStudy based on user's academic state
 *
 * Trigger Types:
 * - overdue_tasks: 2+ overdue assignments
 * - cgpa_gap: Behind on CGPA goal
 * - negative_mood: Recent stress/anxiety patterns
 * - low_energy: Consistently low energy levels
 * - task_overload: 8+ pending tasks
 * - low_grades: Struggling in courses
 * - late_pattern: 3+ late submissions
 * - new_user: First-time user welcome
 */
export default function SmartStudyTriggerBanner({ onOpenSmartStudy }) {
  const [triggerData, setTriggerData] = useState(null);
  const [isVisible, setIsVisible] = useState(true);
  const [isDismissed, setIsDismissed] = useState(false);

  useEffect(() => {
    loadTriggers();
  }, []);

  const loadTriggers = async () => {
    try {
      const response = await api.get('/api/v1/smartstudy/triggers');
      setTriggerData(response.data);

      // Check if user dismissed this session
      const dismissedSession = sessionStorage.getItem('smartstudy_dismissed');
      if (dismissedSession) {
        setIsDismissed(true);
      }
    } catch (error) {
      console.error('Error loading SmartStudy triggers:', error);
    }
  };

  const handleDismiss = () => {
    setIsVisible(false);
    setIsDismissed(true);
    // Remember dismissal for this session only
    sessionStorage.setItem('smartstudy_dismissed', 'true');
  };

  const handleOpenSmartStudy = (suggestedPrompt) => {
    if (onOpenSmartStudy) {
      onOpenSmartStudy(suggestedPrompt);
    }
    setIsVisible(false);
  };

  // Don't show if no triggers, dismissed, or not visible
  if (!triggerData || !triggerData.should_trigger || isDismissed || !isVisible) {
    return null;
  }

  const { urgency, primary_trigger, triggers, trigger_count } = triggerData;

  // Urgency-based styling
  const urgencyStyles = {
    critical: {
      bg: 'bg-gradient-to-r from-red-600 to-red-700',
      border: 'border-red-800',
      text: 'text-white',
      icon: '🚨',
      pulse: true
    },
    high: {
      bg: 'bg-gradient-to-r from-orange-600 to-orange-700',
      border: 'border-orange-800',
      text: 'text-white',
      icon: '⚠️',
      pulse: false
    },
    medium: {
      bg: 'bg-gradient-to-r from-yellow-500 to-yellow-600',
      border: 'border-yellow-700',
      text: 'text-stone-900',
      icon: '💡',
      pulse: false
    },
    low: {
      bg: 'bg-gradient-to-r from-blue-500 to-blue-600',
      border: 'border-blue-700',
      text: 'text-white',
      icon: '🎓',
      pulse: false
    },
    none: {
      bg: 'bg-gradient-to-r from-stone-500 to-stone-600',
      border: 'border-stone-700',
      text: 'text-white',
      icon: 'ℹ️',
      pulse: false
    }
  };

  const style = urgencyStyles[urgency] || urgencyStyles.none;

  return (
    <div className={`relative rounded-xl shadow-md p-4 mb-4 border ${style.bg} ${style.border} ${style.pulse ? 'animate-pulse-subtle' : ''}`}>
      {/* Close Button */}
      <button
        onClick={handleDismiss}
        className={`absolute top-2 right-2 ${style.text} opacity-60 hover:opacity-100 transition-opacity duration-200`}
        aria-label="Dismiss"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <div className="flex items-center gap-3 pr-6">
        {/* Icon */}
        <div className="text-2xl flex-shrink-0">
          {primary_trigger?.icon || style.icon}
        </div>

        {/* Content */}
        <div className="flex-1">
          {/* Title */}
          <h3 className={`text-sm font-semibold ${style.text}`}>
            {primary_trigger?.title || 'SmartStudy Recommendation'}
          </h3>

          {/* Message - only show for critical/high */}
          {(urgency === 'critical' || urgency === 'high') && (
            <p className={`text-xs mt-1 ${style.text} opacity-80`}>
              {primary_trigger?.message || 'Get personalized help with your academics.'}
            </p>
          )}
        </div>

        {/* Action Button */}
        <button
          onClick={() => handleOpenSmartStudy(primary_trigger?.suggested_prompt)}
          className={`${
            urgency === 'critical' || urgency === 'high'
              ? 'bg-white text-orange-700 hover:bg-stone-100'
              : urgency === 'medium'
              ? 'bg-stone-900 text-white hover:bg-stone-800'
              : 'bg-white text-navy-700 hover:bg-stone-100'
          } px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 shadow hover:shadow-md flex items-center gap-1.5 flex-shrink-0`}
        >
          <span className="text-base">🤖</span>
          <span>Get Help</span>
        </button>
      </div>

      {/* Multiple triggers indicator - compact */}
      {trigger_count > 1 && (
        <div className={`text-xs mt-2 ${style.text} opacity-60 flex items-center gap-1`}>
          <span>+{trigger_count - 1} more</span>
          <button
            className="underline hover:no-underline"
            onClick={() => {
              alert(`Areas needing attention:\n${triggers.map(t => `• ${t.title}`).join('\n')}`);
            }}
          >
            view all
          </button>
        </div>
      )}
    </div>
  );
}
