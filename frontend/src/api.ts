import { TasksResponse, Suggestion, Goal, LearningData, InsightsData } from './types';

const API_BASE = 'http://127.0.0.1:8000/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'API request failed');
  }
  return res.json();
}

export const api = {
  getTasks: (date?: string): Promise<TasksResponse> =>
    fetchJson(`${API_BASE}/tasks${date ? `?date=${date}` : ''}`),

  createTask: (data: {
    title: string;
    planned_date?: string;
    category?: string;
    priority?: string;
    estimate_min?: number;
    notes?: string;
    is_top3?: boolean;
    goal_id?: number;
  }) => fetchJson<{ id: number; success: boolean }>(`${API_BASE}/tasks`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  toggleComplete: (taskId: number) =>
    fetchJson<{ status: string }>(`${API_BASE}/tasks/${taskId}/complete`, { method: 'PUT' }),

  toggleTop3: (taskId: number) =>
    fetchJson<{ is_top3: boolean }>(`${API_BASE}/tasks/${taskId}/top3`, { method: 'PUT' }),

  updateTask: (taskId: number, updates: any) =>
    fetchJson<{ success: boolean }>(`${API_BASE}/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    }),

  deleteTask: (taskId: number) =>
    fetchJson<{ success: boolean }>(`${API_BASE}/tasks/${taskId}`, { method: 'DELETE' }),

  addSubtask: (taskId: number, title: string) =>
    fetchJson<{ id: number; success: boolean }>(`${API_BASE}/tasks/${taskId}/subtasks`, {
      method: 'POST',
      body: JSON.stringify({ title }),
    }),

  toggleSubtask: (subtaskId: number) =>
    fetchJson<{ status: string }>(`${API_BASE}/subtasks/${subtaskId}/complete`, { method: 'PUT' }),

  getSuggestions: (date?: string): Promise<Suggestion[]> =>
    fetchJson(`${API_BASE}/suggestions${date ? `?date=${date}` : ''}`),

  acceptSuggestion: (suggestion: Suggestion) =>
    fetchJson<{ id: number; success: boolean }>(`${API_BASE}/suggestions/accept`, {
      method: 'POST',
      body: JSON.stringify(suggestion),
    }),

  getGoals: (): Promise<Goal[]> => fetchJson(`${API_BASE}/goals`),

  createGoal: (data: any) =>
    fetchJson<{ id: number; success: boolean }>(`${API_BASE}/goals`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getLearning: (): Promise<LearningData> => fetchJson(`${API_BASE}/learning`),

  logSession: (data: {
    skill_id: number;
    duration_min: number;
    takeaway: string;
    quality_rating?: number;
    resource_id?: number;
    next_review_days?: number;
  }) => fetchJson<{ id: number; success: boolean }>(`${API_BASE}/learning/sessions`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  getInsights: (days: number = 30): Promise<InsightsData> =>
    fetchJson(`${API_BASE}/insights?days=${days}`),

  getDailyUpdate: (date?: string) =>
    fetchJson<any>(`${API_BASE}/daily-update${date ? `?date=${date}` : ''}`),

  closeDailyUpdate: (data: any) =>
    fetchJson<{ success: boolean }>(`${API_BASE}/daily-update/close`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};
