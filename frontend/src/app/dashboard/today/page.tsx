"use client";

import { useEffect, useState } from "react";

import { Header } from "@/components/layout/Header";
import { EmptyState } from "@/components/ui/EmptyState";
import { TaskList } from "@/components/tasks/TaskList";
import { useAuth } from "@/hooks/useAuth";
import { apiFetch } from "@/lib/api";
import type { DashboardToday, Student } from "@/lib/types";

export default function TodayPage() {
  const { isReady, isAuthenticated } = useAuth(true);
  const [today, setToday] = useState<DashboardToday | null>(null);

  useEffect(() => {
    apiFetch<DashboardToday>("/dashboard/today").then(setToday);
  }, []);

  if (!isReady || !isAuthenticated) {
    return <div className="rounded-[2rem] bg-white p-6 text-sm text-slate-600 shadow-sm">Carregando...</div>;
  }

  return (
    <main className="space-y-6">
      <Header title="Hoje" subtitle="Tarefas de hoje, em atraso e em andamento agrupadas por aluno." />
      {!today ? (
        <div className="rounded-[2rem] bg-white p-6 text-sm text-slate-600 shadow-sm">Carregando visão do dia...</div>
      ) : (
        <div className="space-y-6">
          {today.students.map((student) => {
            const studentEntity: Student = {
              id: student.student_id,
              family_id: "",
              name: student.student_name,
              birth_date: null,
              grade: "",
              grade_label: "",
              school_name: null,
              school_shift: null,
              avatar_color: student.avatar_color,
              is_active: true
            };
            const students = [studentEntity];
            if (student.tasks_due_today.length + student.tasks_overdue.length + student.tasks_in_progress.length === 0) {
              return (
                <section key={student.student_id} className="space-y-3">
                  <h3 className="text-xl font-semibold text-slate-900">{student.student_name}</h3>
                  <EmptyState title="Nenhuma tarefa para hoje" description="Sem itens vencendo hoje nem em atraso." href="/tasks/new" cta="Criar tarefa" />
                </section>
              );
            }
            return (
              <section key={student.student_id} className="space-y-3">
                <h3 className="text-xl font-semibold text-slate-900">{student.student_name}</h3>
                <TaskList tasks={[...student.tasks_overdue, ...student.tasks_due_today, ...student.tasks_in_progress]} students={students} subjects={[]} />
              </section>
            );
          })}
        </div>
      )}
    </main>
  );
}
