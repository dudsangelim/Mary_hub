"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { useAuth } from "@/hooks/useAuth";
import { apiFetch } from "@/lib/api";
import type { ClassifyPendingResult, DashboardSummary } from "@/lib/types";

export default function DashboardPage() {
  const { isReady, isAuthenticated } = useAuth(true);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [classifying, setClassifying] = useState(false);
  const [classifyResult, setClassifyResult] = useState<ClassifyPendingResult | null>(null);

  useEffect(() => {
    apiFetch<DashboardSummary>("/dashboard/summary").then(setSummary);
  }, []);

  async function handleClassifyPending() {
    setClassifying(true);
    setClassifyResult(null);
    try {
      const result = await apiFetch<ClassifyPendingResult>("/tasks/classify-pending", { method: "POST" });
      setClassifyResult(result);
    } finally {
      setClassifying(false);
    }
  }

  if (!isReady || !isAuthenticated) {
    return <div className="rounded-[2rem] bg-white p-6 text-sm text-slate-600 shadow-sm">Carregando...</div>;
  }

  return (
    <main className="space-y-6">
      <Header title="Dashboard" subtitle="Atalhos rápidos para registrar materiais, deveres e observações do dia." />
      <div className="flex flex-wrap items-center gap-3">
        <Button variant="secondary" onClick={handleClassifyPending} disabled={classifying}>
          {classifying ? "Classificando…" : "Classificar pendentes com IA"}
        </Button>
        {classifyResult ? (
          <p className="text-sm text-slate-600">
            {classifyResult.classified} de {classifyResult.total} classificadas
            {classifyResult.skipped > 0 ? ` · ${classifyResult.skipped} ignoradas` : ""}
          </p>
        ) : null}
      </div>
      {!summary || summary.students.length === 0 ? (
        <EmptyState title="Sem dados" description="Rode o seed e faça login para visualizar Lucas e Malu." href="/" cta="Voltar ao login" />
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {summary.students.map((student) => (
            <article key={student.student_id} className="rounded-[2rem] bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h3 className="text-2xl font-semibold text-slate-900">{student.student_name}</h3>
                  <p className="mt-1 text-sm text-slate-600">Resumo rápido por aluno</p>
                </div>
                <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
                  <Link href={`/tutor/${student.student_id}`} className="rounded-2xl bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600">
                    Iniciar Tutor
                  </Link>
                  <Link href={`/tasks?student_id=${student.student_id}`} className="rounded-2xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-200">
                    Ver tarefas
                  </Link>
                </div>
              </div>
              <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-3">
                <div className="rounded-2xl bg-amber-50 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-amber-700">Pendentes</p>
                  <p className="mt-2 text-3xl font-semibold text-amber-900">{student.pending}</p>
                </div>
                <div className="rounded-2xl bg-sky-50 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-sky-700">Em andamento</p>
                  <p className="mt-2 text-3xl font-semibold text-sky-900">{student.in_progress}</p>
                </div>
                <div className="rounded-2xl bg-rose-50 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-rose-700">Atrasadas</p>
                  <p className="mt-2 text-3xl font-semibold text-rose-900">{student.overdue}</p>
                </div>
                <div className="rounded-2xl bg-emerald-50 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-emerald-700">Concluídas</p>
                  <p className="mt-2 text-3xl font-semibold text-emerald-900">{student.done}</p>
                </div>
                <div className="rounded-2xl bg-slate-100 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-600">Materiais</p>
                  <p className="mt-2 text-3xl font-semibold text-slate-900">{student.materials_count}</p>
                </div>
                <div className="rounded-2xl bg-slate-100 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-600">Total</p>
                  <p className="mt-2 text-3xl font-semibold text-slate-900">{student.total_tasks}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
