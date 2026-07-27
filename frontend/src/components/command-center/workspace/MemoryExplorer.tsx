import { useState } from 'react';
import { Database, Search, Filter, Pin, Trash2, Edit3, ExternalLink } from 'lucide-react';

interface Memory {
  id: string;
  content: string;
  type: string;
  importance: number; // 1-10
  confidence: number; // 0.0 - 1.0
  createdDate: string;
  source: string;
  linkedNodes: string[];
  pinned?: boolean;
}

export default function MemoryExplorer() {
  const [activeType, setActiveType] = useState('semantic');
  const [searchQuery, setSearchQuery] = useState('');
  const [memories, setMemories] = useState<Memory[]>([
    {
      id: 'mem_9823',
      content: 'User prefers strict adherence to PEP8 Python guidelines and type annotations.',
      type: 'semantic',
      importance: 9,
      confidence: 0.98,
      createdDate: '2026-07-18',
      source: 'User Interaction',
      linkedNodes: ['Gharieb Mohamed', 'Python'],
      pinned: true
    },
    {
      id: 'mem_1102',
      content: 'Applying for DAAD EPOS Postgrad scholarship at Heidelberg University.',
      type: 'working',
      importance: 10,
      confidence: 1.00,
      createdDate: '2026-07-19',
      source: 'Workspace Document',
      linkedNodes: ['DAAD Scholarship', 'Germany'],
      pinned: true
    },
    {
      id: 'mem_4451',
      content: 'Mentioned Google Cairo as target professional developer organization context.',
      type: 'episodic',
      importance: 8,
      confidence: 0.92,
      createdDate: '2026-07-17',
      source: 'Chat Context',
      linkedNodes: ['Gharieb Mohamed', 'Google'],
      pinned: false
    },
    {
      id: 'mem_5091',
      content: 'Task DAG compilation policy: prioritize local execution before cloud fallback.',
      type: 'procedural',
      importance: 7,
      confidence: 0.95,
      createdDate: '2026-07-16',
      source: 'System Preference',
      linkedNodes: ['NORAY OS', 'Hybrid Router'],
      pinned: false
    }
  ]);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');

  const types = ['Working', 'Conversation', 'Semantic', 'Procedural', 'Workspace', 'Episodic', 'Organization'];

  function handleTogglePin(id: string) {
    setMemories(prev => prev.map(m => m.id === id ? { ...m, pinned: !m.pinned } : m));
  }

  function handleDelete(id: string) {
    setMemories(prev => prev.filter(m => m.id !== id));
  }

  function handleSaveEdit(id: string) {
    setMemories(prev => prev.map(m => m.id === id ? { ...m, content: editContent } : m));
    setEditingId(null);
  }

  const filteredMemories = memories.filter(m => {
    const matchesType = m.type === activeType.toLowerCase();
    const matchesSearch = m.content.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          m.id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  return (
    <div className="w-full h-full bg-[#0a0a0c] p-6 flex flex-col gap-6 overflow-y-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-200 tracking-wide flex items-center gap-2">
          <Database className="text-emerald-500" />
          Semantic & Episodic Memory Explorer
        </h2>
        
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input 
              type="text" 
              placeholder="Search memories..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-xs rounded-lg pl-9 pr-4 py-1.5 focus:outline-none focus:border-emerald-500 transition-colors text-slate-200"
            />
          </div>
          <button className="p-1.5 bg-slate-900 border border-slate-800 rounded-md text-slate-400 hover:text-slate-200"><Filter size={14} /></button>
        </div>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-2 border-b border-slate-900">
        {types.map(t => (
          <button
            key={t}
            onClick={() => setActiveType(t.toLowerCase())}
            className={`px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider whitespace-nowrap transition-colors border ${
              activeType === t.toLowerCase() 
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' 
                : 'bg-slate-950 border-slate-900 text-slate-500 hover:text-slate-300'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="flex-1 space-y-4">
        {filteredMemories.length === 0 ? (
          <div className="text-slate-500 italic text-xs p-4">No memories found in this category.</div>
        ) : (
          <div className="grid gap-4">
            {filteredMemories.map((m) => (
              <div 
                key={m.id} 
                className="p-4 rounded-xl bg-slate-950/40 border border-slate-900 flex flex-col gap-3 relative overflow-hidden"
              >
                <div className="flex justify-between items-center text-[10px] font-mono text-slate-500">
                  <div className="flex items-center gap-2">
                    <span>ID: {m.id}</span>
                    <span>•</span>
                    <span>Created: {m.createdDate}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <button 
                      onClick={() => handleTogglePin(m.id)}
                      className={`hover:text-emerald-400 ${m.pinned ? 'text-emerald-400' : 'text-slate-600'}`}
                    >
                      <Pin size={12} className={m.pinned ? 'fill-emerald-400/20' : ''} />
                    </button>
                    <button 
                      onClick={() => {
                        setEditingId(m.id);
                        setEditContent(m.content);
                      }}
                      className="hover:text-slate-300 text-slate-650"
                    >
                      <Edit3 size={12} />
                    </button>
                    <button 
                      onClick={() => handleDelete(m.id)}
                      className="hover:text-rose-450 text-slate-650"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>

                {editingId === m.id ? (
                  <div className="flex gap-2">
                    <input 
                      type="text" 
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      className="flex-1 bg-slate-900 border border-slate-800 text-xs rounded p-1.5 focus:outline-none text-slate-200"
                    />
                    <button 
                      onClick={() => handleSaveEdit(m.id)}
                      className="px-3 py-1 bg-emerald-600 text-zinc-950 font-bold rounded text-xs"
                    >
                      Save
                    </button>
                  </div>
                ) : (
                  <p className="text-xs text-slate-350 leading-relaxed font-sans">{m.content}</p>
                )}

                <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-900/60 text-[9px] font-mono">
                  <span className="px-2 py-0.5 rounded bg-zinc-900 text-slate-400 uppercase">Confidence: {m.confidence}</span>
                  <span className="px-2 py-0.5 rounded bg-zinc-900 text-slate-400 uppercase">Importance: {m.importance}/10</span>
                  <span className="px-2 py-0.5 rounded bg-zinc-900 text-slate-400 uppercase">Source: {m.source}</span>
                  {m.linkedNodes.map((node, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-emerald-500/5 text-emerald-400/80 border border-emerald-500/10 flex items-center gap-1">
                      <ExternalLink size={8} /> {node}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
