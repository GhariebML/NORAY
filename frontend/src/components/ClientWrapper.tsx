"use client";

import { useState, useEffect } from "react";
import { ToastProvider } from "@/components/ui";
import { CommandPalette } from "@/components/CommandPalette";
import { GlobalKnowledgeFAB } from "@/components/GlobalKnowledgeFAB";
import { KnowledgeDrawer } from "@/components/KnowledgeDrawer";
import { ThemeProvider } from "next-themes";
import { useRouter } from "next/navigation";

export function ClientWrapper({ children }: { children: React.ReactNode }) {
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [knowledgeDrawerOpen, setKnowledgeDrawerOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Catch Ctrl + K
      if (e.ctrlKey && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((prev) => !prev);
      }

      // Catch Alt + K (or Option + K on Mac)
      if (e.altKey && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setKnowledgeDrawerOpen((prev) => !prev);
      }

      // Quick shortcut navigation: Ctrl+Shift+Keys
      if (e.ctrlKey && e.shiftKey) {
        const key = e.key.toUpperCase();
        if (key === "J") {
          e.preventDefault();
          router.push("/jobs");
        } else if (key === "R") {
          e.preventDefault();
          router.push("/workspace");
        } else if (key === "D") {
          e.preventDefault();
          router.push("/documents");
        } else if (key === "M") {
          e.preventDefault();
          router.push("/memory");
        } else if (key === "A") {
          e.preventDefault();
          router.push("/command-center");
        } else if (key === "P") {
          e.preventDefault();
          router.push("/profile");
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [router]);

  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <ToastProvider>
        {children}
        <GlobalKnowledgeFAB onClick={() => setKnowledgeDrawerOpen(true)} />
        <KnowledgeDrawer isOpen={knowledgeDrawerOpen} onClose={() => setKnowledgeDrawerOpen(false)} />
        <CommandPalette isOpen={paletteOpen} onClose={() => setPaletteOpen(false)} />
      </ToastProvider>
    </ThemeProvider>
  );
}
