import React from 'react';
import {
  Activity,
  Cpu,
  FileText,
  Layers,
  RefreshCw,
  ScanEye,
  ShieldCheck,
  SlidersHorizontal
} from 'lucide-react';
import { ApiStatus } from '../api/client';

export type ActiveTab = 'dashboard' | 'events' | 'detection' | 'reports';

interface NavbarProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  apiStatus: ApiStatus | null;
  onRefreshHealth: () => void;
  onToggleDemoMode: () => void;
  isCheckingHealth: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onTabChange,
  apiStatus,
  onRefreshHealth,
  onToggleDemoMode,
  isCheckingHealth
}) => {
  const isDemo = apiStatus?.isDemoMode ?? true;
  const isOnline = apiStatus?.isBackendConnected ?? false;

  return (
    <header className="navbar">
      <div className="navbar-inner">
        {/* Brand */}
        <div className="brand-section" onClick={() => onTabChange('dashboard')}>
          <div className="brand-icon-wrapper">
            <ShieldCheck size={24} />
          </div>
          <div>
            <div className="brand-title">
              <span>RoadGuard AI</span>
              <span className="brand-badge">YOLO26s</span>
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-subtle)' }}>
              Pothole Detection &amp; Reporting System
            </div>
          </div>
        </div>

        {/* Primary Navigation Tabs */}
        <nav className="nav-links">
          <button
            className={`nav-link ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => onTabChange('dashboard')}
          >
            <Activity size={16} />
            <span>Dashboard</span>
          </button>

          <button
            className={`nav-link ${activeTab === 'events' ? 'active' : ''}`}
            onClick={() => onTabChange('events')}
          >
            <Layers size={16} />
            <span>Events Explorer</span>
          </button>

          <button
            className={`nav-link ${activeTab === 'detection' ? 'active' : ''}`}
            onClick={() => onTabChange('detection')}
          >
            <ScanEye size={16} />
            <span>Detection Studio</span>
          </button>

          <button
            className={`nav-link ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => onTabChange('reports')}
          >
            <FileText size={16} />
            <span>Maintenance Reports</span>
          </button>
        </nav>

        {/* System & Connection Status */}
        <div className="nav-status-group">
          {/* Model Indicator */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.75rem',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)'
            }}
            title={apiStatus?.modelStatus.details || 'Primary Candidate Model: YOLO26s'}
          >
            <Cpu size={14} color="var(--indigo)" />
            <span>{apiStatus?.modelStatus.modelName || 'YOLO26s'}</span>
          </div>

          {/* Backend Connection Status Pill */}
          <div
            className={`status-pill ${isOnline && !isDemo ? 'online' : 'demo'}`}
            title={`Backend URL: ${apiStatus?.baseUrl || 'http://localhost:8000'}`}
          >
            <span className="status-dot" />
            <span>{isOnline && !isDemo ? 'API CONNECTED' : 'DEMO MODE'}</span>
          </div>

          {/* Toggle Demo Mode Button */}
          <button
            className="notice-btn"
            style={{ display: 'flex', alignItems: 'center', gap: '5px' }}
            onClick={onToggleDemoMode}
            title={isDemo ? 'Switch to Real Backend API calls' : 'Switch to Local High-Fidelity Demo Dataset'}
          >
            <SlidersHorizontal size={13} />
            <span>{isDemo ? 'Try Live API' : 'Use Demo'}</span>
          </button>

          {/* Refresh Connection Status */}
          <button
            className="notice-btn"
            style={{ padding: '6px', display: 'flex' }}
            onClick={onRefreshHealth}
            disabled={isCheckingHealth}
            title="Refresh Backend API Connection"
            aria-label="Refresh Backend API Connection"
          >
            <RefreshCw size={13} className={isCheckingHealth ? 'spinner' : ''} />
          </button>
        </div>
      </div>
    </header>
  );
};
