export interface Task {
  id: number;
  title: string;
  notes?: string | null;
  planned_date?: string | null;
  due_date?: string | null;
  priority: 'high' | 'medium' | 'low';
  category: 'work' | 'learning' | 'personal';
  goal_id?: number | null;
  learning_item_id?: number | null;
  parent_task_id?: number | null;
  status: 'todo' | 'done' | 'dropped';
  is_top3: number;
  rollover_count: number;
  estimated_min?: number | null;
  actual_min?: number | null;
  completed_at?: string | null;
  completed_date?: string | null;
  subtasks?: Task[];
}

export interface GoalProgress {
  status: 'on_track' | 'behind' | 'ahead' | 'complete';
  done_hours: number;
  target_hours: number;
  percent: number;
  expected_percent?: number | null;
  week_hours: number;
}

export interface GoalItem {
  goal: {
    id: number;
    title: string;
    target_type: string;
    target_hours: number;
    start_date: string;
    target_date?: string | null;
    status: string;
  };
  progress: GoalProgress;
  linked_resources?: any[];
}

export interface RecentSessionItem {
  session: {
    id: number;
    learning_item_id: number;
    session_date: string;
    duration_min: number;
    takeaway: string;
    confidence?: number;
  };
  skill: string;
  resource: string;
}

export interface Suggestion {
  goal_id: number;
  title: string;
  minutes: number;
  reason: string;
}

export interface TodayDashboardData {
  today: string;
  streak: number;
  done_count: number;
  planned_count: number;
  study_min: number;
  top3: Task[];
  tasks: Task[];
  completed: Task[];
  overdue: Task[];
  suggestions: Suggestion[];
  goals: GoalItem[];
  recent_sessions: RecentSessionItem[];
  completion_series?: { date: string; rate: number }[];
  skill_series?: { skill: string; minutes: number }[];
}

export interface DailyUpdatePrefill {
  date: string;
  completed_tasks: Task[];
  open_tasks: Task[];
  study_minutes: number;
  session_takeaways: string[];
  existing?: any;
  is_closed: boolean;
}

export interface LearningItem {
  id: number;
  skill: string;
  resource: string;
  resource_type: string;
  status: string;
  goal_id?: number | null;
}
