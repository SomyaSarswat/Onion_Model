'use client';

import React from 'react';
import {
  LayoutDashboard,
  Scan,
  Layers,
  Search,
  FileText,
  Sliders,
  Settings,
  ShieldAlert
} from 'lucide-react';

export type ActiveTab =
  | 'dashboard'
  | 'analyze'
  | 'batch'
  | 'inspector'
  | 'report'
  | 'standards'
  | 'settings';

interface HeaderProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  standardName?: string;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  standardName = 'NAFED_Relaxed_2026'
}) => {
  const navItems: { id: ActiveTab; label: string; icon: React.ReactNode }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard className="h-4 w-4" /> },
    { id: 'analyze', label: 'Analyze Image', icon: <Scan className="h-4 w-4" /> },
    { id: 'batch', label: 'Batch Analysis', icon: <Layers className="h-4 w-4" /> },
    { id: 'inspector', label: 'Onion Inspector', icon: <Search className="h-4 w-4" /> },
    { id: 'report', label: 'Quality Report', icon: <FileText className="h-4 w-4" /> },
    { id: 'standards', label: 'Grading Standards', icon: <Sliders className="h-4 w-4" /> },
    { id: 'settings', label: 'Settings', icon: <Settings className="h-4 w-4" /> },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/90 backdrop-blur-md">
      {/* Top Banner */}
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3 border-b border-slate-800/60">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-600 to-emerald-500 text-slate-950 font-black shadow-lg shadow-cyan-900/40">
            OG
          </div>
          <div>
            <h1 className="text-base font-extrabold tracking-tight text-slate-100 flex items-center gap-2">
              ONION QUALITY ASSESSMENT & GRADING
              <span className="rounded bg-cyan-950 px-2 py-0.5 text-[10px] font-mono text-cyan-400 border border-cyan-800">
                PROT-V1.0
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Roboflow Vision Detector (veg1-hcqsf-2/4) + Deterministic Rules Engine
            </p>
          </div>
        </div>

        {/* Model & Rules Status Badges */}
        <div className="hidden md:flex items-center gap-3 text-xs">
          <div className="flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-1.5 border border-slate-800">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-400">Standard:</span>
            <strong className="text-slate-200">{standardName}</strong>
          </div>

          <div className="flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-1.5 border border-slate-800 text-slate-300">
            <ShieldAlert className="h-3.5 w-3.5 text-amber-400" />
            <span>YOLOv8x (mAP@50 43.4%)</span>
          </div>
        </div>
      </div>

      {/* Navigation Tabs Bar */}
      <div className="mx-auto flex max-w-7xl px-6">
        <nav className="flex space-x-1 overflow-x-auto py-2">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-medium transition whitespace-nowrap ${
                  isActive
                    ? 'bg-cyan-600 text-white font-semibold shadow-md shadow-cyan-950'
                    : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
