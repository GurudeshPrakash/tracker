import React, { useEffect, useState } from 'react';
import { Sidebar, NavTab } from './components/Sidebar';
import { TaskBoard } from './components/TaskBoard';
import { SuggestionsView } from './components/SuggestionsView';
import { LearningTab } from './components/LearningTab';
import { GoalsTab } from './components/GoalsTab';
import { InsightsTab } from './components/InsightsTab';
import { DailyUpdateModal } from './components/DailyUpdateModal';
import { api } from './api';
import { TasksResponse, Suggestion, Goal, LearningData, Priority } from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('tasks');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const [tasksData, setTasksData] = useState<TasksResponse>({
    today: new Date().toISOString().slice(0, 10),
    in_progress: [],
    todo: [],
    completed: [],
    overdue: [],
    backlog: [],
  });

  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [learningData, setLearningData] = useState<LearningData | null>(null);
  const [showDailyModal, setShowDailyModal] = useState(false);
  const [loading, setLoading] = useState(true);

  const refreshAll = async () => {
    try {
      const [tData, sData, gData, lData] = await Promise.all([
        api.getTasks(),
        api.getSuggestions(),
        api.getGoals(),
        api.getLearning(),
      ]);
      setTasksData(tData);
      setSuggestions(sData);
      setGoals(gData);
      setLearningData(lData);
    } catch (err) {
      console.error('Failed fetching tracker data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshAll();
  }, []);

  const handleToggleComplete = async (id: number) => {
    await api.toggleComplete(id);
    refreshAll();
  };

  const handleToggleTop3 = async (id: number) => {
    try {
      await api.toggleTop3(id);
      refreshAll();
    } catch (err: any) {
      alert(err.message || 'Could not toggle Top-3 (limit 3 per day)');
    }
  };

  const handleAddTask = async (task: {
    title: string;
    category: string;
    priority: Priority;
    estimate_min?: number;
    is_top3?: boolean;
  }) => {
    await api.createTask({
      title: task.title,
      category: task.category,
      priority: task.priority,
      estimate_min: task.estimate_min,
      is_top3: task.is_top3,
      planned_date: tasksData.today,
    });
    refreshAll();
  };

  const handleAddSubtask = async (taskId: number, title: string) => {
    await api.addSubtask(taskId, title);
    refreshAll();
  };

  const handleToggleSubtask = async (subtaskId: number) => {
    await api.toggleSubtask(subtaskId);
    refreshAll();
  };

  const handleAcceptSuggestion = async (sugg: Suggestion) => {
    await api.acceptSuggestion(sugg);
    setCurrentTab('tasks');
    refreshAll();
  };

  const handleLogSession = async (session: {
    skill_id: number;
    duration_min: number;
    takeaway: string;
    quality_rating?: number;
  }) => {
    await api.logSession(session);
    refreshAll();
  };

  const handleCreateGoal = async (data: any) => {
    await api.createGoal(data);
    refreshAll();
  };

  const totalActiveTasks = tasksData.in_progress.length + tasksData.todo.length;
  const openTasksCount = totalActiveTasks + tasksData.overdue.length;

  return (
    <div className="app-container">
      {/* Collapsible/Expanded Sidebar from reference */}
      <Sidebar
        currentTab={currentTab}
        onTabChange={(tab) => {
          if (tab === 'inbox') {
            setShowDailyModal(true);
          } else {
            setCurrentTab(tab);
          }
        }}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        taskCount={totalActiveTasks}
        openTasksCount={openTasksCount}
        selectedCategory={selectedCategory}
        onSelectCategory={setSelectedCategory}
      />

      {/* Main Workspace Area */}
      <main className="main-content">
        {loading ? (
          <div className="tasks-card-container" style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
            Loading your tasks and metrics...
          </div>
        ) : (
          <>
            {currentTab === 'tasks' && (
              <TaskBoard
                inProgress={tasksData.in_progress}
                todo={tasksData.todo}
                completed={tasksData.completed}
                overdue={tasksData.overdue}
                onToggleComplete={handleToggleComplete}
                onToggleTop3={handleToggleTop3}
                onAddTask={handleAddTask}
                onAddSubtask={handleAddSubtask}
                onToggleSubtask={handleToggleSubtask}
                selectedCategory={selectedCategory}
              />
            )}

            {currentTab === 'suggestions' && (
              <SuggestionsView
                suggestions={suggestions}
                onAccept={handleAcceptSuggestion}
              />
            )}

            {currentTab === 'learning' && (
              <LearningTab
                learningData={learningData}
                onLogSession={handleLogSession}
              />
            )}

            {currentTab === 'goals' && (
              <GoalsTab
                goals={goals}
                onCreateGoal={handleCreateGoal}
              />
            )}

            {currentTab === 'insights' && <InsightsTab />}
          </>
        )}
      </main>

      {/* EOD Daily Update Modal */}
      {showDailyModal && (
        <DailyUpdateModal
          onClose={() => setShowDailyModal(false)}
          onSuccess={() => {
            refreshAll();
            alert('Daily close complete! Remaining tasks carried or dropped according to your selection.');
          }}
        />
      )}
    </div>
  );
};

export default App;
