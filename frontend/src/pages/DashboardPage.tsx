import React from 'react';
import {
  AlertTriangle,
  Camera as CameraIcon,
  CheckCircle2,
  ChevronRight,
  Layers,
  MapPin,
  Scan,
  ShieldAlert,
  Wrench
} from 'lucide-react';
import { Camera, PotholeEvent, Report, SystemOverviewStats } from '../types';
import { StatCard } from '../components/StatCard';
import { PotholeMap } from '../components/PotholeMap';
import { StatusBadge } from '../components/StatusBadge';
import { ConfidenceBar } from '../components/ConfidenceBar';

interface DashboardPageProps {
  stats: SystemOverviewStats;
  events: PotholeEvent[];
  reports: Report[];
  cameras: Camera[];
  onSelectEvent: (event: PotholeEvent) => void;
  onNavigateTab: (tab: 'events' | 'detection' | 'reports') => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  stats,
  events,
  reports,
  cameras,
  onSelectEvent,
  onNavigateTab
}) => {
  const urgentReports = reports.filter(r => r.priority === 'urgent' || r.priority === 'high');
  const recentEvents = events.slice(0, 5);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Road Surface Telemetry &amp; Detection</h1>
          <p className="page-subtitle">
            Autonomous visual road damage assessment, temporal hazard aggregation, and municipal repair coordination.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn btn-secondary" onClick={() => onNavigateTab('events')}>
            <Layers size={16} />
            <span>Browse All Events</span>
          </button>
          <button className="btn btn-primary" onClick={() => onNavigateTab('detection')}>
            <Scan size={16} />
            <span>Test Single Image</span>
          </button>
        </div>
      </div>

      {/* KPI Stats Cards */}
      <div className="stats-grid">
        <StatCard
          title="Total Road Hazards"
          value={stats.total_events}
          subtitle="Aggregated temporal events"
          icon={<ShieldAlert size={18} />}
          accentColor="var(--indigo)"
        />

        <StatCard
          title="Confirmed Potholes"
          value={stats.confirmed_potholes}
          subtitle="Passed Event Engine thresholds"
          icon={<AlertTriangle size={18} />}
          accentColor="var(--emerald)"
        />

        <StatCard
          title="Active Work Orders"
          value={reports.filter(r => r.resolution !== 'repaired').length}
          subtitle={`${urgentReports.length} flagged as high/urgent priority`}
          icon={<Wrench size={18} />}
          accentColor="var(--amber)"
        />

        <StatCard
          title="Repaired &amp; Closed"
          value={stats.repaired_count}
          subtitle="Signed off by field teams"
          icon={<CheckCircle2 size={18} />}
          accentColor="var(--cyan)"
        />
      </div>

      {/* Primary Map Grid & Action Section */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '24px' }}>
        {/* Interactive Corridor Map */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>
              Corridor Hazard Heatmap
            </h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
              Live Telemetry Feed
            </span>
          </div>

          <PotholeMap
            events={events}
            cameras={cameras}
            onSelectEvent={onSelectEvent}
          />
        </div>

        {/* High Priority Actions & Urgent Work Orders */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Urgent Maintenance Queue */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertTriangle size={18} color="var(--crimson)" />
                <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff' }}>
                  Urgent Maintenance Queue
                </h3>
              </div>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => onNavigateTab('reports')}
              >
                View Hub
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {urgentReports.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-subtle)' }}>
                  No high-priority work orders pending.
                </div>
              ) : (
                urgentReports.map((report) => (
                  <div
                    key={report.report_id}
                    style={{
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-md)',
                      padding: '12px 14px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.85rem' }}>
                        {report.report_id}
                      </span>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <StatusBadge status={report.priority} type="priority" />
                        <StatusBadge status={report.resolution} type="resolution" />
                      </div>
                    </div>

                    <p style={{ fontSize: '0.825rem', color: 'var(--text-main)', lineHeight: 1.4 }}>
                      {report.notes}
                    </p>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
                      <span>Crew: {report.assigned_crew || 'Unassigned'}</span>
                      {report.estimated_cost && (
                        <span style={{ color: 'var(--amber)', fontFamily: 'var(--font-mono)' }}>
                          ₹{report.estimated_cost.toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Active Field Capture Units */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CameraIcon size={18} color="var(--cyan)" />
                <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff' }}>
                  Mobile Capture Units
                </h3>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--emerald)' }}>
                {cameras.filter(c => c.active).length} Online
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {cameras.map((cam) => (
                <div
                  key={cam.camera_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.825rem'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span
                      style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: cam.active ? 'var(--emerald)' : 'var(--text-subtle)'
                      }}
                    />
                    <div>
                      <div style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{cam.camera_id}</div>
                      <div style={{ fontSize: '0.725rem', color: 'var(--text-subtle)' }}>
                        {cam.location.road_name} ({cam.location.city})
                      </div>
                    </div>
                  </div>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {cam.metadata?.framerate || 30} FPS
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Detected Pothole Events Feed */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>
              Recent Pothole Ingestion Feed
            </h3>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-subtle)' }}>
              Events emitted by the temporal inference tracker and confirmed by the Event Engine.
            </p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => onNavigateTab('events')}>
            View All ({events.length})
          </button>
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Event ID</th>
                <th>Source / Camera</th>
                <th>Location / Corridor</th>
                <th>Confidence</th>
                <th>Status</th>
                <th>Detected At</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {recentEvents.map((evt) => (
                <tr key={evt.event_id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--indigo)' }}>
                    {evt.event_id}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                    {evt.source_id}
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <MapPin size={14} color="var(--emerald)" />
                      <span>{evt.location?.road_name || 'Unspecified Road'}</span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', marginLeft: '20px' }}>
                      {evt.location?.city}, {evt.location?.state}
                    </div>
                  </td>
                  <td style={{ minWidth: '140px' }}>
                    <ConfidenceBar confidence={evt.confidence} />
                  </td>
                  <td>
                    <StatusBadge status={evt.status} />
                  </td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {new Date(evt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => onSelectEvent(evt)}
                      style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
                    >
                      <span>Inspect</span>
                      <ChevronRight size={13} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
