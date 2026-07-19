/**
 * NORAY — Reusable Premium UI & Motion Components
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  User,
  Briefcase,
  GraduationCap,
  ClipboardList,
  FileText,
  TrendingUp,
  Menu,
  X,
  Sun,
  Moon,
  Monitor,
  Activity,
  ChevronLeft,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import { useState, useEffect, useCallback, createContext, useContext } from "react";
import { motion, AnimatePresence, LayoutGroup } from "framer-motion";
import { useTheme } from "next-themes";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/workspace", label: "AI Workspace", icon: MessageSquareComponent },
  { href: "/profile", label: "Profile", icon: User },
  { href: "/jobs", label: "Job Search", icon: Briefcase },
  { href: "/scholarships", label: "Scholarships", icon: GraduationCap },
  { href: "/tracker", label: "Tracker", icon: ClipboardList },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/upskill", label: "Upskill", icon: TrendingUp },
  { href: "/diagnostics", label: "AI Diagnostics", icon: Activity },
];

// Helper to pass the message square icon without circular refs
import { MessageSquare } from "lucide-react";
function MessageSquareComponent(props: any) {
  return <MessageSquare {...props} />;
}

// Toast Context & Provider for globally accessible notifications
interface Toast {
  id: string;
  message: string;
  type: "success" | "error" | "info";
}

const ToastContext = createContext<{
  addToast: (msg: string, type?: "success" | "error" | "info") => void;
} | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((message: string, type: "success" | "error" | "info" = "success") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed bottom-5 right-5 z-[100] flex flex-col gap-2 pointer-events-none">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className={`pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-lg border text-xs font-medium shadow-lg backdrop-blur-md ${
                toast.type === "success"
                  ? "bg-emerald-950/80 border-emerald-500/30 text-emerald-400"
                  : toast.type === "error"
                  ? "bg-red-950/80 border-red-500/30 text-red-400"
                  : "bg-zinc-900/80 border-zinc-700/30 text-zinc-300"
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-current animate-ping" />
              <span>{toast.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Avoid hydration mismatch by waiting for mount
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="h-8 w-24 bg-zinc-900 rounded-lg animate-pulse" />;
  }

  const options = [
    { value: "light" as const, icon: Sun, label: "Light" },
    { value: "dark" as const, icon: Moon, label: "Dark" },
    { value: "system" as const, icon: Monitor, label: "System" },
  ];

  return (
    <div className="flex gap-0.5 rounded-lg bg-zinc-900 border border-zinc-800 p-0.5">
      {options.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          onClick={() => setTheme(value)}
          title={label}
          className={`p-1.5 rounded-md transition-colors ${
            theme === value
              ? "bg-zinc-800 text-zinc-100 shadow-sm"
              : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
          }`}
        >
          <Icon className="w-4 h-4" />
        </button>
      ))}
    </div>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  // Handle collapsible state cache
  useEffect(() => {
    const saved = localStorage.getItem("noray-sidebar-collapsed");
    if (saved) setCollapsed(saved === "true");
  }, []);

  const toggleCollapsed = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem("noray-sidebar-collapsed", String(next));
  };

  return (
    <>
      {/* Mobile hamburger */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="fixed top-4 left-4 z-50 rounded-lg border border-zinc-800 bg-zinc-900/90 backdrop-blur-md p-2 text-white lg:hidden hover:border-zinc-700 transition"
        aria-label="Toggle menu"
      >
        {mobileOpen ? <X size={18} /> : <Menu size={18} />}
      </button>

      {/* Mobile Overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden"
            onClick={() => setMobileOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar Layout */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex flex-col border-r border-zinc-800 bg-zinc-950 text-white transition-all duration-300 lg:static lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        } ${collapsed ? "w-20" : "w-64"}`}
      >
        {/* Logo Section */}
        <div className="flex h-16 items-center justify-between border-b border-zinc-800 px-4">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-600/10 border border-emerald-500/20 text-emerald-400">
              <Sparkles size={18} />
            </div>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-sm font-bold tracking-wider uppercase text-zinc-100"
              >
                NORAY
              </motion.span>
            )}
          </div>
          {/* Collapse toggle (Desktop only) */}
          <button
            onClick={toggleCollapsed}
            className="hidden lg:flex h-6 w-6 items-center justify-center rounded border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-white transition"
          >
            {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          </button>
        </div>

        {/* Navigation Items */}
        <LayoutGroup>
          <nav className="flex-1 space-y-1.5 px-3 py-6">
            {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
              const active = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  onClick={() => setMobileOpen(false)}
                  className={`group relative flex items-center gap-3 rounded-lg py-2.5 transition-all text-xs font-semibold ${
                    active
                      ? "text-emerald-400"
                      : "text-zinc-400 hover:text-zinc-100"
                  } ${collapsed ? "justify-center px-0" : "px-3"}`}
                >
                  <Icon size={16} className={`shrink-0 ${active ? "text-emerald-400" : "text-zinc-500 group-hover:text-zinc-300"}`} />
                  {!collapsed && (
                    <motion.span layoutId={`nav-label-${href}`} className="relative z-10">{label}</motion.span>
                  )}
                  {active && (
                    <motion.div
                      layoutId="sidebar-active-indicator"
                      className="absolute inset-0 -z-10 rounded-lg bg-emerald-500/5 border border-emerald-500/15"
                      transition={{ type: "spring", stiffness: 380, damping: 30 }}
                    />
                  )}
                </Link>
              );
            })}
          </nav>
        </LayoutGroup>

        {/* Sidebar Footer */}
        <div className="border-t border-zinc-800 px-4 py-4 space-y-4">
          <div className="flex items-center justify-between overflow-hidden">
            {!collapsed && <span className="text-[10px] text-zinc-500">Theme</span>}
            <div className={collapsed ? "mx-auto" : ""}>
              <ThemeToggle />
            </div>
          </div>
          {!collapsed && (
            <div className="flex items-center justify-between text-[10px] text-zinc-600">
              <span>NORAY v0.2.0</span>
              <span>AI Operating System</span>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

export function PageHeader({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children?: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-zinc-200/50 dark:border-zinc-800/60 pb-6"
    >
      <div>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white flex items-center gap-2">
          {title}
        </h1>
        {description && (
          <p className="mt-1 text-xs text-zinc-500 tracking-wide">{description}</p>
        )}
      </div>
      {children && <div className="flex items-center gap-3">{children}</div>}
    </motion.div>
  );
}

export function StatCard({
  label,
  value,
  icon: Icon,
  color = "emerald",
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color?: string;
}) {
  const colorClasses: Record<string, string> = {
    emerald: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
    blue: "text-blue-500 bg-blue-500/10 border-blue-500/20",
    amber: "text-amber-500 bg-amber-500/10 border-amber-500/20",
    purple: "text-purple-500 bg-purple-500/10 border-purple-500/20",
    rose: "text-rose-500 bg-rose-500/10 border-rose-500/20",
  };

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="relative rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900/60 backdrop-blur-md transition-shadow hover:shadow-[0_0_20px_-5px_rgba(16,185,129,0.1)] overflow-hidden"
    >
      <div className="flex items-center gap-4">
        <div className={`rounded-lg p-2.5 border ${colorClasses[color] || colorClasses.emerald}`}>
          <Icon size={18} />
        </div>
        <div>
          <p className="text-[10px] uppercase font-bold tracking-wider text-zinc-400">{label}</p>
          <p className="text-xl font-extrabold text-zinc-900 dark:text-white tracking-tight mt-0.5">
            {value}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

export function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl border border-zinc-200 bg-white dark:border-zinc-800/80 dark:bg-zinc-900/35 backdrop-blur-md ${className}`}
    >
      {children}
    </div>
  );
}

export function Button({
  children,
  variant = "primary",
  disabled = false,
  className = "",
  ...props
}: {
  children: React.ReactNode;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  disabled?: boolean;
  className?: string;
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const variants: Record<string, string> = {
    primary:
      "bg-emerald-600 text-white hover:bg-emerald-500 active:bg-emerald-700 border border-emerald-500/30",
    secondary:
      "bg-zinc-100 text-zinc-700 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700 border border-zinc-700/30",
    ghost:
      "bg-transparent text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-850",
    danger:
      "bg-red-600 text-white hover:bg-red-500 active:bg-red-750 border border-red-500/30",
  };

  const MotionButton = motion.button as any;

  return (
    <MotionButton
      whileTap={{ scale: disabled ? 1 : 0.97 }}
      disabled={disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold tracking-wide transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </MotionButton>
  );
}

export function Badge({
  children,
  variant = "default",
  className = "",
}: {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "danger" | "info";
  className?: string;
}) {
  const variants: Record<string, string> = {
    default: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800/80 dark:text-zinc-300 border-zinc-700/30",
    success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    warning: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    danger: "bg-red-500/10 text-red-400 border-red-500/20",
    info: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center justify-center py-14 text-center border border-dashed border-zinc-800 rounded-xl bg-zinc-900/10 px-4"
    >
      <div className="mb-4 rounded-full bg-zinc-900 border border-zinc-800 p-3.5 text-zinc-400">
        <Icon size={24} />
      </div>
      <h3 className="mb-1 text-sm font-bold text-zinc-900 dark:text-white">
        {title}
      </h3>
      <p className="mb-5 max-w-xs text-xs text-zinc-500 leading-relaxed">{description}</p>
      {action}
    </motion.div>
  );
}

export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
        className="h-6 w-6 rounded-full border-2 border-zinc-800 border-t-emerald-500"
      />
    </div>
  );
}

export function SkeletonLoader({ className = "" }: { className?: string }) {
  return (
    <div className={`shimmer rounded bg-zinc-200 dark:bg-zinc-850 ${className}`} />
  );
}

export function PageTransition({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}
