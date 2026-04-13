"use client";

import { useRouter, useSearchParams } from "next/navigation";

import { StudentFilter } from "@/components/filters/StudentFilter";
import { SubjectFilter } from "@/components/filters/SubjectFilter";
import { Header } from "@/components/layout/Header";
import { MaterialList } from "@/components/materials/MaterialList";
import { useAuth } from "@/hooks/useAuth";
import { useMaterials } from "@/hooks/useMaterials";
import { useStudents } from "@/hooks/useStudents";
import { useSubjects } from "@/hooks/useSubjects";

export default function MaterialsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isReady, isAuthenticated } = useAuth(true);
  const { students } = useStudents();
  const studentId = searchParams.get("student_id") ?? "";
  const subjectId = searchParams.get("subject_id") ?? "";
  const { subjects } = useSubjects(students, studentId);
  const params = new URLSearchParams(searchParams.toString());
  const query = params.toString() ? `?${params.toString()}` : "";
  const { data, loading } = useMaterials(query);

  function updateParam(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    router.push(`/materials${params.toString() ? `?${params.toString()}` : ""}`);
  }

  if (!isReady || !isAuthenticated) {
    return <div className="rounded-[2rem] bg-white p-6 text-sm text-slate-600 shadow-sm">Carregando...</div>;
  }

  return (
    <main className="space-y-6">
      <Header title="Materiais" subtitle="Upload manual de foto, PDF e texto com filtros persistentes na URL." />
      <div className="grid gap-3 rounded-[2rem] bg-white p-4 shadow-sm">
        <StudentFilter students={students} value={studentId} onChange={(value) => updateParam("student_id", value)} />
        <SubjectFilter students={students} subjects={subjects} studentId={studentId} value={subjectId} onChange={(value) => updateParam("subject_id", value)} />
      </div>
      {loading ? <div className="rounded-[2rem] bg-white p-6 text-sm text-slate-600 shadow-sm">Carregando materiais...</div> : <MaterialList materials={data?.items ?? []} students={students} subjects={subjects} />}
    </main>
  );
}
