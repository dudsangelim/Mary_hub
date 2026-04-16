"use client";

import { ButtonHTMLAttributes } from "react";

interface BigButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  variant?: "primary" | "success" | "secondary";
}

const VARIANTS = {
  primary: "bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white",
  success: "bg-green-500 hover:bg-green-600 active:bg-green-700 text-white",
  secondary: "bg-gray-200 hover:bg-gray-300 active:bg-gray-400 text-gray-800",
};

export default function BigButton({ label, variant = "primary", className = "", ...props }: BigButtonProps) {
  return (
    <button
      className={`w-full rounded-2xl py-6 text-2xl font-bold shadow-md transition-all active:scale-95 ${VARIANTS[variant]} ${className}`}
      {...props}
    >
      {label}
    </button>
  );
}
