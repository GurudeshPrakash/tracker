import React from 'react';
import { Flame } from 'lucide-react';
import { GoalItem } from '../types';

interface BentoHeroProps {
  streak: number;
  goals: GoalItem[];
}

export const BentoHero: React.FC<BentoHeroProps> = ({ streak, goals }) => {
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
  };

  // Determine top 2 goals or fallback to skills / focus metrics
  const goal1 = goals[0] || {
    goal: { title: 'Skills Mastery' },
    progress: { percent: 78 },
  };
  const goal2 = goals[1] || {
    goal: { title: 'Productivity (Focus)' },
    progress: { percent: 84 },
  };

  // SVG ring circumference for r=38
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const offset1 = circumference - (Math.min(goal1.progress.percent, 100) / 100) * circumference;
  const offset2 = circumference - (Math.min(goal2.progress.percent, 100) / 100) * circumference;

  return (
    <div
      className="bento-card"
      style={{
        border: '1px solid rgba(6, 182, 212, 0.25)',
        boxShadow: '0 0 35px rgba(6, 182, 212, 0.08)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        gridColumn: 'span 2',
      }}
    >
      <div>
        <h2 style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f8fafc', marginBottom: '0.2rem' }}>
          {getGreeting()}, Explorer!
        </h2>
        <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
          Your daily momentum and milestone tracking
        </div>
      </div>

      {/* Daily Streak Section matching concept */}
      <div style={{ margin: '1.25rem 0' }}>
        <div style={{ fontSize: '0.8rem', fontWeight: '600', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.4rem' }}>
          Daily Streak
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem' }}>
          <div style={{
            background: 'rgba(249, 115, 22, 0.2)',
            borderRadius: '50%',
            padding: '0.35rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Flame size={20} color="#f97316" />
          </div>
          <span style={{ fontSize: '1.1rem', fontWeight: '800', color: '#f8fafc', letterSpacing: '0.03em' }}>
            {streak} DAYS <span style={{ color: '#f97316' }}>FIRE</span>
          </span>
          <Flame size={16} color="#f97316" />
        </div>
        {/* Streak Track */}
        <div style={{ width: '100%', height: '8px', background: 'rgba(255, 255, 255, 0.06)', borderRadius: '9999px', overflow: 'hidden' }}>
          <div style={{
            width: `${Math.min(Math.max(streak * 7, 15), 100)}%`,
            height: '100%',
            background: 'linear-gradient(90deg, #f97316 0%, #fbbf24 100%)',
            boxShadow: '0 0 12px rgba(249, 115, 22, 0.5)',
            borderRadius: '9999px',
            transition: 'width 0.5s ease',
          }} />
        </div>
      </div>

      {/* Goal Rings: Progress */}
      <div>
        <div style={{ fontSize: '0.8rem', fontWeight: '600', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
          Goal Rings: Progress
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-around', gap: '1rem' }}>
          {/* Ring 1 - Cyan */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <div style={{ position: 'relative', width: '90px', height: '90px' }}>
              <svg width="90" height="90" viewBox="0 0 90 90" style={{ transform: 'rotate(-90deg)' }}>
                <circle
                  cx="45"
                  cy="45"
                  r={radius}
                  stroke="rgba(6, 182, 212, 0.15)"
                  strokeWidth="8"
                  fill="transparent"
                />
                <circle
                  cx="45"
                  cy="45"
                  r={radius}
                  stroke="#06b6d4"
                  strokeWidth="8"
                  fill="transparent"
                  strokeDasharray={circumference}
                  strokeDashoffset={offset1}
                  strokeLinecap="round"
                  style={{ filter: 'drop-shadow(0 0 8px #06b6d4)', transition: 'stroke-dashoffset 0.8s ease' }}
                />
              </svg>
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: '800',
                fontSize: '1.15rem',
                color: '#f8fafc',
              }}>
                {Math.round(goal1.progress.percent)}%
              </div>
            </div>
            <div>
              <div style={{ fontWeight: '700', fontSize: '0.95rem', color: '#f8fafc' }}>
                {goal1.goal.title}
              </div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>Target Pace</div>
            </div>
          </div>

          {/* Ring 2 - Magenta */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <div style={{ position: 'relative', width: '90px', height: '90px' }}>
              <svg width="90" height="90" viewBox="0 0 90 90" style={{ transform: 'rotate(-90deg)' }}>
                <circle
                  cx="45"
                  cy="45"
                  r={radius}
                  stroke="rgba(236, 72, 153, 0.15)"
                  strokeWidth="8"
                  fill="transparent"
                />
                <circle
                  cx="45"
                  cy="45"
                  r={radius}
                  stroke="#ec4899"
                  strokeWidth="8"
                  fill="transparent"
                  strokeDasharray={circumference}
                  strokeDashoffset={offset2}
                  strokeLinecap="round"
                  style={{ filter: 'drop-shadow(0 0 8px #ec4899)', transition: 'stroke-dashoffset 0.8s ease' }}
                />
              </svg>
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: '800',
                fontSize: '1.15rem',
                color: '#f8fafc',
              }}>
                {Math.round(goal2.progress.percent)}%
              </div>
            </div>
            <div>
              <div style={{ fontWeight: '700', fontSize: '0.95rem', color: '#f8fafc' }}>
                {goal2.goal.title}
              </div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>Weekly Goal</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
