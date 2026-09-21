import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  Plus,
  Sparkles,
  Check,
  Star,
  CheckSquare,
} from 'lucide-react';
import { Task, Priority } from '../types';

interface TaskBoardProps {
  inProgress: Task[];
  todo: Task[];
  completed: Task[];
  overdue: Task[];
  onToggleComplete: (id: number) => void;
  onToggleTop3: (id: number) => void;
  onAddTask: (task: { title: string; category: string; priority: Priority; estimate_min?: number; is_top3?: boolean }) => void;
  onAddSubtask: (taskId: number, title: string) => void;
  onToggleSubtask: (subtaskId: number) => void;
  selectedCategory: string | null;
}

export const TaskBoard: React.FC<TaskBoardProps> = ({
  inProgress,
  todo,
  completed,
  overdue,
  onToggleComplete,
  onToggleTop3,
  onAddTask,
  onAddSubtask,
  onToggleSubtask,
  selectedCategory,
}) => {
  const [inProgressOpen, setInProgressOpen] = useState(true);
  const [todoOpen, setTodoOpen] = useState(true);
  const [completedOpen, setCompletedOpen] = useState(false);
  const [overdueOpen, setOverdueOpen] = useState(true);

  const [expandedTaskIds, setExpandedTaskIds] = useState<number[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newCategory, setNewCategory] = useState('Work');
  const [newPriority, setNewPriority] = useState<Priority>('Medium');
  const [newEstimate, setNewEstimate] = useState<number>(30);
  const [newIsTop3, setNewIsTop3] = useState(false);

  // Subtask input per task
  const [subtaskInputs, setSubtaskInputs] = useState<{ [key: number]: string }>({});

  const toggleExpand = (id: number) => {
    setExpandedTaskIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleCreateTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    onAddTask({
      title: newTitle.trim(),
      category: newCategory,
      priority: newPriority,
      estimate_min: newEstimate,
      is_top3: newIsTop3,
    });
    setNewTitle('');
    setIsModalOpen(false);
  };

  const formatDueDate = (plannedDate: string, rolloverCount: number) => {
    const today = new Date().toISOString().slice(0, 10);
    if (plannedDate === today) {
      return <span className="due-today">Today</span>;
    }
    if (plannedDate < today) {
      return <span className="due-overdue">Overdue ({rolloverCount}x)</span>;
    }
    const daysLeft = Math.ceil((new Date(plannedDate).getTime() - new Date(today).getTime()) / (1000 * 60 * 60 * 24));
    return <span className="due-days-left">{daysLeft} days left</span>;
  };

  const filterCat = (tasks: Task[]) => {
    if (!selectedCategory) return tasks;
    return tasks.filter((t) => t.category.toLowerCase() === selectedCategory.toLowerCase());
  };

  // Format header date like reference: "Mon, July 7"
  const todayFormatted = new Intl.DateTimeFormat('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  }).format(new Date());

  const renderTaskRows = (tasks: Task[]) => {
    return tasks.map((task) => {
      const isExpanded = expandedTaskIds.includes(task.id);
      const isDone = task.status === 'done';

      return (
        <React.Fragment key={task.id}>
          <tr className="task-row">
            <td className="task-title-cell">
              <button
                onClick={() => toggleExpand(task.id)}
                style={{ color: '#94a3b8', padding: '2px' }}
                title="Expand subtasks"
              >
                {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </button>

              <div
                className={`task-checkbox-custom ${isDone ? 'checked' : ''}`}
                onClick={() => onToggleComplete(task.id)}
                title={isDone ? 'Mark todo' : 'Complete task'}
              >
                {isDone && <Check size={12} strokeWidth={3} />}
              </div>

              {/* Category indicator pill */}
              <span
                className={`task-tag-dot ${
                  task.category === 'Work' || task.category === 'Product launch'
                    ? 'pill-purple'
                    : task.category === 'Personal' || task.category === 'Team brainstorm'
                    ? 'pill-blue'
                    : 'pill-cyan'
                }`}
              />

              <span className={`task-title-text ${isDone ? 'done' : ''}`}>
                {task.title}
              </span>

              <button
                onClick={() => onToggleTop3(task.id)}
                style={{
                  marginLeft: 'auto',
                  color: task.is_top3 ? '#f59e0b' : '#cbd5e1',
                  display: 'flex',
                  alignItems: 'center',
                }}
                title={task.is_top3 ? 'In Top 3' : 'Make Top 3'}
              >
                <Star size={14} fill={task.is_top3 ? '#f59e0b' : 'none'} />
              </button>
            </td>

            <td style={{ textAlign: 'center' }}>
              <span
                className={`priority-pill ${
                  task.priority === 'High'
                    ? 'priority-high'
                    : task.priority === 'Low'
                    ? 'priority-low'
                    : 'priority-normal'
                }`}
              >
                {task.priority === 'Medium' ? 'Normal' : task.priority}
              </span>
            </td>

            <td className="due-date-cell">
              {formatDueDate(task.planned_date, task.rollover_count)}
            </td>
          </tr>

          {/* Subtasks dropdown container */}
          {isExpanded && (
            <tr style={{ background: '#f8fafc' }}>
              <td colSpan={3} style={{ padding: '0.5rem 1.5rem 0.75rem 2.5rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {task.subtasks.map((sub) => (
                    <div
                      key={sub.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.65rem',
                        fontSize: '0.86rem',
                        color: sub.status === 'done' ? '#94a3b8' : '#334155',
                      }}
                    >
                      <div
                        className={`task-checkbox-custom ${sub.status === 'done' ? 'checked' : ''}`}
                        onClick={() => onToggleSubtask(sub.id)}
                        style={{ width: '15px', height: '15px' }}
                      >
                        {sub.status === 'done' && <Check size={10} strokeWidth={3} />}
                      </div>
                      <span style={{ textDecoration: sub.status === 'done' ? 'line-through' : 'none' }}>
                        {sub.title}
                      </span>
                    </div>
                  ))}

                  {/* Add subtask inline */}
                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.35rem' }}>
                    <input
                      type="text"
                      placeholder="Add a step..."
                      value={subtaskInputs[task.id] || ''}
                      onChange={(e) =>
                        setSubtaskInputs({ ...subtaskInputs, [task.id]: e.target.value })
                      }
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && subtaskInputs[task.id]?.trim()) {
                          onAddSubtask(task.id, subtaskInputs[task.id].trim());
                          setSubtaskInputs({ ...subtaskInputs, [task.id]: '' });
                        }
                      }}
                      style={{
                        padding: '4px 10px',
                        fontSize: '0.82rem',
                        borderRadius: '6px',
                        border: '1px solid #cbd5e1',
                        flex: 1,
                        maxWidth: '280px',
                      }}
                    />
                    <button
                      className="btn-primary"
                      style={{ padding: '3px 10px', fontSize: '0.78rem' }}
                      onClick={() => {
                        if (subtaskInputs[task.id]?.trim()) {
                          onAddSubtask(task.id, subtaskInputs[task.id].trim());
                          setSubtaskInputs({ ...subtaskInputs, [task.id]: '' });
                        }
                      }}
                    >
                      Add
                    </button>
                  </div>
                </div>
              </td>
            </tr>
          )}
        </React.Fragment>
      );
    });
  };

  const filteredInProgress = filterCat(inProgress);
  const filteredTodo = filterCat(todo);
  const filteredCompleted = filterCat(completed);
  const filteredOverdue = filterCat(overdue);

  return (
    <div>
      {/* Hero Greeting Section per reference image */}
      <section className="hero-header">
        <div>
          <div className="date-text">{todayFormatted}</div>
          <h1 className="greeting-title">Hello, Courtney</h1>
          <h2 className="greeting-subtitle">How can I help you today?</h2>
        </div>

        {/* Ambient floating glowing orb widget from reference image */}
        <div className="ambient-orb-widget" title="Prodify ambient focus mode">
          <Sparkles size={28} className="orb-inner-sparkle" />
        </div>
      </section>

      {/* Main Tasks Card */}
      <div className="tasks-card-container">
        <div className="card-header-bar">
          <div className="card-title-group">
            <div className="card-icon-wrapper">
              <CheckSquare size={20} />
            </div>
            <h3 className="card-title">
              {selectedCategory ? `${selectedCategory} Tasks` : 'My Tasks'}
            </h3>
          </div>

          <button
            className="btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', padding: '0.5rem 1rem' }}
            onClick={() => setIsModalOpen(true)}
          >
            <Plus size={16} />
            <span>New Task</span>
          </button>
        </div>

        {/* IN PROGRESS Section */}
        <div className="section-accordion">
          <div className="accordion-header" onClick={() => setInProgressOpen(!inProgressOpen)}>
            <ChevronDown size={16} className={`chevron-icon ${inProgressOpen ? 'open' : 'closed'}`} />
            <span className="section-badge-pill badge-in-progress">
              IN PROGRESS • {filteredInProgress.length} tasks
            </span>
          </div>

          {inProgressOpen && (
            <table className="task-table">
              <thead>
                <tr className="table-head-row">
                  <th className="th-name">Name</th>
                  <th className="th-priority">Priority</th>
                  <th className="th-due">Due date</th>
                </tr>
              </thead>
              <tbody>{renderTaskRows(filteredInProgress)}</tbody>
            </table>
          )}
        </div>

        {/* Inline Add Task Trigger */}
        <button className="add-task-btn" onClick={() => setIsModalOpen(true)}>
          <Plus size={16} />
          <span>Add task</span>
        </button>

        {/* TO DO Section */}
        <div className="section-accordion" style={{ marginTop: '1.5rem' }}>
          <div className="accordion-header" onClick={() => setTodoOpen(!todoOpen)}>
            <ChevronDown size={16} className={`chevron-icon ${todoOpen ? 'open' : 'closed'}`} />
            <span className="section-badge-pill badge-todo">
              TO DO • {filteredTodo.length} tasks
            </span>
          </div>

          {todoOpen && (
            <table className="task-table">
              <thead>
                <tr className="table-head-row">
                  <th className="th-name">Name</th>
                  <th className="th-priority">Priority</th>
                  <th className="th-due">Due date</th>
                </tr>
              </thead>
              <tbody>{renderTaskRows(filteredTodo)}</tbody>
            </table>
          )}
        </div>

        {/* COMPLETED Section */}
        {filteredCompleted.length > 0 && (
          <div className="section-accordion" style={{ marginTop: '1.5rem' }}>
            <div className="accordion-header" onClick={() => setCompletedOpen(!completedOpen)}>
              <ChevronDown size={16} className={`chevron-icon ${completedOpen ? 'open' : 'closed'}`} />
              <span className="section-badge-pill badge-completed">
                COMPLETED • {filteredCompleted.length} tasks
              </span>
            </div>

            {completedOpen && (
              <table className="task-table">
                <thead>
                  <tr className="table-head-row">
                    <th className="th-name">Name</th>
                    <th className="th-priority">Priority</th>
                    <th className="th-due">Completed</th>
                  </tr>
                </thead>
                <tbody>{renderTaskRows(filteredCompleted)}</tbody>
              </table>
            )}
          </div>
        )}

        {/* OVERDUE Section */}
        {filteredOverdue.length > 0 && (
          <div className="section-accordion" style={{ marginTop: '1.5rem' }}>
            <div className="accordion-header" onClick={() => setOverdueOpen(!overdueOpen)}>
              <ChevronDown size={16} className={`chevron-icon ${overdueOpen ? 'open' : 'closed'}`} />
              <span className="section-badge-pill badge-overdue">
                OVERDUE • {filteredOverdue.length} tasks
              </span>
            </div>

            {overdueOpen && (
              <table className="task-table">
                <thead>
                  <tr className="table-head-row">
                    <th className="th-name">Name</th>
                    <th className="th-priority">Priority</th>
                    <th className="th-due">Due date</th>
                  </tr>
                </thead>
                <tbody>{renderTaskRows(filteredOverdue)}</tbody>
              </table>
            )}
          </div>
        )}
      </div>

      {/* New Task Modal */}
      {isModalOpen && (
        <div className="modal-overlay" onClick={() => setIsModalOpen(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Create New Task</h3>
              <button onClick={() => setIsModalOpen(false)} style={{ color: '#94a3b8' }}>✕</button>
            </div>
            <form onSubmit={handleCreateTask}>
              <div className="form-group">
                <label className="form-label">Task Title</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Send a summary email to stakeholders"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  autoFocus
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Priority</label>
                  <select
                    className="form-input"
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value as Priority)}
                  >
                    <option value="High">High</option>
                    <option value="Medium">Normal</option>
                    <option value="Low">Low</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Category</label>
                  <select
                    className="form-input"
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                  >
                    <option value="Work">Product launch (Work)</option>
                    <option value="Personal">Team brainstorm (Personal)</option>
                    <option value="Learning">Branding launch (Learning)</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Estimate (minutes)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={newEstimate}
                    onChange={(e) => setNewEstimate(Number(e.target.value))}
                    min={5}
                    step={5}
                  />
                </div>

                <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1.5rem' }}>
                  <input
                    type="checkbox"
                    id="top3Checkbox"
                    checked={newIsTop3}
                    onChange={(e) => setNewIsTop3(e.target.checked)}
                    style={{ width: '18px', height: '18px' }}
                  />
                  <label htmlFor="top3Checkbox" style={{ fontSize: '0.9rem', fontWeight: 600, cursor: 'pointer' }}>
                    Make Top-3 Priority
                  </label>
                </div>
              </div>

              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Add Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
