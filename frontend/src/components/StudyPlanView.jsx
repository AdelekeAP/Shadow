import { useState, useEffect } from 'react';
import { getStudyPlans, updateStudyPlanProgress } from '../services/api';
import YouTubePlayer from './YouTubePlayer';
import StudyPlanForm from './studyplan/StudyPlanForm';
import StudyPlanDetails from './studyplan/StudyPlanDetails';

/**
 * StudyPlanView Component
 * Displays AI-generated study plans with day-by-day breakdown
 * Supports different learning styles (visual, audio, reading, kinesthetic)
 * Integrates NotebookLM for audio learners and YouTube videos
 */
export default function StudyPlanView({ onClose }) {
  const [plans, setPlans] = useState([]);
  const [currentPlan, setCurrentPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [showGenerateForm, setShowGenerateForm] = useState(false);

  // YouTube player state
  const [playingVideo, setPlayingVideo] = useState(null);

  useEffect(() => {
    loadStudyPlans();
  }, []);

  const loadStudyPlans = async () => {
    try {
      setLoading(true);
      const data = await getStudyPlans(false);
      setPlans(data);

      const activePlan = data.find(p => p.is_active);
      if (activePlan) {
        setCurrentPlan(activePlan);
      } else if (data.length > 0) {
        setCurrentPlan(data[0]);
      }
    } catch (error) {
      console.error('Error loading study plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePlanGenerated = async () => {
    await loadStudyPlans();
    setShowGenerateForm(false);
  };

  const handleBeforeScore = async (score) => {
    if (!currentPlan) return;
    try {
      await updateStudyPlanProgress(currentPlan.id, { beforeScore: score });
      setCurrentPlan({ ...currentPlan, before_score: score });
    } catch (error) {
      console.error('Error saving before score:', error);
    }
  };

  const handleAfterScore = async (score) => {
    if (!currentPlan) return;
    try {
      await updateStudyPlanProgress(currentPlan.id, { afterScore: score });
      const effectivenessScore = currentPlan.before_score != null
        ? score - currentPlan.before_score
        : null;
      setCurrentPlan({
        ...currentPlan,
        after_score: score,
        effectiveness_score: effectivenessScore
      });
    } catch (error) {
      console.error('Error saving after score:', error);
    }
  };

  const handleDayComplete = async (dayNumber) => {
    if (!currentPlan) return;

    try {
      const totalDays = currentPlan.plan_data.days?.length || 0;
      const completedDays = currentPlan.completed_days || [];

      let newCompletedDays;
      if (completedDays.includes(dayNumber)) {
        newCompletedDays = completedDays.filter(d => d !== dayNumber);
      } else {
        newCompletedDays = [...completedDays, dayNumber];
      }

      const completionPercentage = (newCompletedDays.length / totalDays) * 100;

      await updateStudyPlanProgress(currentPlan.id, {
        completionPercentage,
        isActive: completionPercentage < 100
      });

      setCurrentPlan({
        ...currentPlan,
        completed_days: newCompletedDays,
        completion_percentage: completionPercentage,
        is_active: completionPercentage < 100
      });
    } catch (error) {
      console.error('Error updating progress:', error);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-stone-900/40 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl p-8 shadow-2xl">
          <div className="text-center">
            <div className="animate-spin text-6xl mb-4">{'\uD83C\uDF93'}</div>
            <p className="text-stone-600">Loading study plans...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-stone-900/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-6xl w-full h-[90vh] flex flex-col animate-scale-in">

        {/* Header */}
        <div className="bg-gradient-to-r from-navy-800 to-navy-700 text-white p-6 rounded-t-2xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-white/20 rounded-full p-2">
                <span className="text-2xl">{'\uD83D\uDCDA'}</span>
              </div>
              <div>
                <h2 className="text-2xl font-bold">AI Study Plans</h2>
                <p className="text-navy-200 text-sm">Personalized learning paths generated for you</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {!showGenerateForm && (
                <button
                  onClick={() => setShowGenerateForm(true)}
                  className="bg-emerald-500 hover:bg-emerald-600 px-4 py-2 rounded-xl transition-all duration-200 flex items-center gap-2"
                >
                  <span className="text-xl">{'\u2728'}</span>
                  <span className="text-sm font-semibold">New Plan</span>
                </button>
              )}
              <button
                onClick={onClose}
                className="text-white hover:bg-white/20 rounded-lg p-2 transition-all duration-200"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Generate Plan Form */}
        {showGenerateForm && (
          <StudyPlanForm
            generating={generating}
            setGenerating={setGenerating}
            onPlanGenerated={handlePlanGenerated}
            onCancel={() => setShowGenerateForm(false)}
          />
        )}

        {/* Main Content */}
        <div className="flex-1 overflow-hidden flex">

          {/* Sidebar - Plan List */}
          <div className="w-80 bg-stone-50 border-r border-stone-200 overflow-y-auto">
            <div className="p-4">
              <h3 className="text-sm font-bold text-stone-500 uppercase tracking-wide mb-3">
                Your Plans ({plans.length})
              </h3>

              {plans.length === 0 ? (
                <div className="text-center py-8 text-stone-500">
                  <div className="text-4xl mb-2">{'\uD83D\uDCDA'}</div>
                  <p className="text-sm">No study plans yet</p>
                  <p className="text-xs mt-1">Click "New Plan" to create one!</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {plans.map((plan) => (
                    <button
                      key={plan.id}
                      onClick={() => setCurrentPlan(plan)}
                      className={`w-full text-left p-4 rounded-xl transition-all duration-200 ${
                        currentPlan?.id === plan.id
                          ? 'bg-navy-600 text-white shadow-lg'
                          : 'bg-white hover:bg-stone-100 text-stone-800'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-semibold text-sm line-clamp-2">{plan.topic}</h4>
                        {plan.is_active && (
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            currentPlan?.id === plan.id
                              ? 'bg-white/20 text-white'
                              : 'bg-emerald-100 text-emerald-700'
                          }`}>
                            Active
                          </span>
                        )}
                      </div>

                      <div className="mb-2">
                        <div className={`h-1.5 rounded-full overflow-hidden ${
                          currentPlan?.id === plan.id ? 'bg-white/20' : 'bg-stone-200'
                        }`}>
                          <div
                            className={`h-full transition-all duration-500 ${
                              currentPlan?.id === plan.id ? 'bg-white' : 'bg-navy-600'
                            }`}
                            style={{ width: `${plan.completion_percentage || 0}%` }}
                          />
                        </div>
                      </div>

                      <div className={`flex items-center justify-between text-xs ${
                        currentPlan?.id === plan.id ? 'text-navy-100' : 'text-stone-500'
                      }`}>
                        <span>{plan.duration_days} days</span>
                        <span>{Math.round(plan.completion_percentage || 0)}% complete</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Main View - Study Plan Details */}
          <div className="flex-1 overflow-y-auto p-6">
            {currentPlan ? (
              <StudyPlanDetails
                plan={currentPlan}
                onDayComplete={handleDayComplete}
                onPlayVideo={setPlayingVideo}
                onSubmitBeforeScore={handleBeforeScore}
                onSubmitAfterScore={handleAfterScore}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-stone-400">
                <div className="text-center">
                  <div className="text-6xl mb-4">{'\uD83D\uDCDA'}</div>
                  <p className="text-lg">Select a study plan to view details</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* YouTube Player Modal */}
      {playingVideo && (
        <YouTubePlayer
          videoUrl={playingVideo.url}
          title={playingVideo.title}
          onClose={() => setPlayingVideo(null)}
          autoplay={true}
        />
      )}
    </div>
  );
}
