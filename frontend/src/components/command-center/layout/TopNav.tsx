import { Settings } from 'lucide-react';

export default function TopNav() {
  return (
    <div className="h-12 border-b border-slate-800/50 bg-slate-900/50 backdrop-blur-md flex items-center justify-between px-4 z-50">
      <div className="flex items-center gap-3">
        <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
        <span className="font-bold text-sm tracking-widest text-slate-200">NORAY OS</span>
        <span className="px-2 py-0.5 rounded text-[10px] uppercase font-semibold bg-slate-800 text-slate-400">Command Center</span>
      </div>
      
      <div className="flex items-center gap-4 text-slate-400">
        <button className="hover:text-slate-200 transition-colors">
          <Settings size={16} />
        </button>
      </div>
    </div>
  );
}
