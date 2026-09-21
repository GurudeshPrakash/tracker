export type Priority = 'High' | 'Medium' | 'Low';
export type TaskStatus = 'todo' | 'done' | 'dropped';

export interface Subtask {
  id: number;
  title: string;
  status: 'todo' | 'done';
}

export interface Task {
  id: number;
  title: string;
  planned_date: string;
  category: string;
  priority: Priority;
  status: TaskStatus;
  is_top3: boolean;
  estimate_min?: number;
  actual_min?: number;
  notes?: string;
  rollover_count: number;
  completed_at?: string;
  subtasks: Subtask[];
}

export interface TasksResponse {
  today: string;
  in_progress: Task[];
  todo: Task[];
  completed: Task[];
  overdue: Task[];
  backlog: Task[];
}

export interface Suggestion {
  goal_id: number;
  goal_title: string;
  title: string;
  category: string;
  duration_min: number;
  reason: string;
  planned_date: string;
}

export interface Goal {
  id: number;
  title: string;
  category: string;
  status: string;
  target_hours?: number;
  target_date?: string;
  weekly_hours_target?: number;
  logged_minutes: number;
  progress_pct: number;
  resources: { id: number; title: string; type: string; url?: string }[];
}

export interface Skill {
  id: number;
  name: string;
  category: string;
  proficiency: string;
}

export interface Session {
  id: number;
  skill_id: number;
  duration_min: number;
  takeaway: string;
  session_date: string;
  quality_rating?: number;
}

export interface ReviewItem {
  id: number;
  takeaway: string;
  duration_min: number;
  session_date: string;
  next_review_date: string;
}

export interface LearningData {
  skills: Skill[];
  resources: any[];
  sessions: Session[];
  review_queue: ReviewItem[];
}

export interface InsightsData {
  streak: number;
  completion_rate: number;
  average_rating: number;
  study_by_skill: { skill_name: string; total_min: number }[];
}
