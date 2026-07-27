import { Shield } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

export default function Governance() {
  const costHistory = [
    { date: 'Jul 14', cost: 0.012 },
    { date: 'Jul 15', cost: 0.034 },
    { date: 'Jul 16', cost: 0.056 },
    { date: 'Jul 17', cost: 0.022 },
    { date: 'Jul 18', cost: 0.042 },
    { date: 'Jul 19', cost: 0.015 }
  ];

  return (
    <div className="w-full h-full bg-[#0a0a0c] p-6 flex flex-col gap-6 overflow-y-auto font-sans">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-200 tracking-wide flex items-center gap-2">
          <Shield className="text-emerald-500" />
          AI Governance & Cost Telemetry
        </h2>
        <span className="text-xs text-slate-500 font-mono">Status: Policy Enforced</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Cost Telemetry Chart */}
        <div className="lg:col-span-2 p-5 border border-slate-800 rounded-xl bg-slate-950/40 flex flex-col justify-between">
          <div className="text-xs text-slate-400 font-semibold mb-4 flex justify-between items-center">
            <span>Daily Cumulative LLM Cost</span>
            <span className="font-mono text-emerald-400 font-bold">Total: $0.181</span>
          </div>

          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={costHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" strokeOpacity={0.4} />
                <XAxis dataKey="date" stroke="#374151" tick={{ fill: '#9ca3af', fontSize: 10 }} />
                <YAxis stroke="#374151" tick={{ fill: '#9ca3af', fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151' }} />
                <Bar dataKey="cost" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Safety & Compliance Status */}
        <div className="p-5 border border-slate-800 rounded-xl bg-slate-950/40 flex flex-col gap-4">
          <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Compliance Registry</div>
          
          <div className="space-y-3.5 text-xs">
            <div className="p-3 bg-slate-900/20 rounded border border-slate-850 flex items-center justify-between">
              <div>
                <span className="font-bold text-slate-200">API Keys Encryption</span>
                <p className="text-[10px] text-slate-550 mt-0.5 font-mono">Secure environment variables</p>
              </div>
              <span className="text-[10px] text-emerald-400 font-bold uppercase font-mono">Active</span>
            </div>

            <div className="p-3 bg-slate-900/20 rounded border border-slate-850 flex items-center justify-between">
              <div>
                <span className="font-bold text-slate-200">Hallucination Detection</span>
                <p className="text-[10px] text-slate-550 mt-0.5 font-mono">NLI-based context verification</p>
              </div>
              <span className="text-[10px] text-emerald-400 font-bold uppercase font-mono">Enabled</span>
            </div>

            <div className="p-3 bg-slate-900/20 rounded border border-slate-850 flex items-center justify-between">
              <div>
                <span className="font-bold text-slate-200">Cost Limitation Cap</span>
                <p className="text-[10px] text-slate-550 mt-0.5 font-mono">$2.00 Daily soft limit</p>
              </div>
              <span className="text-[10px] text-amber-400 font-bold uppercase font-mono">$0.18 Used</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
