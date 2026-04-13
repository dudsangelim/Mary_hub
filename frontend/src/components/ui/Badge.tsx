import type { PropsWithChildren } from "react";

import { getTaskStatusLabel } from "@/lib/labels";

const palette: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800",
  in_progress: "bg-sky-100 text-sky-800",
  done: "bg-emerald-100 text-emerald-800",
  overdue: "bg-rose-100 text-rose-800",
  default: "bg-slate-100 text-slate-700"
};

export function Badge({ children }: PropsWithChildren) {
  const value = String(children);
  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${palette[value] ?? palette.default}`}>{getTaskStatusLabel(value)}</span>;
}
