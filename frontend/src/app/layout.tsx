import type { Metadata } from "next";
import { Sidebar } from "@/components/ui";
import { ClientWrapper } from "@/components/ClientWrapper";
import "./globals.css";

export const metadata: Metadata = {
  title: "NORAY — AI Career OS",
  description: "AI-powered career operating system for jobs, scholarships, and professional growth",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className="h-full antialiased"
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col lg:flex-row" suppressHydrationWarning>
        <ClientWrapper>
          <Sidebar />
          <main className="flex-1 overflow-auto">
            <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
              {children}
            </div>
          </main>
        </ClientWrapper>
      </body>
    </html>
  );
}
