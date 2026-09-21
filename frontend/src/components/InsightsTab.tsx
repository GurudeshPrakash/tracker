import React, { useEffect, useState } from 'react';
import { Flame, CheckCircle, Clock } from 'lucide-react';
import { api } from '../api';
import { InsightsData } from '../types';

export const InsightsTab: React.FC = () => {
  const [data, setData] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getInsights().then((res) => {
      setData(res);
      setLoading(false);
    });
  }, []);

  if (loading || !data) {
    return <div className="tasks-card-container">Loading analytics...</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Metric Highlights */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
        <div
          className="tasks-card-container"
          style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: 0 }}
        >
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: '#fef3c7',
              color: '#d97706',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Flame size={24} />
          </div>
          <div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f172a' }}>{data.streak} Days</div>
            <div style={{ fontSize: '0.82rem', color: '#64748b', fontWeight: 600 }}>Active Daily Streak</div>
          </div>
        </div>

        <div
          className="tasks-card-container"
          style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: 0 }}
        >
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: '#dcfce7',
              color: '#15803d',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CheckCircle size={24} />
          </div>
          <div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f172a' }}>
              {Math.round(data.completion_rate * 100)}%
            </div>
            <div style={{ fontSize: '0.82rem', color: '#64748b', fontWeight: 600 }}>30-Day Completion Rate</div>
          </div>
        </div>

        <div
          className="tasks-card-container"
          style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: 0 }}
        >
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: '#ede9fe',
              color: '#7c3aed',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Clock size={24} />
          </div>
          <div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f172a' }}>
              {data.average_rating ? `${data.average_rating} ★` : '4.5 ★'}
            </div>
            <div style={{ fontSize: '0.82rem', color: '#64748b', fontWeight: 600 }}>Avg Quality Rating</div>
          </div>
        </div>
      </div>

      {/* Study by Skill Breakdown */}
      <div className="tasks-card-container">
        <h3 className="card-title" style={{ marginBottom: '1.25rem' }}>Study Minutes by Skill (Past 30 Days)</h3>
        {data.study_by_skill.length === 0 ? (
          <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
            No study sessions recorded yet. Start deliberate practice in the Learning tab!
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {data.study_by_skill.map((item, idx) => (
              <div key={idx}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.88rem', fontWeight: 600, marginBottom: '6px' }}>
                  <span>{item.skill_name}</span>
                  <span style={{ color: '#7c3aed' }}>{item.total_min} mins</span>
                </div>
                <div style={{ width: '100%', height: '10px', background: '#f1f5f9', borderRadius: '5px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${Math.min((item.total_min / 300) * 100, 100)}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
                      borderRadius: '5px',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
