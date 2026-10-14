import React, { useState, useEffect, useCallback } from 'react';
import { apiClient, ApiStatus } from './api/client';
import { Camera, PotholeEvent, PotholeEventStatus, Report, SystemOverviewStats } from './types';
import { MOCK_CAMERAS, MOCK_SYSTEM_STATS } from './data/mockData';
import { Navbar, ActiveTab } from './components/Navbar';
import { NotificationBanner } from './components/NotificationBanner';
import { DashboardPage } from './pages/DashboardPage';
import { EventsPage } from './pages/EventsPage';
import { DetectionStudio } from './pages/DetectionStudio';
import { ReportsPage } from './pages/ReportsPage';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('dashboard');
  const [apiStatus, setApiStatus] = useState<ApiStatus | null>(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState<boolean>(false);

  // Core Data
  const [events, setEvents] = useState<PotholeEvent[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [cameras] = useState<Camera[]>(MOCK_CAMERAS);
  const [stats, setStats] = useState<SystemOverviewStats>(MOCK_SYSTEM_STATS);
  const [selectedEvent, setSelectedEvent] = useState<PotholeEvent | null>(null);
  const [preselectedEventIdForReport, setPreselectedEventIdForReport] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [dismissDemoBanner, setDismissDemoBanner] = useState<boolean>(false);

  // Check health and initialize
  const refreshHealth = useCallback(async () => {
    setIsCheckingHealth(true);
    try {
      const status = await apiClient.checkBackendHealth();
      setApiStatus(status);
    } catch (err: unknown) {
      console.warn('Backend health check error:', err);
    } finally {
      setIsCheckingHealth(false);
    }
  }, []);

  // Fetch events and reports
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setGlobalError(null);
    try {
      const [eventsRes, reportsRes] = await Promise.all([
        apiClient.getEvents(),
        apiClient.getReports()
      ]);

      setEvents(eventsRes.events);
      setReports(reportsRes.reports);

      // Recompute stats
      const confirmed = eventsRes.events.filter(e => e.status === 'confirmed').length;
      const repaired = reportsRes.reports.filter(r => r.resolution === 'repaired').length;
      const urgent = reportsRes.reports.filter(r => r.priority === 'urgent' || r.priority === 'high').length;
      const avgConf = eventsRes.events.length > 0
        ? eventsRes.events.reduce((acc, cur) => acc + cur.confidence, 0) / eventsRes.events.length
        : 0.85;

      setStats({
        total_events: eventsRes.events.length,
        confirmed_potholes: confirmed,
        pending_inspection: eventsRes.events.filter(e => e.status === 'pending' || e.status === 'candidate').length,
        repaired_count: repaired,
        active_cameras: MOCK_CAMERAS.filter(c => c.active).length,
        average_confidence: avgConf,
        urgent_reports: urgent
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch data from API';
      setGlobalError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshHealth();
    fetchData();
  }, [refreshHealth, fetchData]);

  // Toggle demo mode
  const handleToggleDemoMode = async () => {
    const nextMode = !apiClient.isUsingDemoMode();
    apiClient.setForceDemoMode(nextMode);
    await refreshHealth();
    await fetchData();
  };

  // Event status update
  const handleUpdateEventStatus = async (eventId: string, newStatus: PotholeEventStatus) => {
    const res = await apiClient.updateEventStatus(eventId, newStatus);
    if (res.success && res.event) {
      setEvents(prev => prev.map(e => e.event_id === eventId ? res.event! : e));
      if (selectedEvent && selectedEvent.event_id === eventId) {
        setSelectedEvent(res.event);
      }
    }
  };

  // Create report
  const handleCreateReport = async (reportData: Omit<Report, 'report_id' | 'submitted_at'>) => {
    const res = await apiClient.createReport(reportData);
    setReports(prev => [res.report, ...prev]);
    // Also refresh events as event might have updated report_id
    fetchData();
  };

  // Update report
  const handleUpdateReport = async (reportId: string, updates: Partial<Report>) => {
    const res = await apiClient.updateReport(reportId, updates);
    if (res.report) {
      setReports(prev => prev.map(r => r.report_id === reportId ? res.report! : r));
    }
  };

  // Navigate to report creation from event
  const handleCreateReportForEvent = (event: PotholeEvent) => {
    setSelectedEvent(null);
    setPreselectedEventIdForReport(event.event_id);
    setActiveTab('reports');
  };

  return (
    <div className="app-container">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        onTabChange={(tab) => {
          setActiveTab(tab);
          setPreselectedEventIdForReport(null);
        }}
        apiStatus={apiStatus}
        onRefreshHealth={refreshHealth}
        onToggleDemoMode={handleToggleDemoMode}
        isCheckingHealth={isCheckingHealth}
      />

      {/* Main App Canvas */}
      <main className="main-content">
        {/* Global Error Notice */}
        {globalError && (
          <NotificationBanner
            type="error"
            title="API Communication Error"
            message={globalError}
            actionText="Retry Request"
            onAction={fetchData}
            onDismiss={() => setGlobalError(null)}
          />
        )}

        {/* Demo Mode / Backend Offline Banner */}
        {apiStatus?.isDemoMode && !dismissDemoBanner && (
          <NotificationBanner
            type="warning"
            title="Demonstration Mode Active"
            message={`The backend server at ${apiStatus.baseUrl} is unreachable or in demo mode. Displaying verified sample road damage dataset from Indian corridors.`}
            actionText="Check Connection"
            onAction={refreshHealth}
            onDismiss={() => setDismissDemoBanner(true)}
          />
        )}

        {/* Active Page Component */}
        {activeTab === 'dashboard' && (
          <DashboardPage
            stats={stats}
            events={events}
            reports={reports}
            cameras={cameras}
            onSelectEvent={(evt) => setSelectedEvent(evt)}
            onNavigateTab={(tab) => setActiveTab(tab)}
          />
        )}

        {activeTab === 'events' && (
          <EventsPage
            events={events}
            cameras={cameras}
            selectedEvent={selectedEvent}
            onSelectEvent={(evt) => setSelectedEvent(evt)}
            onUpdateEventStatus={handleUpdateEventStatus}
            onCreateReportForEvent={handleCreateReportForEvent}
            onRefresh={fetchData}
            isLoading={isLoading}
            isDemo={apiStatus?.isDemoMode ?? true}
          />
        )}

        {activeTab === 'detection' && <DetectionStudio />}

        {activeTab === 'reports' && (
          <ReportsPage
            reports={reports}
            events={events}
            onCreateReport={handleCreateReport}
            onUpdateReport={handleUpdateReport}
            onRefresh={fetchData}
            isLoading={isLoading}
            isDemo={apiStatus?.isDemoMode ?? true}
            preselectedEventId={preselectedEventIdForReport}
          />
        )}
      </main>
    </div>
  );
};
