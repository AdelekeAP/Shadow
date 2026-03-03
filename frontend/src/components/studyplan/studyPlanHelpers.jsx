/**
 * Utility functions for Study Plan components
 */

/**
 * Convert URLs in text to clickable links
 */
export const linkifyText = (text) => {
  if (!text) return null;

  const urlPattern = /(https?:\/\/[^\s<]+[^<.,:;"')\]\s])/g;
  const parts = text.split(urlPattern);

  return parts.map((part, index) => {
    if (part.match(urlPattern)) {
      return (
        <a
          key={index}
          href={part}
          target="_blank"
          rel="noopener noreferrer"
          className="text-navy-700 hover:text-navy-900 underline break-all font-medium"
          onClick={(e) => e.stopPropagation()}
        >
          {part}
        </a>
      );
    }
    return part;
  });
};

export const getLearningStyleIcon = (style) => {
  const icons = {
    visual: 'Visual',
    audio: 'Audio',
    reading: 'Reading',
    kinesthetic: 'Hands-on',
    auto: 'Auto'
  };
  return icons[style] || 'Study';
};

export const getActivityIcon = (type) => {
  const icons = {
    reading: 'Read',
    video: 'Watch',
    practice: 'Code',
    interactive: 'Try',
    project: 'Build',
    review: 'Review',
    writing: 'Write'
  };
  return icons[type] || 'Task';
};

export const getDifficultyColor = (difficulty) => {
  const colors = {
    easy: 'text-emerald-600 bg-emerald-50',
    medium: 'text-amber-600 bg-amber-50',
    hard: 'text-red-600 bg-red-50'
  };
  return colors[difficulty] || 'text-surface-400 bg-surface-100';
};

export const getNotebookLMLink = (topic, activityContent) => {
  const content = `Study Topic: ${topic}\n\nActivity: ${activityContent}`;
  const encodedContent = encodeURIComponent(content);
  return `https://notebooklm.google.com/notebook/new?content=${encodedContent}`;
};

export const getNoteColorClass = (color) => {
  const colors = {
    yellow: 'bg-amber-50 border-amber-300',
    green: 'bg-emerald-50 border-emerald-300',
    blue: 'bg-blue-50 border-blue-300',
    pink: 'bg-pink-50 border-pink-300',
    orange: 'bg-orange-50 border-orange-300'
  };
  return colors[color] || colors.yellow;
};

export const getNoteTypeIcon = (type) => {
  const icons = {
    note: 'Note',
    highlight: 'Key',
    question: '?',
    summary: 'Sum'
  };
  return icons[type] || icons.note;
};

export const getResourceStyle = (resourceType) => {
  const styles = {
    youtube_video: {
      gradient: 'from-red-50/60 to-orange-50/40',
      border: 'border-red-200/60 hover:border-red-300',
      iconBg: 'bg-red-600',
      icon: 'youtube',
      badge: 'Video'
    },
    documentation: {
      gradient: 'from-blue-50/60 to-indigo-50/40',
      border: 'border-blue-200/60 hover:border-blue-300',
      iconBg: 'bg-blue-600',
      icon: 'docs',
      badge: 'Documentation'
    },
    article: {
      gradient: 'from-violet-50/60 to-purple-50/40',
      border: 'border-violet-200/60 hover:border-violet-300',
      iconBg: 'bg-violet-600',
      icon: 'article',
      badge: 'Article'
    },
    practice: {
      gradient: 'from-emerald-50/60 to-green-50/40',
      border: 'border-emerald-200/60 hover:border-emerald-300',
      iconBg: 'bg-emerald-600',
      icon: 'practice',
      badge: 'Practice'
    },
    interactive: {
      gradient: 'from-cyan-50/60 to-teal-50/40',
      border: 'border-cyan-200/60 hover:border-cyan-300',
      iconBg: 'bg-cyan-600',
      icon: 'interactive',
      badge: 'Interactive'
    },
    reddit_post: {
      gradient: 'from-orange-50/60 to-amber-50/40',
      border: 'border-orange-200/60 hover:border-orange-300',
      iconBg: 'bg-orange-600',
      icon: 'reddit',
      badge: 'Discussion'
    },
    uploaded_slides: {
      gradient: 'from-amber-50/60 to-yellow-50/40',
      border: 'border-amber-200/60 hover:border-amber-300',
      iconBg: 'bg-amber-600',
      icon: 'docs',
      badge: 'Your Slides'
    },
    ai_generated: {
      gradient: 'from-surface-50 to-navy-50/30',
      border: 'border-surface-200/60 hover:border-navy-300/40',
      iconBg: 'bg-navy-700',
      icon: 'ai',
      badge: 'AI Guide'
    }
  };
  return styles[resourceType] || styles.ai_generated;
};

export const getYouTubeVideoId = (url) => {
  if (!url) return null;
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\s]+)/,
    /youtube\.com\/embed\/([^&\s]+)/
  ];
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) return match[1];
  }
  return null;
};
