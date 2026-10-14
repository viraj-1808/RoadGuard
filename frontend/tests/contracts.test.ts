import { describe, it, expect } from 'vitest';
import { PotholeEvent, Detection, Report } from '../src/types';
import { MOCK_POTHOLE_EVENTS, MOCK_REPORTS } from '../src/data/mockData';

describe('Event Schemas & API Contract Verification', () => {
  it('validates Detection contract fields per docs/EVENT_SCHEMAS.md#1-detection', () => {
    const sampleDetection: Detection = {
      class: 'pothole',
      confidence: 0.92,
      bbox: [100, 200, 300, 400],
      frame_id: 'frame-001',
      capture_timestamp: '2026-10-14T10:00:00Z',
      source_id: 'CAM-01'
    };

    expect(sampleDetection.class).toBe('pothole');
    expect(sampleDetection.confidence).toBeGreaterThanOrEqual(0);
    expect(sampleDetection.confidence).toBeLessThanOrEqual(1);
    expect(sampleDetection.bbox).toHaveLength(4);
    expect(sampleDetection.bbox[0]).toBeLessThan(sampleDetection.bbox[2]);
    expect(sampleDetection.bbox[1]).toBeLessThan(sampleDetection.bbox[3]);
    expect(sampleDetection.frame_id).toBeDefined();
    expect(sampleDetection.capture_timestamp).toBeDefined();
  });

  it('validates PotholeEvent contract per docs/EVENT_SCHEMAS.md#3-potholeevent', () => {
    MOCK_POTHOLE_EVENTS.forEach((event: PotholeEvent) => {
      expect(event.event_id).toMatch(/^evt-/);
      expect(event.source_id).toBeDefined();
      expect(event.timestamp).toBeDefined();
      expect(event.confidence).toBeGreaterThanOrEqual(0);
      expect(event.confidence).toBeLessThanOrEqual(1);
      expect(['candidate', 'confirmed', 'closed', 'pending', 'approved', 'rejected', 'resolved']).toContain(event.status);
      expect(event.evidence).toBeInstanceOf(Array);
      expect(event.evidence.length).toBeGreaterThan(0);
    });
  });

  it('validates Report contract per docs/EVENT_SCHEMAS.md#4-report', () => {
    MOCK_REPORTS.forEach((report: Report) => {
      expect(report.report_id).toMatch(/^rep-/);
      expect(report.event_id).toMatch(/^evt-/);
      expect(report.submitted_by).toBeDefined();
      expect(report.submitted_at).toBeDefined();
      expect(['low', 'medium', 'high', 'urgent']).toContain(report.priority);
      expect(['pending', 'scheduled', 'in_progress', 'repaired', 'rejected']).toContain(report.resolution);
      expect(['pending', 'approved', 'resolved']).toContain(report.status);
    });
  });
});
