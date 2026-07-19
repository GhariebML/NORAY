"use client";

import { useState, useEffect } from "react";
import { ToastProvider } from "@/components/ui";
import { CommandPalette } from "@/components/CommandPalette";

import { ThemeProvider } from "next-themes";

export function ClientWrapper({ children }: { children: React.ReactNode }) {
  const [paletteOpen, setPaletteOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Catch Ctrl + K
      if (e.ctrlKey && e.key === "k") {
        e.preventDefault();
        setPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <ToastProvider>
        {children}
        <CommandPalette isOpen={paletteOpen} onClose={() => setPaletteOpen(false)} />
      </ToastProvider>
    </ThemeProvider>
  );
}
