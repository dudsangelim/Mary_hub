"use client";

import { useRouter, useSearchParams } from "next/navigation";

import { StudentFilter } from "@/components/filters/StudentFilter";
import { SubjectFilter } from "@/components/filters/SubjectFilter";
import { Header } from "@/components/layout/Header";
import { TaskList } from "@/components/tasks/TaskList";
import { Select } from "@/components/ui/Select";
import { apiFetch } from "@/lib/api";
import { getTaskStatusLabel } from "@/lib/labels";
import { useAuth } from "@/hooks/useAuth";
import { useStudents } from "@/hooks/useStudents";
import { useSubjects } from "@/hooks/useSubjects";
import { useTasks } from "@/hooks/useTasks";
import type { Task } from "@/lib/types";

export default function TasksPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isReady, isAuthenticated } = useAuth(true);
  const { students } = useStudents();
  const studentId = searchParams.get("student_id") ?? "";
  const subjectId = searchParams.get("subject_id") ?? "";
  const status = searchParams.get("status") ?? "";
  const { subjects } = useSubjects(students, studentId);
  const params = new URLSearchParams(searchParams.toString());
  const query = params.toString() ? `?${params.toString()}` : "";
  const { data, loading, setData } = useTasks(query);

  function updateParam(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    router.push(`/tasks${params.toString() ? `?${params.toString()}` : ""}`);
  }

  function matchesCurrentView(task: Task) {
    if (status) {
      return task.status === status;
    }

    return task.status !== "done";
  }

  async function handleStatusChange(task: Task, nextStatus: string) {
    const updatedTask = await apiFetch<Task>(`/tasks/${task.id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status: nextStatus })
    });

    setData((current) => {
      if (!current) return current;

      const nextItems = current.items
        .map((item) => (item.id === updatedTask.id ? updatedTask : item))
        .filter(matchesCurrentView);

      return {
        ...current,
        items: nextItems
      };
    });
  }

  if (!isReady || !isAuthenticated) {
    return <div className="rounded-[2rem] bg-white p-6 text-sm text-slate-600 shadow-sm">Carregando...</div>;
  }

  return (
    <main className="space-y-6">
      <Header title="Tarefas" subtitle="Lista filtrável por aluno, disciplina e status. Tarefas concluídas ficam arquivadas fora da visão padrão." />
      <div className="grid gap-3 rounded-[2rem] bg-white p-4 shadow-sm md:grid-cols-3">
        <StudentFilter students={students} value={studentId} onChange={(value) => updateParam("student_id", value)} />
        <SubjectFilter students={students} subjects={subjects} studentId={studentId} value={subjectId} onChange={(value) => updateParam("subject_id", value)} />
        <Select value={status} onChange={(event) => updateParam("status", event.target.value)}>
          <option value="">Ativas</option>
          <option value="pending">{getTaskStatusLabel("pending")}</option>
          <option value="in_progress">{getTaskStatusLabel("in_progress")}</option>
          <option value="done">Arquivadas ({getTaskStatusLabel("done")})</option>
          <option value="overdue">{getTaskStatusLabel("overdue")}</option>
        </Select>
      </div>
      {loading ? <div className="rounded-[2rem] bg-white p-6 text-sm text-slate-600 shadow-sm">Carregando tarefas...</div> : <TaskList tasks={data?.items ?? []} students={students} subjects={subjects} onStatusChange={handleStatusChange} />}
    </main>
  );
}
