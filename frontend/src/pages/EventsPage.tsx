import React, { useState } from 'react';
import {
  Eye,
  FilePlus,
  Filter,
  MapPin,
  RefreshCw,
  Search,
  Sliders,
  X
} from 'lucide-react';
import { Camera, PotholeEvent, PotholeEventStatus } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ConfidenceBar } from '../components/ConfidenceBar';
import { EvidenceViewer } from '../components/EvidenceViewer';
import { Modal } from '../components/Modal';

interface EventsPageProps {
  events: PotholeEvent[];
  cameras: Camera[];
  selectedEvent: PotholeEvent | null;
  onSelectEvent: (event: PotholeEvent | null) => void;
  onUpdateEventStatus: (eventId: string, status: PotholeEventStatus) => Promise<void>;
  onCreateReportForEvent: (event: PotholeEvent) => void;
  onRefresh: () => void;
  isLoading: boolean;
  isDemo: boolean;
}

export const EventsPage: React.FC<EventsPageProps> = ({
  events,
  cameras,
  selectedEvent,
  onSelectEvent,
  onUpdateEventStatus,
  onCreateReportForEvent,
  onRefresh,
  isLoading,
  isDemo
}) => {
  // Filter state
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [minConfidence, setMinConfidence] = useState<number>(50);
  const [cameraFilter, setCameraFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isUpdatingStatus, setIsUpdatingStatus] = useState<boolean>(false);

  // Filter application
  const filteredEvents = events.filter((evt) => {
    if (statusFilter !== 'all' && evt.status !== statusFilter) return false;
    if (evt.confidence < minConfidence / 100) return false;
    if (cameraFilter !== 'all' && evt.source_id !== cameraFilter) return false;
    if (searchQuery.trim().length > 0) {
      const q = searchQuery.toLowerCase();
      const matchId = evt.event_id.toLowerCase().includes(q);
      const matchRoad = evt.location?.road_name?.toLowerCase().includes(q);
      const matchCity = evt.location?.city?.toLowerCase().includes(q);
      if (!matchId && !matchRoad && !matchCity) return false;
    }
    return true;
  });

  const handleStatusChange = async (newStatus: PotholeEventStatus) => {
    if (!selectedEvent) return;
    setIsUpdatingStatus(true);
    try {
      await onUpdateEventStatus(selectedEvent.event_id, newStatus);
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Pothole Events Explorer</h1>
          <p className="page-subtitle">
            Query, filter, and inspect verified road surface damage events emitted by the inference pipeline.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            className="btn btn-secondary btn-sm"
            onClick={onRefresh}
            disabled={isLoading}
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={14} className={isLoading ? 'spinner' : ''} />
            <span>Refresh Events</span>
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="filter-bar">
        {/* Search */}
        <div className="filter-group">
          <div className="filter-input-wrap">
            <Search size={16} className="filter-input-icon" />
            <input
              type="text"
              placeholder="Search by Event ID, Road, or City..."
              className="filter-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                style={{
                  position: 'absolute',
                  right: '10px',
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-subtle)',
                  cursor: 'pointer'
                }}
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Status Dropdown */}
          <select
            className="select-dropdown"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All Statuses</option>
            <option value="confirmed">Confirmed</option>
            <option value="candidate">Candidate</option>
            <option value="pending">Pending</option>
            <option value="resolved">Resolved</option>
            <option value="rejected">Rejected</option>
          </select>

          {/* Camera Dropdown */}
          <select
            className="select-dropdown"
            value={cameraFilter}
            onChange={(e) => setCameraFilter(e.target.value)}
          >
            <option value="all">All Cameras</option>
            {cameras.map((c) => (
              <option key={c.camera_id} value={c.camera_id}>
                {c.camera_id} ({c.location.city})
              </option>
            ))}
          </select>
        </div>

        {/* Confidence Slider */}
        <div className="filter-group">
          <div className="slider-group">
            <Sliders size={14} />
            <span>Min Confidence:</span>
            <input
              type="range"
              min="50"
              max="95"
              step="5"
              value={minConfidence}
              onChange={(e) => setMinConfidence(Number(e.target.value))}
            />
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--emerald)' }}>
              {minConfidence}%
            </span>
          </div>

          {(statusFilter !== 'all' || minConfidence > 50 || cameraFilter !== 'all' || searchQuery) && (
            <button
              className="notice-btn"
              onClick={() => {
                setStatusFilter('all');
                setMinConfidence(50);
                setCameraFilter('all');
                setSearchQuery('');
              }}
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Events Results Summary */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
        <span>
          Showing <strong>{filteredEvents.length}</strong> of <strong>{events.length}</strong> events
          {isDemo && <span style={{ marginLeft: '8px', color: 'var(--amber)' }}>(Demo Dataset)</span>}
        </span>
      </div>

      {/* Events Table / Card Feed */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {filteredEvents.length === 0 ? (
          <div style={{ padding: '64px 20px', textAlign: 'center', color: 'var(--text-subtle)' }}>
            <Filter size={32} style={{ marginBottom: '12px', opacity: 0.5 }} />
            <h3 style={{ color: '#fff', fontSize: '1.1rem', marginBottom: '6px' }}>No matching events found</h3>
            <p style={{ fontSize: '0.85rem' }}>Try broadening your confidence threshold or status filter criteria.</p>
          </div>
        ) : (
          <div className="table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Event ID</th>
                  <th>Camera Unit</th>
                  <th>Corridor Location</th>
                  <th>Detection Confidence</th>
                  <th>Status</th>
                  <th>Timestamp</th>
                  <th>Evidence</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.map((evt) => (
                  <tr key={evt.event_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--indigo)' }}>
                      {evt.event_id}
                    </td>

                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                      {evt.source_id}
                    </td>

                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 500 }}>
                        <MapPin size={14} color="var(--emerald)" />
                        <span>{evt.location?.road_name || 'Highway Segment'}</span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', marginLeft: '20px' }}>
                        {evt.location?.city}, {evt.location?.state}
                      </div>
                    </td>

                    <td style={{ minWidth: '150px' }}>
                      <ConfidenceBar confidence={evt.confidence} />
                    </td>

                    <td>
                      <StatusBadge status={evt.status} />
                    </td>

                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      {new Date(evt.timestamp).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>

                    <td>
                      {evt.evidence && evt.evidence.length > 0 ? (
                        <div
                          style={{
                            width: '42px',
                            height: '28px',
                            borderRadius: '4px',
                            overflow: 'hidden',
                            border: '1px solid var(--border-medium)',
                            cursor: 'pointer'
                          }}
                          onClick={() => onSelectEvent(evt)}
                          title="Click to view high-resolution evidence"
                        >
                          <img
                            src={evt.evidence[0].thumbnail_url || evt.evidence[0].storage_path}
                            alt="Evidence Thumbnail"
                            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          />
                        </div>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>None</span>
                      )}
                    </td>

                    <td>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => onSelectEvent(evt)}
                        >
                          <Eye size={13} />
                          <span>Inspect</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Selected Event Details & Evidence Modal */}
      {selectedEvent && (
        <Modal
          isOpen={true}
          onClose={() => onSelectEvent(null)}
          title={`Event Inspection // ${selectedEvent.event_id}`}
          maxWidth="760px"
          footer={
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.775rem', color: 'var(--text-subtle)' }}>Update State:</span>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => handleStatusChange('confirmed')}
                  disabled={isUpdatingStatus || selectedEvent.status === 'confirmed'}
                >
                  Confirm
                </button>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => handleStatusChange('resolved')}
                  disabled={isUpdatingStatus || selectedEvent.status === 'resolved'}
                >
                  Resolve
                </button>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => handleStatusChange('rejected')}
                  disabled={isUpdatingStatus || selectedEvent.status === 'rejected'}
                >
                  Reject
                </button>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => onCreateReportForEvent(selectedEvent)}
                >
                  <FilePlus size={14} />
                  <span>Generate Report</span>
                </button>
                <button className="btn btn-secondary btn-sm" onClick={() => onSelectEvent(null)}>
                  Close
                </button>
              </div>
            </div>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            {/* Top metadata grid */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: '12px',
                background: 'var(--bg-card)',
                padding: '14px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)'
              }}
            >
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>Event Status</div>
                <div style={{ marginTop: '4px' }}>
                  <StatusBadge status={selectedEvent.status} />
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>Peak Confidence</div>
                <div style={{ marginTop: '4px' }}>
                  <ConfidenceBar confidence={selectedEvent.confidence} />
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>Camera Source</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--cyan)' }}>
                  {selectedEvent.source_id}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>Track Identifier</div>
                <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                  {selectedEvent.track_id || 'N/A'}
                </div>
              </div>
            </div>

            {/* Location Banner */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 14px',
                background: 'rgba(16, 185, 129, 0.08)',
                border: '1px solid rgba(16, 185, 129, 0.25)',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.85rem'
              }}
            >
              <MapPin size={16} color="var(--emerald)" />
              <div>
                <strong>{selectedEvent.location?.road_name}</strong>
                <span style={{ color: 'var(--text-muted)', marginLeft: '6px' }}>
                  ({selectedEvent.location?.latitude.toFixed(4)}°N, {selectedEvent.location?.longitude.toFixed(4)}°E)
                </span>
              </div>
            </div>

            {/* Evidence Image Viewer with Bounding Box Overlay */}
            {selectedEvent.evidence && selectedEvent.evidence.length > 0 ? (
              <EvidenceViewer
                imageUrl={selectedEvent.evidence[0].thumbnail_url || selectedEvent.evidence[0].storage_path}
                bboxes={selectedEvent.bbox ? [selectedEvent.bbox] : []}
                confidence={selectedEvent.confidence}
                label="pothole"
                timestamp={selectedEvent.timestamp}
                frameId={selectedEvent.evidence[0].evidence_id}
              />
            ) : (
              <div
                style={{
                  padding: '40px',
                  textAlign: 'center',
                  background: 'var(--bg-card)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-subtle)'
                }}
              >
                No media evidence attached to this event.
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};
