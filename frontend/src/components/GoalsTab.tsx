import React, { useState } from 'react';
import { Target, Plus } from 'lucide-react';
import { Goal } from '../types';

interface GoalsTabProps {
  goals: Goal[];
  onCreateGoal: (data: any) => void;
}

export const GoalsTab: React.FC<GoalsTabProps> = ({ goals, onCreateGoal }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Work');
  const [targetHours, setTargetHours] = useState(20);
  const [weeklyTarget, setWeeklyTarget] = useState(5);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    onCreateGoal({
      title: title.trim(),
      category,
      target_hours: targetHours,
      weekly_hours_target: weeklyTarget,
    });
    setTitle('');
    setIsModalOpen(false);
  };

  return (
    <div className="tasks-card-container">
      <div className="card-header-bar">
        <div className="card-title-group">
          <div className="card-icon-wrapper" style={{ color: '#8b5cf6' }}>
            <Target size={22} />
          </div>
          <div>
            <h3 className="card-title">Goals & Milestones</h3>
            <p style={{ fontSize: '0.86rem', color: '#64748b' }}>
              Target tracking, cumulative progress, and linked learning resources.
            </p>
          </div>
        </div>

        <button
          className="btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
          onClick={() => setIsModalOpen(true)}
        >
          <Plus size={16} />
          <span>New Goal</span>
        </button>
      </div>

      {goals.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '2.5rem', color: '#94a3b8' }}>
          No goals established yet. Create one to enable smart daily suggestions!
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem', marginTop: '1rem' }}>
          {goals.map((g) => {
            const loggedHours = (g.logged_minutes / 60).toFixed(1);
            return (
              <div
                key={g.id}
                style={{
                  padding: '1.25rem',
                  borderRadius: '16px',
                  border: '1px solid #e2e8f0',
                  background: '#ffffff',
                  boxShadow: 'var(--shadow-sm)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span className="section-badge-pill badge-in-progress" style={{ fontSize: '0.72rem' }}>
                    {g.category}
                  </span>
                  <span style={{ fontSize: '0.82rem', fontWeight: 700, color: g.status === 'active' ? '#16a34a' : '#94a3b8' }}>
                    {g.status.toUpperCase()}
                  </span>
                </div>

                <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#0f172a' }}>{g.title}</h4>

                {/* Progress bar */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#64748b', marginBottom: '4px' }}>
                    <span>{loggedHours}h / {g.target_hours || '—'}h logged</span>
                    <span style={{ fontWeight: 700, color: '#7c3aed' }}>{g.progress_pct}%</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${Math.min(g.progress_pct, 100)}%`,
                        height: '100%',
                        background: 'linear-gradient(90deg, #7c3aed, #06b6d4)',
                        borderRadius: '4px',
                        transition: 'width 0.3s ease',
                      }}
                    />
                  </div>
                </div>

                {g.weekly_hours_target && (
                  <div style={{ fontSize: '0.82rem', color: '#64748b' }}>
                    Weekly Pace: <strong>{g.weekly_hours_target} hrs/week</strong>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Goal Modal */}
      {isModalOpen && (
        <div className="modal-overlay" onClick={() => setIsModalOpen(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Create Goal</h3>
              <button onClick={() => setIsModalOpen(false)} style={{ color: '#94a3b8' }}>✕</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Goal Title</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Master React & System Design"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Category</label>
                  <select className="form-input" value={category} onChange={(e) => setCategory(e.target.value)}>
                    <option value="Work">Product launch (Work)</option>
                    <option value="Personal">Team brainstorm (Personal)</option>
                    <option value="Learning">Branding launch (Learning)</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Target Total Hours</label>
                  <input
                    type="number"
                    className="form-input"
                    value={targetHours}
                    onChange={(e) => setTargetHours(Number(e.target.value))}
                    min={1}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Weekly Hours Target (for AI suggestions)</label>
                <input
                  type="number"
                  className="form-input"
                  value={weeklyTarget}
                  onChange={(e) => setWeeklyTarget(Number(e.target.value))}
                  min={1}
                />
              </div>

              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Create Goal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
