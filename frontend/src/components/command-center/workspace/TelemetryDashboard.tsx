import { Activity } from 'lucide-react';
import { LineChart, Line, XAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

const dummyData = [
  { time: '10:00', latency: 450, tokens: 1200 },
  { time: '10:01', latency: 800, tokens: 3500 },
  { time: '10:02', latency: 300, tokens: 900 },
  { time: '10:03', latency: 1200, tokens: 8000 },
];

export default function TelemetryDashboard() {
  return (
    <div className="w-full h-full bg-[#0a0a0c] p-6 overflow-y-auto">
      <h2 className="text-xl font-bold text-slate-200 tracking-wide flex items-center gap-2 mb-8">
        <Activity className="text-emerald-500" />
        Telemetry & Performance
      </h2>

      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="p-5 rounded-xl bg-slate-900/40 border border-slate-800/50">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Avg Latency</div>
          <div className="text-3xl font-mono text-emerald-400">450ms</div>
        </div>
        <div className="p-5 rounded-xl bg-slate-900/40 border border-slate-800/50">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Tokens / Sec</div>
          <div className="text-3xl font-mono text-emerald-400">84.2</div>
        </div>
        <div className="p-5 rounded-xl bg-slate-900/40 border border-slate-800/50">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Cost (Last 1h)</div>
          <div className="text-3xl font-mono text-emerald-400">$0.042</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="h-64 p-5 rounded-xl bg-slate-900/40 border border-slate-800/50 flex flex-col">
           <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Latency Trend</div>
           <div className="flex-1">
             <ResponsiveContainer width="100%" height="100%">
               <AreaChart data={dummyData}>
                 <XAxis dataKey="time" hide />
                 <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#cbd5e1' }} />
                 <Area type="monotone" dataKey="latency" stroke="#10b981" fill="#10b981" fillOpacity={0.1} />
               </AreaChart>
             </ResponsiveContainer>
           </div>
        </div>
        
        <div className="h-64 p-5 rounded-xl bg-slate-900/40 border border-slate-800/50 flex flex-col">
           <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Token Usage</div>
           <div className="flex-1">
             <ResponsiveContainer width="100%" height="100%">
               <LineChart data={dummyData}>
                 <XAxis dataKey="time" hide />
                 <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#cbd5e1' }} />
                 <Line type="stepAfter" dataKey="tokens" stroke="#8b5cf6" strokeWidth={2} dot={false} />
               </LineChart>
             </ResponsiveContainer>
           </div>
        </div>
      </div>
    </div>
  );
}
