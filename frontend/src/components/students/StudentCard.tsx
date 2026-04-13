import Link from "next/link";

import type { Student } from "@/lib/types";

export function StudentCard({ student }: { student: Student }) {
  return (
    <Link href={`/students/${student.id}`} className="rounded-[2rem] bg-white p-5 shadow-sm transition hover:-translate-y-0.5">
      <div className="flex items-center gap-4">
        <div className="h-12 w-12 rounded-2xl" style={{ backgroundColor: student.avatar_color }} />
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{student.name}</h3>
          <p className="text-sm text-slate-600">{student.grade_label}</p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-slate-600">
        <div className="rounded-2xl bg-slate-50 p-3">Foco: {student.profile?.best_study_time ?? "a definir"}</div>
        <div className="rounded-2xl bg-slate-50 p-3">Atenção: {student.profile?.attention_span_minutes ?? "-"} min</div>
      </div>
    </Link>
  );
}
