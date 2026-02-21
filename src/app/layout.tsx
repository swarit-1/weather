import type { Metadata } from "next";
import { Inter, IBM_Plex_Sans } from "next/font/google";
<<<<<<< HEAD
import Script from "next/script";
=======
>>>>>>> origin/main
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
<<<<<<< HEAD
      <head>
        <Script
          id="crypto-randomuuid-polyfill"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              (function () {
                var g = typeof globalThis !== "undefined" ? globalThis : window;
                if (!g) return;
                var c = g.crypto;
                if (!c) return;
                if (typeof c.randomUUID === "function") return;

                var uuid = function () {
                  if (typeof c.getRandomValues === "function") {
                    var bytes = new Uint8Array(16);
                    c.getRandomValues(bytes);
                    bytes[6] = (bytes[6] & 15) | 64;
                    bytes[8] = (bytes[8] & 63) | 128;
                    var hex = Array.prototype.map.call(bytes, function (b) {
                      return b.toString(16).padStart(2, "0");
                    });
                    return (
                      hex.slice(0, 4).join("") + "-" +
                      hex.slice(4, 6).join("") + "-" +
                      hex.slice(6, 8).join("") + "-" +
                      hex.slice(8, 10).join("") + "-" +
                      hex.slice(10, 16).join("")
                    );
                  }
                  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (ch) {
                    var r = Math.random() * 16 | 0;
                    var v = ch === "x" ? r : (r & 3) | 8;
                    return v.toString(16);
                  });
                };

                try {
                  Object.defineProperty(c, "randomUUID", { value: uuid, configurable: true });
                } catch (_e) {
                  c.randomUUID = uuid;
                }
              })();
            `,
          }}
        />
      </head>
=======
>>>>>>> origin/main
      <body>
        <StoreProvider>{children}</StoreProvider>
      </body>
    </html>
  );
}
