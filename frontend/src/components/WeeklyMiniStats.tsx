import React from 'react';

interface WeeklyMiniStatsProps {
  doneCount: number;
  plannedCount: number;
  studyMin: number;
  completionSeries?: { date: string; rate: number }[];
  skillSeries?: { skill: string; minutes: number }[];
}

export const WeeklyMiniStats: React.FC<WeeklyMiniStatsProps> = ({
  doneCount,
  plannedCount,
  studyMin,
  completionSeries = [],
  skillSeries = [],
}) => {
  const hours = (studyMin / 60).toFixed(1);

  // Compute real vertical bars for skills
  const maxSkillMin = Math.max(...skillSeries.map((s) => s.minutes), 60);
  const skillsDisplay = skillSeries.length > 0
    ? skillSeries.slice(0, 6).map((s) => ({
        skill: s.skill,
        height: Math.max(Math.round((s.minutes / maxSkillMin) * 90), 15),
        min: s.minutes,
      }))
    : [
        { skill: 'Study', height: 10, min: 0 },
        { skill: 'Code', height: 10, min: 0 },
        { skill: 'Theory', height: 10, min: 0 },
      ];

  // Compute real sparkline points for completion series (last 7 days)
  const sparklineData = completionSeries.length > 0 ? completionSeries.slice(-7) : [];
  const points = sparklineData.map((d, i) => {
    const x = Math.round(15 + (i / Math.max(sparklineData.length - 1, 1)) * 170);
    const y = Math.round(48 - (d.rate / 100) * 38);
    return { x, y, rate: d.rate };
  });
  const pointsString = points.map((p) => `${p.x},${p.y}`).join(' ');

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: '1.25rem',
      gridColumn: 'span 3',
    }}>
      {/* 1. Real Skills Investment / Bar Card */}
      <div className="bento-card" style={{ padding: '1.25rem' }}>
        <div style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', marginBottom: '0.35rem' }}>
          Weekly Progress
        </div>
        <div style={{ fontSize: '1.05rem', fontWeight: '800', color: '#f8fafc', marginBottom: '0.75rem' }}>
          Skills Investment
        </div>

        {/* Vertical bars graphic */}
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', height: '65px', padding: '0 0.5rem' }}>
          {skillsDisplay.map((s, i) => (
            <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.3rem' }} title={`${s.skill}: ${s.min}m`}>
              <div
                style={{
                  width: '16px',
                  height: `${s.height}%`,
                  borderRadius: '6px',
                  background: 'linear-gradient(180deg, #a855f7 0%, #06b6d4 100%)',
                  boxShadow: '0 0 10px rgba(168, 85, 247, 0.3)',
                  transition: 'height 0.5s ease',
                }}
              />
              <span style={{ fontSize: '0.65rem', color: '#64748b', maxWidth: '32px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {s.skill}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 2. Real Tasks Velocity Sparkline Card */}
      <div className="bento-card" style={{ padding: '1.25rem' }}>
        <div style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', marginBottom: '0.35rem' }}>
          Weekly Velocity
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <div style={{ fontSize: '1.05rem', fontWeight: '800', color: '#f8fafc' }}>
            Daily Completion %
          </div>
          <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#06b6d4' }}>
            {doneCount} / {plannedCount} Today
          </span>
        </div>

        {/* Real SVG Sparkline */}
        <div style={{ height: '65px', width: '100%', display: 'flex', alignItems: 'center' }}>
          {points.length > 1 ? (
            <svg width="100%" height="55" viewBox="0 0 200 55" preserveAspectRatio="none">
              <defs>
                <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#a855f7" />
                  <stop offset="100%" stopColor="#06b6d4" />
                </linearGradient>
              </defs>
              <polyline
                fill="none"
                stroke="url(#lineGrad)"
                strokeWidth="3.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={pointsString}
                style={{ filter: 'drop-shadow(0 0 6px rgba(6, 182, 212, 0.4))' }}
              />
              {points.map((p, idx) => (
                <circle key={idx} cx={p.x} cy={p.y} r="3.5" fill="#06b6d4" stroke="#0a0d14" strokeWidth="2" />
              ))}
            </svg>
          ) : (
            <div style={{ fontSize: '0.8rem', color: '#64748b', fontStyle: 'italic', textAlign: 'center', width: '100%' }}>
              Trendline will generate as you complete daily reflections.
            </div>
          )}
        </div>
      </div>

      {/* 3. Real Learning Hours Card */}
      <div className="bento-card" style={{ padding: '1.25rem' }}>
        <div style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', marginBottom: '0.35rem' }}>
          Weekly Target
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
          <div style={{ fontSize: '1.05rem', fontWeight: '800', color: '#f8fafc' }}>
            Study Hours
          </div>
          <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#ec4899' }}>
            {hours}h logged
          </span>
        </div>

        {/* Real Circular gauge */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '65px' }}>
          <svg width="65" height="65" viewBox="0 0 65 65" style={{ transform: 'rotate(-90deg)' }}>
            <circle cx="32.5" cy="32.5" r="24" stroke="rgba(236, 72, 153, 0.15)" strokeWidth="6" fill="transparent" />
            <circle
              cx="32.5"
              cy="32.5"
              r="24"
              stroke="#06b6d4"
              strokeWidth="6"
              fill="transparent"
              strokeDasharray={2 * Math.PI * 24}
              strokeDashoffset={(2 * Math.PI * 24) * (1 - Math.min(Number(hours) / 10, 1))}
              strokeLinecap="round"
              style={{ filter: 'drop-shadow(0 0 6px #06b6d4)', transition: 'stroke-dashoffset 0.8s ease' }}
            />
          </svg>
          <div style={{ marginLeft: '1rem' }}>
            <div style={{ fontSize: '1.2rem', fontWeight: '800', color: '#f8fafc' }}>{hours}h</div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Target: 10h/wk</div>
          </div>
        </div>
      </div>
    </div>
  );
};
