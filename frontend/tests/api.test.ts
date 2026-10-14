import { describe, it, expect, beforeEach } from 'vitest';
import { apiClient } from '../src/api/client';

describe('RoadGuardApiClient Integration & Fallback Suite', () => {
  beforeEach(() => {
    // Ensure test runs in isolated demo mode
    apiClient.setForceDemoMode(true);
  });

  it('correctly reads base URL configuration without trailing slash', () => {
    apiClient.setBaseUrl('http://api.roadguard.internal:8000/');
    expect(apiClient.getBaseUrl()).toBe('http://api.roadguard.internal:8000');
  });

  it('fetches events with confidence filtering', async () => {
    const { events, isDemo } = await apiClient.getEvents({ min_confidence: 0.85 });
    expect(isDemo).toBe(true);
    expect(events.length).toBeGreaterThan(0);
    events.forEach(e => {
      expect(e.confidence).toBeGreaterThanOrEqual(0.85);
    });
  });

  it('fetches events with status filtering', async () => {
    const { events } = await apiClient.getEvents({ status: 'confirmed' });
    events.forEach(e => {
      expect(e.status).toBe('confirmed');
    });
  });

  it('updates event status successfully in local state', async () => {
    const { events } = await apiClient.getEvents();
    const target = events[0];
    const newStatus = target.status === 'confirmed' ? 'resolved' : 'confirmed';

    const res = await apiClient.updateEventStatus(target.event_id, newStatus);
    expect(res.success).toBe(true);
    expect(res.event?.status).toBe(newStatus);

    const check = await apiClient.getEventById(target.event_id);
    expect(check.event?.status).toBe(newStatus);
  });

  it('creates and manages maintenance reports', async () => {
    const createRes = await apiClient.createReport({
      event_id: 'evt-2026-0091',
      submitted_by: 'Test Inspector',
      priority: 'urgent',
      resolution: 'scheduled',
      status: 'approved',
      notes: 'Automated test work order',
      assigned_crew: 'Test Unit Alpha',
      estimated_cost: 15000
    });

    expect(createRes.report.report_id).toMatch(/^rep-/);
    expect(createRes.report.submitted_at).toBeDefined();

    // Advance resolution
    const updateRes = await apiClient.updateReport(createRes.report.report_id, {
      resolution: 'in_progress'
    });
    expect(updateRes.report?.resolution).toBe('in_progress');
  });
});
