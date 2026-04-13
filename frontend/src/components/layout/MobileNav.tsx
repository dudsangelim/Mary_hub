"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { href: "/dashboard", label: "Painel" },
  { href: "/students", label: "Alunos" },
  { href: "/materials", label: "Materiais" },
  { href: "/tasks", label: "Tarefas" },
  { href: "/integrations", label: "Integrações" }
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-20 border-t border-slate-200 bg-white/95 px-4 py-3 lg:hidden">
      <div className="grid grid-cols-5 gap-2">
        {items.map((item) => (
          <Link key={item.href} href={item.href} className={`rounded-2xl px-3 py-2 text-center text-xs font-semibold ${pathname === item.href ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"}`}>
            {item.label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
