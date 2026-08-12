import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Clip Factory",
  description: "Colle une vidéo, récupère tes clips verticaux.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
