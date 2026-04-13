import type { Material, Student, Subject } from "@/lib/types";

export function MaterialCard({ material, students, subjects }: { material: Material; students: Student[]; subjects: Subject[] }) {
  const student = students.find((item) => item.id === material.student_id);
  const subject = subjects.find((item) => item.id === material.subject_id);
  const sourceLabel = material.source === "plurall_library" ? "Biblioteca Plurall" : material.source === "manual_upload" ? "Upload manual" : material.source;

  return (
    <article className="rounded-[2rem] bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{material.title}</h3>
          <p className="text-sm text-slate-600">
            {student?.name ?? "Aluno"} · {subject?.name ?? "Sem disciplina"}
          </p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase text-slate-700">{material.material_type}</span>
      </div>
      <p className="mt-4 text-sm text-slate-700">{material.description || material.text_content || "Sem descrição"}</p>
      <p className="mt-3 text-xs text-slate-500">Fonte: {sourceLabel}</p>
      {material.tags.length ? <p className="mt-1 text-xs text-slate-500">Tags: {material.tags.join(", ")}</p> : null}
      {material.file_name ? <p className="mt-3 text-xs text-slate-500">Arquivo: {material.file_name}</p> : null}
    </article>
  );
}
