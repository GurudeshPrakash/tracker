import React, { useState, useEffect } from 'react';
import { Target, Plus, CheckCircle, Pause, Play, Trash2, Flame } from 'lucide-react';
import { fetchGoals, createGoal, updateGoalStatus } from '../api';
import { useFocusMode } from '../FocusContext';

export const GoalsView: React.FC = () => {
  const [goals, setGoals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [title, setTitle] = useState('');
  const [targetType, setTargetType] = useState('weekly_hours');
  const [targetHours, setTargetHours] = useState(5);
  const [error, setError] = useState<string | null>(null);

  const { isFocusMode, startFocus, setActiveTopic, activeTopic } = useFocusMode();

  const load = () => {
    setLoading(true);
    fetchGoals()
      .then(setGoals)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    try {
      await createGoal({
        title: title.trim(),
        target_type: targetType,
        target_hours: targetHours,
        start_date: new Date().toISOString().split('T')[0],
      });
      setTitle('');
      setShowAdd(false);
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleStatus = async (id: number, status: string) => {
    try {
      await updateGoalStatus(id, status);
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div style={{ padding: '0.5rem 0', width: '100%', maxWidth: '1440px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <h2 style={{ fontSize: '1.8rem', fontWeight: '800', color: '#f8fafc' }}>
              🎯 Strategic Objectives & Goals
            </h2>
            {isFocusMode && (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  padding: '0.2rem 0.65rem',
                  borderRadius: '9999px',
                  background: 'rgba(236, 72, 153, 0.2)',
                  border: '1px solid #ec4899',
                  color: '#f472b6',
                  fontSize: '0.75rem',
                  fontWeight: 800,
                }}
              >
                <Flame size={13} /> FOCUS TAB
              </span>
            )}
          </div>
          <div style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            Track weekly milestones and expected completion pace
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {!isFocusMode && (
            <button
              onClick={() => startFocus(goals[0]?.goal?.title || 'Goal Progression')}
              style={{
                background: 'linear-gradient(135deg, #ec4899 0%, #d946ef 100%)',
                border: 'none',
                color: '#ffffff',
                padding: '0.65rem 1.15rem',
                borderRadius: '12px',
                fontWeight: '700',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                boxShadow: '0 0 15px rgba(236, 72, 153, 0.35)',
              }}
            >
              <Flame size={16} /> Start Focus Mode
            </button>
          )}
          <button
            onClick={() => setShowAdd(!showAdd)}
            style={{
              background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
              border: 'none',
              color: '#ffffff',
              padding: '0.65rem 1.25rem',
              borderRadius: '12px',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              boxShadow: '0 0 15px rgba(6, 182, 212, 0.3)',
            }}
          >
            <Plus size={16} /> New Goal
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#fca5a5', padding: '0.75rem', borderRadius: '12px', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {showAdd && (
        <form onSubmit={handleCreate} className="bento-card" style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div style={{ flex: 2, minWidth: '200px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.3rem' }}>Goal Title</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Master Distributed Systems"
              style={{ width: '100%', padding: '0.65rem', borderRadius: '10px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
            />
          </div>
          <div style={{ width: '160px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.3rem' }}>Target Type</label>
            <select
              value={targetType}
              onChange={(e) => setTargetType(e.target.value)}
              style={{ width: '100%', padding: '0.65rem', borderRadius: '10px', background: '#121727', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
            >
              <option value="weekly_hours">Weekly Hours</option>
              <option value="total_hours">Total Hours</option>
            </select>
          </div>
          <div style={{ width: '130px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.3rem' }}>Target Hours</label>
            <input
              type="number"
              min={1}
              required
              value={targetHours}
              onChange={(e) => setTargetHours(Number(e.target.value))}
              style={{ width: '100%', padding: '0.65rem', borderRadius: '10px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
            />
          </div>
          <button
            type="submit"
            style={{ padding: '0.65rem 1.25rem', borderRadius: '10px', background: '#06b6d4', color: '#fff', border: 'none', fontWeight: '700', cursor: 'pointer' }}
          >
            Create Goal
          </button>
        </form>
      )}

      {loading ? (
        <div style={{ color: '#94a3b8' }}>Loading goals...</div>
      ) : goals.length === 0 ? (
        <div className="bento-card" style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>
          No goals created yet. Click "+ New Goal" to establish your targets.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '1.25rem' }}>
          {goals.map(({ goal, progress, linked_resources }) => {
            const isCurrentFocus = isFocusMode && activeTopic === goal.title;
            return (
              <div
                key={goal.id}
                className="bento-card"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  border: isCurrentFocus
                    ? '1px solid #ec4899'
                    : '1px solid rgba(255, 255, 255, 0.08)',
                  boxShadow: isCurrentFocus ? '0 0 25px rgba(236,72,153,0.2)' : 'none',
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <h3 style={{ fontSize: '1.15rem', fontWeight: '800', color: '#f8fafc' }}>{goal.title}</h3>
                        {isCurrentFocus && (
                          <span style={{ fontSize: '0.68rem', color: '#f472b6', fontWeight: '800' }}>
                            ACTIVE FOCUS
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                        {goal.target_type.replace('_', ' ')} &bull; Target: {goal.target_hours}h
                      </div>
                    </div>
                    <span className={`pill-neon-${progress.status === 'behind' ? 'high' : 'low'}`}>
                      {progress.status.toUpperCase()}
                    </span>
                  </div>

                  {/* Progress bar */}
                  <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '9999px', overflow: 'hidden', margin: '1rem 0' }}>
                    <div
                      style={{
                        width: `${Math.min(progress.percent, 100)}%`,
                        height: '100%',
                        background: 'linear-gradient(90deg, #06b6d4 0%, #ec4899 100%)',
                        borderRadius: '9999px',
                      }}
                    />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: '#cbd5e1', marginBottom: '0.75rem' }}>
                    <span>Done: <b>{progress.done_hours.toFixed(1)}h</b></span>
                    <span>Progress: <b>{Math.round(progress.percent)}%</b></span>
                  </div>

                  {linked_resources && linked_resources.length > 0 && (
                    <div style={{ fontSize: '0.78rem', color: '#94a3b8', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '0.5rem' }}>
                      Linked: {linked_resources.map((r: any) => r.skill).join(', ')}
                    </div>
                  )}
                </div>

                {/* Actions & Focus button */}
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.25rem', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '0.75rem', flexWrap: 'wrap' }}>
                  {isFocusMode && !isCurrentFocus && (
                    <button
                      onClick={() => setActiveTopic(goal.title)}
                      style={{
                        width: '100%',
                        marginBottom: '0.35rem',
                        padding: '0.35rem',
                        borderRadius: '8px',
                        background: 'rgba(236, 72, 153, 0.15)',
                        border: '1px solid rgba(236, 72, 153, 0.4)',
                        color: '#f472b6',
                        fontSize: '0.75rem',
                        fontWeight: '700',
                        cursor: 'pointer',
                      }}
                    >
                      Focus on this Goal
                    </button>
                  )}
                  {goal.status === 'active' && (
                    <button
                      onClick={() => handleStatus(goal.id, 'done')}
                      style={{ flex: 1, padding: '0.4rem', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#34d399', fontSize: '0.75rem', fontWeight: '700', cursor: 'pointer' }}
                    >
                      Done
                    </button>
                  )}
                  {goal.status === 'active' ? (
                    <button
                      onClick={() => handleStatus(goal.id, 'paused')}
                      style={{ flex: 1, padding: '0.4rem', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.3)', color: '#fbbf24', fontSize: '0.75rem', fontWeight: '700', cursor: 'pointer' }}
                    >
                      Pause
                    </button>
                  ) : (
                    <button
                      onClick={() => handleStatus(goal.id, 'active')}
                      style={{ flex: 1, padding: '0.4rem', borderRadius: '8px', background: 'rgba(6, 182, 212, 0.15)', border: '1px solid rgba(6, 182, 212, 0.3)', color: '#06b6d4', fontSize: '0.75rem', fontWeight: '700', cursor: 'pointer' }}
                    >
                      Resume
                    </button>
                  )}
                  <button
                    onClick={() => handleStatus(goal.id, 'dropped')}
                    style={{ padding: '0.4rem 0.6rem', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', fontSize: '0.75rem', cursor: 'pointer' }}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
