import React from 'react';

interface ConfidenceBarProps {
  confidence: number; // 0.0 to 1.0
  showLabel?: boolean;
  size?: 'sm' | 'md';
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({
  confidence,
  showLabel = true,
  size = 'md'
}) => {
  const percentage = Math.min(100, Math.max(0, Math.round(confidence * 100)));

  // Color selection based on confidence spectrum
  let color = 'var(--crimson)';
  if (confidence >= 0.85) {
    color = 'var(--emerald)';
  } else if (confidence >= 0.70) {
    color = 'var(--amber)';
  }

  const height = size === 'sm' ? '6px' : '9px';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: '100%' }}>
      <div
        style={{
          flex: 1,
          height,
          background: 'rgba(255, 255, 255, 0.08)',
          borderRadius: '9999px',
          overflow: 'hidden',
          position: 'relative'
        }}
      >
        <div
          style={{
            width: `${percentage}%`,
            height: '100%',
            background: color,
            borderRadius: '9999px',
            boxShadow: `0 0 8px ${color}`,
            transition: 'width 0.4s ease'
          }}
        />
      </div>
      {showLabel && (
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: size === 'sm' ? '0.7rem' : '0.8rem',
            fontWeight: 600,
            color,
            minWidth: '42px',
            textAlign: 'right'
          }}
        >
          {percentage}%
        </span>
      )}
    </div>
  );
};
