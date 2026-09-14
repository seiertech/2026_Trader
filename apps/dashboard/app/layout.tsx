import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Trading Command",
  description:
    "Human Control Plane — evidence-driven market intelligence & edge validation (TC-SPEC-001 v1.3).",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          fontFamily:
            "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
          background: "#0b0e14",
          color: "#d7dce5",
        }}
      >
        {children}
      </body>
    </html>
  );
}
