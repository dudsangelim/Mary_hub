import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type Props = PropsWithChildren<ButtonHTMLAttributes<HTMLButtonElement>> & {
  variant?: "primary" | "secondary" | "danger";
};

const styles = {
  primary: "bg-slate-900 text-white hover:bg-slate-800",
  secondary: "bg-white text-slate-900 border border-slate-200 hover:bg-slate-50",
  danger: "bg-red-600 text-white hover:bg-red-500"
};

export function Button({ children, className = "", variant = "primary", ...props }: Props) {
  return (
    <button
      className={`rounded-2xl px-4 py-2 text-sm font-semibold transition ${styles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
