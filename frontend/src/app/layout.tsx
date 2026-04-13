import type { Metadata } from "next";

import "@/app/globals.css";

export const metadata: Metadata = {
  title: "Mary Education Hub",
  description: "Hub escolar familiar para Lucas e Malu"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
