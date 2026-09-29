import React, { useEffect, useState } from 'react';
import { CalendarDays } from 'lucide-react';
import { fetchReviews, saveReview } from '../api';
import { ReviewsPayload } from '../types';

function shiftWeek(iso: string, days: number): string {
  const d = new Date(`${iso}T00:00:00`);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export const WeeklyReviewView: React.FC = () => {
  const [payload, setPayload] = useState<ReviewsPayload | null>(null);
  const [week, setWeek] = useState<string | undefined>(undefined);
  const [wins, setWins] = useState('');
  const [blockers, setBlockers] = useState('');
  const [nextFocus, setNextFocus] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);

  const load = (targetWeek?: string) => {
    setLoading(true);
    setError(null);
    fetchReviews(targetWeek)
      .then((res) => {
        setPayload(res);
        setWeek(res.selected_week);
        setWins(res.review?.wins || '');
        setBlockers(res.review?.blockers || '');
        setNextFocus(res.review?.next_focus || '');
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!week) return;
    setSaving(true);
    setError(null);
    setSavedMsg(null);
    try {
      await saveReview({ week_start: week, wins, blockers, next_focus: nextFocus });
      setSavedMsg('Weekly review saved.');
      load(week);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading && !payload) {
    return <div style={{ padding: '2rem', color: '#94a3b8' }}>Loading weekly review...</div>;
  }

  const summary = payload?.summary;

  return (
    <div style={{ padding: '1rem', width: '100%', maxWidth: '980px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: '1rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.8rem', fontWeight: '800', color: '#f8fafc' }}>
            Weekly Review
          </h2>
          <div style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
            Close the week, then set next week’s focus
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button
            onClick={() => week && load(shiftWeek(week, -7))}
            style={{ padding: '0.5rem 0.75rem', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.1)', background: 'transparent', color: '#cbd5e1', cursor: 'pointer' }}
          >
            ← Prev
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#06b6d4', fontWeight: 700 }}>
            <CalendarDays size={16} /> Week of {week}
          </div>
          <button
            onClick={() => week && load(shiftWeek(week, 7))}
            style={{ padding: '0.5rem 0.75rem', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.1)', background: 'transparent', color: '#cbd5e1', cursor: 'pointer' }}
          >
            Next →
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#fca5a5', padding: '0.75rem', borderRadius: '12px', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.25rem' }}>
          <div className="bento-card">
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 700 }}>TASKS DONE</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fff' }}>{summary.tasks_completed}</div>
          </div>
          <div className="bento-card">
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 700 }}>COMPLETION</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fff' }}>{Math.round(summary.completion_rate)}%</div>
          </div>
          <div className="bento-card">
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 700 }}>STUDY</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fff' }}>{summary.study_hours}h</div>
          </div>
          <div className="bento-card">
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 700 }}>AVG RATING</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fff' }}>
              {summary.avg_rating != null ? Number(summary.avg_rating).toFixed(1) : '—'}
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
        <div className="bento-card" style={{ fontSize: '0.88rem', color: '#cbd5e1' }}>
          <b style={{ color: '#f8fafc' }}>Peak day:</b>{' '}
          {summary?.best_day
            ? `${summary.best_day.date} · ${summary.best_day.rating}★ · ${summary.best_day.completed} tasks`
            : 'No ratings this week'}
        </div>
        <div className="bento-card" style={{ fontSize: '0.88rem', color: '#cbd5e1' }}>
          <b style={{ color: '#f8fafc' }}>Top skill:</b> {summary?.top_skill || 'No sessions logged'}
        </div>
      </div>

      {summary?.takeaways && summary.takeaways.length > 0 && (
        <div className="bento-card" style={{ marginBottom: '1.25rem' }}>
          <div style={{ fontWeight: 800, color: '#f8fafc', marginBottom: '0.5rem' }}>Takeaways this week</div>
          <ul style={{ marginLeft: '1.1rem', color: '#94a3b8', fontSize: '0.88rem' }}>
            {summary.takeaways.slice(0, 8).map((tw, i) => (
              <li key={i} style={{ marginBottom: '0.25rem' }}>{tw}</li>
            ))}
          </ul>
        </div>
      )}

      <form onSubmit={handleSave} className="bento-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Wins</label>
          <textarea
            rows={3}
            value={wins}
            onChange={(e) => setWins(e.target.value)}
            placeholder="What actually moved this week?"
            style={{ width: '100%', padding: '0.75rem', borderRadius: '12px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Blockers</label>
          <textarea
            rows={2}
            value={blockers}
            onChange={(e) => setBlockers(e.target.value)}
            placeholder="What repeatedly slowed you down?"
            style={{ width: '100%', padding: '0.75rem', borderRadius: '12px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Next week focus</label>
          <textarea
            rows={2}
            value={nextFocus}
            onChange={(e) => setNextFocus(e.target.value)}
            placeholder="One outcome that would make next week a win"
            style={{ width: '100%', padding: '0.75rem', borderRadius: '12px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
          />
        </div>
        {savedMsg && <div style={{ color: '#34d399', fontSize: '0.85rem' }}>{savedMsg}</div>}
        <button
          type="submit"
          disabled={saving}
          style={{
            alignSelf: 'flex-start',
            padding: '0.7rem 1.25rem',
            borderRadius: '12px',
            border: 'none',
            background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
            color: '#fff',
            fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          {saving ? 'Saving...' : 'Save weekly review'}
        </button>
      </form>
    </div>
  );
};
