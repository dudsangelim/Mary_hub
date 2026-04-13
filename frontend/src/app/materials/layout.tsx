"use client";

import { MobileNav } from "@/components/layout/MobileNav";
import { Sidebar } from "@/components/layout/Sidebar";
import { useAuth } from "@/hooks/useAuth";

export default function MaterialsLayout({ children }: { children: React.ReactNode }) {
  const { isReady, isAuthenticated } = useAuth(true);

  if (!isReady || !isAuthenticated) {
    return <div className="p-10 text-center text-sm text-slate-600">Carregando...</div>;
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-7xl gap-6 px-4 py-4 pb-24 lg:px-6 lg:py-6">
      <Sidebar />
      <div className="flex-1">{children}</div>
      <MobileNav />
    </div>
  );
}
