import React from 'react';
import { Sparkles, Plus, Clock, Target } from 'lucide-react';
import { Suggestion } from '../types';

interface SuggestionsViewProps {
  suggestions: Suggestion[];
  onAccept: (sugg: Suggestion) => void;
}

export const SuggestionsView: React.FC<SuggestionsViewProps> = ({ suggestions, onAccept }) => {
  return (
    <div className="tasks-card-container">
      <div className="card-header-bar">
        <div className="card-title-group">
          <div className="card-icon-wrapper" style={{ color: '#8b5cf6' }}>
            <Sparkles size={22} />
          </div>
          <div>
            <h3 className="card-title">Prodify AI Suggestions</h3>
            <p style={{ fontSize: '0.86rem', color: '#64748b', marginTop: '2px' }}>
              Goal-aligned study tasks generated automatically from your weekly targets.
            </p>
          </div>
        </div>
      </div>

      {suggestions.length === 0 ? (
        <div style={{ padding: '2.5rem 1rem', textAlign: 'center', color: '#94a3b8' }}>
          <Sparkles size={36} style={{ marginBottom: '0.5rem', color: '#cbd5e1' }} />
          <p style={{ fontWeight: 600 }}>All goal targets are currently on track for today!</p>
          <p style={{ fontSize: '0.85rem', marginTop: '4px' }}>No additional study sessions required.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
          {suggestions.map((sugg, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '1rem 1.25rem',
                borderRadius: '14px',
                border: '1px solid #f1f5f9',
                background: 'linear-gradient(135deg, rgba(248, 250, 252, 0.8) 0%, rgba(245, 243, 255, 0.6) 100%)',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                  <span className="section-badge-pill badge-in-progress" style={{ fontSize: '0.72rem' }}>
                    {sugg.category}
                  </span>
                  <span style={{ fontSize: '0.82rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Target size={13} /> {sugg.goal_title}
                  </span>
                </div>
                <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a' }}>{sugg.title}</h4>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.4rem', fontSize: '0.84rem', color: '#64748b' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={14} /> {sugg.duration_min} mins recommended
                  </span>
                  <span>•</span>
                  <span>{sugg.reason}</span>
                </div>
              </div>

              <button
                className="btn-primary"
                onClick={() => onAccept(sugg)}
                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.55rem 1.1rem' }}
              >
                <Plus size={15} />
                <span>Accept into Today</span>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
