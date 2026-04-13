"use client";

import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";

export function Header({ title, subtitle }: { title: string; subtitle: string }) {
  const router = useRouter();
  const { logout } = useAuth();

  return (
    <header className="rounded-[2rem] bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-slate-500">Mary Education Hub</p>
          <h2 className="mt-1 text-3xl font-semibold text-slate-900">{title}</h2>
          <p className="mt-1 text-sm text-slate-600">{subtitle}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => router.push("/tasks/new")}>
            + Dever
          </Button>
          <Button variant="secondary" onClick={() => router.push("/materials/new?mode=file")}>
            + Material (foto)
          </Button>
          <Button variant="secondary" onClick={() => router.push("/materials/new?mode=text&source=guardian_note")}>
            Observação do dia
          </Button>
          <Button variant="danger" onClick={logout}>
            Sair
          </Button>
        </div>
      </div>
    </header>
  );
}
