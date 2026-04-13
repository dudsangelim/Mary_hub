"use client";

import { useEffect, useState } from "react";

import { Header } from "@/components/layout/Header";
import { useAuth } from "@/hooks/useAuth";
import { apiFetch } from "@/lib/api";
import type { Student } from "@/lib/types";

export default function StudentDetailPage({ params }: { params: { id: string } }) {
  const { isReady, isAuthenticated } = useAuth(true);
  const [student, setStudent] = useState<Student | null>(null);

  useEffect(() => {
    apiFetch<Student>(`/students/${params.id}`).then(setStudent);
  }, [params.id]);

  if (!isReady || !isAuthenticated || !student) {
    return <div className="rounded-[2rem] bg-white p-6 text-sm text-slate-600 shadow-sm">Carregando aluno...</div>;
  }

  return (
    <main className="space-y-6">
      <Header title={student.name} subtitle={student.grade_label} />
      <div className="grid gap-4 xl:grid-cols-2">
        <section className="rounded-[2rem] bg-white p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900">Perfil de estudo</h3>
          <dl className="mt-4 space-y-3 text-sm text-slate-700">
            <div>
              <dt className="font-semibold">Melhor período</dt>
              <dd>{student.profile?.best_study_time ?? "Não definido"}</dd>
            </div>
            <div>
              <dt className="font-semibold">Atenção</dt>
              <dd>{student.profile?.attention_span_minutes ?? "-"} minutos</dd>
            </div>
            <div>
              <dt className="font-semibold">Notas</dt>
              <dd>{student.profile?.notes ?? "Sem notas"}</dd>
            </div>
          </dl>
        </section>
        <section className="rounded-[2rem] bg-white p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900">Interesses</h3>
          <div className="mt-4 flex flex-wrap gap-2">
            {(student.interests?.interests ?? []).length > 0 ? (
              student.interests?.interests.map((interest) => (
                <span key={interest} className="rounded-full bg-slate-100 px-3 py-2 text-sm text-slate-700">
                  {interest}
                </span>
              ))
            ) : (
              <p className="text-sm text-slate-600">Perfil de interesses ainda vazio.</p>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
