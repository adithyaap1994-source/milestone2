import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "Mutual Fund FAQ Assistant",
  description: "Phase 2 dark mode testing frontend"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
