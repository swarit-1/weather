import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "StormOps Console",
  description: "Live weather detection and risk for Austin area",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
