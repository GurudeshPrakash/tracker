import React, { useState, useEffect } from 'react';
import { BarChart3, Flame, Star, Clock, CheckCircle2 } from 'lucide-react';
import { fetchStats } from '../api';

export const InsightsView: React.FC = () => {
  const [statsData, setStatsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats()
      .then(setStatsData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: '2rem', color: '#94a3b8' }}>Loading insights...</div>;
  if (!statsData) return <div style={{ padding: '2rem', color: '#f87171' }}>Failed to load insights.</div>;

  return (
    <div style={{ padding: '1rem', width: '100%' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.8rem', fontWeight: '800', color: '#f8fafc' }}>
          📊 Analytical Insights & Momentum
        </h2>
        <div style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
          Real-time execution metrics, study trends, and energy ratings
        </div>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.25rem', marginBottom: '1.5rem' }}>
        <div className="bento-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f97316', fontSize: '0.8rem', fontWeight: '700', textTransform: 'uppercase' }}>
            <Flame size={16} /> Daily Streak
          </div>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: '#fff', marginTop: '0.4rem' }}>
            {statsData.streak} Days
          </div>
          <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Consecutive updates</div>
        </div>

        <div className="bento-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#fbbf24', fontSize: '0.8rem', fontWeight: '700', textTransform: 'uppercase' }}>
            <Star size={16} /> Avg Rating
          </div>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: '#fff', marginTop: '0.4rem' }}>
            {statsData.avg_rating ? statsData.avg_rating.toFixed(1) : '—'} <span style={{ fontSize: '1rem', color: '#64748b' }}>/ 5</span>
          </div>
          <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Daily satisfaction energy</div>
        </div>

        <div className="bento-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#ec4899', fontSize: '0.8rem', fontWeight: '700', textTransform: 'uppercase' }}>
            <Clock size={16} /> Total Focused Study
          </div>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: '#fff', marginTop: '0.4rem' }}>
            {(statsData.total_study_min / 60).toFixed(1)}h
          </div>
          <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Recorded deep learning</div>
        </div>

        <div className="bento-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#06b6d4', fontSize: '0.8rem', fontWeight: '700', textTransform: 'uppercase' }}>
            <CheckCircle2 size={16} /> Tasks Finished
          </div>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: '#fff', marginTop: '0.4rem' }}>
            {statsData.tasks_completed}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Items completed in window</div>
        </div>
      </div>

      {/* Breakdown Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
        <div className="bento-card">
          <h3 style={{ fontSize: '1.1rem', fontWeight: '800', color: '#f8fafc', marginBottom: '1rem' }}>
            📈 Daily Completion Rates
          </h3>
          {statsData.completion_rate_series && statsData.completion_rate_series.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {statsData.completion_rate_series.slice(-7).map((item: any) => (
                <div key={item.date} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>{item.date}</span>
                  <div style={{ width: '60%', height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div style={{ width: `${item.rate}%`, height: '100%', background: '#10b981', borderRadius: '9999px' }} />
                  </div>
                  <span style={{ fontSize: '0.85rem', color: '#10b981', fontWeight: '700' }}>{Math.round(item.rate)}%</span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: '#64748b', fontSize: '0.9rem' }}>No close-outs recorded yet.</div>
          )}
        </div>

        <div className="bento-card">
          <h3 style={{ fontSize: '1.1rem', fontWeight: '800', color: '#f8fafc', marginBottom: '1rem' }}>
            📚 Study Time by Skill
          </h3>
          {statsData.study_minutes_by_skill && statsData.study_minutes_by_skill.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {statsData.study_minutes_by_skill.map((item: any) => (
                <div key={item.skill} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '0.85rem', color: '#f8fafc', fontWeight: '600' }}>{item.skill}</span>
                  <span style={{ fontSize: '0.85rem', color: '#ec4899', fontWeight: '700' }}>{item.minutes} mins</span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: '#64748b', fontSize: '0.9rem' }}>No study sessions recorded yet.</div>
          )}
        </div>
      </div>
    </div>
  );
};
