import React, { useState, useEffect } from 'react';
import { BookOpen, Plus, Atom, RotateCw, Check, X } from 'lucide-react';
import { fetchLearningData, createLearningItem } from '../api';
import { LearningItem } from '../types';

export const LearningView: React.FC<{ onOpenLogModal: () => void }> = ({ onOpenLogModal }) => {
  const [items, setItems] = useState<LearningItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [skill, setSkill] = useState('');
  const [resource, setResource] = useState('');
  const [resourceType, setResourceType] = useState('course');
  const [error, setError] = useState<string | null>(null);

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
    <div style={{ padding: '1rem', width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.8rem', fontWeight: '800', color: '#f8fafc' }}>
            📚 Continuous Skill Mastery Hub
          </h2>
          <div style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
            Curate study materials, track deep work sessions, and test recall
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
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
              background: 'linear-gradient(135deg, #ec4899 0%, #a855f7 100%)',
              border: 'none',
              color: '#ffffff',
              padding: '0.65rem 1.25rem',
              borderRadius: '12px',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              boxShadow: '0 0 15px rgba(236, 72, 153, 0.4)',
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
          {items.map((item) => (
            <div key={item.id} className="bento-card" style={{ border: '1px solid rgba(236,72,153,0.2)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                <span className="pill-neon-med" style={{ borderColor: '#ec4899', color: '#f472b6', background: 'rgba(236,72,153,0.1)' }}>
                  {item.resource_type.toUpperCase()}
                </span>
                <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: '700' }}>
                  {item.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: '800', color: '#f8fafc', marginBottom: '0.3rem' }}>
                {item.skill}
              </h3>
              <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                {item.resource}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
