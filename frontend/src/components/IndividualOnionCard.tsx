'use client';

import React from 'react';
import { OnionInstance } from '@/types/onion';
import { CheckCircle2, XCircle, AlertTriangle, ShieldCheck, Ruler, Bug } from 'lucide-react';

interface IndividualOnionCardProps {
  onion: OnionInstance;
  isSelected?: boolean;
  onSelect?: (id: string) => void;
}

export const IndividualOnionCard: React.FC<IndividualOnionCardProps> = ({
  onion,
  isSelected = false,
  onSelect
}) => {
  let gradeBadgeColor = 'bg-rose-950 text-rose-300 border-rose-800';
  let gradeIcon = <XCircle className="h-5 w-5 text-rose-400" />;
  let gradeTitle = 'NON-COMPLIANT';

  if (onion.grade === 'GRADE_A') {
    gradeBadgeColor = 'bg-emerald-950 text-emerald-300 border-emerald-800';
    gradeIcon = <ShieldCheck className="h-5 w-5 text-emerald-400" />;
    gradeTitle = 'GRADE A (PREMIUM)';
  } else if (onion.grade === 'URS') {
    gradeBadgeColor = 'bg-amber-950 text-amber-300 border-amber-800';
    gradeIcon = <AlertTriangle className="h-5 w-5 text-amber-400" />;
    gradeTitle = 'URS (RELAXED SPEC)';
  }

  return (
    <div
      onClick={() => onSelect && onSelect(onion.id)}
      className={`rounded-xl border p-5 transition cursor-pointer shadow-lg ${
        isSelected
          ? 'border-cyan-500 bg-slate-900 ring-2 ring-cyan-500/30'
          : 'border-slate-800 bg-slate-900/80 hover:border-slate-700 hover:bg-slate-900'
      }`}
    >
      {/* Header & Grade Badge */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-slate-100">{onion.id.toUpperCase()}</span>
            <span className="text-xs font-mono text-slate-400">({Math.round(onion.confidence * 100)}% detection conf)</span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <Ruler className="h-4 w-4 text-cyan-400" />
            <span className="text-sm font-semibold text-slate-200">
              {onion.diameter_mm ? `${onion.diameter_mm} mm` : 'Size Unmeasured'}
            </span>
            {onion.measurement_method && (
              <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-400 border border-slate-700">
                tag: {onion.measurement_method}
              </span>
            )}
          </div>
        </div>

        <div className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-bold ${gradeBadgeColor}`}>
          {gradeIcon}
          <span>{gradeTitle}</span>
        </div>
      </div>

      {/* Detected Defects */}
      <div className="py-3">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
          <Bug className="h-3.5 w-3.5 text-purple-400" /> Associated Defect Visual Evidence
        </h4>
        {onion.defects.length === 0 ? (
          <p className="text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-900/50 p-2 rounded-md">
            No defect instances matched to this onion bounding box.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {onion.defects.map((def, i) => (
              <span
                key={i}
                className={`rounded-md px-2.5 py-1 text-xs font-medium border ${
                  def.is_confirmed
                    ? 'bg-purple-950 text-purple-200 border-purple-800'
                    : 'bg-slate-800 text-slate-400 border-slate-700'
                }`}
              >
                {def.status_text}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Deterministic Rules Check Table */}
      <div className="py-2">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Deterministic Standards Evaluation
        </h4>
        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 font-medium">
              <tr>
                <th className="p-2">Criterion</th>
                <th className="p-2">Measured Value</th>
                <th className="p-2">Standard Limit</th>
                <th className="p-2 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-900/40">
              {onion.checks.map((chk, i) => (
                <tr key={i} className="hover:bg-slate-800/30">
                  <td className="p-2 font-medium text-slate-300">{chk.criterion}</td>
                  <td className="p-2 text-slate-200 font-mono">{chk.value}</td>
                  <td className="p-2 text-slate-400">{chk.limit}</td>
                  <td className="p-2 text-right">
                    {chk.status === 'PASS' ? (
                      <span className="inline-flex items-center gap-1 rounded bg-emerald-950/80 px-2 py-0.5 font-bold text-emerald-400 border border-emerald-800">
                        <CheckCircle2 className="h-3 w-3" /> PASS
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded bg-rose-950/80 px-2 py-0.5 font-bold text-rose-400 border border-rose-800">
                        <XCircle className="h-3 w-3" /> FAIL
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Explicit Qualification / Failure Reasons */}
      <div className="mt-3 pt-3 border-t border-slate-800">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
          Rules Engine Reasons & Disclosures
        </h4>
        <ul className="space-y-1">
          {onion.reasons.map((r, i) => (
            <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
              <span className="text-cyan-400">•</span>
              <span>{r}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
