"use client";

import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "@/lib/api";
import type { Student, Subject } from "@/lib/types";

export function useSubjects(students: Student[], studentId = "") {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const grades = useMemo(() => {
    if (studentId) {
      const student = students.find((item) => item.id === studentId);
      return student ? [student.grade] : [];
    }

    return [...new Set(students.map((student) => student.grade))];
  }, [studentId, students]);

  useEffect(() => {
    let cancelled = false;

    async function loadSubjects() {
      if (grades.length === 0) {
        setSubjects([]);
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const responses = await Promise.all(grades.map((grade) => apiFetch<Subject[]>(`/subjects?grade=${grade}`)));
        const merged = responses.flat().sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));

        if (!cancelled) {
          setSubjects(merged);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Erro ao carregar disciplinas");
          setSubjects([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadSubjects();

    return () => {
      cancelled = true;
    };
  }, [grades]);

  return { subjects, loading, error };
}
