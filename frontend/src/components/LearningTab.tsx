import React, { useState } from 'react';
import { BookOpen, Award, Plus } from 'lucide-react';
import { LearningData } from '../types';

interface LearningTabProps {
  learningData: LearningData | null;
  onLogSession: (session: {
    skill_id: number;
    duration_min: number;
    takeaway: string;
    quality_rating?: number;
  }) => void;
}

export const LearningTab: React.FC<LearningTabProps> = ({ learningData, onLogSession }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [skillId, setSkillId] = useState<number>(1);
  const [duration, setDuration] = useState(45);
  const [takeaway, setTakeaway] = useState('');
  const [quality, setQuality] = useState(4);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!takeaway.trim()) return;
    onLogSession({
      skill_id: skillId,
      duration_min: duration,
      takeaway: takeaway.trim(),
      quality_rating: quality,
    });
    setTakeaway('');
    setIsModalOpen(false);
  };

  if (!learningData) {
    return <div className="tasks-card-container">Loading learning system...</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner */}
      <div className="tasks-card-container">
        <div className="card-header-bar">
          <div className="card-title-group">
            <div className="card-icon-wrapper" style={{ color: '#06b6d4' }}>
              <BookOpen size={22} />
            </div>
            <div>
              <h3 className="card-title">Skills & Learning Sessions</h3>
              <p style={{ fontSize: '0.86rem', color: '#64748b' }}>
                Track deliberate practice, spaced repetition takeaways, and skill mastery.
              </p>
            </div>
          </div>

          <button
            className="btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
            onClick={() => {
              if (learningData.skills.length > 0) setSkillId(learningData.skills[0].id);
              setIsModalOpen(true);
            }}
          >
            <Plus size={16} />
            <span>Log Study Session</span>
          </button>
        </div>

        {/* Skills Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
          {learningData.skills.map((skill) => (
            <div
              key={skill.id}
              style={{
                padding: '1rem',
                borderRadius: '12px',
                border: '1px solid #f1f5f9',
                background: '#ffffff',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                <span className="section-badge-pill badge-in-progress" style={{ fontSize: '0.7rem' }}>
                  {skill.category}
                </span>
                <span style={{ fontSize: '0.78rem', color: '#7c3aed', fontWeight: 700 }}>
                  {skill.proficiency}
                </span>
              </div>
              <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a' }}>{skill.name}</h4>
            </div>
          ))}
        </div>
      </div>

      {/* Spaced Repetition Review Queue */}
      <div className="tasks-card-container">
        <div className="card-header-bar">
          <div className="card-title-group">
            <div className="card-icon-wrapper" style={{ color: '#8b5cf6' }}>
              <Award size={20} />
            </div>
            <h3 className="card-title">Spaced Repetition Review Queue</h3>
          </div>
        </div>

        {learningData.review_queue.length === 0 ? (
          <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
            No reviews due today! All previous key takeaways have been refreshed.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {learningData.review_queue.map((item) => (
              <div
                key={item.id}
                style={{
                  padding: '1rem',
                  borderRadius: '10px',
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                }}
              >
                <div style={{ fontSize: '0.78rem', color: '#64748b', marginBottom: '4px' }}>
                  Learned on {item.session_date} ({item.duration_min} min session)
                </div>
                <div style={{ fontSize: '0.95rem', fontWeight: 600, color: '#1e293b' }}>
                  "{item.takeaway}"
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Logged Sessions */}
      <div className="tasks-card-container">
        <h3 className="card-title" style={{ marginBottom: '1rem' }}>Recent Study History</h3>
        {learningData.sessions.length === 0 ? (
          <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>No sessions logged yet.</p>
        ) : (
          <table className="task-table">
            <thead>
              <tr className="table-head-row">
                <th style={{ width: '20%' }}>Date</th>
                <th style={{ width: '15%' }}>Duration</th>
                <th style={{ width: '50%' }}>Key Takeaway</th>
                <th style={{ width: '15%', textAlign: 'right' }}>Quality</th>
              </tr>
            </thead>
            <tbody>
              {learningData.sessions.map((sess) => (
                <tr key={sess.id} className="task-row">
                  <td style={{ fontSize: '0.88rem', color: '#64748b' }}>{sess.session_date}</td>
                  <td style={{ fontSize: '0.88rem', fontWeight: 600 }}>{sess.duration_min} min</td>
                  <td style={{ fontSize: '0.9rem', fontWeight: 500, color: '#1e293b' }}>{sess.takeaway}</td>
                  <td style={{ textAlign: 'right', color: '#f59e0b', fontWeight: 700 }}>
                    {sess.quality_rating ? `${sess.quality_rating} ★` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Log Session Modal */}
      {isModalOpen && (
        <div className="modal-overlay" onClick={() => setIsModalOpen(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Log Deliberate Study Session</h3>
              <button onClick={() => setIsModalOpen(false)} style={{ color: '#94a3b8' }}>✕</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Select Skill</label>
                <select
                  className="form-input"
                  value={skillId}
                  onChange={(e) => setSkillId(Number(e.target.value))}
                >
                  {learningData.skills.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.category})
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Duration (minutes)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={duration}
                    onChange={(e) => setDuration(Number(e.target.value))}
                    min={5}
                    step={5}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Session Quality (1-5)</label>
                  <select
                    className="form-input"
                    value={quality}
                    onChange={(e) => setQuality(Number(e.target.value))}
                  >
                    {[1, 2, 3, 4, 5].map((q) => (
                      <option key={q} value={q}>
                        {q} ★
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">
                  Key Takeaway <span style={{ color: '#ef4444' }}>* (Required per spec)</span>
                </label>
                <textarea
                  className="form-input"
                  rows={3}
                  placeholder="What one key insight or formula did you master in this session?"
                  value={takeaway}
                  onChange={(e) => setTakeaway(e.target.value)}
                  required
                />
              </div>

              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save Session
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
