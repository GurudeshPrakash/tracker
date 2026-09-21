import React, { useState, useEffect } from 'react';
import { api } from '../api';

interface DailyUpdateModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export const DailyUpdateModal: React.FC<DailyUpdateModalProps> = ({ onClose, onSuccess }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [carryTaskIds, setCarryTaskIds] = useState<number[]>([]);
  const [wins, setWins] = useState('');
  const [blockers, setBlockers] = useState('');
  const [focusTomorrow, setFocusTomorrow] = useState('');
  const [moodRating, setMoodRating] = useState(4);
  const [prodRating, setProdRating] = useState(4);

  useEffect(() => {
    api.getDailyUpdate().then((res) => {
      setData(res);
      // Default: all open tasks carry forward
      setCarryTaskIds(res.open_tasks.map((t: any) => t.id));
      if (res.existing) {
        setWins(res.existing.wins || '');
        setBlockers(res.existing.blockers || '');
        setFocusTomorrow(res.existing.focus_tomorrow || '');
        setMoodRating(res.existing.mood_rating || 4);
        setProdRating(res.existing.productivity_rating || 4);
      }
      setLoading(false);
    });
  }, []);

  const toggleCarry = (id: number) => {
    setCarryTaskIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!data) return;
    const dropIds = data.open_tasks
      .map((t: any) => t.id)
      .filter((id: number) => !carryTaskIds.includes(id));

    await api.closeDailyUpdate({
      report_date: data.report_date,
      carry_task_ids: carryTaskIds,
      drop_task_ids: dropIds,
      wins,
      blockers,
      focus_tomorrow: focusTomorrow,
      mood_rating: moodRating,
      productivity_rating: prodRating,
    });

    onSuccess();
    onClose();
  };

  if (loading) {
    return (
      <div className="modal-overlay">
        <div className="modal-card" style={{ textAlign: 'center', padding: '2.5rem' }}>
          Loading daily review...
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-card"
        style={{ maxWidth: '640px', maxHeight: '90vh', overflowY: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <h3 className="modal-title">Daily Update & Close Day</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>Date: {data.report_date}</p>
          </div>
          <button onClick={onClose} style={{ color: '#94a3b8' }}>✕</button>
        </div>

        {/* Prefill stats */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '0.75rem',
            background: '#f8fafc',
            padding: '1rem',
            borderRadius: '12px',
            marginBottom: '1.25rem',
            textAlign: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#7c3aed' }}>
              {data.prefill.completed_count} / {data.prefill.planned_count}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>Tasks Done</div>
          </div>
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#06b6d4' }}>
              {data.prefill.study_minutes} min
            </div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>Study Time</div>
          </div>
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#10b981' }}>
              {data.prefill.planned_count > 0
                ? Math.round((data.prefill.completed_count / data.prefill.planned_count) * 100)
                : 100}
              %
            </div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>Completion</div>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Open Tasks Selection */}
          {data.open_tasks.length > 0 && (
            <div style={{ marginBottom: '1.25rem' }}>
              <label className="form-label">
                Unfinished Tasks ({data.open_tasks.length}) — Choose Carry Forward or Drop
              </label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {data.open_tasks.map((task: any) => {
                  const isCarried = carryTaskIds.includes(task.id);
                  return (
                    <div
                      key={task.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.6rem 0.85rem',
                        background: isCarried ? '#f0fdf4' : '#fef2f2',
                        border: `1px solid ${isCarried ? '#bbf7d0' : '#fecaca'}`,
                        borderRadius: '8px',
                        cursor: 'pointer',
                      }}
                      onClick={() => toggleCarry(task.id)}
                    >
                      <span style={{ fontSize: '0.88rem', fontWeight: 600, color: '#1e293b' }}>
                        {task.title}
                      </span>
                      <span
                        style={{
                          fontSize: '0.78rem',
                          fontWeight: 700,
                          color: isCarried ? '#16a34a' : '#dc2626',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                        }}
                      >
                        {isCarried ? 'Carry to tomorrow' : 'Drop task'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Wins & Accomplishments</label>
            <textarea
              className="form-input"
              rows={2}
              placeholder="What went well today?"
              value={wins}
              onChange={(e) => setWins(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Blockers or Challenges</label>
            <textarea
              className="form-input"
              rows={2}
              placeholder="What slowed you down?"
              value={blockers}
              onChange={(e) => setBlockers(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Top Focus for Tomorrow</label>
            <input
              type="text"
              className="form-input"
              placeholder="Key priority for tomorrow"
              value={focusTomorrow}
              onChange={(e) => setFocusTomorrow(e.target.value)}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label className="form-label">Mood Rating (1-5)</label>
              <select
                className="form-input"
                value={moodRating}
                onChange={(e) => setMoodRating(Number(e.target.value))}
              >
                {[1, 2, 3, 4, 5].map((r) => (
                  <option key={r} value={r}>
                    {r} ★
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="form-label">Productivity Rating (1-5)</label>
              <select
                className="form-input"
                value={prodRating}
                onChange={(e) => setProdRating(Number(e.target.value))}
              >
                {[1, 2, 3, 4, 5].map((r) => (
                  <option key={r} value={r}>
                    {r} ★
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              Close My Day
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
