import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, Plus, Atom, Sparkles } from 'lucide-react';
import { RecentSessionItem } from '../types';

interface ActiveLearningBentoProps {
  recentSessions: RecentSessionItem[];
  onOpenLogModal: (initialDurationMin?: number) => void;
}

export const ActiveLearningBento: React.FC<ActiveLearningBentoProps> = ({
  recentSessions,
  onOpenLogModal,
}) => {
  // Real live stopwatch starting at 0
  const [seconds, setSeconds] = useState<number>(0);
  const [isRunning, setIsRunning] = useState<boolean>(false);

  useEffect(() => {
    let interval: any = null;
    if (isRunning) {
      interval = setInterval(() => {
        setSeconds((s) => s + 1);
      }, 1000);
    } else if (!isRunning && seconds !== 0) {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isRunning, seconds]);

  const formatTimer = (totalSeconds: number) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const handleLogTimer = () => {
    const elapsedMinutes = Math.max(Math.round(seconds / 60), 1);
    onOpenLogModal(elapsedMinutes);
  };

  const activeTopic = recentSessions[0]?.skill || 'Focus Learning Session';

  return (
    <div
      className="bento-card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        gridRow: 'span 2',
        border: '1px solid rgba(236, 72, 153, 0.25)',
        boxShadow: '0 0 35px rgba(236, 72, 153, 0.08)',
      }}
    >
      <div>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
          <div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: '800', color: '#f8fafc' }}>
              Active Learning Session
            </h3>
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
            Live Study Timer
          </div>

          {/* Digital Timer Clock */}
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(0, 0, 0, 0.45)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '18px',
            padding: '0.6rem 1.75rem',
            fontSize: '2.5rem',
            fontWeight: '800',
            fontFamily: 'var(--font-mono)',
            letterSpacing: '0.08em',
            color: '#ffffff',
            boxShadow: 'inset 0 2px 10px rgba(0, 0, 0, 0.8), 0 0 20px rgba(236, 72, 153, 0.15)',
          }}>
            {formatTimer(seconds)}
          </div>

          {/* Timer controls */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '0.65rem', marginTop: '0.85rem' }}>
            <button
              onClick={() => setIsRunning(!isRunning)}
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
              {isRunning ? 'Pause' : 'Start Focus'}
            </button>
            <button
              onClick={() => { setIsRunning(false); setSeconds(0); }}
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
