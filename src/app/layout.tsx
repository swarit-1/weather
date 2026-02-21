import type { Metadata } from "next";
import { Inter, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";
import { StoreProvider } from "@/lib/store";

const headingFont = Inter({ subsets: ["latin"], weight: ["500", "600", "700"], variable: "--font-heading" });
const bodyFont = IBM_Plex_Sans({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-body" });

export const metadata: Metadata = {
  metadataBase: new URL("http://localhost:3000"),
  title: "AI Grid Operations Copilot",
  description:
    "Autonomous grid operations intelligence for live weather monitoring, deterministic risk scoring, and multi-agent playbook generation.",
  icons: {
    icon: "/favicon.svg",
  },
  openGraph: {
    title: "AI Grid Operations Copilot",
    description:
      "Autonomous grid operations intelligence for live weather monitoring, deterministic risk scoring, and multi-agent playbook generation.",
    type: "website",
    url: "/",
    images: [
      {
        url: "/og/ai-grid-copilot.svg",
        width: 1200,
        height: 630,
        alt: "AI Grid Operations Copilot terminal view",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "AI Grid Operations Copilot",
    description:
      "Autonomous grid operations intelligence for live weather monitoring, deterministic risk scoring, and multi-agent playbook generation.",
    images: ["/og/ai-grid-copilot.svg"],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${headingFont.variable} ${bodyFont.variable}`}>
      <body>
        <StoreProvider>{children}</StoreProvider>
      </body>
    </html>
  );
}
