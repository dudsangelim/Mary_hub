"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import type { Student } from "@/lib/types";

export function useStudents() {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Student[]>("/students")
      .then(setStudents)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return { students, loading, error };
}
