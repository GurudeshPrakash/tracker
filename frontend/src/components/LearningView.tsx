import React, { useState, useEffect } from 'react';
import { BookOpen, Plus, Atom, RotateCw, Check, X, Flame, Play } from 'lucide-react';
import { fetchLearningData, createLearningItem } from '../api';
import { LearningItem } from '../types';
import { useFocusMode } from '../FocusContext';

export const LearningView: React.FC<{ onOpenLogModal: () => void }> = ({ onOpenLogModal }) => {
  const [items, setItems] = useState<LearningItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [skill, setSkill] = useState('');
  const [resource, setResource] = useState('');
  const [resourceType, setResourceType] = useState('course');
  const [error, setError] = useState<string | null>(null);

  const { isFocusMode, startFocus, setActiveTopic, activeTopic } = useFocusMode();

  const load = () => {
    setLoading(true);
    fetchLearningData()
      .then((res) => setItems(res.items))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!skill.trim() || !resource.trim()) return;
    try {
      await createLearningItem({
        skill: skill.trim(),
        resource: resource.trim(),
        resource_type: resourceType,
        status: 'in_progress',
      });
      setSkill('');
      setResource('');
      setShowAdd(false);
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
              📚 Continuous Skill Mastery Hub
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
            Curate study materials, track deep work sessions, and test recall
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {!isFocusMode && (
            <button
              onClick={() => startFocus(items[0]?.skill || 'Continuous Learning')}
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
                boxShadow: '0 0 15px rgba(236, 72, 153, 0.4)',
              }}
            >
              <Flame size={16} /> Start Focus Mode
            </button>
          )}
          <button
            onClick={() => setShowAdd(!showAdd)}
            style={{
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: '#ffffff',
              padding: '0.65rem 1.15rem',
              borderRadius: '12px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <Plus size={16} /> New Resource
          </button>
          <button
            onClick={onOpenLogModal}
            style={{
              background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
              border: 'none',
              color: '#ffffff',
              padding: '0.65rem 1.25rem',
              borderRadius: '12px',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              boxShadow: '0 0 15px rgba(99, 102, 241, 0.35)',
            }}
          >
            ⏱️ Log Session
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
          <div style={{ flex: 1, minWidth: '180px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.3rem' }}>Skill Category</label>
            <input
              type="text"
              required
              value={skill}
              onChange={(e) => setSkill(e.target.value)}
              placeholder="e.g. Next.js, Rust"
              style={{ width: '100%', padding: '0.65rem', borderRadius: '10px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
            />
          </div>
          <div style={{ flex: 2, minWidth: '220px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.3rem' }}>Resource / Book / Course</label>
            <input
              type="text"
              required
              value={resource}
              onChange={(e) => setResource(e.target.value)}
              placeholder="e.g. Full-Stack Open"
              style={{ width: '100%', padding: '0.65rem', borderRadius: '10px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
            />
          </div>
          <div style={{ width: '140px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.3rem' }}>Type</label>
            <select
              value={resourceType}
              onChange={(e) => setResourceType(e.target.value)}
              style={{ width: '100%', padding: '0.65rem', borderRadius: '10px', background: '#121727', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}
            >
              <option value="course">Course</option>
              <option value="book">Book</option>
              <option value="video">Video</option>
              <option value="project">Project</option>
              <option value="practice">Practice</option>
            </select>
          </div>
          <button
            type="submit"
            style={{ padding: '0.65rem 1.25rem', borderRadius: '10px', background: '#ec4899', color: '#fff', border: 'none', fontWeight: '700', cursor: 'pointer' }}
          >
            Add Resource
          </button>
        </form>
      )}

      {loading ? (
        <div style={{ color: '#94a3b8' }}>Loading learning resources...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {items.map((item) => {
            const isCurrentFocus = isFocusMode && activeTopic === item.skill;
            return (
              <div
                key={item.id}
                className="bento-card"
                style={{
                  border: isCurrentFocus
                    ? '1px solid #ec4899'
                    : '1px solid rgba(236,72,153,0.2)',
                  boxShadow: isCurrentFocus ? '0 0 25px rgba(236,72,153,0.2)' : 'none',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                  <span className="pill-neon-med" style={{ borderColor: '#ec4899', color: '#f472b6', background: 'rgba(236,72,153,0.1)' }}>
                    {item.resource_type.toUpperCase()}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {isCurrentFocus ? (
                      <span style={{ fontSize: '0.72rem', color: '#f472b6', fontWeight: '800' }}>
                        ACTIVE FOCUS
                      </span>
                    ) : isFocusMode ? (
                      <button
                        onClick={() => setActiveTopic(item.skill)}
                        style={{
                          background: 'rgba(236, 72, 153, 0.15)',
                          border: '1px solid rgba(236, 72, 153, 0.4)',
                          color: '#f472b6',
                          borderRadius: '8px',
                          padding: '0.2rem 0.5rem',
                          fontSize: '0.7rem',
                          fontWeight: '700',
                          cursor: 'pointer',
                        }}
                      >
                        Focus On This
                      </button>
                    ) : null}
                    <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: '700' }}>
                      {item.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                </div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: '800', color: '#f8fafc', marginBottom: '0.3rem' }}>
                  {item.skill}
                </h3>
                <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                  {item.resource}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
