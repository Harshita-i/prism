import type { Metadata } from "next";
import "./globals.css";
import { PrismProvider } from "@/components/workspace/PrismProvider";
import { WorkspaceShell } from "@/components/workspace/WorkspaceShell";

export const metadata: Metadata = {
  title: "Prism | Decision Intelligence",
  description: "Enterprise decision intelligence workspace.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <PrismProvider>
          <WorkspaceShell>{children}</WorkspaceShell>
        </PrismProvider>
      </body>
    </html>
  );
}
