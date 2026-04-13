"use client";

import { Header } from "@/components/layout/Header";
import { StudentCard } from "@/components/students/StudentCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { useAuth } from "@/hooks/useAuth";
import { useStudents } from "@/hooks/useStudents";

export default function StudentsPage() {
  const { isReady, isAuthenticated } = useAuth(true);
  const { students, loading } = useStudents();

  if (!isReady || !isAuthenticated) {
    return <div className="rounded-[2rem] bg-white p-6 text-sm text-slate-600 shadow-sm">Carregando...</div>;
  }

  return (
    <main className="space-y-6">
      <Header title="Alunos" subtitle="Perfis, rotinas e resumo rápido por aluno." />
      {loading ? (
        <div className="rounded-[2rem] bg-white p-6 text-sm text-slate-600 shadow-sm">Carregando alunos...</div>
      ) : students.length === 0 ? (
        <EmptyState title="Sem alunos" description="O seed ainda não foi aplicado." href="/" cta="Voltar" />
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {students.map((student) => (
            <StudentCard key={student.id} student={student} />
          ))}
        </div>
      )}
    </main>
  );
}
