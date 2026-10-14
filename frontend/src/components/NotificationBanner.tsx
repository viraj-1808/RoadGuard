import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle, Info, X } from 'lucide-react';

interface NotificationBannerProps {
  type?: 'warning' | 'info' | 'error' | 'success';
  title?: string;
  message: string;
  actionText?: string;
  onAction?: () => void;
  onDismiss?: () => void;
}

export const NotificationBanner: React.FC<NotificationBannerProps> = ({
  type = 'info',
  title,
  message,
  actionText,
  onAction,
  onDismiss
}) => {
  const getIcon = () => {
    switch (type) {
      case 'warning':
        return <AlertTriangle size={18} style={{ color: 'var(--amber)', flexShrink: 0 }} />;
      case 'error':
        return <AlertCircle size={18} style={{ color: 'var(--crimson)', flexShrink: 0 }} />;
      case 'success':
        return <CheckCircle size={18} style={{ color: 'var(--emerald)', flexShrink: 0 }} />;
      case 'info':
      default:
        return <Info size={18} style={{ color: 'var(--cyan)', flexShrink: 0 }} />;
    }
  };

  return (
    <div className={`notice-banner ${type}`}>
      <div className="notice-content">
        {getIcon()}
        <div>
          {title && <div style={{ fontWeight: 600, marginBottom: '2px' }}>{title}</div>}
          <div>{message}</div>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {actionText && onAction && (
          <button className="notice-btn" onClick={onAction}>
            {actionText}
          </button>
        )}
        {onDismiss && (
          <button
            onClick={onDismiss}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'inherit',
              cursor: 'pointer',
              display: 'flex',
              padding: '2px'
            }}
            aria-label="Dismiss banner"
          >
            <X size={15} />
          </button>
        )}
      </div>
    </div>
  );
};
