import type { Metadata } from "next";
import { Sidebar } from "@/components/ui";
import { ClientWrapper } from "@/components/ClientWrapper";
import { WorkspaceTabs } from "@/components/WorkspaceTabs";
import { TaskManagerBar } from "@/components/TaskManagerBar";
import "./globals.css";

export const metadata: Metadata = {
  title: "NORAY — AI Operating System",
  description: "Enterprise-grade AI Operating System for careers, academic scholarships, and automated document engineering",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className="h-full antialiased dark"
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col lg:flex-row bg-[#060911] text-[#f8fafc] selection:bg-emerald-500/30 selection:text-emerald-300" suppressHydrationWarning>
        <ClientWrapper>
          <Sidebar />
          <main className="flex-1 flex flex-col min-w-0 overflow-hidden bg-[#060911]">
            <WorkspaceTabs />
            <div className="flex-1 overflow-auto px-4 py-6 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
              {children}
            </div>
            <TaskManagerBar />
          </main>
        </ClientWrapper>
      </body>
    </html>
  );
}
