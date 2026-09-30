import React from 'react';
import { Play, Pause, CheckCircle, X, Lock, Flame, Sparkles } from 'lucide-react';
import { useFocusMode } from '../FocusContext';

interface FocusModeBarProps {
  onOpenLogModal: (durationMin: number) => void;
}

export const FocusModeBar: React.FC<FocusModeBarProps> = ({ onOpenLogModal }) => {
  const {
    isFocusMode,
    isRunning,
    seconds,
    activeTopic,
    setActiveTopic,
    pauseFocus,
    resumeFocus,
    stopFocus,
    formatTime,
    toastMessage,
    clearToast,
  } = useFocusMode();

  if (!isFocusMode) {
    return null;
  }

  const handleFinishAndLog = () => {
    const elapsedMinutes = Math.max(1, Math.round(seconds / 60));
    onOpenLogModal(elapsedMinutes);
  };

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto 1.25rem' }}>
      {/* Toast Notification if user attempted to click a locked tab */}
      {toastMessage && (
        <div
          style={{
            marginBottom: '0.85rem',
            padding: '0.75rem 1.25rem',
            borderRadius: '14px',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            color: '#fca5a5',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.9rem',
            fontWeight: 600,
            boxShadow: '0 4px 20px rgba(239, 68, 68, 0.2)',
            animation: 'fadeIn 0.2s ease',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <Lock size={18} color="#f87171" />
            <span>{toastMessage}</span>
          </div>
          <button
            onClick={clearToast}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#fca5a5',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              padding: '0.2rem',
            }}
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Main Glassmorphic Focus HUD Bar */}
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.15) 0%, rgba(99, 102, 241, 0.12) 50%, rgba(6, 182, 212, 0.1) 100%)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)',
          border: '1px solid rgba(236, 72, 153, 0.35)',
          borderRadius: '20px',
          padding: '0.9rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
          boxShadow: '0 0 35px rgba(236, 72, 153, 0.18)',
        }}
      >
        {/* Left: Badge & Topic */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.35rem 0.85rem',
              borderRadius: '9999px',
              background: 'rgba(236, 72, 153, 0.25)',
              border: '1px solid #ec4899',
              color: '#f472b6',
              fontSize: '0.8rem',
              fontWeight: 800,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: isRunning ? '#ec4899' : '#f59e0b',
                boxShadow: isRunning ? '0 0 10px #ec4899' : '0 0 8px #f59e0b',
                animation: isRunning ? 'pulse 1.5s infinite' : 'none',
              }}
            />
            <Flame size={15} />
            <span>{isRunning ? 'FOCUS MODE ACTIVE' : 'FOCUS PAUSED'}</span>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Current Focus
            </div>
            <input
              type="text"
              value={activeTopic}
              onChange={(e) => setActiveTopic(e.target.value)}
              placeholder="What are you mastering right now?"
              style={{
                background: 'rgba(0, 0, 0, 0.25)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '8px',
                padding: '0.2rem 0.6rem',
                color: '#ffffff',
                fontSize: '0.9rem',
                fontWeight: 600,
                outline: 'none',
                minWidth: '220px',
              }}
            />
          </div>
        </div>

        {/* Center: Live Digital Stopwatch */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              background: 'rgba(0, 0, 0, 0.65)',
              border: '1px solid rgba(236, 72, 153, 0.4)',
              borderRadius: '14px',
              padding: '0.35rem 1.25rem',
              fontSize: '1.85rem',
              fontWeight: 800,
              fontFamily: 'var(--font-mono)',
              letterSpacing: '0.08em',
              color: '#ffffff',
              boxShadow: 'inset 0 2px 8px rgba(0, 0, 0, 0.7), 0 0 15px rgba(236, 72, 153, 0.25)',
            }}
          >
            {formatTime(seconds)}
          </div>
        </div>

        {/* Right: Controls & Lock indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* Pause / Resume */}
          <button
            onClick={() => (isRunning ? pauseFocus() : resumeFocus())}
            style={{
              background: isRunning ? 'rgba(245, 158, 11, 0.2)' : 'linear-gradient(135deg, #ec4899 0%, #d946ef 100%)',
              border: isRunning ? '1px solid #f59e0b' : 'none',
              color: '#ffffff',
              borderRadius: '12px',
              padding: '0.5rem 1rem',
              fontSize: '0.85rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              boxShadow: isRunning ? 'none' : '0 0 15px rgba(236, 72, 153, 0.4)',
              transition: 'all 0.2s',
            }}
          >
            {isRunning ? <Pause size={15} /> : <Play size={15} fill="#ffffff" />}
            <span>{isRunning ? 'Pause' : 'Resume'}</span>
          </button>

          {/* Finish & Log */}
          <button
            onClick={handleFinishAndLog}
            style={{
              background: 'rgba(16, 185, 129, 0.2)',
              border: '1px solid rgba(16, 185, 129, 0.5)',
              color: '#6ee7b7',
              borderRadius: '12px',
              padding: '0.5rem 1.05rem',
              fontSize: '0.85rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              boxShadow: '0 0 15px rgba(16, 185, 129, 0.25)',
              transition: 'all 0.2s',
            }}
          >
            <CheckCircle size={15} />
            <span>Finish & Log</span>
          </button>

          {/* Exit Focus Mode */}
          <button
            onClick={() => {
              if (window.confirm('Exit Focus Mode and unlock all tabs? (Your active timer will stop)')) {
                stopFocus();
              }
            }}
            title="Exit Focus Mode & unlock tabs"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              color: '#94a3b8',
              borderRadius: '12px',
              padding: '0.5rem 0.75rem',
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <X size={15} />
            <span>Exit Focus</span>
          </button>
        </div>
      </div>
    </div>
  );
};
