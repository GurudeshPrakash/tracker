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
import { SettingsView } from './components/SettingsView';
import { WeeklyReviewView } from './components/WeeklyReviewView';
import { FocusModeBar } from './components/FocusModeBar';
import { FocusProvider, useFocusMode } from './FocusContext';
import {
  fetchTodayData,
  completeTask,
  uncompleteTask,
  toggleTop3,
  dropTask,
  createTask,
} from './api';
import { Suggestion, TodayDashboardData } from './types';

function AppContent() {
  const [activeTab, setActiveTab] = useState<string>('today');
  const [dashboardData, setDashboardData] = useState<TodayDashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Focus mode hook
  const { isFocusMode, isTabAllowed, stopFocus } = useFocusMode();

  // Modal triggers
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [subtaskParentId, setSubtaskParentId] = useState<number | null>(null);
  const [isDailyUpdateOpen, setIsDailyUpdateOpen] = useState(false);
  const [isLogSessionOpen, setIsLogSessionOpen] = useState(false);
  const [logDuration, setLogDuration] = useState<number>(30);
  const [timerResetKey, setTimerResetKey] = useState(0);

  // Enforce tab restriction: only 'learning' and 'goals' tabs work during focus mode!
  useEffect(() => {
    if (isFocusMode && !isTabAllowed(activeTab)) {
      setActiveTab('learning');
    }
  }, [isFocusMode, activeTab, isTabAllowed]);

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

  const handleAcceptSuggestion = async (suggestion: Suggestion) => {
    try {
      await createTask({
        title: suggestion.title,
        priority: 'high',
        category: 'learning',
        estimated_min: suggestion.minutes,
        goal_id: suggestion.goal_id,
      });
      loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const openAddSubtask = (parentId: number) => {
    setSubtaskParentId(parentId);
    setIsTaskModalOpen(true);
  };

  const handleTabSelection = (tab: string) => {
    if (isFocusMode && !isTabAllowed(tab)) {
      return;
    }
    setActiveTab(tab);
  };

  const handleOpenDailyUpdate = () => {
    if (isFocusMode) {
      return;
    }
    setIsDailyUpdateOpen(true);
  };

  const hour = new Date().getHours();
  const showClosePrompt = Boolean(dashboardData && !dashboardData.day_closed && hour >= 17);

  return (
    <div style={{ display: 'flex', minHeight: '100vh', width: '100vw' }}>
      {/* Floating Left Glass Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={handleTabSelection}
        onOpenDailyUpdate={handleOpenDailyUpdate}
      />

      {/* Main Content Workspace */}
      <main
        style={{
          flex: 1,
          padding: '1.25rem 2rem 2rem 1.25rem',
          overflowY: 'auto',
          maxHeight: '100vh',
        }}
      >
        {/* Top Focus Mode HUD Bar */}
        <FocusModeBar
          onOpenLogModal={(mins) => {
            setLogDuration(mins || 30);
            setIsLogSessionOpen(true);
          }}
        />

        {error && (
          <div
            style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid #ef4444',
              color: '#fca5a5',
              padding: '1rem',
              borderRadius: '16px',
              marginBottom: '1.25rem',
            }}
          >
            {error}
          </div>
        )}

        {loading && !dashboardData ? (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '60vh',
              color: '#06b6d4',
              fontSize: '1.1rem',
              fontWeight: '700',
            }}
          >
            ⚡ Initializing FLUX Workspace...
          </div>
        ) : (
          <>
            {activeTab === 'today' && !isFocusMode && dashboardData && (
              <div>
                {dashboardData.day_closed && (
                  <div
                    style={{
                      maxWidth: '1440px',
                      margin: '0 auto 1rem',
                      padding: '0.75rem 1rem',
                      borderRadius: '14px',
                      border: '1px solid rgba(16, 185, 129, 0.3)',
                      background: 'rgba(16, 185, 129, 0.08)',
                      color: '#6ee7b7',
                      fontSize: '0.88rem',
                      fontWeight: 600,
                    }}
                  >
                    Today is closed. Open Daily Update to edit the reflection — leftover tasks already moved or dropped.
                  </div>
                )}
                {showClosePrompt && (
                  <div
                    style={{
                      maxWidth: '1440px',
                      margin: '0 auto 1rem',
                      padding: '0.75rem 1rem',
                      borderRadius: '14px',
                      border: '1px solid rgba(99, 102, 241, 0.35)',
                      background: 'rgba(99, 102, 241, 0.1)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '1rem',
                      flexWrap: 'wrap',
                    }}
                  >
                    <span style={{ color: '#c7d2fe', fontSize: '0.9rem', fontWeight: 600 }}>
                      Wrap the day to keep your streak and decide what carries to tomorrow.
                    </span>
                    <button
                      onClick={handleOpenDailyUpdate}
                      style={{
                        border: 'none',
                        borderRadius: '10px',
                        padding: '0.45rem 0.9rem',
                        background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                        color: '#fff',
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      Close day
                    </button>
                  </div>
                )}

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1.4fr 1fr 1fr',
                    gap: '1.25rem',
                    maxWidth: '1440px',
                    margin: '0 auto',
                  }}
                >
                  {/* 1. Today's Tasks Column (Left) */}
                  <TaskBoard
                    tasks={dashboardData.tasks}
                    top3={dashboardData.top3}
                    completed={dashboardData.completed}
                    overdue={dashboardData.overdue}
                    suggestions={dashboardData.suggestions}
                    onComplete={handleCompleteTask}
                    onUncomplete={handleUncompleteTask}
                    onToggleTop3={handleToggleTop3}
                    onDrop={handleDropTask}
                    onAddTask={() => {
                      setSubtaskParentId(null);
                      setIsTaskModalOpen(true);
                    }}
                    onAddSubtask={openAddSubtask}
                    onAcceptSuggestion={handleAcceptSuggestion}
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
                    resetKey={timerResetKey}
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
              </div>
            )}

            {activeTab === 'goals' && <GoalsView />}
            {activeTab === 'learning' && (
              <LearningView
                onOpenLogModal={() => {
                  setLogDuration(30);
                  setIsLogSessionOpen(true);
                }}
              />
            )}
            {activeTab === 'weekly' && !isFocusMode && <WeeklyReviewView />}
            {activeTab === 'insights' && !isFocusMode && <InsightsView />}
            {activeTab === 'settings' && !isFocusMode && <SettingsView />}
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

      {isDailyUpdateOpen && !isFocusMode && (
        <DailyUpdateModal
          onClose={() => setIsDailyUpdateOpen(false)}
          onSuccess={loadData}
        />
      )}

      {isLogSessionOpen && (
        <LogSessionModal
          initialDurationMin={logDuration}
          onClose={() => setIsLogSessionOpen(false)}
          onSuccess={() => {
            stopFocus();
            setTimerResetKey((k) => k + 1);
            loadData();
          }}
        />
      )}
    </div>
  );
}

export function App() {
  return (
    <FocusProvider>
      <AppContent />
    </FocusProvider>
  );
}

export default App;
