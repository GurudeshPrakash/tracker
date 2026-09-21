import React from 'react';
import { Calendar, FileText, BookOpen, Target, BarChart3, Settings, Zap } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
  onOpenDailyUpdate: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab, onOpenDailyUpdate }) => {
  const navItems = [
    { id: 'today', label: 'Today', icon: Calendar },
    { id: 'daily-update', label: 'Daily Update', icon: FileText, action: onOpenDailyUpdate },
    { id: 'learning', label: 'Learning', icon: BookOpen },
    { id: 'goals', label: 'Goals', icon: Target },
    { id: 'insights', label: 'Insights', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside style={{
      width: '240px',
      background: 'rgba(15, 19, 32, 0.75)',
      backdropFilter: 'blur(24px)',
      WebkitBackdropFilter: 'blur(24px)',
      borderRight: '1px solid rgba(255, 255, 255, 0.08)',
      borderRadius: '24px',
      margin: '1.25rem 0 1.25rem 1.25rem',
      padding: '1.75rem 1.25rem',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4)',
      height: 'calc(100vh - 2.5rem)',
      position: 'sticky',
      top: '1.25rem',
    }}>
      <div>
        {/* Brand Logo matching image */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '2.5rem', paddingLeft: '0.5rem' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 50%, #6366f1 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 18px rgba(6, 182, 212, 0.4)',
          }}>
            <Zap size={22} color="#ffffff" />
          </div>
          <span style={{
            fontSize: '1.4rem',
            fontWeight: '800',
            letterSpacing: '0.04em',
            background: 'linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            FLUX
          </span>
        </div>

        {/* Nav list */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  if (item.action) {
                    item.action();
                  } else {
                    onSelectTab(item.id);
                  }
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.9rem',
                  padding: '0.85rem 1rem',
                  borderRadius: '14px',
                  border: isActive ? '1px solid rgba(6, 182, 212, 0.4)' : '1px solid transparent',
                  background: isActive ? 'rgba(6, 182, 212, 0.12)' : 'transparent',
                  color: isActive ? '#ffffff' : '#94a3b8',
                  fontWeight: isActive ? '700' : '500',
                  fontSize: '0.95rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  textAlign: 'left',
                  width: '100%',
                  boxShadow: isActive ? '0 0 15px rgba(6, 182, 212, 0.15)' : 'none',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                    e.currentTarget.style.color = '#e2e8f0';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.color = '#94a3b8';
                  }
                }}
              >
                <Icon size={19} color={isActive ? '#06b6d4' : '#64748b'} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer / Status Indicator */}
      <div style={{
        padding: '0.85rem',
        background: 'rgba(255, 255, 255, 0.02)',
        borderRadius: '14px',
        border: '1px solid rgba(255, 255, 255, 0.05)',
      }}>
        <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          System Engine
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.3rem' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981' }} />
          <span style={{ fontSize: '0.82rem', color: '#cbd5e1', fontWeight: '600' }}>SQLite &bull; Synced</span>
        </div>
      </div>
    </aside>
  );
};
