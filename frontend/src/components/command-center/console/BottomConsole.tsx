import { useState, useRef, useEffect } from 'react';
import { useLogStore } from '../store/logStore';
import { Terminal, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';

export default function BottomConsole() {
  const { logs } = useLogStore();
  const [activeTab, setActiveTab] = useState<'logs' | 'hitl'>('logs');
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom for streaming logs
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="h-64 border-t border-slate-800/50 bg-[#0a0a0c]/80 backdrop-blur flex flex-col font-mono text-xs">
      <div className="flex items-center border-b border-slate-800/50 px-2 bg-slate-900/50">
        <button 
          onClick={() => setActiveTab('logs')}
          className={clsx("px-4 py-2 uppercase tracking-widest font-semibold flex items-center gap-2 transition-colors border-b-2", activeTab === 'logs' ? "border-emerald-500 text-emerald-400" : "border-transparent text-slate-500 hover:text-slate-300")}
        >
          <Terminal size={14} /> System Logs
        </button>
        <button 
          onClick={() => setActiveTab('hitl')}
          className={clsx("px-4 py-2 uppercase tracking-widest font-semibold flex items-center gap-2 transition-colors border-b-2", activeTab === 'hitl' ? "border-amber-500 text-amber-400" : "border-transparent text-slate-500 hover:text-slate-300")}
        >
          <AlertCircle size={14} /> HITL Inbox
          {logs.filter(l => l.event_type === 'ApprovalRequested').length > 0 && (
            <span className="bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded-full text-[9px]">
              {logs.filter(l => l.event_type === 'ApprovalRequested').length}
            </span>
          )}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-1 scroll-smooth" ref={scrollRef}>
        {activeTab === 'logs' ? (
          logs.length === 0 ? (
            <div className="text-slate-500 italic">System ready. Waiting for events...</div>
          ) : (
            <AnimatePresence initial={false}>
              {[...logs].reverse().map((log) => (
                <motion.div 
                  key={log.event_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-start gap-3 py-0.5 group"
                >
                  <span className="text-slate-600 shrink-0 select-none" suppressHydrationWarning>
                    {new Date(log.timestamp).toLocaleTimeString([], { hour12: false })}
                  </span>
                  <span className={clsx("shrink-0 font-bold", 
                    log.severity === 'error' ? 'text-rose-400' :
                    log.severity === 'warning' ? 'text-amber-400' :
                    'text-emerald-400'
                  )}>
                    [{log.event_type}]
                  </span>
                  <span className="text-slate-300 break-words group-hover:text-white transition-colors">
                    {JSON.stringify(log.metadata)}
                  </span>
                </motion.div>
              ))}
            </AnimatePresence>
          )
        ) : (
          <div className="flex flex-col gap-2">
            {logs.filter(l => l.event_type === 'ApprovalRequested').map((req) => (
               <div key={req.event_id} className="border border-amber-900/50 bg-amber-950/20 rounded p-3 flex justify-between items-center">
                  <div className="flex flex-col gap-1">
                    <span className="text-amber-400 font-bold uppercase tracking-wider text-[10px]">Action Required</span>
                    <span className="text-slate-200 text-sm">{req.metadata?.summary || 'Pending approval'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded flex items-center gap-2 hover:bg-emerald-500/20 transition-colors">
                      <CheckCircle size={14} /> Approve
                    </button>
                    <button className="px-3 py-1 bg-rose-500/10 text-rose-400 border border-rose-500/30 rounded flex items-center gap-2 hover:bg-rose-500/20 transition-colors">
                      <XCircle size={14} /> Reject
                    </button>
                  </div>
               </div>
            ))}
            {logs.filter(l => l.event_type === 'ApprovalRequested').length === 0 && (
              <div className="text-slate-500 italic">No pending HITL approvals.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
