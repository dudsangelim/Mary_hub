import { apiFetch } from "@/lib/api";

export interface SessionStep {
  index: number;
  kind: "intro" | "task" | "celebration";
  task_id: string | null;
  task_title: string | null;
  subject: string | null;
  pages: string | null;
  book_reference: string | null;
  instruction: string | null;
  audio_key: string | null;
  done: boolean;
}

export interface TutorSession {
  id: string;
  student_id: string | null;
  plan_id: string;
  task_id: string | null;
  title: string;
  scheduled_date: string;
  session_kind: string;
  status: string;
  runtime_state: Record<string, unknown>;
  steps: SessionStep[];
  outcome: Record<string, unknown>;
}

export interface TutorNextResponse {
  session_id: string;
  step: SessionStep | null;
  is_last: boolean;
  message: string | null;
}

export interface TTSResponse {
  audio_key: string;
  cached: boolean;
}

const API = (process.env.NEXT_PUBLIC_API_URL ?? "/api/v1").replace(/\/$/, "");

export async function createOrGetSession(
  studentId: string,
  scheduledDate: string,
  sessionKind = "homework"
): Promise<TutorSession> {
  return apiFetch<TutorSession>("/tutor/sessions", {
    method: "POST",
    body: JSON.stringify({ student_id: studentId, scheduled_date: scheduledDate, session_kind: sessionKind }),
  });
}

export async function getSession(sessionId: string): Promise<TutorSession> {
  return apiFetch<TutorSession>(`/tutor/sessions/${sessionId}`);
}

export async function nextStep(
  sessionId: string,
  stepIndex: number,
  markDone = false
): Promise<TutorNextResponse> {
  return apiFetch<TutorNextResponse>(`/tutor/sessions/${sessionId}/next`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, step_index: stepIndex, mark_done: markDone }),
  });
}

export async function requestTTS(text: string, voice = "nova"): Promise<TTSResponse> {
  return apiFetch<TTSResponse>("/tutor/tts", {
    method: "POST",
    body: JSON.stringify({ text, voice }),
  });
}

export function getTTSAudioUrl(audioKey: string): string {
  const bare = audioKey.replace(/^tts:audio:/, "");
  return `${API}/tutor/tts/${bare}`;
}
