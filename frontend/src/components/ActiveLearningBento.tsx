import React from 'react';
import { Play, Pause, RotateCcw, Plus, Atom, Sparkles, Flame } from 'lucide-react';
import { RecentSessionItem } from '../types';
import { useFocusMode } from '../FocusContext';

interface ActiveLearningBentoProps {
  recentSessions: RecentSessionItem[];
  onOpenLogModal: (initialDurationMin?: number) => void;
  resetKey?: number;
}

export const ActiveLearningBento: React.FC<ActiveLearningBentoProps> = ({
  recentSessions,
  onOpenLogModal,
}) => {
  const {
    isFocusMode,
    isRunning,
    seconds,
    startFocus,
    pauseFocus,
    resumeFocus,
    resetTimer,
    formatTime,
  } = useFocusMode();

  const activeTopic = recentSessions[0]?.skill || 'Focus Learning Session';

  const handleStartOrToggle = () => {
    if (!isFocusMode) {
      startFocus(activeTopic);
    } else if (isRunning) {
      pauseFocus();
    } else {
      resumeFocus();
    }
  };

  const handleLogTimer = () => {
    const elapsedMinutes = Math.max(Math.round(seconds / 60), 1);
    onOpenLogModal(elapsedMinutes);
  };

  return (
    <div
      className="bento-card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        gridRow: 'span 2',
        border: isFocusMode ? '1px solid rgba(236, 72, 153, 0.5)' : '1px solid rgba(236, 72, 153, 0.25)',
        boxShadow: isFocusMode
          ? '0 0 45px rgba(236, 72, 153, 0.16)'
          : '0 0 35px rgba(236, 72, 153, 0.08)',
        transition: 'all 0.3s ease',
      }}
    >
      <div>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <h3 style={{ fontSize: '1.2rem', fontWeight: '800', color: '#f8fafc' }}>
                Active Learning Session
              </h3>
              {isFocusMode && (
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    background: 'rgba(236, 72, 153, 0.2)',
                    border: '1px solid #ec4899',
                    color: '#f472b6',
                    fontSize: '0.65rem',
                    fontWeight: '800',
                    padding: '0.15rem 0.45rem',
                    borderRadius: '9999px',
                  }}
                >
                  <Flame size={11} /> ON
                </span>
              )}
            </div>
            <div style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '0.2rem' }}>
              Topic: <span style={{ color: '#ec4899', fontWeight: '700' }}>{activeTopic}</span>
            </div>
          </div>
          <button
            onClick={() => onOpenLogModal(Math.max(Math.round(seconds / 60), 15))}
            style={{
              background: 'rgba(236, 72, 153, 0.15)',
              border: '1px solid rgba(236, 72, 153, 0.4)',
              color: '#f472b6',
              borderRadius: '10px',
              padding: '0.35rem 0.65rem',
              fontSize: '0.75rem',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.25rem',
            }}
          >
            <Plus size={14} /> Log
          </button>
        </div>

        {/* Study Timer Section */}
        <div style={{ margin: '1.25rem 0', textAlign: 'center' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#94a3b8', marginBottom: '0.4rem' }}>
            Live Focus Study Timer
          </div>

          {/* Digital Timer Clock */}
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(0, 0, 0, 0.45)',
            border: isFocusMode ? '1px solid rgba(236, 72, 153, 0.4)' : '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '18px',
            padding: '0.6rem 1.75rem',
            fontSize: '2.5rem',
            fontWeight: '800',
            fontFamily: 'var(--font-mono)',
            letterSpacing: '0.08em',
            color: '#ffffff',
            boxShadow: 'inset 0 2px 10px rgba(0, 0, 0, 0.8), 0 0 20px rgba(236, 72, 153, 0.15)',
          }}>
            {formatTime(seconds)}
          </div>

          {/* Timer controls */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '0.65rem', marginTop: '0.85rem' }}>
            <button
              onClick={handleStartOrToggle}
              style={{
                background: isRunning ? 'rgba(245, 158, 11, 0.2)' : 'linear-gradient(135deg, #ec4899 0%, #d946ef 100%)',
                border: isRunning ? '1px solid #f59e0b' : 'none',
                color: '#ffffff',
                borderRadius: '9999px',
                padding: '0.45rem 1rem',
                fontSize: '0.8rem',
                fontWeight: '700',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                boxShadow: '0 0 15px rgba(236, 72, 153, 0.4)',
              }}
            >
              {isRunning ? <Pause size={14} /> : <Play size={14} fill="#ffffff" />}
              {isFocusMode ? (isRunning ? 'Pause' : 'Resume') : 'Start Focus'}
            </button>
            <button
              onClick={resetTimer}
              title="Reset timer"
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#94a3b8',
                borderRadius: '9999px',
                padding: '0.45rem 0.85rem',
                fontSize: '0.8rem',
                cursor: 'pointer',
              }}
            >
              <RotateCcw size={14} />
            </button>
            {seconds >= 60 && (
              <button
                onClick={handleLogTimer}
                style={{
                  background: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  color: '#34d399',
                  borderRadius: '9999px',
                  padding: '0.45rem 0.85rem',
                  fontSize: '0.8rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                }}
              >
                Log {Math.round(seconds / 60)}m
              </button>
            )}
          </div>
        </div>

        {/* Recent Takeaways Stream */}
        <div style={{ marginTop: '1.25rem' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', marginBottom: '0.65rem' }}>
            Recent Key Takeaways
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {recentSessions.length === 0 ? (
              <div style={{ fontSize: '0.85rem', color: '#64748b', fontStyle: 'italic', padding: '0.5rem' }}>
                No takeaways logged yet. Complete study sessions to see your knowledge base grow!
              </div>
            ) : (
              recentSessions.slice(0, 3).map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.6rem',
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid rgba(255, 255, 255, 0.05)',
                    borderRadius: '12px',
                    padding: '0.65rem 0.85rem',
                  }}
                >
                  <span style={{ color: idx % 2 === 0 ? '#06b6d4' : '#ec4899', marginTop: '0.15rem' }}>
                    {idx % 2 === 0 ? <Atom size={16} /> : <Sparkles size={16} />}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.85rem', color: '#f1f5f9', fontWeight: '500' }}>
                      {item.session.takeaway}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                      {item.skill} &bull; {item.session.session_date} ({item.session.duration_min}m)
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
