import { getAccessToken } from "@/lib/auth";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "/api/v1").replace(/\/$/, "");

type RequestOptions = RequestInit & {
  auth?: boolean;
};

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", options.body instanceof FormData ? "" : "application/json");

  if (options.auth !== false) {
    const token = getAccessToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  if (options.body instanceof FormData) {
    headers.delete("Content-Type");
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    let message = "Erro inesperado";
    try {
      const payload = await response.json();
      message = payload.error?.message ?? message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
