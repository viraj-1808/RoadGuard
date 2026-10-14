import React, { useState } from 'react';
import { Navigation, ShieldAlert, Video } from 'lucide-react';
import { PotholeEvent, Camera } from '../types';
import { StatusBadge } from './StatusBadge';

interface PotholeMapProps {
  events: PotholeEvent[];
  cameras: Camera[];
  onSelectEvent: (event: PotholeEvent) => void;
}

export const PotholeMap: React.FC<PotholeMapProps> = ({
  events,
  cameras,
  onSelectEvent
}) => {
  const [selectedPin, setSelectedPin] = useState<PotholeEvent | null>(null);
  const [viewFilter, setViewFilter] = useState<'all' | 'severe' | 'cameras'>('all');

  // Map coordinates normalized to 0-100% canvas positions for visual simulation
  const getEventCoordinates = (index: number) => {
    const offsets = [
      { top: 48, left: 32 },
      { top: 62, left: 58 },
      { top: 28, left: 74 },
      { top: 72, left: 24 },
      { top: 38, left: 45 },
      { top: 80, left: 82 }
    ];
    return offsets[index % offsets.length];
  };

  const getCameraCoordinates = (index: number) => {
    const offsets = [
      { top: 40, left: 28 },
      { top: 56, left: 62 },
      { top: 22, left: 70 },
      { top: 85, left: 78 }
    ];
    return offsets[index % offsets.length];
  };

  const filteredEvents = events.filter(e => {
    if (viewFilter === 'severe') return e.confidence >= 0.90 || e.status === 'confirmed';
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Map Control Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Navigation size={16} color="var(--cyan)" />
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)' }}>
            Spatial Road Surface Damage Telemetry
          </span>
        </div>

        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            className={`btn btn-sm ${viewFilter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setViewFilter('all')}
          >
            All Hazards ({events.length})
          </button>
          <button
            className={`btn btn-sm ${viewFilter === 'severe' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setViewFilter('severe')}
          >
            High Severity
          </button>
          <button
            className={`btn btn-sm ${viewFilter === 'cameras' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setViewFilter('cameras')}
          >
            Active Feeds ({cameras.filter(c => c.active).length})
          </button>
        </div>
      </div>

      {/* Map Graphic Canvas */}
      <div className="map-canvas-container">
        <div className="map-grid-bg" />

        {/* Stylized Highway Arteries */}
        <svg
          style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
        >
          {/* Main Expressway Line */}
          <path
            d="M 10 90 Q 40 50 75 25 T 95 15"
            fill="none"
            stroke="rgba(255, 255, 255, 0.15)"
            strokeWidth="3.5"
            strokeDasharray="2 1"
          />
          <path
            d="M 10 90 Q 40 50 75 25 T 95 15"
            fill="none"
            stroke="rgba(6, 182, 212, 0.2)"
            strokeWidth="8"
          />
          {/* Secondary Arterial Road */}
          <path
            d="M 25 15 Q 45 45 60 70 T 88 85"
            fill="none"
            stroke="rgba(255, 255, 255, 0.1)"
            strokeWidth="2.5"
          />
          {/* Ring Road Connector */}
          <circle
            cx="48"
            cy="52"
            r="26"
            fill="none"
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth="2"
            strokeDasharray="4 2"
          />
        </svg>

        {/* Camera Nodes */}
        {cameras.map((cam, idx) => {
          const coord = getCameraCoordinates(idx);
          return (
            <div
              key={cam.camera_id}
              style={{
                position: 'absolute',
                top: `${coord.top}%`,
                left: `${coord.left}%`,
                transform: 'translate(-50%, -50%)',
                zIndex: 5,
                cursor: 'pointer'
              }}
              title={`${cam.camera_id} - ${cam.location.road_name}`}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  background: cam.active ? 'rgba(6, 182, 212, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                  border: `1px solid ${cam.active ? 'var(--cyan)' : 'var(--border-subtle)'}`,
                  padding: '3px 7px',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '0.675rem',
                  fontFamily: 'var(--font-mono)',
                  color: cam.active ? 'var(--cyan)' : 'var(--text-subtle)'
                }}
              >
                <Video size={10} />
                <span>{cam.camera_id}</span>
              </div>
            </div>
          );
        })}

        {/* Pothole Hazard Markers */}
        {viewFilter !== 'cameras' &&
          filteredEvents.map((evt, idx) => {
            const coord = getEventCoordinates(idx);
            const isSevere = evt.confidence >= 0.90;
            const markerColor = isSevere ? 'var(--crimson)' : 'var(--amber)';

            return (
              <div
                key={evt.event_id}
                className="map-marker"
                style={{
                  top: `${coord.top}%`,
                  left: `${coord.left}%`,
                  color: markerColor
                }}
                onClick={() => {
                  setSelectedPin(evt);
                  onSelectEvent(evt);
                }}
              >
                <div className="marker-pulse" />
                <div className="marker-inner" style={{ background: markerColor }} />
              </div>
            );
          })}

        {/* Floating Selected Pin Card */}
        {selectedPin && (
          <div
            style={{
              position: 'absolute',
              bottom: '16px',
              left: '16px',
              right: '16px',
              maxWidth: '380px',
              background: 'rgba(14, 20, 34, 0.95)',
              backdropFilter: 'blur(12px)',
              border: '1px solid var(--border-medium)',
              borderRadius: 'var(--radius-lg)',
              padding: '14px',
              zIndex: 30,
              boxShadow: 'var(--shadow-lg)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldAlert size={16} color="var(--emerald)" />
                <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)', fontSize: '0.875rem' }}>
                  {selectedPin.event_id}
                </span>
              </div>
              <StatusBadge status={selectedPin.status} />
            </div>

            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
              <div>{selectedPin.location?.road_name}</div>
              <div style={{ color: 'var(--text-subtle)', fontSize: '0.75rem' }}>
                {selectedPin.location?.city}, {selectedPin.location?.state}
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px' }}>
              <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                Confidence: <strong style={{ color: 'var(--emerald)' }}>{Math.round(selectedPin.confidence * 100)}%</strong>
              </div>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => onSelectEvent(selectedPin)}
              >
                Inspect Event
              </button>
            </div>
          </div>
        )}

        {/* Legend */}
        <div
          style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            background: 'rgba(10, 15, 26, 0.85)',
            backdropFilter: 'blur(8px)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '8px 12px',
            fontSize: '0.725rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '5px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--crimson)' }} />
            <span>Severe Damage (Conf &gt; 90%)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--amber)' }} />
            <span>Moderate Hazard (Conf &gt; 70%)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--cyan)' }} />
            <span>Connected Mobile Camera</span>
          </div>
        </div>
      </div>
    </div>
  );
};
