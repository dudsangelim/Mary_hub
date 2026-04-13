"use client";

import { Select } from "@/components/ui/Select";
import type { Student, Subject } from "@/lib/types";

export function SubjectFilter({
  students,
  subjects,
  studentId,
  value,
  onChange
}: {
  students: Student[];
  subjects: Subject[];
  studentId: string;
  value: string;
  onChange: (value: string) => void;
}) {
  const student = students.find((item) => item.id === studentId);
  const options = student ? subjects.filter((item) => item.grade === student.grade) : subjects;

  return (
    <Select value={value} onChange={(event) => onChange(event.target.value)}>
      <option value="">Todas as disciplinas</option>
      {options.map((subject) => (
        <option key={subject.id} value={subject.id}>
          {subject.name}
        </option>
      ))}
    </Select>
  );
}
