'use client';

import React, { useRef, useEffect } from 'react';
import { OnionInstance, CalibrationResult, RoboflowPrediction } from '@/types/onion';

interface BoundingBoxCanvasProps {
  imageSrc: string;
  imageWidth: number;
  imageHeight: number;
  onions: OnionInstance[];
  calibration: CalibrationResult;
  selectedOnionId?: string | null;
  onSelectOnion?: (onionId: string) => void;
  showRawDefects?: boolean;
  rawPredictions?: RoboflowPrediction[];
}

export const BoundingBoxCanvas: React.FC<BoundingBoxCanvasProps> = ({
  imageSrc,
  imageWidth,
  imageHeight,
  onions,
  calibration,
  selectedOnionId,
  onSelectOnion,
  showRawDefects = true,
  rawPredictions = []
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = imageSrc;

    img.onload = () => {
      // Set canvas render resolution to match image native size
      canvas.width = img.width;
      canvas.height = img.height;

      // Draw background image
      ctx.drawImage(img, 0, 0);

      // 1. Draw Calibration Object Bounding Box if detected
      if (calibration.detected && calibration.ref_bbox) {
        const rb = calibration.ref_bbox;
        ctx.strokeStyle = '#06B6D4'; // Cyan
        ctx.lineWidth = 4;
        ctx.setLineDash([6, 4]);
        ctx.strokeRect(rb.xmin, rb.ymin, rb.width, rb.height);
        ctx.setLineDash([]);

        // Badge
        ctx.fillStyle = '#06B6D4';
        ctx.fillRect(rb.xmin, Math.max(0, rb.ymin - 26), 160, 24);
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 12px Inter, sans-serif';
        ctx.fillText(`[REF] ${calibration.ref_type.toUpperCase()} (${calibration.ref_size_mm}mm)`, rb.xmin + 6, Math.max(16, rb.ymin - 8));
      }

      // 2. Draw Onion Bounding Boxes & Badges
      onions.forEach((onion) => {
        const isSelected = onion.id === selectedOnionId;
        const b = onion.bbox;

        let strokeColor = '#EF4444'; // Non-Compliant Red
        let badgeBg = '#EF4444';
        let gradeText = 'NON-COMPLIANT';

        if (onion.grade === 'GRADE_A') {
          strokeColor = '#10B981'; // Emerald Green
          badgeBg = '#10B981';
          gradeText = 'GRADE A';
        } else if (onion.grade === 'URS') {
          strokeColor = '#F59E0B'; // Amber Yellow
          badgeBg = '#F59E0B';
          gradeText = 'URS';
        }

        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = isSelected ? 6 : 3;
        ctx.strokeRect(b.xmin, b.ymin, b.width, b.height);

        if (isSelected) {
          ctx.fillStyle = strokeColor + '22'; // Semi-transparent highlight fill
          ctx.fillRect(b.xmin, b.ymin, b.width, b.height);
        }

        // Onion Header Label
        const diaText = onion.diameter_mm ? ` | ${onion.diameter_mm}mm` : '';
        const labelText = `${onion.id.toUpperCase()} • ${gradeText}${diaText}`;
        ctx.font = 'bold 13px Inter, sans-serif';
        const textWidth = ctx.measureText(labelText).width;

        ctx.fillStyle = badgeBg;
        ctx.fillRect(b.xmin, Math.max(0, b.ymin - 28), textWidth + 16, 26);
        ctx.fillStyle = '#FFFFFF';
        ctx.fillText(labelText, b.xmin + 8, Math.max(18, b.ymin - 9));

        // Draw Onion Defects
        onion.defects.forEach((defect, idx) => {
          const db = defect.bbox;
          ctx.strokeStyle = '#A855F7'; // Purple
          ctx.lineWidth = 2;
          ctx.setLineDash([4, 2]);
          ctx.strokeRect(db.xmin, db.ymin, db.width, db.height);
          ctx.setLineDash([]);

          // Defect Label
          const dLabel = `${defect.defect_class} (${Math.round(defect.confidence * 100)}%)`;
          ctx.fillStyle = '#A855F7';
          ctx.fillRect(db.xmin, db.ymin, ctx.measureText(dLabel).width + 12, 20);
          ctx.fillStyle = '#FFFFFF';
          ctx.font = '11px Inter, sans-serif';
          ctx.fillText(dLabel, db.xmin + 6, db.ymin + 14);
        });
      });
    };
  }, [imageSrc, onions, calibration, selectedOnionId, showRawDefects, rawPredictions]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onSelectOnion || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const clickX = (e.clientX - rect.left) * scaleX;
    const clickY = (e.clientY - rect.top) * scaleY;

    // Find onion box clicked
    const clickedOnion = onions.find((o) => {
      return (
        clickX >= o.bbox.xmin &&
        clickX <= o.bbox.xmax &&
        clickY >= o.bbox.ymin &&
        clickY <= o.bbox.ymax
      );
    });

    if (clickedOnion) {
      onSelectOnion(clickedOnion.id);
    }
  };

  return (
    <div className="relative w-full overflow-hidden rounded-xl border border-slate-700 bg-slate-900 shadow-2xl">
      <canvas
        ref={canvasRef}
        onClick={handleCanvasClick}
        className="w-full h-auto cursor-pointer block object-contain"
        style={{ maxHeight: '75vh' }}
      />
      <div className="absolute bottom-3 left-3 flex flex-wrap gap-2 rounded-lg bg-slate-950/80 p-2 text-xs text-slate-300 backdrop-blur-md border border-slate-800">
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-emerald-500"></span> Grade A (45-65mm)</span>
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-amber-500"></span> URS (35-70mm)</span>
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-rose-500"></span> Non-Compliant</span>
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-cyan-400"></span> Calibration Ref</span>
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-purple-500"></span> Defect Callout</span>
      </div>
    </div>
  );
};
