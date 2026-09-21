import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { BentoHero } from './components/BentoHero';
import { TaskBoard } from './components/TaskBoard';
import { ActiveLearningBento } from './components/ActiveLearningBento';
import { WeeklyMiniStats } from './components/WeeklyMiniStats';
import { NewTaskModal } from './components/NewTaskModal';
import { DailyUpdateModal } from './components/DailyUpdateModal';
import { LogSessionModal } from './components/LogSessionModal';
import { GoalsView } from './components/GoalsView';
import { LearningView } from './components/LearningView';
import { InsightsView } from './components/InsightsView';
import {
  fetchTodayData,
  completeTask,
  uncompleteTask,
  toggleTop3,
  dropTask,
} from './api';
import { TodayDashboardData } from './types';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('today');
  const [dashboardData, setDashboardData] = useState<TodayDashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modal triggers
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [subtaskParentId, setSubtaskParentId] = useState<number | null>(null);
  const [isDailyUpdateOpen, setIsDailyUpdateOpen] = useState(false);
  const [isLogSessionOpen, setIsLogSessionOpen] = useState(false);
  const [logDuration, setLogDuration] = useState<number>(30);

  const loadData = async () => {
    try {
      const data = await fetchTodayData();
      setDashboardData(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Poll updates every 30s
    return () => clearInterval(interval);
  }, []);

  const handleCompleteTask = async (id: number) => {
    try {
      await completeTask(id);
      loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleUncompleteTask = async (id: number) => {
    try {
      await uncompleteTask(id);
      loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleToggleTop3 = async (id: number, current: boolean) => {
    try {
      await toggleTop3(id, !current);
      loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDropTask = async (id: number) => {
    try {
      await dropTask(id);
      loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const openAddSubtask = (parentId: number) => {
    setSubtaskParentId(parentId);
    setIsTaskModalOpen(true);
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', width: '100vw' }}>
      {/* Floating Left Glass Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onOpenDailyUpdate={() => setIsDailyUpdateOpen(true)}
      />

      {/* Main Content Workspace */}
      <main style={{
        flex: 1,
        padding: '1.25rem 2rem 2rem 1.25rem',
        overflowY: 'auto',
        maxHeight: '100vh',
      }}>
        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid #ef4444',
            color: '#fca5a5',
            padding: '1rem',
            borderRadius: '16px',
            marginBottom: '1.25rem',
          }}>
            {error}
          </div>
        )}

        {loading && !dashboardData ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', color: '#06b6d4', fontSize: '1.1rem', fontWeight: '700' }}>
            ⚡ Initializing FLUX Workspace...
          </div>
        ) : (
          <>
            {activeTab === 'today' && dashboardData && (
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1.4fr 1fr 1fr',
                gap: '1.25rem',
                maxWidth: '1440px',
                margin: '0 auto',
              }}>
                {/* 1. Today's Tasks Column (Left) */}
                <TaskBoard
                  tasks={dashboardData.tasks}
                  top3={dashboardData.top3}
                  completed={dashboardData.completed}
                  onComplete={handleCompleteTask}
                  onUncomplete={handleUncompleteTask}
                  onToggleTop3={handleToggleTop3}
                  onDrop={handleDropTask}
                  onAddTask={() => {
                    setSubtaskParentId(null);
                    setIsTaskModalOpen(true);
                  }}
                  onAddSubtask={openAddSubtask}
                />

                {/* 2. Bento Hero Card (Center Top) */}
                <BentoHero
                  streak={dashboardData.streak}
                  goals={dashboardData.goals}
                  doneCount={dashboardData.done_count}
                  plannedCount={dashboardData.planned_count}
                  studyMin={dashboardData.study_min}
                />

                {/* 3. Active Learning Bento (Right) */}
                <ActiveLearningBento
                  recentSessions={dashboardData.recent_sessions}
                  onOpenLogModal={(mins) => {
                    setLogDuration(mins || 30);
                    setIsLogSessionOpen(true);
                  }}
                />

                {/* 4. Weekly Mini-Stats (Bottom Row) */}
                <WeeklyMiniStats
                  doneCount={dashboardData.done_count}
                  plannedCount={dashboardData.planned_count}
                  studyMin={dashboardData.study_min}
                  completionSeries={dashboardData.completion_series}
                  skillSeries={dashboardData.skill_series}
                />
              </div>
            )}

            {activeTab === 'goals' && <GoalsView />}
            {activeTab === 'learning' && <LearningView onOpenLogModal={() => setIsLogSessionOpen(true)} />}
            {activeTab === 'insights' && <InsightsView />}
            {activeTab === 'settings' && (
              <div className="bento-card" style={{ maxWidth: '800px', margin: '1rem auto' }}>
                <h2 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f8fafc', marginBottom: '1rem' }}>
                  ⚙️ System Management
                </h2>
                <div style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                  Database backups and recurring task schedule configurations
                </div>
                <button
                  onClick={() => {
                    fetch('/api/backups', { method: 'POST' })
                      .then((r) => r.json())
                      .then((d) => alert(`Backup created: ${d.filename}`))
                      .catch((e) => alert(e.message));
                  }}
                  style={{
                    padding: '0.75rem 1.5rem',
                    borderRadius: '12px',
                    border: 'none',
                    background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
                    color: '#fff',
                    fontWeight: '700',
                    cursor: 'pointer',
                  }}
                >
                  📦 Create Instant Database Backup
                </button>
              </div>
            )}
          </>
        )}
      </main>

      {/* Modals */}
      {isTaskModalOpen && (
        <NewTaskModal
          parentId={subtaskParentId}
          onClose={() => {
            setIsTaskModalOpen(false);
            setSubtaskParentId(null);
          }}
          onSuccess={loadData}
        />
      )}

      {isDailyUpdateOpen && (
        <DailyUpdateModal
          onClose={() => setIsDailyUpdateOpen(false)}
          onSuccess={loadData}
        />
      )}

      {isLogSessionOpen && (
        <LogSessionModal
          initialDurationMin={logDuration}
          onClose={() => setIsLogSessionOpen(false)}
          onSuccess={loadData}
        />
      )}
    </div>
  );
}

export default App;
