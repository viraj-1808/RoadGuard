import React, { useRef, useEffect, useState } from 'react';
import { Eye, EyeOff, ShieldAlert } from 'lucide-react';
import { BoundingBox } from '../types';

interface EvidenceViewerProps {
  imageUrl: string;
  bboxes?: BoundingBox[];
  confidence?: number;
  label?: string;
  timestamp?: string;
  frameId?: string;
}

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({
  imageUrl,
  bboxes = [],
  confidence,
  label = 'pothole',
  timestamp,
  frameId
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [showOverlay, setShowOverlay] = useState(true);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 1280, height: 720 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = imageUrl;

    img.onload = () => {
      setImageLoaded(true);
      const w = img.naturalWidth || 1280;
      const h = img.naturalHeight || 720;
      setDimensions({ width: w, height: h });

      canvas.width = w;
      canvas.height = h;

      // Draw base image
      ctx.drawImage(img, 0, 0, w, h);

      // If overlay is enabled and bounding boxes are provided, draw them
      if (showOverlay && bboxes && bboxes.length > 0) {
        bboxes.forEach((bbox, idx) => {
          const [x1, y1, x2, y2] = bbox;
          const boxWidth = x2 - x1;
          const boxHeight = y2 - y1;

          // Glowing bounding box stroke
          ctx.save();
          ctx.strokeStyle = '#10B981';
          ctx.lineWidth = Math.max(3, Math.round(w / 400));
          ctx.shadowColor = 'rgba(16, 185, 129, 0.6)';
          ctx.shadowBlur = 12;

          ctx.strokeRect(x1, y1, boxWidth, boxHeight);

          // Semi-transparent fill
          ctx.fillStyle = 'rgba(16, 185, 129, 0.12)';
          ctx.fillRect(x1, y1, boxWidth, boxHeight);

          // Corner brackets
          const cornerLen = Math.min(20, boxWidth / 4, boxHeight / 4);
          ctx.strokeStyle = '#34D399';
          ctx.lineWidth = Math.max(4, Math.round(w / 300));
          ctx.beginPath();
          // Top-left
          ctx.moveTo(x1, y1 + cornerLen);
          ctx.lineTo(x1, y1);
          ctx.lineTo(x1 + cornerLen, y1);
          // Top-right
          ctx.moveTo(x2 - cornerLen, y1);
          ctx.lineTo(x2, y1);
          ctx.lineTo(x2, y1 + cornerLen);
          // Bottom-right
          ctx.moveTo(x2, y2 - cornerLen);
          ctx.lineTo(x2, y2);
          ctx.lineTo(x2 - cornerLen, y2);
          // Bottom-left
          ctx.moveTo(x1 + cornerLen, y2);
          ctx.lineTo(x1, y2);
          ctx.lineTo(x1, y2 - cornerLen);
          ctx.stroke();

          // Confidence & Tag Badge
          const textConfidence = confidence !== undefined ? `${Math.round(confidence * 100)}%` : '';
          const tagText = `${label.toUpperCase()} #${idx + 1} ${textConfidence}`;

          ctx.font = `bold ${Math.max(12, Math.round(w / 80))}px 'JetBrains Mono', monospace`;
          const textMetrics = ctx.measureText(tagText);
          const textWidth = textMetrics.width;
          const tagHeight = Math.max(22, Math.round(w / 50));

          const tagY = y1 - tagHeight > 0 ? y1 - tagHeight : y1 + 4;
          ctx.fillStyle = '#10B981';
          ctx.fillRect(x1, tagY, textWidth + 14, tagHeight);

          ctx.fillStyle = '#062B1A';
          ctx.fillText(tagText, x1 + 7, tagY + tagHeight - 6);

          ctx.restore();
        });
      }
    };
  }, [imageUrl, bboxes, showOverlay, confidence, label]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Viewer Stage */}
      <div className="detection-stage-container">
        <canvas ref={canvasRef} className="detection-canvas" />

        {!imageLoaded && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#090D16',
              color: 'var(--text-muted)'
            }}
          >
            Loading evidence frame...
          </div>
        )}

        {/* Floating Controls Bar */}
        <div
          style={{
            position: 'absolute',
            bottom: '12px',
            right: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(10, 15, 26, 0.85)',
            backdropFilter: 'blur(8px)',
            padding: '6px 12px',
            borderRadius: 'var(--radius-full)',
            border: '1px solid var(--border-medium)',
            zIndex: 10
          }}
        >
          <button
            onClick={() => setShowOverlay(!showOverlay)}
            className="notice-btn"
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            title={showOverlay ? 'Hide Detection Bounding Box' : 'Show Detection Bounding Box'}
          >
            {showOverlay ? <EyeOff size={14} /> : <Eye size={14} />}
            {showOverlay ? 'Hide Box' : 'Show Box'}
          </button>

          <span style={{ color: 'var(--text-subtle)', fontSize: '0.75rem' }}>|</span>

          <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            {dimensions.width}×{dimensions.height}
          </span>
        </div>
      </div>

      {/* Metadata Table / Coordinates Readout */}
      {bboxes.length > 0 && (
        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
            fontSize: '0.8rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontWeight: 600, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <ShieldAlert size={15} color="var(--emerald)" />
              Detected Object Coordinates (Normalized to Frame)
            </span>
            {frameId && (
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-subtle)' }}>
                Frame: {frameId}
              </span>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {bboxes.map((bbox, idx) => {
              const [x1, y1, x2, y2] = bbox;
              const w = x2 - x1;
              const h = y2 - y1;
              return (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: 'var(--bg-card)',
                    padding: '6px 10px',
                    borderRadius: 'var(--radius-sm)',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--emerald)'
                  }}
                >
                  <span>
                    Box #{idx + 1}: [{x1}, {y1}, {x2}, {y2}]
                  </span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                    Area: {w}×{h}px ({w * h} px²)
                  </span>
                </div>
              );
            })}
          </div>

          {timestamp && (
            <div style={{ marginTop: '8px', fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
              Captured: {new Date(timestamp).toLocaleString()}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
