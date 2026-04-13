"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { apiFetch } from "@/lib/api";
import type { Student, Subject } from "@/lib/types";

export function TaskForm({ students, subjects }: { students: Student[]; subjects: Subject[] }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [studentId, setStudentId] = useState(searchParams.get("student_id") ?? students[0]?.id ?? "");
  const [subjectId, setSubjectId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [parentNotes, setParentNotes] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [priority, setPriority] = useState("normal");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await apiFetch("/tasks", {
        method: "POST",
        body: JSON.stringify({
          student_id: studentId,
          title,
          description,
          subject_id: subjectId || null,
          due_date: dueDate || null,
          priority,
          parent_notes: parentNotes
        })
      });
      router.push(`/tasks?student_id=${studentId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar tarefa");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="space-y-4 rounded-[2rem] bg-white p-6 shadow-sm" onSubmit={handleSubmit}>
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
      <Input placeholder="Título da tarefa" value={title} onChange={(event) => setTitle(event.target.value)} />
      <Input type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} />
      <Select value={priority} onChange={(event) => setPriority(event.target.value)}>
        <option value="low">Baixa</option>
        <option value="normal">Normal</option>
        <option value="high">Alta</option>
        <option value="urgent">Urgente</option>
      </Select>
      <textarea
        className="min-h-32 w-full rounded-3xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-slate-400"
        placeholder="Descrição"
        value={description}
        onChange={(event) => setDescription(event.target.value)}
      />
      <textarea
        className="min-h-24 w-full rounded-3xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-slate-400"
        placeholder="Observações dos responsáveis"
        value={parentNotes}
        onChange={(event) => setParentNotes(event.target.value)}
      />
      {error ? <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}
      <Button type="submit" disabled={saving || !studentId || !title}>
        {saving ? "Salvando..." : "Salvar tarefa"}
      </Button>
    </form>
  );
}
