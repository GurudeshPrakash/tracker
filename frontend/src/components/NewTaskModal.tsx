import React, { useState } from 'react';
import { X } from 'lucide-react';
import { createTask, addSubtask } from '../api';

interface NewTaskModalProps {
  parentId?: number | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const NewTaskModal: React.FC<NewTaskModalProps> = ({ parentId, onClose, onSuccess }) => {
  const [title, setTitle] = useState('');
  const [priority, setPriority] = useState<'high' | 'medium' | 'low'>('medium');
  const [category, setCategory] = useState<'work' | 'learning' | 'personal'>('work');
  const [estimatedMin, setEstimatedMin] = useState<number>(30);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setLoading(true);
    setError(null);
    try {
      if (parentId) {
        await addSubtask(parentId, title.trim());
      } else {
        await createTask({
          title: title.trim(),
          priority,
          category,
          estimated_min: estimatedMin,
        });
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save task');
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
      background: 'rgba(0, 0, 0, 0.7)',
      backdropFilter: 'blur(10px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        background: 'rgba(18, 24, 38, 0.98)',
        border: '1px solid rgba(255, 255, 255, 0.12)',
        borderRadius: '24px',
        padding: '2rem',
        width: '100%',
        maxWidth: '480px',
        boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1.3rem', fontWeight: '800', color: '#f8fafc' }}>
            {parentId ? '🔨 Break Down Subtask' : '➕ Create New Task'}
          </h3>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#fca5a5', padding: '0.6rem', borderRadius: '10px', fontSize: '0.85rem', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: '600' }}>
              Task Title
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="What outcome are you aiming for?"
              style={{
                width: '100%',
                padding: '0.85rem',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                background: 'rgba(255, 255, 255, 0.04)',
                color: '#ffffff',
                fontSize: '0.95rem',
                outline: 'none',
              }}
            />
          </div>

          {!parentId && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: '600' }}>
                  Priority
                </label>
                <select
                  value={priority}
                  onChange={(e: any) => setPriority(e.target.value)}
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
                  <option value="high">High Priority</option>
                  <option value="medium">Medium Priority</option>
                  <option value="low">Low Priority</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: '600' }}>
                  Category
                </label>
                <select
                  value={category}
                  onChange={(e: any) => setCategory(e.target.value)}
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
                  <option value="work">Work</option>
                  <option value="learning">Learning</option>
                  <option value="personal">Personal</option>
                </select>
              </div>
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: '600' }}>
              Estimated Duration (Minutes)
            </label>
            <input
              type="number"
              min={5}
              step={5}
              value={estimatedMin}
              onChange={(e) => setEstimatedMin(Number(e.target.value))}
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

          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
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
              disabled={loading}
              style={{
                flex: 1,
                padding: '0.85rem',
                borderRadius: '14px',
                border: 'none',
                background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
                color: '#ffffff',
                fontWeight: '700',
                cursor: 'pointer',
                boxShadow: '0 0 15px rgba(6, 182, 212, 0.4)',
              }}
            >
              {loading ? 'Saving...' : 'Add Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
