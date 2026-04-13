"use client";

import type { Student } from "@/lib/types";

export function StudentSelector({
  students,
  value,
  onChange
}: {
  students: Student[];
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1">
      <button className={`rounded-full px-4 py-2 text-sm font-semibold ${value === "" ? "bg-slate-900 text-white" : "bg-white text-slate-700"}`} onClick={() => onChange("")}>
        Todos
      </button>
      {students.map((student) => (
        <button
          key={student.id}
          className={`rounded-full px-4 py-2 text-sm font-semibold ${value === student.id ? "text-white" : "bg-white text-slate-700"}`}
          style={{ backgroundColor: value === student.id ? student.avatar_color : undefined }}
          onClick={() => onChange(student.id)}
        >
          {student.name}
        </button>
      ))}
    </div>
  );
}
