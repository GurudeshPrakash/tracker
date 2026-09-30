import React from 'react';
import {
  Calendar,
  FileText,
  BookOpen,
  Target,
  BarChart3,
  Settings,
  Zap,
  CalendarRange,
  Lock,
  Flame,
  Play,
  Pause,
  Sparkles,
} from 'lucide-react';
import { useFocusMode } from '../FocusContext';

interface SidebarProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
  onOpenDailyUpdate: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab, onOpenDailyUpdate }) => {
  const {
    isFocusMode,
    isRunning,
    seconds,
    startFocus,
    pauseFocus,
    resumeFocus,
    stopFocus,
    isTabAllowed,
    triggerLockedNotice,
    formatTime,
  } = useFocusMode();

  const navItems = [
    { id: 'today', label: 'Today', icon: Calendar },
    { id: 'daily-update', label: 'Daily Update', icon: FileText, action: onOpenDailyUpdate },
    { id: 'learning', label: 'Learning', icon: BookOpen },
    { id: 'goals', label: 'Goals', icon: Target },
    { id: 'weekly', label: 'Weekly Review', icon: CalendarRange },
    { id: 'insights', label: 'Insights', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const handleTabClick = (item: (typeof navItems)[0]) => {
    if (isFocusMode && !isTabAllowed(item.id)) {
      triggerLockedNotice(item.label);
      return;
    }

    if (item.action) {
      item.action();
    } else {
      onSelectTab(item.id);
    }
  };

  return (
    <aside
      style={{
        width: '250px',
        minWidth: '250px',
        background: 'rgba(15, 19, 32, 0.85)',
        backdropFilter: 'blur(24px)',
        WebkitBackdropFilter: 'blur(24px)',
        borderRight: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '24px',
        margin: '1.25rem 0 1.25rem 1.25rem',
        padding: '1.5rem 1.15rem',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.45)',
        height: 'calc(100vh - 2.5rem)',
        position: 'sticky',
        top: '1.25rem',
        zIndex: 50,
      }}
    >
      <div>
        {/* Brand Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.75rem', paddingLeft: '0.5rem' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 50%, #6366f1 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 18px rgba(6, 182, 212, 0.4)',
            }}
          >
            <Zap size={22} color="#ffffff" />
          </div>
          <span
            style={{
              fontSize: '1.4rem',
              fontWeight: '800',
              letterSpacing: '0.04em',
              background: 'linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            FLUX
          </span>
        </div>

        {/* Focus Mode Control Card */}
        <div
          style={{
            marginBottom: '1.5rem',
            padding: '0.9rem',
            borderRadius: '16px',
            background: isFocusMode
              ? 'linear-gradient(135deg, rgba(236, 72, 153, 0.16) 0%, rgba(168, 85, 247, 0.12) 100%)'
              : 'rgba(255, 255, 255, 0.03)',
            border: isFocusMode ? '1px solid rgba(236, 72, 153, 0.4)' : '1px solid rgba(255, 255, 255, 0.07)',
            boxShadow: isFocusMode ? '0 0 20px rgba(236, 72, 153, 0.18)' : 'none',
            transition: 'all 0.3s ease',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Flame size={16} color={isFocusMode ? '#ec4899' : '#94a3b8'} />
              <span
                style={{
                  fontSize: '0.78rem',
                  fontWeight: '800',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  color: isFocusMode ? '#f472b6' : '#94a3b8',
                }}
              >
                Focus Mode
              </span>
            </div>
            {isFocusMode && (
              <span
                style={{
                  fontSize: '0.68rem',
                  fontWeight: '800',
                  padding: '0.15rem 0.45rem',
                  borderRadius: '9999px',
                  background: isRunning ? 'rgba(236, 72, 153, 0.3)' : 'rgba(245, 158, 11, 0.25)',
                  color: isRunning ? '#f472b6' : '#fbbf24',
                  border: isRunning ? '1px solid #ec4899' : '1px solid #f59e0b',
                }}
              >
                {isRunning ? 'ACTIVE' : 'PAUSED'}
              </span>
            )}
          </div>

          {isFocusMode ? (
            <div>
              <div
                style={{
                  fontSize: '1.4rem',
                  fontWeight: '800',
                  fontFamily: 'var(--font-mono)',
                  color: '#ffffff',
                  textAlign: 'center',
                  margin: '0.4rem 0',
                  letterSpacing: '0.05em',
                  textShadow: '0 0 12px rgba(236, 72, 153, 0.5)',
                }}
              >
                {formatTime(seconds)}
              </div>
              <div
                style={{
                  fontSize: '0.7rem',
                  color: '#cbd5e1',
                  textAlign: 'center',
                  marginBottom: '0.65rem',
                }}
              >
                Goal & Learning tabs only
              </div>
              <div style={{ display: 'flex', gap: '0.4rem' }}>
                <button
                  onClick={() => (isRunning ? pauseFocus() : resumeFocus())}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.3rem',
                    background: isRunning ? 'rgba(245, 158, 11, 0.2)' : 'linear-gradient(135deg, #ec4899 0%, #d946ef 100%)',
                    border: isRunning ? '1px solid #f59e0b' : 'none',
                    color: '#ffffff',
                    borderRadius: '10px',
                    padding: '0.4rem 0',
                    fontSize: '0.75rem',
                    fontWeight: '700',
                    cursor: 'pointer',
                  }}
                >
                  {isRunning ? <Pause size={12} /> : <Play size={12} fill="#ffffff" />}
                  <span>{isRunning ? 'Pause' : 'Resume'}</span>
                </button>
                <button
                  onClick={() => {
                    if (window.confirm('Turn off Focus Mode and unlock all tabs?')) {
                      stopFocus();
                    }
                  }}
                  style={{
                    padding: '0.4rem 0.6rem',
                    background: 'rgba(255, 255, 255, 0.06)',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    color: '#94a3b8',
                    borderRadius: '10px',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                  }}
                  title="Turn off Focus Mode"
                >
                  Turn Off
                </button>
              </div>
            </div>
          ) : (
            <div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginBottom: '0.6rem', lineHeight: '1.3' }}>
                Lock distractions and focus solely on Goals & Learning.
              </div>
              <button
                onClick={() => startFocus()}
                style={{
                  width: '100%',
                  background: 'linear-gradient(135deg, #ec4899 0%, #a855f7 100%)',
                  border: 'none',
                  borderRadius: '10px',
                  color: '#ffffff',
                  padding: '0.45rem',
                  fontSize: '0.78rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.4rem',
                  boxShadow: '0 0 12px rgba(236, 72, 153, 0.3)',
                }}
              >
                <Play size={13} fill="#ffffff" />
                <span>Start Focus Mode</span>
              </button>
            </div>
          )}
        </div>

        {/* Nav list */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            const isAllowed = isTabAllowed(item.id);
            const isLocked = isFocusMode && !isAllowed;

            return (
              <button
                key={item.id}
                onClick={() => handleTabClick(item)}
                title={isLocked ? 'Locked in Focus Mode (only Goals & Learning allowed)' : undefined}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem 0.9rem',
                  borderRadius: '14px',
                  border: isActive
                    ? '1px solid rgba(6, 182, 212, 0.4)'
                    : isFocusMode && isAllowed
                    ? '1px solid rgba(236, 72, 153, 0.25)'
                    : '1px solid transparent',
                  background: isActive
                    ? 'rgba(6, 182, 212, 0.12)'
                    : isFocusMode && isAllowed
                    ? 'rgba(236, 72, 153, 0.05)'
                    : 'transparent',
                  color: isLocked ? '#64748b' : isActive ? '#ffffff' : '#94a3b8',
                  fontWeight: isActive ? '700' : '500',
                  fontSize: '0.92rem',
                  cursor: isLocked ? 'not-allowed' : 'pointer',
                  opacity: isLocked ? 0.4 : 1,
                  transition: 'all 0.2s ease',
                  textAlign: 'left',
                  width: '100%',
                  boxShadow: isActive ? '0 0 15px rgba(6, 182, 212, 0.15)' : 'none',
                }}
                onMouseEnter={(e) => {
                  if (isLocked) {
                    e.currentTarget.style.background = 'rgba(239, 68, 68, 0.08)';
                    e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.3)';
                  } else if (!isActive) {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                    e.currentTarget.style.color = '#e2e8f0';
                  }
                }}
                onMouseLeave={(e) => {
                  if (isLocked) {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.borderColor = 'transparent';
                  } else if (!isActive) {
                    e.currentTarget.style.background =
                      isFocusMode && isAllowed ? 'rgba(236, 72, 153, 0.05)' : 'transparent';
                    e.currentTarget.style.color = '#94a3b8';
                  }
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <Icon size={18} color={isLocked ? '#475569' : isActive ? '#06b6d4' : '#64748b'} />
                  <span>{item.label}</span>
                </div>

                {/* Status indicator pill / lock icon */}
                {isLocked && <Lock size={14} color="#64748b" />}
                {isFocusMode && isAllowed && (
                  <span
                    style={{
                      fontSize: '0.65rem',
                      fontWeight: '800',
                      padding: '0.15rem 0.4rem',
                      borderRadius: '9999px',
                      background: 'rgba(236, 72, 153, 0.2)',
                      color: '#f472b6',
                      border: '1px solid rgba(236, 72, 153, 0.3)',
                    }}
                  >
                    FOCUS
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer / Status Indicator */}
      <div
        style={{
          padding: '0.85rem',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '14px',
          border: '1px solid rgba(255, 255, 255, 0.05)',
        }}
      >
        <div style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          System Engine
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.3rem' }}>
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: isFocusMode ? '#ec4899' : '#10b981',
              boxShadow: isFocusMode ? '0 0 8px #ec4899' : '0 0 8px #10b981',
            }}
          />
          <span style={{ fontSize: '0.8rem', color: '#cbd5e1', fontWeight: '600' }}>
            {isFocusMode ? 'Focus Lockdown' : 'SQLite • Synced'}
          </span>
        </div>
      </div>
    </aside>
  );
};
