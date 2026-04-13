"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/today", label: "Hoje" },
  { href: "/students", label: "Alunos" },
  { href: "/materials", label: "Materiais" },
  { href: "/tasks", label: "Tarefas" },
  { href: "/integrations", label: "Integrações" }
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 rounded-[2rem] bg-slate-950 p-6 text-white lg:block">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-emerald-300">Mary</p>
        <h1 className="mt-2 text-2xl font-semibold">Education Hub</h1>
      </div>
      <nav className="mt-8 space-y-2">
        {items.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`block rounded-2xl px-4 py-3 text-sm ${pathname === item.href ? "bg-white/15" : "text-slate-300 hover:bg-white/10"}`}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
