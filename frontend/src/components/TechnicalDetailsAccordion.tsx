'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Cpu, Info, ShieldAlert } from 'lucide-react';
import { RoboflowPrediction, CalibrationResult } from '@/types/onion';

interface TechnicalDetailsProps {
  rawPredictions: RoboflowPrediction[];
  calibration: CalibrationResult;
  roboflowModelId?: string;
}

export const TechnicalDetailsAccordion: React.FC<TechnicalDetailsProps> = ({
  rawPredictions,
  calibration,
  roboflowModelId = 'veg1-hcqsf-2/4'
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/60 shadow-md">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between p-4 text-left transition hover:bg-slate-800/50 rounded-xl"
      >
        <div className="flex items-center gap-3">
          <Cpu className="h-5 w-5 text-cyan-400" />
          <div>
            <h3 className="text-sm font-semibold text-slate-200">
              Technical ML & Computer Vision Details
            </h3>
            <p className="text-xs text-slate-400">
              Roboflow raw predictions, bounding box metrics, and model performance metrics
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-cyan-950 px-2.5 py-1 text-xs font-medium text-cyan-400 border border-cyan-800">
            Prototype-Grade Vision Detector
          </span>
          {isOpen ? (
            <ChevronUp className="h-5 w-5 text-slate-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-slate-400" />
          )}
        </div>
      </button>

      {isOpen && (
        <div className="border-t border-slate-800 p-5 space-y-5 text-xs text-slate-300">
          {/* Model Specification Banner */}
          <div className="rounded-lg bg-slate-950 p-4 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-cyan-400">Model Identifier: {roboflowModelId}</span>
              <span className="text-slate-400">Architecture: YOLOv8x Object Detection</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              Reported Vision Metrics: <strong className="text-slate-200">mAP@50: 43.4%</strong> | <strong className="text-slate-200">Precision: 57.3%</strong> | <strong className="text-slate-200">Recall: 51.5%</strong>.
            </p>
            <div className="flex items-center gap-2 text-amber-400 pt-1">
              <ShieldAlert className="h-4 w-4 shrink-0" />
              <span>
                <strong>System Disclosure:</strong> This Roboflow model serves as visual evidence only. All final grading decisions (Grade A, URS, Non-Compliant) are strictly computed by our deterministic rules engine.
              </span>
            </div>
          </div>

          {/* Calibration Math */}
          <div className="rounded-lg bg-slate-950 p-4 border border-slate-800 space-y-2">
            <h4 className="font-semibold text-slate-200 flex items-center gap-2">
              <Info className="h-4 w-4 text-cyan-400" /> OpenCV Spatial Calibration Parameters
            </h4>
            <div className="grid grid-cols-2 gap-4 pt-1">
              <div>
                <span className="text-slate-400">Reference Type:</span> {calibration.ref_type.toUpperCase()}
              </div>
              <div>
                <span className="text-slate-400">Known Physical Size:</span> {calibration.ref_size_mm} mm
              </div>
              <div>
                <span className="text-slate-400">Measured Pixel Width:</span> {calibration.ref_pixel_width ? `${calibration.ref_pixel_width} px` : 'N/A'}
              </div>
              <div>
                <span className="text-slate-400">Scale Ratio (Pixels per MM):</span> {calibration.pixels_per_mm ? `${calibration.pixels_per_mm} px/mm` : 'Uncalibrated'}
              </div>
            </div>
          </div>

          {/* Raw Roboflow Predictions Table */}
          <div className="space-y-2">
            <h4 className="font-semibold text-slate-200">Raw Predictions Payload ({rawPredictions.length} detections)</h4>
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left font-mono text-xs">
                <thead className="bg-slate-950 text-slate-400">
                  <tr>
                    <th className="p-2.5">#</th>
                    <th className="p-2.5">Class Name</th>
                    <th className="p-2.5">Confidence</th>
                    <th className="p-2.5">Center (X, Y)</th>
                    <th className="p-2.5">Size (W x H)</th>
                    <th className="p-2.5">BBox [xmin, ymin, xmax, ymax]</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 bg-slate-900/50">
                  {rawPredictions.map((pred, i) => (
                    <tr key={i} className="hover:bg-slate-800/40">
                      <td className="p-2.5 text-slate-500">{i + 1}</td>
                      <td className="p-2.5 font-semibold text-cyan-300">{pred.class}</td>
                      <td className="p-2.5 text-amber-300">{(pred.confidence * 100).toFixed(1)}%</td>
                      <td className="p-2.5">({pred.x}, {pred.y})</td>
                      <td className="p-2.5">{pred.width} x {pred.height} px</td>
                      <td className="p-2.5 text-slate-400">[{pred.xmin}, {pred.ymin}, {pred.xmax}, {pred.ymax}]</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
