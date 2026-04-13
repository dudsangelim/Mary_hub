"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import type { Material, PaginatedResponse } from "@/lib/types";

export function useMaterials(query = "") {
  const [data, setData] = useState<PaginatedResponse<Material> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    apiFetch<PaginatedResponse<Material>>(`/materials${query}`)
      .then(setData)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [query]);

  return { data, loading, error };
}
