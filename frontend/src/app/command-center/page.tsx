'use client';

import { useEffect } from 'react';
import { wsClient } from '@/components/command-center/store/websocketClient';
import CommandCenterLayout from '@/components/command-center/layout/CommandCenterLayout';

export default function CommandCenterPage() {
  useEffect(() => {
    wsClient.connect();
    return () => {
      wsClient.disconnect();
    };
  }, []);

  // Use fixed positioning to break out of the root layout's sidebar/padding
  return (
    <div className="fixed inset-0 z-50 h-screen w-full bg-[#0a0a0c] text-slate-200 overflow-hidden font-sans">
      <CommandCenterLayout />
    </div>
  );
}
