"use client";

import { Header } from "@/components/layout/Header";
import { TaskForm } from "@/components/tasks/TaskForm";
import { useAuth } from "@/hooks/useAuth";
import { useStudents } from "@/hooks/useStudents";
import { useSubjects } from "@/hooks/useSubjects";

export default function NewTaskPage() {
  const { isReady, isAuthenticated } = useAuth(true);
  const { students, loading: studentsLoading } = useStudents();
  const { subjects } = useSubjects(students);

  if (!isReady || !isAuthenticated || studentsLoading) {
    return <div className="rounded-[2rem] bg-white p-6 text-sm text-slate-600 shadow-sm">Carregando...</div>;
  }

  return (
    <main className="space-y-6">
      <Header title="Nova tarefa" subtitle="Cadastro manual de dever com aluno, disciplina e data de entrega." />
      <TaskForm students={students} subjects={subjects} />
    </main>
  );
}
