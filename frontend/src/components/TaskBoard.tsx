import React, { useState } from 'react';
import { Plus, Check, Star, Trash2, GitBranch, MoreVertical } from 'lucide-react';
import { Task } from '../types';

interface TaskBoardProps {
  tasks: Task[];
  top3: Task[];
  completed: Task[];
  onComplete: (id: number) => void;
  onUncomplete: (id: number) => void;
  onToggleTop3: (id: number, current: boolean) => void;
  onDrop: (id: number) => void;
  onAddTask: () => void;
  onAddSubtask: (parentId: number) => void;
}

export const TaskBoard: React.FC<TaskBoardProps> = ({
  tasks,
  top3,
  completed,
  onComplete,
  onUncomplete,
  onToggleTop3,
  onDrop,
  onAddTask,
  onAddSubtask,
}) => {
  const [activeFilter, setActiveFilter] = useState<'all' | 'todo' | 'completed'>('all');

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

  const displayedTasks = activeFilter === 'completed' ? completed : tasks;

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
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '800', color: '#f8fafc' }}>
              Today's Tasks
            </h3>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
              {tasks.length} pending &bull; {completed.length} completed
            </span>
          </div>

          {/* Quick tab toggle */}
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

        {/* Task List */}
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

                    {/* Actions */}
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
                      <button
                        onClick={() => onDrop(t.id)}
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
                    </div>
                  </div>

                  {/* Task Checkbox & Title */}
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

                      {/* Rollover alert */}
                      {t.rollover_count >= 3 && !isDone && (
                        <div style={{ marginTop: '0.3rem' }}>
                          <span className="pill-rollover-warning">
                            ⚠️ Rolled over {t.rollover_count}x
                          </span>
                        </div>
                      )}

                      {/* Subtasks */}
                      {t.subtasks && t.subtasks.length > 0 && (
                        <div style={{ marginTop: '0.5rem', paddingLeft: '0.5rem', borderLeft: '2px solid rgba(255,255,255,0.06)' }}>
                          {t.subtasks.map((sub) => (
                            <div key={sub.id} style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '0.2rem 0' }}>
                              &bull; {sub.title} {sub.status === 'done' ? '✅' : '⏳'}
                            </div>
                          ))}
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

      {/* Add Task Button matching image */}
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
