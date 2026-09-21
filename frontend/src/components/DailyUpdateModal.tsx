import React, { useState, useEffect } from 'react';
import { X, Moon, CheckCircle2, ArrowRight } from 'lucide-react';
import { fetchDailyUpdate, closeDailyUpdate } from '../api';
import { DailyUpdatePrefill } from '../types';

interface DailyUpdateModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export const DailyUpdateModal: React.FC<DailyUpdateModalProps> = ({ onClose, onSuccess }) => {
  const [data, setData] = useState<DailyUpdatePrefill | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [summary, setSummary] = useState('');
  const [learned, setLearned] = useState('');
  const [studyMin, setStudyMin] = useState(0);
  const [rating, setRating] = useState(4);
  const [blockers, setBlockers] = useState('');
  const [tomorrowFocus, setTomorrowFocus] = useState('');
  const [carryMap, setCarryMap] = useState<Record<number, boolean>>({});

  useEffect(() => {
    fetchDailyUpdate()
      .then((res) => {
        setData(res);
        const defaultSum = res.completed_tasks.map((t) => `• ${t.title}`).join('\n');
        const defaultLearn = res.session_takeaways.map((tw) => `• ${tw}`).join('\n');

        setSummary(res.existing?.completed_summary || defaultSum);
        setLearned(res.existing?.learned_today || defaultLearn);
        setStudyMin(res.existing?.study_minutes ?? res.study_minutes);
        setRating(res.existing?.day_rating || 4);
        setBlockers(res.existing?.blockers || '');
        setTomorrowFocus(res.existing?.tomorrow_focus || '');

        const initialCarry: Record<number, boolean> = {};
        res.open_tasks.forEach((t) => {
          initialCarry[t.id] = true;
        });
        setCarryMap(initialCarry);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!data) return;

    setSubmitting(true);
    setError(null);
    try {
      const carryIds = Object.keys(carryMap)
        .filter((k) => carryMap[Number(k)])
        .map(Number);

      await closeDailyUpdate({
        date: data.date,
        completed_summary: summary,
        learned_today: learned,
        study_minutes: studyMin,
        day_rating: rating,
        blockers,
        tomorrow_focus: tomorrowFocus,
        carry_task_ids: carryIds,
      });

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to close day');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(12px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1.5rem',
    }}>
      <div style={{
        background: 'rgba(16, 21, 35, 0.98)',
        border: '1px solid rgba(255, 255, 255, 0.12)',
        borderRadius: '26px',
        padding: '2.25rem',
        width: '100%',
        maxWidth: '680px',
        maxHeight: '90vh',
        overflowY: 'auto',
        boxShadow: '0 30px 70px rgba(0, 0, 0, 0.9)',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <div style={{ background: 'rgba(99, 102, 241, 0.2)', padding: '0.4rem', borderRadius: '10px' }}>
              <Moon size={22} color="#818cf8" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.4rem', fontWeight: '800', color: '#f8fafc' }}>
                Evening Daily Reflection
              </h3>
              <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                Close out {data?.date || 'today'} &bull; Preserve streak &bull; Move tasks forward
              </div>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>Preparing daily summary...</div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {error && (
              <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#fca5a5', padding: '0.65rem', borderRadius: '12px', fontSize: '0.85rem' }}>
                {error}
              </div>
            )}

            {/* Completed accomplishments */}
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#cbd5e1', fontWeight: '700', marginBottom: '0.4rem' }}>
                What I accomplished today
              </label>
              <textarea
                rows={3}
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.85rem',
                  borderRadius: '14px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  background: 'rgba(255, 255, 255, 0.03)',
                  color: '#ffffff',
                  fontSize: '0.9rem',
                  outline: 'none',
                }}
              />
            </div>

            {/* Learning takeaways */}
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#cbd5e1', fontWeight: '700', marginBottom: '0.4rem' }}>
                Key discoveries & takeaways
              </label>
              <textarea
                rows={3}
                value={learned}
                onChange={(e) => setLearned(e.target.value)}
                placeholder="What did you learn or master today?"
                style={{
                  width: '100%',
                  padding: '0.85rem',
                  borderRadius: '14px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  background: 'rgba(255, 255, 255, 0.03)',
                  color: '#ffffff',
                  fontSize: '0.9rem',
                  outline: 'none',
                }}
              />
            </div>

            {/* Metrics Row: Study Mins & Day Rating */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#cbd5e1', fontWeight: '700', marginBottom: '0.4rem' }}>
                  Total Study Minutes
                </label>
                <input
                  type="number"
                  min={0}
                  step={5}
                  value={studyMin}
                  onChange={(e) => setStudyMin(Number(e.target.value))}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    borderRadius: '12px',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    background: 'rgba(255, 255, 255, 0.03)',
                    color: '#ffffff',
                    outline: 'none',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#cbd5e1', fontWeight: '700', marginBottom: '0.4rem' }}>
                  Satisfaction Energy ⭐ (1-5)
                </label>
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.2rem' }}>
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setRating(star)}
                      style={{
                        flex: 1,
                        padding: '0.55rem',
                        borderRadius: '10px',
                        border: rating >= star ? '1px solid #fbbf24' : '1px solid rgba(255, 255, 255, 0.1)',
                        background: rating >= star ? 'rgba(251, 191, 36, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                        color: rating >= star ? '#fbbf24' : '#64748b',
                        fontSize: '1rem',
                        fontWeight: '700',
                        cursor: 'pointer',
                      }}
                    >
                      {star}★
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Blockers & Tomorrow Focus */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#cbd5e1', fontWeight: '700', marginBottom: '0.4rem' }}>
                  Blockers / Friction
                </label>
                <input
                  type="text"
                  value={blockers}
                  onChange={(e) => setBlockers(e.target.value)}
                  placeholder="Any interruptions or blockers?"
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    borderRadius: '12px',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    background: 'rgba(255, 255, 255, 0.03)',
                    color: '#ffffff',
                    outline: 'none',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#cbd5e1', fontWeight: '700', marginBottom: '0.4rem' }}>
                  Tomorrow's Single Focus
                </label>
                <input
                  type="text"
                  value={tomorrowFocus}
                  onChange={(e) => setTomorrowFocus(e.target.value)}
                  placeholder="Most vital outcome tomorrow"
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    borderRadius: '12px',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    background: 'rgba(255, 255, 255, 0.03)',
                    color: '#ffffff',
                    outline: 'none',
                  }}
                />
              </div>
            </div>

            {/* Open tasks carry over disposition */}
            {data && data.open_tasks.length > 0 && (
              <div style={{
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '16px',
                padding: '1rem',
              }}>
                <div style={{ fontSize: '0.9rem', fontWeight: '700', color: '#f8fafc', marginBottom: '0.25rem' }}>
                  ⏳ Unfinished Tasks Rollover
                </div>
                <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.65rem' }}>
                  Checked tasks will be carried over to tomorrow. Unchecked tasks will be marked dropped.
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {data.open_tasks.map((task) => (
                    <label
                      key={task.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.6rem',
                        fontSize: '0.88rem',
                        color: '#f1f5f9',
                        cursor: 'pointer',
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={carryMap[task.id] ?? true}
                        onChange={(e) => setCarryMap({ ...carryMap, [task.id]: e.target.checked })}
                        style={{ accentColor: '#06b6d4', width: '16px', height: '16px' }}
                      />
                      <span>{task.title}</span>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>({task.priority})</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Buttons */}
            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
              <button
                type="button"
                onClick={onClose}
                style={{
                  flex: 1,
                  padding: '0.85rem',
                  borderRadius: '14px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  background: 'transparent',
                  color: '#94a3b8',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                style={{
                  flex: 2,
                  padding: '0.85rem',
                  borderRadius: '14px',
                  border: 'none',
                  background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                  color: '#ffffff',
                  fontWeight: '700',
                  cursor: 'pointer',
                  boxShadow: '0 0 20px rgba(99, 102, 241, 0.4)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.4rem',
                }}
              >
                {submitting ? 'Closing Day...' : '🌙 Complete Close-Out & Plan Tomorrow'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
