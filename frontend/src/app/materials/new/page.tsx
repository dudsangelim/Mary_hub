"use client";

import { Header } from "@/components/layout/Header";
import { UploadForm } from "@/components/materials/UploadForm";
import { useAuth } from "@/hooks/useAuth";
import { useStudents } from "@/hooks/useStudents";
import { useSubjects } from "@/hooks/useSubjects";

export default function NewMaterialPage() {
  const { isReady, isAuthenticated } = useAuth(true);
  const { students, loading: studentsLoading } = useStudents();
  const { subjects } = useSubjects(students);

  if (!isReady || !isAuthenticated || studentsLoading) {
    return <div className="rounded-[2rem] bg-white p-6 text-sm text-slate-600 shadow-sm">Carregando...</div>;
  }

  return (
    <main className="space-y-6">
      <Header title="Novo material" subtitle="Texto puro, observação do dia ou upload de foto/PDF." />
      <UploadForm students={students} subjects={subjects} />
    </main>
  );
}
