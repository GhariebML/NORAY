import type { Metadata } from "next";
import { Sidebar } from "@/components/ui";
import { ClientWrapper } from "@/components/ClientWrapper";
import { WorkspaceTabs } from "@/components/WorkspaceTabs";
import { TaskManagerBar } from "@/components/TaskManagerBar";
import {
  Server,
  Zap,
  Cpu,
  User,
} from "lucide-react";
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
      <body className="min-h-full flex flex-col lg:flex-row bg-[#09090b] text-[#fafafa] selection:bg-emerald-500/30 selection:text-emerald-300" suppressHydrationWarning>
        <ClientWrapper>
          <Sidebar />
          <main className="flex-1 flex flex-col min-w-0 overflow-hidden bg-[#09090b]">
            
            {/* Enterprise Top Navigation bar */}
            <header className="h-14 border-b border-zinc-900 bg-zinc-950/70 backdrop-blur-md px-6 flex items-center justify-between shrink-0 select-none z-10">
              <div className="flex items-center gap-6 text-xs text-zinc-400">
                <div className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="font-semibold text-zinc-300 font-mono">NORAY OS</span>
                </div>
                
                <span className="text-zinc-800">|</span>
                
                <div className="hidden sm:flex items-center gap-1.5">
                  <Cpu size={12} className="text-emerald-400" />
                  <span>Model: <span className="font-mono text-zinc-200">llama3.1:8b</span></span>
                </div>

                <span className="hidden sm:inline text-zinc-800">|</span>

                <div className="hidden md:flex items-center gap-1.5">
                  <Zap size={12} className="text-emerald-400" />
                  <span>Latency: <span className="font-mono text-zinc-200">320ms</span></span>
                </div>

                <span className="hidden md:inline text-zinc-800">|</span>

                <div className="hidden lg:flex items-center gap-1.5">
                  <Server size={12} className="text-emerald-400" />
                  <span>Footprint: <span className="font-mono text-zinc-200">VRAM 3.4GB (12% CPU)</span></span>
                </div>
              </div>

              <div className="flex items-center gap-4 text-xs">
                {/* Active Provider indicator */}
                <div className="flex items-center gap-1.5 px-2 py-0.5 rounded border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 font-mono text-[10px]">
                  <span>HYBRID_ROUTER</span>
                </div>

                {/* Profile Widget */}
                <div className="flex items-center gap-2 pl-2 border-l border-zinc-900">
                  <div className="h-6 w-6 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400">
                    <User size={12} />
                  </div>
                  <span className="hidden lg:inline text-zinc-300 font-medium">Gharieb Mohamed</span>
                </div>
              </div>
            </header>

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
