"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { FileUpload } from "@/components/ui/FileUpload";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { apiFetch } from "@/lib/api";
import type { Student, Subject } from "@/lib/types";

export function UploadForm({ students, subjects }: { students: Student[]; subjects: Subject[] }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const mode = searchParams.get("mode") ?? "text";
  const source = searchParams.get("source") ?? "manual_upload";
  const [studentId, setStudentId] = useState(searchParams.get("student_id") ?? students[0]?.id ?? "");
  const [subjectId, setSubjectId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [textContent, setTextContent] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);

  const student = students.find((item) => item.id === studentId);
  const subjectOptions = subjects.filter((item) => item.grade === student?.grade);

  useEffect(() => {
    if (!studentId && students.length > 0) {
      setStudentId(searchParams.get("student_id") ?? students[0].id);
    }
  }, [searchParams, studentId, students]);

  useEffect(() => {
    if (subjectId && !subjectOptions.some((subject) => subject.id === subjectId)) {
      setSubjectId("");
    }
  }, [subjectId, subjectOptions]);

  async function handleSubmit() {
    setSaving(true);
    try {
      if (mode === "file" && file) {
        const form = new FormData();
        form.append("file", file);
        form.append("student_id", studentId);
        form.append("title", title);
        if (subjectId) form.append("subject_id", subjectId);
        if (description) form.append("description", description);
        await apiFetch("/materials/upload", { method: "POST", body: form });
      } else {
        await apiFetch("/materials", {
          method: "POST",
          body: JSON.stringify({
            student_id: studentId,
            title,
            description,
            subject_id: subjectId || null,
            material_type: source === "guardian_note" ? "text" : "text",
            text_content: textContent,
            source
          })
        });
      }
      router.push("/materials");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4 rounded-[2rem] bg-white p-6 shadow-sm">
      <div className="grid gap-4 md:grid-cols-2">
        <Select value={studentId} onChange={(event) => setStudentId(event.target.value)}>
          {!studentId ? <option value="">Selecione o aluno</option> : null}
          {students.map((student) => (
            <option key={student.id} value={student.id}>
              {student.name}
            </option>
          ))}
        </Select>
        <Select value={subjectId} onChange={(event) => setSubjectId(event.target.value)}>
          <option value="">Sem disciplina</option>
          {subjectOptions.map((subject) => (
            <option key={subject.id} value={subject.id}>
              {subject.name}
            </option>
          ))}
        </Select>
      </div>
      <Input placeholder="Título do material" value={title} onChange={(event) => setTitle(event.target.value)} />
      <Input placeholder="Descrição curta" value={description} onChange={(event) => setDescription(event.target.value)} />
      {mode === "file" ? (
        <FileUpload file={file} onChange={setFile} />
      ) : (
        <textarea
          className="min-h-40 w-full rounded-3xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-slate-400"
          placeholder={source === "guardian_note" ? "Observação do dia" : "Conteúdo do material"}
          value={textContent}
          onChange={(event) => setTextContent(event.target.value)}
        />
      )}
      <Button onClick={handleSubmit} disabled={saving || !studentId || !title || (mode === "file" ? !file : !textContent)}>
        {saving ? "Salvando..." : "Salvar material"}
      </Button>
    </div>
  );
}
