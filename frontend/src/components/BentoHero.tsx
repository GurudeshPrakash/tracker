import React from 'react';
import { Flame } from 'lucide-react';
import { GoalItem } from '../types';

interface BentoHeroProps {
  streak: number;
  goals: GoalItem[];
  doneCount: number;
  plannedCount: number;
  studyMin: number;
}

export const BentoHero: React.FC<BentoHeroProps> = ({
  streak,
  goals,
  doneCount,
  plannedCount,
  studyMin,
}) => {
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
  };

  // Real ring data calculation
  const todayTaskPercent = plannedCount > 0 ? Math.round((doneCount / plannedCount) * 100) : 0;
  const todayStudyPercent = Math.min(Math.round((studyMin / 60) * 100), 100);

  let ring1 = {
    title: 'Daily Tasks',
    subtitle: `${doneCount} of ${plannedCount} Done`,
    percent: todayTaskPercent,
    color: '#06b6d4',
  };

  let ring2 = {
    title: 'Daily Study',
    subtitle: `${studyMin}m / 60m Target`,
    percent: todayStudyPercent,
    color: '#ec4899',
  };

  if (goals.length >= 2) {
    ring1 = {
      title: goals[0].goal.title,
      subtitle: `${goals[0].progress.done_hours.toFixed(1)}h / ${goals[0].goal.target_hours}h`,
      percent: Math.min(Math.round(goals[0].progress.percent), 100),
      color: '#06b6d4',
    };
    ring2 = {
      title: goals[1].goal.title,
      subtitle: `${goals[1].progress.done_hours.toFixed(1)}h / ${goals[1].goal.target_hours}h`,
      percent: Math.min(Math.round(goals[1].progress.percent), 100),
      color: '#ec4899',
    };
  } else if (goals.length === 1) {
    ring1 = {
      title: goals[0].goal.title,
      subtitle: `${goals[0].progress.done_hours.toFixed(1)}h / ${goals[0].goal.target_hours}h`,
      percent: Math.min(Math.round(goals[0].progress.percent), 100),
      color: '#06b6d4',
    };
  }

  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const offset1 = circumference - (ring1.percent / 100) * circumference;
  const offset2 = circumference - (ring2.percent / 100) * circumference;

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
          Real-time productivity momentum and milestone tracking
        </div>
      </div>

      {/* Daily Streak Section */}
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
            width: `${Math.min(streak > 0 ? Math.max(streak * 7, 10) : 0, 100)}%`,
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
          Goal Rings: Live Progress
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
                  stroke={ring1.color}
                  strokeWidth="8"
                  fill="transparent"
                  strokeDasharray={circumference}
                  strokeDashoffset={offset1}
                  strokeLinecap="round"
                  style={{ filter: `drop-shadow(0 0 8px ${ring1.color})`, transition: 'stroke-dashoffset 0.8s ease' }}
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
                {ring1.percent}%
              </div>
            </div>
            <div>
              <div style={{ fontWeight: '700', fontSize: '0.95rem', color: '#f8fafc', maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {ring1.title}
              </div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>{ring1.subtitle}</div>
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
                  stroke={ring2.color}
                  strokeWidth="8"
                  fill="transparent"
                  strokeDasharray={circumference}
                  strokeDashoffset={offset2}
                  strokeLinecap="round"
                  style={{ filter: `drop-shadow(0 0 8px ${ring2.color})`, transition: 'stroke-dashoffset 0.8s ease' }}
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
                {ring2.percent}%
              </div>
            </div>
            <div>
              <div style={{ fontWeight: '700', fontSize: '0.95rem', color: '#f8fafc', maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {ring2.title}
              </div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>{ring2.subtitle}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
