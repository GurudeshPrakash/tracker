import {
  TodayDashboardData,
  Task,
  DailyUpdatePrefill,
  LearningItem,
  SettingsData,
  RecurringTask,
  RecurringTaskForm,
  NotificationSettings,
  CloseDayResult,
  ReviewsPayload,
  User,
  AuthResponse,
} from './types';

const BASE = '/api';
const TOKEN_KEY = 'flux_auth_token';
const USER_KEY = 'flux_auth_user';

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  const u = localStorage.getItem(USER_KEY);
  if (!u) return null;
  try {
    return JSON.parse(u);
  } catch {
    return null;
  }
}

export function setAuthSession(token: string, user: User) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  window.dispatchEvent(new Event('flux:auth_changed'));
}

export function clearAuthSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  window.dispatchEvent(new Event('flux:auth_changed'));
}

export async function authFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const token = getStoredToken();
  const headers = new Headers(init?.headers || {});
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  const response = await fetch(input, { ...init, headers });
  if (response.status === 401) {
    clearAuthSession();
  }
  return response;
}

// ---------------------------------------------------------------------------
// Authentication Endpoints
// ---------------------------------------------------------------------------
export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to log in. Check your credentials.');
  }
  const data: AuthResponse = await res.json();
  setAuthSession(data.token, data.user);
  return data;
}

export async function register(email: string, password: string, name?: string): Promise<AuthResponse> {
  const res = await fetch(`${BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to create account.');
  }
  const data: AuthResponse = await res.json();
  setAuthSession(data.token, data.user);
  return data;
}

export async function fetchCurrentUser(): Promise<User> {
  const res = await authFetch(`${BASE}/auth/me`);
  if (!res.ok) throw new Error('Failed to fetch user profile');
  const user = await res.json();
  const token = getStoredToken();
  if (token) {
    setAuthSession(token, user);
  }
  return user;
}

export function logout(): void {
  clearAuthSession();
}

// ---------------------------------------------------------------------------
// Dashboard & Tasks (Scoped)
// ---------------------------------------------------------------------------
export async function fetchTodayData(): Promise<TodayDashboardData> {
  const res = await authFetch(`${BASE}/today`);
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
  const res = await authFetch(`${BASE}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create task');
  return res.json();
}

export async function completeTask(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/tasks/${id}/complete`, { method: 'POST' });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to complete task');
  }
}

export async function uncompleteTask(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/tasks/${id}/uncomplete`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to uncomplete task');
}

export async function toggleTop3(id: number, is_top3: boolean): Promise<void> {
  const res = await authFetch(`${BASE}/tasks/${id}/top3`, {
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
  const res = await authFetch(`${BASE}/tasks/${id}/drop`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to drop task');
}

export async function addSubtask(parentId: number, title: string): Promise<Task> {
  const res = await authFetch(`${BASE}/tasks/${parentId}/subtasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error('Failed to add subtask');
  return res.json();
}

export async function fetchDailyUpdate(date?: string): Promise<DailyUpdatePrefill> {
  const url = date ? `${BASE}/daily-update?date=${date}` : `${BASE}/daily-update`;
  const res = await authFetch(url);
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
}): Promise<CloseDayResult> {
  const res = await authFetch(`${BASE}/daily-update/close`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to close day');
  return res.json();
}

export async function updateDailyUpdate(data: {
  date: string;
  completed_summary: string;
  learned_today: string;
  study_minutes: number;
  day_rating: number;
  blockers: string;
  tomorrow_focus: string;
}): Promise<any> {
  const res = await authFetch(`${BASE}/daily-update`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update daily reflection');
  return res.json();
}

export async function logStudySession(data: {
  learning_item_id: number;
  duration_min: number;
  takeaway: string;
  confidence?: number;
  task_id?: number;
}): Promise<any> {
  const res = await authFetch(`${BASE}/learning/sessions`, {
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
  const res = await authFetch(`${BASE}/learning`);
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
  const res = await authFetch(`${BASE}/learning/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create learning item');
  return res.json();
}

export async function fetchGoals(): Promise<any[]> {
  const res = await authFetch(`${BASE}/goals`);
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
  const res = await authFetch(`${BASE}/goals`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create goal');
  return res.json();
}

export async function updateGoalStatus(goalId: number, status: string): Promise<any> {
  const res = await authFetch(`${BASE}/goals/${goalId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error('Failed to update goal');
  return res.json();
}

export async function fetchReviews(week?: string): Promise<ReviewsPayload> {
  const url = week ? `${BASE}/reviews?week=${week}` : `${BASE}/reviews`;
  const res = await authFetch(url);
  if (!res.ok) throw new Error('Failed to load weekly review');
  return res.json();
}

export async function saveReview(data: {
  week_start: string;
  wins: string;
  blockers: string;
  next_focus: string;
}): Promise<any> {
  const res = await authFetch(`${BASE}/reviews`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to save weekly review');
  return res.json();
}

export async function fetchStats(start?: string, end?: string): Promise<any> {
  const url = start && end ? `${BASE}/stats?start=${start}&end=${end}` : `${BASE}/stats`;
  const res = await authFetch(url);
  if (!res.ok) throw new Error('Failed to load stats');
  return res.json();
}

// ---------------------------------------------------------------------------
// Settings, Backups, Recurring, Exports, & Notifications
// ---------------------------------------------------------------------------
export async function fetchSettings(): Promise<SettingsData> {
  const res = await authFetch(`${BASE}/settings`);
  if (!res.ok) throw new Error('Failed to load settings');
  return res.json();
}

export async function createBackup(): Promise<{ success: boolean; filename: string }> {
  const res = await authFetch(`${BASE}/backups`, { method: 'POST' });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to create backup');
  }
  return res.json();
}

export async function restoreBackup(filename: string): Promise<{ success: boolean; message: string }> {
  const res = await authFetch(`${BASE}/backups/restore`, {
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
  const res = await authFetch(`${BASE}/backups/upload`, {
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
  const res = await authFetch(`${BASE}/recurring`);
  if (!res.ok) throw new Error('Failed to load recurring tasks');
  return res.json();
}

export async function createRecurringTask(data: RecurringTaskForm): Promise<RecurringTask> {
  const res = await authFetch(`${BASE}/recurring`, {
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
  const res = await authFetch(`${BASE}/recurring/${id}`, {
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
  const res = await authFetch(`${BASE}/recurring/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete recurring rule');
  return res.json();
}

export async function triggerRecurringGeneration(date?: string): Promise<{ success: boolean; date: string; generated_count: number }> {
  const res = await authFetch(`${BASE}/recurring/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(date ? { date } : {}),
  });
  if (!res.ok) throw new Error('Failed to run recurring generator');
  return res.json();
}

export async function fetchNotificationSettings(): Promise<NotificationSettings> {
  const res = await authFetch(`${BASE}/settings/notifications`);
  if (!res.ok) throw new Error('Failed to load notification settings');
  return res.json();
}

export async function testNotification(mode: 'morning' | 'evening'): Promise<{ success: boolean; title: string; message: string }> {
  const res = await authFetch(`${BASE}/settings/test-notification?mode=${mode}`, { method: 'POST' });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to trigger notification');
  }
  return res.json();
}
