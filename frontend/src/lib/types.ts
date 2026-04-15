export type Guardian = {
  id: string;
  name: string;
  email: string;
  role: string;
  is_primary: boolean;
  is_active: boolean;
};

export type Family = {
  id: string;
  name: string;
  timezone: string;
  settings: Record<string, unknown>;
  is_active: boolean;
  guardians: Guardian[];
};

export type StudentProfile = {
  id: string;
  student_id: string;
  learning_style: string | null;
  attention_span_minutes: number | null;
  best_study_time: string | null;
  difficulty_areas: string[];
  strength_areas: string[];
  notes: string | null;
};

export type InterestProfile = {
  id: string;
  student_id: string;
  interests: string[];
  favorite_subjects: string[];
  hobbies: string[];
  motivators: string[];
  aversions: string[];
};

export type Student = {
  id: string;
  family_id: string;
  name: string;
  birth_date: string | null;
  grade: string;
  grade_label: string;
  school_name: string | null;
  school_shift: string | null;
  avatar_color: string;
  is_active: boolean;
  profile?: StudentProfile | null;
  interests?: InterestProfile | null;
};

export type Subject = {
  id: string;
  name: string;
  slug: string;
  grade: string;
  category: string;
  description: string | null;
  is_active: boolean;
};

export type CurriculumItem = {
  id: string;
  subject_id: string;
  title: string;
  description: string | null;
  bncc_code: string | null;
  order_index: number;
  semester: number | null;
  difficulty_level: string;
  source_type: string;
  source_reference: string | null;
};

export type Material = {
  id: string;
  student_id: string;
  uploaded_by: string;
  title: string;
  description: string | null;
  subject_id: string | null;
  material_type: string;
  file_path: string | null;
  file_name: string | null;
  file_size_bytes: number | null;
  mime_type: string | null;
  text_content: string | null;
  source: string;
  tags: string[];
  is_processed: boolean;
  created_at: string;
  updated_at: string;
};

export type Task = {
  id: string;
  student_id: string;
  created_by: string;
  material_id: string | null;
  title: string;
  description: string | null;
  subject_id: string | null;
  task_type: string;
  due_date: string | null;
  due_time: string | null;
  status: string;
  priority: string;
  parent_notes: string | null;
  estimated_minutes: number | null;
  completed_at: string | null;
  source: string;
  created_at: string;
  updated_at: string;
};

export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  per_page: number;
};

export type DashboardTodayStudent = {
  student_id: string;
  student_name: string;
  avatar_color: string;
  tasks_due_today: Task[];
  tasks_overdue: Task[];
  tasks_in_progress: Task[];
};

export type DashboardToday = {
  date: string;
  students: DashboardTodayStudent[];
};

export type DashboardSummaryStudent = {
  student_id: string;
  student_name: string;
  total_tasks: number;
  pending: number;
  in_progress: number;
  done: number;
  overdue: number;
  materials_count: number;
};

export type DashboardSummary = {
  students: DashboardSummaryStudent[];
};

export type AuthPayload = {
  guardian: Guardian;
  family_id: string;
  tokens: {
    access_token: string;
    refresh_token: string;
    token_type: string;
  };
};

export type ProviderAccount = {
  id: string;
  student_id: string;
  provider_name: string;
  provider_type: string;
  is_active: boolean;
  last_sync_at: string | null;
  sync_config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  has_credentials: boolean;
};

export type ProviderSyncLog = {
  id: string;
  provider_account_id: string;
  sync_type: string;
  status: string;
  items_found: number;
  items_synced: number;
  items_failed: number;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
  sync_metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ProviderSyncTriggerResponse = {
  provider_account: ProviderAccount;
  sync_log: ProviderSyncLog;
  message: string;
};

export type ClassificationResult = {
  ok: boolean;
  task_id: string;
  curriculum_item_id: string | null;
  difficulty_assessed: string | null;
  estimated_duration: number | null;
  classification_confidence: number | null;
  reasoning: string;
  classified_at: string | null;
};

export type ClassifyPendingResult = {
  ok: boolean;
  message: string;
  total: number;
  classified: number;
  skipped: number;
  failed: number;
};
