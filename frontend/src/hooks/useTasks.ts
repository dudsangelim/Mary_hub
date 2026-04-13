"use client";

import { Dispatch, SetStateAction, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import type { PaginatedResponse, Task } from "@/lib/types";

export function useTasks(query = "") {
  const [data, setData] = useState<PaginatedResponse<Task> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    apiFetch<PaginatedResponse<Task>>(`/tasks${query}`)
      .then(setData)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [query]);

  return { data, loading, error, setData: setData as Dispatch<SetStateAction<PaginatedResponse<Task> | null>> };
}
