"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { apiFetch } from "@/lib/api";
import { setTokens } from "@/lib/auth";
import type { AuthPayload } from "@/lib/types";

export default function HomePage() {
  const router = useRouter();
  const [email, setEmail] = useState("eduardo@mary.local");
  const [password, setPassword] = useState("mary2026");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const auth = await apiFetch<AuthPayload>("/auth/login", {
        method: "POST",
        auth: false,
        body: JSON.stringify({ email, password })
      });
      setTokens(auth.tokens.access_token, auth.tokens.refresh_token);
      router.push("/dashboard");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="grid w-full max-w-5xl gap-8 rounded-[2.5rem] bg-white p-6 shadow-xl lg:grid-cols-[1.2fr_0.8fr] lg:p-10">
        <section className="rounded-[2rem] bg-slate-950 p-8 text-white">
          <p className="text-xs uppercase tracking-[0.3em] text-emerald-300">Mary Education Hub</p>
          <h1 className="mt-4 text-4xl font-semibold leading-tight">Organização escolar manual, centrada na família, pronta para uso.</h1>
          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl bg-white/10 p-4 text-sm">Lucas e Malu com acompanhamento por aluno.</div>
            <div className="rounded-2xl bg-white/10 p-4 text-sm">Tarefas, materiais e visão do dia.</div>
            <div className="rounded-2xl bg-white/10 p-4 text-sm">Sem IA, sem integrações externas, só o MVP funcional.</div>
          </div>
        </section>
        <section className="rounded-[2rem] border border-slate-200 p-8">
          <h2 className="text-2xl font-semibold text-slate-900">Entrar</h2>
          <p className="mt-2 text-sm text-slate-600">Use a conta seed do PRD para acessar o painel.</p>
          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <Input placeholder="Email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
            <Input placeholder="Senha" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            {error ? <p className="text-sm text-red-600">{error}</p> : null}
            <Button className="w-full" disabled={loading}>
              {loading ? "Entrando..." : "Entrar"}
            </Button>
          </form>
        </section>
      </div>
    </main>
  );
}
