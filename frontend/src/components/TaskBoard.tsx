import React, { useState } from 'react';
import { Plus, Check, Star, Trash2, GitBranch, Lightbulb } from 'lucide-react';
import { Suggestion, Task } from '../types';

interface TaskBoardProps {
  tasks: Task[];
  top3: Task[];
  completed: Task[];
  overdue?: Task[];
  suggestions?: Suggestion[];
  onComplete: (id: number) => void;
  onUncomplete: (id: number) => void;
  onToggleTop3: (id: number, current: boolean) => void;
  onDrop: (id: number) => void;
  onAddTask: () => void;
  onAddSubtask: (parentId: number) => void;
  onAcceptSuggestion?: (suggestion: Suggestion) => void;
}

const PRIORITY_RANK: Record<string, number> = { high: 0, medium: 1, low: 2 };

export const TaskBoard: React.FC<TaskBoardProps> = ({
  tasks,
  completed,
  overdue = [],
  suggestions = [],
  onComplete,
  onUncomplete,
  onToggleTop3,
  onDrop,
  onAddTask,
  onAddSubtask,
  onAcceptSuggestion,
}) => {
  const [activeFilter, setActiveFilter] = useState<'all' | 'completed'>('all');

  const getPriorityPill = (priority: string) => {
    switch (priority) {
      case 'high':
        return <span className="pill-neon-high">⚡ High</span>;
      case 'low':
        return <span className="pill-neon-low">↓ Low</span>;
      default:
        return <span className="pill-neon-med">⚡ Med</span>;
    }
  };

  const topLevelTasks = tasks
    .filter((t) => !t.parent_task_id)
    .sort((a, b) => {
      if (Boolean(a.is_top3) !== Boolean(b.is_top3)) return a.is_top3 ? -1 : 1;
      return (PRIORITY_RANK[a.priority] ?? 1) - (PRIORITY_RANK[b.priority] ?? 1);
    });

  const displayedTasks = activeFilter === 'completed' ? completed : topLevelTasks;

  const handleDrop = (task: Task) => {
    const label = task.status === 'done' ? 'remove this completed task' : `drop "${task.title}"`;
    if (window.confirm(`Drop this item? Unchecked close-out items are dropped too — ${label}.`)) {
      onDrop(task.id);
    }
  };

  return (
    <div
      className="bento-card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        gridRow: 'span 2',
        minHeight: '480px',
      }}
    >
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '800', color: '#f8fafc' }}>
              Today's Tasks
            </h3>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
              {topLevelTasks.length} pending &bull; {completed.length} completed
              {overdue.length > 0 ? ` • ${overdue.length} overdue` : ''}
            </span>
          </div>

          <div style={{
            background: 'rgba(255, 255, 255, 0.04)',
            padding: '0.2rem',
            borderRadius: '10px',
            display: 'flex',
            gap: '0.2rem',
          }}>
            <button
              onClick={() => setActiveFilter('all')}
              style={{
                background: activeFilter === 'all' ? 'rgba(6, 182, 212, 0.2)' : 'transparent',
                border: 'none',
                color: activeFilter === 'all' ? '#06b6d4' : '#64748b',
                padding: '0.3rem 0.6rem',
                borderRadius: '8px',
                fontSize: '0.75rem',
                fontWeight: '700',
                cursor: 'pointer',
              }}
            >
              Active
            </button>
            <button
              onClick={() => setActiveFilter('completed')}
              style={{
                background: activeFilter === 'completed' ? 'rgba(6, 182, 212, 0.2)' : 'transparent',
                border: 'none',
                color: activeFilter === 'completed' ? '#06b6d4' : '#64748b',
                padding: '0.3rem 0.6rem',
                borderRadius: '8px',
                fontSize: '0.75rem',
                fontWeight: '700',
                cursor: 'pointer',
              }}
            >
              Done ({completed.length})
            </button>
          </div>
        </div>

        {activeFilter === 'all' && suggestions.length > 0 && (
          <div style={{
            marginBottom: '0.85rem',
            padding: '0.75rem',
            borderRadius: '14px',
            border: '1px solid rgba(251, 191, 36, 0.25)',
            background: 'rgba(251, 191, 36, 0.06)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem', fontWeight: 700, color: '#fbbf24', marginBottom: '0.5rem' }}>
              <Lightbulb size={14} /> Suggested from behind goals
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
              {suggestions.map((s) => (
                <div key={`${s.goal_id}-${s.title}`} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
                  <div>
                    <div style={{ fontSize: '0.82rem', color: '#f8fafc', fontWeight: 600 }}>{s.title}</div>
                    <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{s.reason}</div>
                  </div>
                  {onAcceptSuggestion && (
                    <button
                      onClick={() => onAcceptSuggestion(s)}
                      style={{
                        flexShrink: 0,
                        background: 'rgba(251, 191, 36, 0.15)',
                        border: '1px solid rgba(251, 191, 36, 0.4)',
                        color: '#fbbf24',
                        borderRadius: '8px',
                        padding: '0.3rem 0.55rem',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      Add
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeFilter === 'all' && overdue.length > 0 && (
          <div style={{
            marginBottom: '0.85rem',
            padding: '0.65rem 0.75rem',
            borderRadius: '12px',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            background: 'rgba(239, 68, 68, 0.08)',
            fontSize: '0.8rem',
            color: '#fca5a5',
          }}>
            Overdue: {overdue.map((t) => t.title).join(', ')}
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', maxHeight: '440px', overflowY: 'auto', paddingRight: '0.25rem' }}>
          {displayedTasks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2.5rem 1rem', color: '#64748b', fontSize: '0.9rem' }}>
              {activeFilter === 'completed' ? 'No completed tasks yet today.' : 'No tasks on your board. Click "+ Add task" to get started!'}
            </div>
          ) : (
            displayedTasks.map((t) => {
              const isDone = activeFilter === 'completed';
              const isTop3 = Boolean(t.is_top3);

              return (
                <div
                  key={t.id}
                  style={{
                    background: 'rgba(255, 255, 255, 0.025)',
                    border: isTop3 ? '1px solid rgba(245, 158, 11, 0.35)' : '1px solid rgba(255, 255, 255, 0.06)',
                    borderRadius: '16px',
                    padding: '0.85rem 1rem',
                    transition: 'all 0.2s ease',
                    position: 'relative',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      {getPriorityPill(t.priority)}
                      <span style={{
                        fontSize: '0.75rem',
                        color: '#94a3b8',
                        background: 'rgba(255, 255, 255, 0.05)',
                        padding: '0.15rem 0.5rem',
                        borderRadius: '6px',
                        textTransform: 'capitalize',
                      }}>
                        {t.category}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      {!isDone && (
                        <button
                          onClick={() => onToggleTop3(t.id, isTop3)}
                          title={isTop3 ? 'Remove Top-3' : 'Mark Top-3 Priority'}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            cursor: 'pointer',
                            color: isTop3 ? '#fbbf24' : '#475569',
                            padding: '0.2rem',
                          }}
                        >
                          <Star size={16} fill={isTop3 ? '#fbbf24' : 'none'} />
                        </button>
                      )}
                      {!isDone && (
                        <button
                          onClick={() => onAddSubtask(t.id)}
                          title="Add subtask"
                          style={{
                            background: 'transparent',
                            border: 'none',
                            cursor: 'pointer',
                            color: '#64748b',
                            padding: '0.2rem',
                          }}
                        >
                          <GitBranch size={15} />
                        </button>
                      )}
                      {!isDone && (
                        <button
                          onClick={() => handleDrop(t)}
                          title="Drop task"
                          style={{
                            background: 'transparent',
                            border: 'none',
                            cursor: 'pointer',
                            color: '#475569',
                            padding: '0.2rem',
                          }}
                        >
                          <Trash2 size={15} />
                        </button>
                      )}
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                    <button
                      onClick={() => (isDone ? onUncomplete(t.id) : onComplete(t.id))}
                      style={{
                        width: '20px',
                        height: '20px',
                        borderRadius: '6px',
                        border: isDone ? 'none' : '2px solid rgba(255, 255, 255, 0.25)',
                        background: isDone ? '#06b6d4' : 'transparent',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        marginTop: '0.15rem',
                        flexShrink: 0,
                        boxShadow: isDone ? '0 0 10px rgba(6, 182, 212, 0.6)' : 'none',
                        transition: 'all 0.2s ease',
                      }}
                    >
                      {isDone && <Check size={14} color="#000000" strokeWidth={3} />}
                    </button>

                    <div style={{ flex: 1 }}>
                      <div style={{
                        fontSize: '0.92rem',
                        fontWeight: '600',
                        color: isDone ? '#64748b' : '#f8fafc',
                        textDecoration: isDone ? 'line-through' : 'none',
                      }}>
                        {t.title}
                      </div>

                      {t.rollover_count >= 3 && !isDone && (
                        <div style={{ marginTop: '0.3rem' }}>
                          <span className="pill-rollover-warning">
                            ⚠️ Rolled over {t.rollover_count}x
                          </span>
                        </div>
                      )}

                      {t.subtasks && t.subtasks.length > 0 && (
                        <div style={{ marginTop: '0.5rem', paddingLeft: '0.5rem', borderLeft: '2px solid rgba(255,255,255,0.06)' }}>
                          {t.subtasks.map((sub) => {
                            const subDone = sub.status === 'done';
                            return (
                              <div key={sub.id} style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', margin: '0.3rem 0' }}>
                                <button
                                  onClick={() => (subDone ? onUncomplete(sub.id) : onComplete(sub.id))}
                                  title={subDone ? 'Reopen subtask' : 'Complete subtask'}
                                  style={{
                                    width: '16px',
                                    height: '16px',
                                    borderRadius: '4px',
                                    border: subDone ? 'none' : '2px solid rgba(255, 255, 255, 0.25)',
                                    background: subDone ? '#06b6d4' : 'transparent',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    cursor: 'pointer',
                                    flexShrink: 0,
                                  }}
                                >
                                  {subDone && <Check size={10} color="#000000" strokeWidth={3} />}
                                </button>
                                <span style={{
                                  fontSize: '0.8rem',
                                  color: subDone ? '#64748b' : '#94a3b8',
                                  textDecoration: subDone ? 'line-through' : 'none',
                                }}>
                                  {sub.title}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      <button
        onClick={onAddTask}
        style={{
          width: '100%',
          marginTop: '1rem',
          padding: '0.75rem',
          borderRadius: '16px',
          border: '1px dashed rgba(255, 255, 255, 0.15)',
          background: 'rgba(255, 255, 255, 0.03)',
          color: '#cbd5e1',
          fontSize: '0.9rem',
          fontWeight: '600',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.4rem',
          transition: 'all 0.2s ease',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = '#06b6d4';
          e.currentTarget.style.color = '#06b6d4';
          e.currentTarget.style.background = 'rgba(6, 182, 212, 0.06)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.15)';
          e.currentTarget.style.color = '#cbd5e1';
          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
        }}
      >
        <Plus size={16} /> Add task
      </button>
    </div>
  );
};
