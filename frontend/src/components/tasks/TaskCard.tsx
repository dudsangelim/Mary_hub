import type { Student, Subject, Task } from "@/lib/types";

import { Badge } from "@/components/ui/Badge";
import { getTaskPriorityLabel, getTaskStatusLabel } from "@/lib/labels";

export function TaskCard({ task, students, subjects, onStatusChange }: { task: Task; students: Student[]; subjects: Subject[]; onStatusChange?: (task: Task, status: string) => void }) {
  const student = students.find((item) => item.id === task.student_id);
  const subject = subjects.find((item) => item.id === task.subject_id);

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
      {onStatusChange ? (
        <div className="mt-4 flex gap-2">
          {["pending", "in_progress", "done"].map((status) => (
            <button key={status} className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700" onClick={() => onStatusChange(task, status)}>
              {getTaskStatusLabel(status)}
            </button>
          ))}
        </div>
      ) : null}
    </article>
  );
}
