"use client";

import { useState } from "react";

import type { ClassificationResult, Student, Subject, Task } from "@/lib/types";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { getTaskPriorityLabel, getTaskStatusLabel } from "@/lib/labels";
import { apiFetch } from "@/lib/api";

const _DIFFICULTY_LABEL: Record<string, string> = {
  easy: "fácil",
  normal: "normal",
  hard: "difícil",
};

export function TaskCard({
  task,
  students,
  subjects,
  onStatusChange,
}: {
  task: Task;
  students: Student[];
  subjects: Subject[];
  onStatusChange?: (task: Task, status: string) => void;
}) {
  const student = students.find((item) => item.id === task.student_id);
  const subject = subjects.find((item) => item.id === task.subject_id);
  const [classifying, setClassifying] = useState(false);
  const [classification, setClassification] = useState<ClassificationResult | null>(null);
  const [classifyError, setClassifyError] = useState<string | null>(null);

  async function handleClassify() {
    setClassifying(true);
    setClassifyError(null);
    try {
      const result = await apiFetch<ClassificationResult>(`/tasks/${task.id}/classify`, { method: "POST" });
      setClassification(result);
    } catch (err) {
      setClassifyError(err instanceof Error ? err.message : "Erro ao classificar");
    } finally {
      setClassifying(false);
    }
  }

  const hasClassification = classification?.ok && (classification.difficulty_assessed || classification.curriculum_item_id);

  return (
    <article className="rounded-[2rem] bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{task.title}</h3>
          <p className="text-sm text-slate-600">
            {student?.name ?? "Aluno"} · {subject?.name ?? "Sem disciplina"}
          </p>
        </div>
        <Badge>{task.status}</Badge>
      </div>
      <p className="mt-3 text-sm text-slate-700">{task.parent_notes || task.description || "Sem observações."}</p>

      <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-500">
        <span>Entrega: {task.due_date ?? "sem data"}</span>
        <span>Prioridade: {getTaskPriorityLabel(task.priority)}</span>
      </div>

      {hasClassification ? (
        <div className="mt-3 rounded-2xl bg-violet-50 px-3 py-2 text-xs text-violet-700">
          <span className="font-semibold">IA:</span>{" "}
          {classification.difficulty_assessed ? _DIFFICULTY_LABEL[classification.difficulty_assessed] ?? classification.difficulty_assessed : ""}
          {classification.estimated_duration ? ` · ~${classification.estimated_duration} min` : ""}
          {classification.classification_confidence != null ? ` · confiança ${Math.round(classification.classification_confidence * 100)}%` : ""}
          {classification.reasoning ? <span className="mt-1 block text-violet-600">{classification.reasoning}</span> : null}
        </div>
      ) : null}

      {classifyError ? (
        <p className="mt-2 text-xs text-red-600">{classifyError}</p>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2">
        {onStatusChange
          ? ["pending", "in_progress", "done"].map((s) => (
              <button key={s} className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700" onClick={() => onStatusChange(task, s)}>
                {getTaskStatusLabel(s)}
              </button>
            ))
          : null}
        {!hasClassification ? (
          <Button variant="secondary" onClick={handleClassify} disabled={classifying}>
            {classifying ? "Classificando…" : "Classificar IA"}
          </Button>
        ) : null}
      </div>
    </article>
  );
}
