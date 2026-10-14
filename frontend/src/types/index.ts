/**
 * Domain types matching authoritative contracts in:
 * - docs/EVENT_SCHEMAS.md
 * - docs/API_CONTRACTS.md
 * - docs/DATABASE_SCHEMA.md
 */

// Bounding box in pixel coordinates [x1, y1, x2, y2]
export type BoundingBox = [number, number, number, number];

// Single frame-level observation produced by detector (docs/EVENT_SCHEMAS.md#1-detection)
export interface Detection {
  class: 'pothole';
  confidence: number; // [0 - 1]
  bbox: BoundingBox; // [x1, y1, x2, y2]
  frame_id: string;
  capture_timestamp: string; // ISO 8601 string
  track_id?: string;
  source_id?: string;
}

// Temporal association of detections (docs/EVENT_SCHEMAS.md#2-track)
export interface Track {
  track_id: string;
  source_id: string;
  first_seen: string;
  last_seen: string;
  detections: Detection[];
  avg_confidence?: number;
  max_confidence?: number;
  status?: 'active' | 'expired' | 'confirmed';
}

// Stored media evidence associated with an event (docs/DATABASE_SCHEMA.md#evidence)
export interface EvidenceItem {
  evidence_id: string;
  media_type: 'image' | 'video' | 'thermal';
  storage_path: string;
  captured_at: string;
  verified?: boolean;
  thumbnail_url?: string;
}

// Logical/reportable pothole occurrence (docs/EVENT_SCHEMAS.md#3-potholeevent)
export type PotholeEventStatus =
  | 'candidate'
  | 'confirmed'
  | 'closed'
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'resolved';

export interface LocationMetadata {
  latitude: number;
  longitude: number;
  road_name?: string;
  city?: string;
  state?: string;
}

export interface PotholeEvent {
  event_id: string;
  source_id: string; // Camera/source identifier
  timestamp: string; // ISO 8601
  confidence: number; // 0.0 - 1.0
  bbox?: BoundingBox | null;
  location?: LocationMetadata;
  evidence: EvidenceItem[];
  status: PotholeEventStatus;
  report_id?: string | null;
  track_id?: string;
  model_version?: string;
}

// Actionable municipal maintenance report (docs/EVENT_SCHEMAS.md#4-report)
export type ReportPriority = 'low' | 'medium' | 'high' | 'urgent';
export type ReportResolution = 'pending' | 'scheduled' | 'in_progress' | 'repaired' | 'rejected';
export type ReportStatus = 'pending' | 'approved' | 'resolved';

export interface Report {
  report_id: string;
  event_id: string;
  submitted_by: string;
  submitted_at: string;
  priority: ReportPriority;
  resolution: ReportResolution;
  status: ReportStatus;
  notes?: string;
  assigned_crew?: string;
  estimated_cost?: number;
}

// Camera device metadata (docs/DATABASE_SCHEMA.md#camera)
export interface Camera {
  camera_id: string;
  location: LocationMetadata;
  active: boolean;
  metadata?: {
    model?: string;
    resolution?: string;
    framerate?: number;
    installation_type?: 'vehicle_mounted' | 'fixed_pole' | 'drone';
  };
}

// Ad-hoc Image Upload Detection Result (Extension for Frontend Detection Studio)
export interface DetectionResult {
  image_url: string;
  image_width: number;
  image_height: number;
  processing_time_ms: number;
  detections: Detection[];
  model_info: {
    model_name: string;
    model_version?: string;
    is_active: boolean;
    weights_loaded: boolean;
  };
  is_demo_data?: boolean;
}

// Filter query parameters for GET /api/events
export interface EventFilterParams {
  status?: PotholeEventStatus | 'all';
  min_confidence?: number;
  source_id?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

// Summary Statistics for Dashboard
export interface SystemOverviewStats {
  total_events: number;
  confirmed_potholes: number;
  pending_inspection: number;
  repaired_count: number;
  active_cameras: number;
  average_confidence: number;
  urgent_reports: number;
}
