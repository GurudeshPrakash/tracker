import {
  TodayDashboardData,
  Task,
  DailyUpdatePrefill,
  LearningItem,
  SettingsData,
  BackupInfo,
  RecurringTask,
  RecurringTaskForm,
  NotificationSettings,
} from './types';

const BASE = '/api';

export async function fetchTodayData(): Promise<TodayDashboardData> {
  const res = await fetch(`${BASE}/today`);
  if (!res.ok) throw new Error('Failed to load dashboard data');
  return res.json();
}

export async function createTask(data: {
  title: string;
  priority?: string;
  category?: string;
  estimated_min?: number;
  goal_id?: number;
  learning_item_id?: number;
  planned_date?: string;
  notes?: string;
}): Promise<Task> {
  const res = await fetch(`${BASE}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create task');
  return res.json();
}

export async function completeTask(id: number): Promise<void> {
  const res = await fetch(`${BASE}/tasks/${id}/complete`, { method: 'POST' });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to complete task');
  }
}

export async function uncompleteTask(id: number): Promise<void> {
  const res = await fetch(`${BASE}/tasks/${id}/uncomplete`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to uncomplete task');
}

export async function toggleTop3(id: number, is_top3: boolean): Promise<void> {
  const res = await fetch(`${BASE}/tasks/${id}/top3`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ is_top3 }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to toggle Top 3');
  }
}

export async function dropTask(id: number): Promise<void> {
  const res = await fetch(`${BASE}/tasks/${id}/drop`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to drop task');
}

export async function addSubtask(parentId: number, title: string): Promise<Task> {
  const res = await fetch(`${BASE}/tasks/${parentId}/subtasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error('Failed to add subtask');
  return res.json();
}

export async function fetchDailyUpdate(date?: string): Promise<DailyUpdatePrefill> {
  const url = date ? `${BASE}/daily-update?date=${date}` : `${BASE}/daily-update`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to load daily update');
  return res.json();
}

export async function closeDailyUpdate(data: {
  date: string;
  completed_summary: string;
  learned_today: string;
  study_minutes: number;
  day_rating: number;
  blockers: string;
  tomorrow_focus: string;
  carry_task_ids: number[];
}): Promise<any> {
  const res = await fetch(`${BASE}/daily-update/close`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to close day');
  return res.json();
}

export async function logStudySession(data: {
  learning_item_id: number;
  duration_min: number;
  takeaway: string;
  confidence?: number;
  task_id?: number;
}): Promise<any> {
  const res = await fetch(`${BASE}/learning/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to log study session');
  }
  return res.json();
}

export async function fetchLearningData(): Promise<{ items: LearningItem[]; distinct_skills: string[]; goals: any[] }> {
  const res = await fetch(`${BASE}/learning`);
  if (!res.ok) throw new Error('Failed to fetch learning data');
  return res.json();
}

export async function createLearningItem(data: {
  skill: string;
  resource: string;
  resource_type: string;
  status: string;
  goal_id?: number;
}): Promise<any> {
  const res = await fetch(`${BASE}/learning/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create learning item');
  return res.json();
}

export async function fetchGoals(): Promise<any[]> {
  const res = await fetch(`${BASE}/goals`);
  if (!res.ok) throw new Error('Failed to fetch goals');
  return res.json();
}

export async function createGoal(data: {
  title: string;
  target_type: string;
  target_hours: number;
  start_date: string;
  target_date?: string;
}): Promise<any> {
  const res = await fetch(`${BASE}/goals`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create goal');
  return res.json();
}

export async function updateGoalStatus(goalId: number, status: string): Promise<any> {
  const res = await fetch(`${BASE}/goals/${goalId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error('Failed to update goal');
  return res.json();
}

export async function fetchStats(start?: string, end?: string): Promise<any> {
  const url = start && end ? `${BASE}/stats?start=${start}&end=${end}` : `${BASE}/stats`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to load stats');
  return res.json();
}

// ---------------------------------------------------------------------------
// Settings, Backups, Recurring, Exports, & Notifications
// ---------------------------------------------------------------------------

export async function fetchSettings(): Promise<SettingsData> {
  const res = await fetch(`${BASE}/settings`);
  if (!res.ok) throw new Error('Failed to load settings');
  return res.json();
}

export async function createBackup(): Promise<{ success: boolean; filename: string }> {
  const res = await fetch(`${BASE}/backups`, { method: 'POST' });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to create backup');
  }
  return res.json();
}

export async function restoreBackup(filename: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${BASE}/backups/restore`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to restore backup');
  }
  return res.json();
}

export async function uploadAndRestoreBackup(file: File): Promise<{ success: boolean; message: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${BASE}/backups/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to restore uploaded database');
  }
  return res.json();
}

export async function fetchRecurringTasks(): Promise<RecurringTask[]> {
  const res = await fetch(`${BASE}/recurring`);
  if (!res.ok) throw new Error('Failed to load recurring tasks');
  return res.json();
}

export async function createRecurringTask(data: RecurringTaskForm): Promise<RecurringTask> {
  const res = await fetch(`${BASE}/recurring`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to create recurring rule');
  }
  return res.json();
}

export async function updateRecurringTask(id: number, data: Partial<RecurringTask>): Promise<any> {
  const res = await fetch(`${BASE}/recurring/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to update recurring task');
  }
  return res.json();
}

export async function deleteRecurringTask(id: number): Promise<any> {
  const res = await fetch(`${BASE}/recurring/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete recurring rule');
  return res.json();
}

export async function triggerRecurringGeneration(date?: string): Promise<{ success: boolean; date: string; generated_count: number }> {
  const res = await fetch(`${BASE}/recurring/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(date ? { date } : {}),
  });
  if (!res.ok) throw new Error('Failed to run recurring generator');
  return res.json();
}

export async function fetchNotificationSettings(): Promise<NotificationSettings> {
  const res = await fetch(`${BASE}/settings/notifications`);
  if (!res.ok) throw new Error('Failed to load notification settings');
  return res.json();
}

export async function testNotification(mode: 'morning' | 'evening'): Promise<{ success: boolean; title: string; message: string }> {
  const res = await fetch(`${BASE}/settings/test-notification?mode=${mode}`, { method: 'POST' });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to trigger notification');
  }
  return res.json();
}

