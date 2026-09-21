import React from 'react';
import {
  Home,
  Sparkles,
  CheckSquare,
  Inbox,
  Calendar,
  BarChart2,
  ChevronDown,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react';

export type NavTab = 'tasks' | 'suggestions' | 'inbox' | 'learning' | 'goals' | 'insights';

interface SidebarProps {
  currentTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  taskCount: number;
  openTasksCount: number;
  selectedCategory: string | null;
  onSelectCategory: (cat: string | null) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onTabChange,
  isCollapsed,
  onToggleCollapse,
  taskCount,
  openTasksCount,
  selectedCategory,
  onSelectCategory,
}) => {
  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : 'expanded'}`}>
      {/* macOS window control dots + collapse button */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', marginBottom: '1.25rem' }}>
        <div className="window-controls">
          <div className="window-dot dot-red" />
          <div className="window-dot dot-amber" />
          <div className="window-dot dot-green" />
        </div>
        <button
          onClick={onToggleCollapse}
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          style={{ color: '#94a3b8', padding: '4px' }}
        >
          {isCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
        </button>
      </div>

      {/* User profile */}
      <div className="user-profile">
        <div className="avatar-wrapper">
          <img
            src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=120"
            alt="Courtney Henry"
            className="avatar-img"
          />
          <span className="status-dot-online" />
        </div>
        {!isCollapsed && (
          <>
            <div className="user-info">
              <span className="user-name">Courtney Henry</span>
              <span className="user-status">Online</span>
            </div>
            <ChevronDown size={14} color="#94a3b8" />
          </>
        )}
      </div>

      {/* Navigation section */}
      <nav className="nav-section">
        <button
          className={`nav-item ${currentTab === 'tasks' && !selectedCategory ? 'active' : ''}`}
          onClick={() => {
            onSelectCategory(null);
            onTabChange('tasks');
          }}
          title="Home"
        >
          <Home size={18} />
          {!isCollapsed && <span>Home</span>}
        </button>

        <button
          className={`nav-item ${currentTab === 'suggestions' ? 'active' : ''}`}
          onClick={() => onTabChange('suggestions')}
          title="Smart AI Suggestions"
        >
          <Sparkles size={18} />
          {!isCollapsed && <span>Prodify AI</span>}
        </button>

        <button
          className={`nav-item ${currentTab === 'tasks' ? 'active' : ''}`}
          onClick={() => onTabChange('tasks')}
          title="My Tasks"
        >
          <CheckSquare size={18} />
          {!isCollapsed && (
            <>
              <span>My tasks</span>
              {taskCount > 0 && <span className="nav-badge-teal">{taskCount}</span>}
            </>
          )}
        </button>

        <button
          className={`nav-item ${currentTab === 'inbox' ? 'active' : ''}`}
          onClick={() => onTabChange('inbox')}
          title="Daily Update / Inbox"
        >
          <Inbox size={18} />
          {!isCollapsed && (
            <>
              <span>Inbox</span>
              {openTasksCount > 0 && <span className="badge-count">{openTasksCount}</span>}
            </>
          )}
        </button>

        <button
          className={`nav-item ${currentTab === 'learning' ? 'active' : ''}`}
          onClick={() => onTabChange('learning')}
          title="Learning & Skills"
        >
          <Calendar size={18} />
          {!isCollapsed && <span>Learning</span>}
        </button>

        <button
          className={`nav-item ${currentTab === 'insights' ? 'active' : ''}`}
          onClick={() => onTabChange('insights')}
          title="Reports & Analytics"
        >
          <BarChart2 size={18} />
          {!isCollapsed && <span>Reports & Analytics</span>}
        </button>
      </nav>

      {/* My Projects / Categories section */}
      {!isCollapsed ? (
        <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
          <div className="projects-header">
            <span className="projects-title">My Projects</span>
            <button
              className="add-project-btn"
              onClick={() => {
                const name = prompt('New project/category name:');
                if (name) onSelectCategory(name);
              }}
            >
              + Add
            </button>
          </div>

          <div
            className={`project-item ${selectedCategory === 'Product launch' ? 'active' : ''}`}
            onClick={() => {
              onSelectCategory(selectedCategory === 'Product launch' ? null : 'Product launch');
              onTabChange('tasks');
            }}
          >
            <span className="project-pill pill-purple" />
            <span>Product launch</span>
          </div>

          <div
            className={`project-item ${selectedCategory === 'Team brainstorm' ? 'active' : ''}`}
            onClick={() => {
              onSelectCategory(selectedCategory === 'Team brainstorm' ? null : 'Team brainstorm');
              onTabChange('tasks');
            }}
          >
            <span className="project-pill pill-blue" />
            <span>Team brainstorm</span>
          </div>

          <div
            className={`project-item ${selectedCategory === 'Branding launch' ? 'active' : ''}`}
            onClick={() => {
              onSelectCategory(selectedCategory === 'Branding launch' ? null : 'Branding launch');
              onTabChange('tasks');
            }}
          >
            <span className="project-pill pill-cyan" />
            <span>Branding launch</span>
          </div>
        </div>
      ) : (
        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem', alignItems: 'center' }}>
          <span className="project-pill pill-purple" title="Product launch" />
          <span className="project-pill pill-blue" title="Team brainstorm" />
          <span className="project-pill pill-cyan" title="Branding launch" />
        </div>
      )}
    </aside>
  );
};
