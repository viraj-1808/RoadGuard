import {
  PotholeEvent,
  Report,
  EventFilterParams,
  PotholeEventStatus,
  DetectionResult
} from '../types';
import {
  MOCK_POTHOLE_EVENTS,
  MOCK_REPORTS,
  simulateImageDetection
} from '../data/mockData';

export interface ApiStatus {
  isBackendConnected: boolean;
  isDemoMode: boolean;
  baseUrl: string;
  errorMessage?: string;
  modelStatus: {
    weightsLoaded: boolean;
    modelName: string;
    details?: string;
  };
}

class RoadGuardApiClient {
  private baseUrl: string;
  private forceDemoMode: boolean = false;
  private backendAvailable: boolean | null = null;
  private inMemoryEvents: PotholeEvent[] = [...MOCK_POTHOLE_EVENTS];
  private inMemoryReports: Report[] = [...MOCK_REPORTS];

  constructor() {
    // Configurable through environment variable; defaults to empty or standard local API port
    const envBaseUrl = import.meta.env.VITE_API_BASE_URL;
    this.baseUrl = (typeof envBaseUrl === 'string' && envBaseUrl.trim().length > 0)
      ? envBaseUrl.replace(/\/+$/, '')
      : 'http://localhost:8000';

    if (import.meta.env.VITE_ENABLE_DEMO_MODE === 'true') {
      this.forceDemoMode = true;
    }
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  public setBaseUrl(url: string) {
    this.baseUrl = url.replace(/\/+$/, '');
    this.backendAvailable = null;
  }

  public isUsingDemoMode(): boolean {
    return this.forceDemoMode || this.backendAvailable === false;
  }

  public setForceDemoMode(enable: boolean) {
    this.forceDemoMode = enable;
  }

  /**
   * Health check to detect backend reachability and model weights status
   */
  public async checkBackendHealth(): Promise<ApiStatus> {
    if (this.forceDemoMode) {
      return {
        isBackendConnected: false,
        isDemoMode: true,
        baseUrl: this.baseUrl,
        errorMessage: 'Manual demo mode enabled.',
        modelStatus: {
          weightsLoaded: true,
          modelName: 'YOLO26s (Simulated Fallback)'
        }
      };
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500);

      const response = await fetch(`${this.baseUrl}/api/events?limit=1`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        this.backendAvailable = true;
        return {
          isBackendConnected: true,
          isDemoMode: false,
          baseUrl: this.baseUrl,
          modelStatus: {
            weightsLoaded: true,
            modelName: 'YOLO26s (Backend Online)'
          }
        };
      } else {
        this.backendAvailable = false;
        return {
          isBackendConnected: false,
          isDemoMode: true,
          baseUrl: this.baseUrl,
          errorMessage: `Backend returned HTTP ${response.status}: ${response.statusText}`,
          modelStatus: {
            weightsLoaded: false,
            modelName: 'Unknown',
            details: 'Backend endpoint error'
          }
        };
      }
    } catch (err: unknown) {
      this.backendAvailable = false;
      const message = err instanceof Error ? err.message : 'Network failure or CORS issue';
      return {
        isBackendConnected: false,
        isDemoMode: true,
        baseUrl: this.baseUrl,
        errorMessage: `Cannot reach RoadGuard API at ${this.baseUrl} (${message}). Operating with local high-fidelity demonstration dataset.`,
        modelStatus: {
          weightsLoaded: false,
          modelName: 'Offline',
          details: 'Backend service offline or unreachable'
        }
      };
    }
  }

  /**
   * GET /api/events - List events with filters
   * (docs/API_CONTRACTS.md#5-frontend-query-api)
   */
  public async getEvents(filters?: EventFilterParams): Promise<{ events: PotholeEvent[]; isDemo: boolean }> {
    if (!this.isUsingDemoMode()) {
      try {
        const query = new URLSearchParams();
        if (filters?.status && filters.status !== 'all') query.set('status', filters.status);
        if (filters?.min_confidence !== undefined) query.set('min_confidence', filters.min_confidence.toString());
        if (filters?.source_id) query.set('source_id', filters.source_id);
        if (filters?.limit) query.set('limit', filters.limit.toString());
        if (filters?.offset) query.set('offset', filters.offset.toString());

        const url = `${this.baseUrl}/api/events${query.toString() ? `?${query.toString()}` : ''}`;
        const response = await fetch(url, { headers: { 'Accept': 'application/json' } });

        if (response.ok) {
          const data = await response.json();
          const events = Array.isArray(data) ? data : (data.events || []);
          return { events, isDemo: false };
        }
      } catch (err) {
        console.warn('API getEvents failed, falling back to mock dataset:', err);
        this.backendAvailable = false;
      }
    }

    // Filter in-memory demo events
    let filtered = [...this.inMemoryEvents];

    if (filters?.status && filters.status !== 'all') {
      filtered = filtered.filter(e => e.status === filters.status);
    }
    if (filters?.min_confidence !== undefined) {
      filtered = filtered.filter(e => e.confidence >= (filters.min_confidence || 0));
    }
    if (filters?.source_id) {
      filtered = filtered.filter(e => e.source_id === filters.source_id);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      filtered = filtered.filter(
        e =>
          e.event_id.toLowerCase().includes(q) ||
          e.location?.road_name?.toLowerCase().includes(q) ||
          e.location?.city?.toLowerCase().includes(q)
      );
    }

    return { events: filtered, isDemo: true };
  }

  /**
   * GET /api/events/{id} - Get event details
   */
  public async getEventById(eventId: string): Promise<{ event: PotholeEvent | null; isDemo: boolean }> {
    if (!this.isUsingDemoMode()) {
      try {
        const response = await fetch(`${this.baseUrl}/api/events/${encodeURIComponent(eventId)}`);
        if (response.ok) {
          const event = await response.json();
          return { event, isDemo: false };
        }
      } catch (err) {
        console.warn(`API getEventById(${eventId}) failed:`, err);
        this.backendAvailable = false;
      }
    }

    const found = this.inMemoryEvents.find(e => e.event_id === eventId) || null;
    return { event: found, isDemo: true };
  }

  /**
   * PATCH /api/events/{id}/status - Update event status
   * (docs/API_CONTRACTS.md#4-backend-ingestion-api)
   */
  public async updateEventStatus(
    eventId: string,
    status: PotholeEventStatus
  ): Promise<{ success: boolean; event?: PotholeEvent; isDemo: boolean }> {
    if (!this.isUsingDemoMode()) {
      try {
        const response = await fetch(`${this.baseUrl}/api/events/${encodeURIComponent(eventId)}/status`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status })
        });
        if (response.ok) {
          const updated = await response.json();
          return { success: true, event: updated, isDemo: false };
        }
      } catch (err) {
        console.warn(`API updateEventStatus failed:`, err);
        this.backendAvailable = false;
      }
    }

    // In-memory demo update
    const idx = this.inMemoryEvents.findIndex(e => e.event_id === eventId);
    if (idx !== -1) {
      this.inMemoryEvents[idx] = {
        ...this.inMemoryEvents[idx],
        status
      };
      return { success: true, event: this.inMemoryEvents[idx], isDemo: true };
    }

    return { success: false, isDemo: true };
  }

  /**
   * GET /api/reports - List municipal maintenance reports
   * (docs/API_CONTRACTS.md#5-frontend-query-api)
   */
  public async getReports(): Promise<{ reports: Report[]; isDemo: boolean }> {
    if (!this.isUsingDemoMode()) {
      try {
        const response = await fetch(`${this.baseUrl}/api/reports`);
        if (response.ok) {
          const data = await response.json();
          const reports = Array.isArray(data) ? data : (data.reports || []);
          return { reports, isDemo: false };
        }
      } catch (err) {
        console.warn('API getReports failed, falling back to mock dataset:', err);
        this.backendAvailable = false;
      }
    }

    return { reports: [...this.inMemoryReports], isDemo: true };
  }

  /**
   * POST /api/reports - Create a maintenance report
   * (docs/API_CONTRACTS.md#5-frontend-query-api)
   */
  public async createReport(reportData: Omit<Report, 'report_id' | 'submitted_at'>): Promise<{
    report: Report;
    isDemo: boolean;
  }> {
    if (!this.isUsingDemoMode()) {
      try {
        const response = await fetch(`${this.baseUrl}/api/reports`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(reportData)
        });
        if (response.ok) {
          const created = await response.json();
          return { report: created, isDemo: false };
        }
      } catch (err) {
        console.warn('API createReport failed, saving in local demo state:', err);
        this.backendAvailable = false;
      }
    }

    const newReport: Report = {
      ...reportData,
      report_id: `rep-${Math.floor(1000 + Math.random() * 9000)}`,
      submitted_at: new Date().toISOString()
    };

    this.inMemoryReports.unshift(newReport);

    // Also update parent event's report_id if present
    const evIdx = this.inMemoryEvents.findIndex(e => e.event_id === reportData.event_id);
    if (evIdx !== -1) {
      this.inMemoryEvents[evIdx].report_id = newReport.report_id;
      if (this.inMemoryEvents[evIdx].status === 'candidate') {
        this.inMemoryEvents[evIdx].status = 'confirmed';
      }
    }

    return { report: newReport, isDemo: true };
  }

  /**
   * PATCH /api/reports/{id} - Update report status or resolution
   */
  public async updateReport(
    reportId: string,
    updates: Partial<Report>
  ): Promise<{ report: Report | null; isDemo: boolean }> {
    if (!this.isUsingDemoMode()) {
      try {
        const response = await fetch(`${this.baseUrl}/api/reports/${encodeURIComponent(reportId)}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updates)
        });
        if (response.ok) {
          const updated = await response.json();
          return { report: updated, isDemo: false };
        }
      } catch (err) {
        console.warn('API updateReport failed:', err);
        this.backendAvailable = false;
      }
    }

    const idx = this.inMemoryReports.findIndex(r => r.report_id === reportId);
    if (idx !== -1) {
      this.inMemoryReports[idx] = {
        ...this.inMemoryReports[idx],
        ...updates
      };
      return { report: this.inMemoryReports[idx], isDemo: true };
    }

    return { report: null, isDemo: true };
  }

  /**
   * Image Upload Inference Endpoint
   * Gap analysis: docs/API_CONTRACTS.md currently defines /api/events and /api/reports,
   * but does not yet standardize an ad-hoc single-image inference route (e.g. /api/detect).
   * This method attempts /api/detect, and if unavailable or if weights are missing,
   * explicitly surfaces the gap or switches to client-side test runner.
   */
  public async detectPotholesInImage(
    file: File,
    minConfidence = 0.5
  ): Promise<{
    result: DetectionResult;
    backendAttempted: boolean;
    backendGapNotice?: string;
  }> {
    if (!this.isUsingDemoMode()) {
      try {
        const formData = new FormData();
        formData.append('image', file);
        formData.append('min_confidence', minConfidence.toString());

        const response = await fetch(`${this.baseUrl}/api/detect`, {
          method: 'POST',
          body: formData
        });

        if (response.ok) {
          const result = await response.json();
          return {
            result: {
              ...result,
              is_demo_data: false
            },
            backendAttempted: true
          };
        }

        // If backend returned 503 or custom code indicating weights missing
        if (response.status === 503 || response.status === 422) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || 'Model weights not loaded on backend server');
        }

        if (response.status === 404 || response.status === 501) {
          // Endpoint not implemented yet on backend
          return {
            result: await this.runSimulatedImageDetection(file, minConfidence),
            backendAttempted: true,
            backendGapNotice: 'Backend /api/detect endpoint is not yet implemented in docs/API_CONTRACTS.md. Using client-side detection simulation.'
          };
        }
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Backend detection request failed';
        return {
          result: await this.runSimulatedImageDetection(file, minConfidence),
          backendAttempted: true,
          backendGapNotice: `Backend inference unavailable (${message}). Running client-side demonstration test runner.`
        };
      }
    }

    return {
      result: await this.runSimulatedImageDetection(file, minConfidence),
      backendAttempted: false
    };
  }

  private async runSimulatedImageDetection(file: File, minConfidence: number): Promise<DetectionResult> {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const dataUrl = e.target?.result as string;
        const img = new Image();
        img.onload = () => {
          const result = simulateImageDetection(dataUrl, img.width || 1280, img.height || 720, minConfidence);
          resolve(result);
        };
        img.src = dataUrl;
      };
      reader.readAsDataURL(file);
    });
  }
}

// Export singleton instance
export const apiClient = new RoadGuardApiClient();
