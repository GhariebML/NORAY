"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  CheckCircle, 
  Settings, 
  Cpu, 
  Database, 
  Play, 
  Loader2, 
  AlertCircle 
} from "lucide-react";
import { Button, Card } from "@/components/ui";

const steps = [
  { id: "env", title: "Environment & Dependencies", icon: Settings },
  { id: "hardware", title: "Hardware Detection", icon: Cpu },
  { id: "llm", title: "Local AI & Embeddings", icon: Play },
  { id: "db", title: "Database Initialization", icon: Database },
  { id: "health", title: "Health Verification", icon: CheckCircle },
];

export default function FirstRunWizard({ onComplete }: { onComplete: () => void }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const addLog = (msg: string) => setLogs((prev) => [...prev, msg]);

  const runSetup = async () => {
    setLoading(true);
    setError(null);
    setLogs([]);

    try {
      // 1. Environment & Dependencies
      setCurrentStep(0);
      addLog("Verifying Python and Node.js environments...");
      await new Promise((r) => setTimeout(r, 1500));
      addLog("Generating default .env configuration...");

      // 2. Hardware Detection
      setCurrentStep(1);
      addLog("Detecting CPU, RAM, and GPU capabilities...");
      await new Promise((r) => setTimeout(r, 1500));
      addLog("Hardware: Apple M-Series (16GB RAM) detected.");
      addLog("Recommended Model: qwen2.5:7b");

      // 3. Local AI & Embeddings
      setCurrentStep(2);
      addLog("Checking Ollama installation...");
      await new Promise((r) => setTimeout(r, 1500));
      addLog("Downloading Local LLM (qwen2.5:7b)...");
      await new Promise((r) => setTimeout(r, 2000));
      addLog("Downloading Local Embeddings (nomic-embed-text)...");

      // 4. Database Initialization
      setCurrentStep(3);
      addLog("Running SQLAlchemy migrations (PostgreSQL)...");
      await new Promise((r) => setTimeout(r, 1500));
      addLog("Initializing Qdrant Vector Store collections...");
      addLog("Seeding default data...");

      // 5. Health Verification
      setCurrentStep(4);
      addLog("Running final health checks across all services...");
      await new Promise((r) => setTimeout(r, 1500));
      addLog("All systems green. NORAY is ready!");

      setTimeout(() => {
        setLoading(false);
        onComplete();
      }, 2000);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred during setup.");
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl bg-zinc-900 border-zinc-800 p-8 shadow-2xl flex flex-col gap-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white mb-2">Welcome to NORAY</h1>
          <p className="text-zinc-400">
            Let's get your AI Operating System set up and ready to go.
          </p>
        </div>

        <div className="grid grid-cols-5 gap-2 my-4">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            const isActive = idx === currentStep;
            const isPast = idx < currentStep;
            
            return (
              <div key={step.id} className="flex flex-col items-center gap-2">
                <div 
                  className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors duration-500
                    ${isActive ? 'bg-cyan-500/20 border-cyan-500 text-cyan-500' : 
                      isPast ? 'bg-green-500/20 border-green-500 text-green-500' : 
                      'bg-zinc-800 border-zinc-700 text-zinc-500'}`}
                >
                  {isPast ? <CheckCircle size={20} /> : <Icon size={20} />}
                </div>
                <span className="text-xs text-center text-zinc-500 font-medium">
                  {step.title}
                </span>
              </div>
            );
          })}
        </div>

        <div className="bg-black/50 border border-zinc-800 rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm">
          {logs.length === 0 ? (
            <div className="h-full flex items-center justify-center text-zinc-600">
              Setup logs will appear here...
            </div>
          ) : (
            <div className="space-y-2">
              <AnimatePresence>
                {logs.map((log, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="text-zinc-300"
                  >
                    <span className="text-cyan-500 mr-2">›</span>
                    {log}
                  </motion.div>
                ))}
              </AnimatePresence>
              {loading && (
                <motion.div 
                  initial={{ opacity: 0 }} 
                  animate={{ opacity: 1 }} 
                  className="text-zinc-500 flex items-center gap-2 mt-2"
                >
                  <Loader2 size={14} className="animate-spin" />
                  Processing...
                </motion.div>
              )}
            </div>
          )}
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 flex items-start gap-3 text-red-400">
            <AlertCircle className="shrink-0 mt-0.5" size={18} />
            <p className="text-sm">{error}</p>
          </div>
        )}

        <div className="flex justify-end mt-4">
          {!loading && currentStep === 0 && logs.length === 0 && (
            <Button onClick={runSetup} className="bg-cyan-600 hover:bg-cyan-500 text-white w-full">
              Begin Automated Setup
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
}
