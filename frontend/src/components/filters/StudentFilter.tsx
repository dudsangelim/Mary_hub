"use client";

import type { Student } from "@/lib/types";
import { StudentSelector } from "@/components/students/StudentSelector";

export function StudentFilter({ students, value, onChange }: { students: Student[]; value: string; onChange: (value: string) => void }) {
  return <StudentSelector students={students} value={value} onChange={onChange} />;
}
