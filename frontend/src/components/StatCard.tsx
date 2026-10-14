import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  accentColor?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  accentColor = 'var(--emerald)'
}) => {
  return (
    <div className="stat-card">
      <div className="stat-header">
        <span className="stat-title">{title}</span>
        <div
          className="stat-icon"
          style={{
            background: `color-mix(in srgb, ${accentColor} 15%, transparent)`,
            color: accentColor,
            border: `1px solid color-mix(in srgb, ${accentColor} 30%, transparent)`
          }}
        >
          {icon}
        </div>
      </div>
      <div className="stat-value">{value}</div>
      {subtitle && <div className="stat-footer">{subtitle}</div>}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: '2px',
          background: `linear-gradient(90deg, ${accentColor}, transparent)`
        }}
      />
    </div>
  );
};
