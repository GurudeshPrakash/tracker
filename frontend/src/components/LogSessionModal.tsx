import React, { useState, useEffect } from 'react';
import { X, BookOpen } from 'lucide-react';
import { logStudySession, fetchLearningData } from '../api';
import { LearningItem } from '../types';

interface LogSessionModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export const LogSessionModal: React.FC<LogSessionModalProps> = ({ onClose, onSuccess }) => {
  const [items, setItems] = useState<LearningItem[]>([]);
  const [selectedItemId, setSelectedItemId] = useState<number | ''>('');
  const [duration, setDuration] = useState<number>(30);
  const [takeaway, setTakeaway] = useState<string>('');
  const [confidence, setConfidence] = useState<number>(4);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLearningData()
      .then((res) => {
        setItems(res.items);
        if (res.items.length > 0) {
          setSelectedItemId(res.items[0].id);
        }
      })
      .catch((err) => setError(err.message));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedItemId) {
      setError('Please choose or create a learning resource first.');
      return;
    }
    if (!takeaway.trim()) {
      setError('Key takeaway is required! Condense your learning into at least 1 insight.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await logStudySession({
        learning_item_id: Number(selectedItemId),
        duration_min: duration,
        takeaway: takeaway.trim(),
        confidence,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to record session');
    } finally {
      setLoading(false);
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
      backdropFilter: 'blur(10px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        background: 'rgba(18, 24, 38, 0.98)',
        border: '1px solid rgba(236, 72, 153, 0.3)',
        borderRadius: '24px',
        padding: '2rem',
        width: '100%',
        maxWidth: '500px',
        boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8), 0 0 30px rgba(236, 72, 153, 0.1)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <div style={{ background: 'rgba(236, 72, 153, 0.2)', padding: '0.4rem', borderRadius: '10px' }}>
              <BookOpen size={20} color="#ec4899" />
            </div>
            <h3 style={{ fontSize: '1.3rem', fontWeight: '800', color: '#f8fafc' }}>
              Record Study Session
            </h3>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#fca5a5', padding: '0.65rem', borderRadius: '12px', fontSize: '0.85rem', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: '600' }}>
              Learning Resource
            </label>
            {items.length === 0 ? (
              <div style={{ fontSize: '0.85rem', color: '#f87171' }}>
                No resources created yet. Go to the Learning tab to add one!
              </div>
            ) : (
              <select
                value={selectedItemId}
                onChange={(e) => setSelectedItemId(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  borderRadius: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  background: '#121727',
                  color: '#ffffff',
                  outline: 'none',
                }}
              >
                {items.map((it) => (
                  <option key={it.id} value={it.id}>
                    {it.skill} — {it.resource}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: '600' }}>
              Duration (Minutes)
            </label>
            <input
              type="number"
              min={1}
              step={5}
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              style={{
                width: '100%',
                padding: '0.75rem',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                background: 'rgba(255, 255, 255, 0.04)',
                color: '#ffffff',
                outline: 'none',
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: '600' }}>
              Key Takeaway / Breakthrough (Required)
            </label>
            <textarea
              required
              rows={3}
              value={takeaway}
              onChange={(e) => setTakeaway(e.target.value)}
              placeholder="What core concept, syntax, or principle did you learn?"
              style={{
                width: '100%',
                padding: '0.8rem',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                background: 'rgba(255, 255, 255, 0.04)',
                color: '#ffffff',
                outline: 'none',
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: '600' }}>
              Retention Confidence ⭐ (1: Shaky - 5: Confident)
            </label>
            <input
              type="range"
              min={1}
              max={5}
              value={confidence}
              onChange={(e) => setConfidence(Number(e.target.value))}
              style={{ width: '100%', accentColor: '#ec4899' }}
            />
            <div style={{ textAlign: 'right', fontSize: '0.85rem', color: '#ec4899', fontWeight: '700' }}>
              {confidence} / 5
            </div>
          </div>

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
              disabled={loading || items.length === 0}
              style={{
                flex: 1,
                padding: '0.85rem',
                borderRadius: '14px',
                border: 'none',
                background: 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)',
                color: '#ffffff',
                fontWeight: '700',
                cursor: 'pointer',
                boxShadow: '0 0 15px rgba(236, 72, 153, 0.4)',
              }}
            >
              {loading ? 'Logging...' : 'Save Session'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
