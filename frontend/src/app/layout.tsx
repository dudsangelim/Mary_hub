import type { Metadata } from "next";

import "@/app/globals.css";
import SWRegistrar from "@/components/SWRegistrar";

export const metadata: Metadata = {
  title: "Mary Education Hub",
  description: "Hub escolar familiar para Lucas e Malu",
  manifest: "/manifest.json",
  themeColor: "#3b82f6",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#3b82f6" />
        <link rel="apple-touch-icon" href="/icons/icon-192.png" />
      </head>
      <body>
        <SWRegistrar />
        {children}
      </body>
    </html>
  );
}
