import React from 'react';

interface WeeklyMiniStatsProps {
  doneCount: number;
  plannedCount: number;
  studyMin: number;
}

export const WeeklyMiniStats: React.FC<WeeklyMiniStatsProps> = ({
  doneCount,
  plannedCount,
  studyMin,
}) => {
  const hours = (studyMin / 60).toFixed(1);

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: '1.25rem',
      gridColumn: 'span 3',
    }}>
      {/* 1. Skills Acquired / Bar Card */}
      <div className="bento-card" style={{ padding: '1.25rem' }}>
        <div style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', marginBottom: '0.35rem' }}>
          Weekly Progress
        </div>
        <div style={{ fontSize: '1.05rem', fontWeight: '800', color: '#f8fafc', marginBottom: '1rem' }}>
          Skills Investment
        </div>

        {/* Vertical bars graphic */}
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', height: '65px', padding: '0 0.5rem' }}>
          {[40, 75, 55, 95, 60, 85].map((height, i) => (
            <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.4rem' }}>
              <div
                style={{
                  width: '14px',
                  height: `${height}%`,
                  borderRadius: '6px',
                  background: 'linear-gradient(180deg, #a855f7 0%, #06b6d4 100%)',
                  boxShadow: '0 0 10px rgba(168, 85, 247, 0.3)',
                  transition: 'height 0.5s ease',
                }}
              />
            </div>
          ))}
        </div>
      </div>

      {/* 2. Tasks Completed Sparkline Card */}
      <div className="bento-card" style={{ padding: '1.25rem' }}>
        <div style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', marginBottom: '0.35rem' }}>
          Weekly Progress
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <div style={{ fontSize: '1.05rem', fontWeight: '800', color: '#f8fafc' }}>
            Tasks Velocity
          </div>
          <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#06b6d4' }}>
            {doneCount} finished
          </span>
        </div>

        {/* Mini SVG Sparkline */}
        <div style={{ height: '65px', width: '100%', display: 'flex', alignItems: 'center' }}>
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
              points="10,42 45,30 80,38 120,18 160,24 190,10"
              style={{ filter: 'drop-shadow(0 0 6px rgba(6, 182, 212, 0.4))' }}
            />
            {[
              [10, 42],
              [45, 30],
              [80, 38],
              [120, 18],
              [160, 24],
              [190, 10],
            ].map(([cx, cy], idx) => (
              <circle key={idx} cx={cx} cy={cy} r="4" fill="#06b6d4" stroke="#0a0d14" strokeWidth="2" />
            ))}
          </svg>
        </div>
      </div>

      {/* 3. Learning Hours Card */}
      <div className="bento-card" style={{ padding: '1.25rem' }}>
        <div style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', marginBottom: '0.35rem' }}>
          Weekly Progress
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
          <div style={{ fontSize: '1.05rem', fontWeight: '800', color: '#f8fafc' }}>
            Learning Hours
          </div>
          <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#ec4899' }}>
            {hours}h logged
          </span>
        </div>

        {/* Circular gauge */}
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
              strokeDashoffset={(2 * Math.PI * 24) * 0.35}
              strokeLinecap="round"
              style={{ filter: 'drop-shadow(0 0 6px #06b6d4)' }}
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
