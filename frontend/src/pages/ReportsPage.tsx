import React, { useState } from 'react';
import {
  CheckCircle2,
  Download,
  FileCheck,
  FilePlus,
  Plus,
  RefreshCw,
  Search,
  Wrench,
  X
} from 'lucide-react';
import { PotholeEvent, Report, ReportPriority, ReportResolution } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';

interface ReportsPageProps {
  reports: Report[];
  events: PotholeEvent[];
  onCreateReport: (reportData: Omit<Report, 'report_id' | 'submitted_at'>) => Promise<void>;
  onUpdateReport: (reportId: string, updates: Partial<Report>) => Promise<void>;
  onRefresh: () => void;
  isLoading: boolean;
  isDemo: boolean;
  preselectedEventId?: string | null;
}

export const ReportsPage: React.FC<ReportsPageProps> = ({
  reports,
  events,
  onCreateReport,
  onUpdateReport,
  onRefresh,
  isLoading,
  isDemo,
  preselectedEventId
}) => {
  // Filters
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [resolutionFilter, setResolutionFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Create Modal
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(!!preselectedEventId);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [selectedEventId, setSelectedEventId] = useState<string>(preselectedEventId || (events[0]?.event_id ?? ''));
  const [submittedBy, setSubmittedBy] = useState<string>('Road Inspector S. Nair');
  const [priority, setPriority] = useState<ReportPriority>('high');
  const [resolution, setResolution] = useState<ReportResolution>('scheduled');
  const [notes, setNotes] = useState<string>('');
  const [assignedCrew, setAssignedCrew] = useState<string>('Zone 4 Asphalt Maintenance Crew');
  const [estimatedCost, setEstimatedCost] = useState<number>(18500);

  // Filter application
  const filteredReports = reports.filter((r) => {
    if (priorityFilter !== 'all' && r.priority !== priorityFilter) return false;
    if (resolutionFilter !== 'all' && r.resolution !== resolutionFilter) return false;
    if (searchQuery.trim().length > 0) {
      const q = searchQuery.toLowerCase();
      const matchId = r.report_id.toLowerCase().includes(q);
      const matchEvt = r.event_id.toLowerCase().includes(q);
      const matchNotes = r.notes?.toLowerCase().includes(q);
      const matchCrew = r.assigned_crew?.toLowerCase().includes(q);
      if (!matchId && !matchEvt && !matchNotes && !matchCrew) return false;
    }
    return true;
  });

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEventId) return;

    setIsSubmitting(true);
    try {
      await onCreateReport({
        event_id: selectedEventId,
        submitted_by: submittedBy,
        priority,
        resolution,
        status: resolution === 'repaired' ? 'resolved' : 'approved',
        notes,
        assigned_crew: assignedCrew,
        estimated_cost: Number(estimatedCost)
      });
      setIsCreateModalOpen(false);
      setNotes('');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAdvanceResolution = async (report: Report, nextResolution: ReportResolution) => {
    await onUpdateReport(report.report_id, {
      resolution: nextResolution,
      status: nextResolution === 'repaired' ? 'resolved' : 'approved'
    });
  };

  const exportCsv = () => {
    const headers = ['Report ID', 'Event ID', 'Submitted By', 'Submitted At', 'Priority', 'Resolution', 'Status', 'Cost', 'Notes'];
    const rows = filteredReports.map(r => [
      r.report_id,
      r.event_id,
      `"${r.submitted_by}"`,
      r.submitted_at,
      r.priority,
      r.resolution,
      r.status,
      r.estimated_cost || 0,
      `"${(r.notes || '').replace(/"/g, '""')}"`
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `roadguard_maintenance_reports_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Municipal Maintenance Reports</h1>
          <p className="page-subtitle">
            Manage repair work orders, allocate road maintenance squads, track asphalt laying, and record repair sign-offs.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button className="btn btn-secondary btn-sm" onClick={exportCsv} title="Export CSV for municipal records">
            <Download size={14} />
            <span>Export CSV</span>
          </button>

          <button className="btn btn-secondary btn-sm" onClick={onRefresh} disabled={isLoading}>
            <RefreshCw size={14} className={isLoading ? 'spinner' : ''} />
            <span>Refresh</span>
          </button>

          <button className="btn btn-primary btn-sm" onClick={() => setIsCreateModalOpen(true)}>
            <Plus size={15} />
            <span>New Work Order</span>
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="filter-bar">
        <div className="filter-group">
          <div className="filter-input-wrap">
            <Search size={16} className="filter-input-icon" />
            <input
              type="text"
              placeholder="Search by Report ID, Crew, or Notes..."
              className="filter-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                style={{ position: 'absolute', right: '10px', background: 'transparent', border: 'none', color: 'var(--text-subtle)', cursor: 'pointer' }}
              >
                <X size={14} />
              </button>
            )}
          </div>

          <select
            className="select-dropdown"
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
          >
            <option value="all">All Priorities</option>
            <option value="urgent">Urgent</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select
            className="select-dropdown"
            value={resolutionFilter}
            onChange={(e) => setResolutionFilter(e.target.value)}
          >
            <option value="all">All Resolutions</option>
            <option value="scheduled">Scheduled</option>
            <option value="in_progress">In Progress</option>
            <option value="repaired">Repaired &amp; Closed</option>
            <option value="pending">Pending</option>
          </select>
        </div>

        <div className="filter-group">
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Showing <strong>{filteredReports.length}</strong> reports {isDemo && <span style={{ color: 'var(--amber)' }}>(Demo Data)</span>}
          </span>
        </div>
      </div>

      {/* Reports Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {filteredReports.length === 0 ? (
          <div style={{ padding: '64px 20px', textAlign: 'center', color: 'var(--text-subtle)' }}>
            <FileCheck size={32} style={{ marginBottom: '12px', opacity: 0.5 }} />
            <h3 style={{ color: '#fff', fontSize: '1.1rem', marginBottom: '6px' }}>No maintenance reports found</h3>
            <p style={{ fontSize: '0.85rem' }}>Create a new repair work order or adjust filter selections.</p>
          </div>
        ) : (
          <div className="table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Report ID</th>
                  <th>Linked Event</th>
                  <th>Urgency Priority</th>
                  <th>Workflow Status</th>
                  <th>Assigned Repair Crew</th>
                  <th>Estimated Cost</th>
                  <th>Submitted At</th>
                  <th>Action / Workflow</th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.map((report) => (
                  <tr key={report.report_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--indigo)' }}>
                      {report.report_id}
                    </td>

                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                      {report.event_id}
                    </td>

                    <td>
                      <StatusBadge status={report.priority} type="priority" />
                    </td>

                    <td>
                      <StatusBadge status={report.resolution} type="resolution" />
                    </td>

                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.825rem' }}>
                        <Wrench size={13} color="var(--text-muted)" />
                        <span>{report.assigned_crew || 'Unassigned'}</span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', marginLeft: '19px' }}>
                        By: {report.submitted_by}
                      </div>
                    </td>

                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      {report.estimated_cost ? `₹${report.estimated_cost.toLocaleString()}` : '—'}
                    </td>

                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      {new Date(report.submitted_at).toLocaleDateString([], {
                        month: 'short',
                        day: 'numeric'
                      })}
                    </td>

                    <td>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        {report.resolution === 'scheduled' && (
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => handleAdvanceResolution(report, 'in_progress')}
                            title="Mark repairs in progress"
                          >
                            Start Work
                          </button>
                        )}

                        {report.resolution === 'in_progress' && (
                          <button
                            className="btn btn-primary btn-sm"
                            onClick={() => handleAdvanceResolution(report, 'repaired')}
                            title="Mark pothole repaired & closed"
                          >
                            <CheckCircle2 size={13} />
                            <span>Mark Repaired</span>
                          </button>
                        )}

                        {report.resolution === 'repaired' && (
                          <span style={{ fontSize: '0.75rem', color: 'var(--emerald)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <CheckCircle2 size={13} />
                            <span>Verified</span>
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create New Report Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create Municipal Maintenance Work Order"
        maxWidth="600px"
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', width: '100%' }}>
            <button className="btn btn-secondary btn-sm" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </button>
            <button
              className="btn btn-primary btn-sm"
              onClick={handleCreateSubmit}
              disabled={isSubmitting || !selectedEventId}
            >
              <FilePlus size={14} />
              <span>{isSubmitting ? 'Submitting Order...' : 'Dispatch Work Order'}</span>
            </button>
          </div>
        }
      >
        <form onSubmit={handleCreateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="form-group">
            <label className="form-label">Target Pothole Event</label>
            <select
              className="form-control"
              value={selectedEventId}
              onChange={(e) => setSelectedEventId(e.target.value)}
              required
            >
              {events.map((evt) => (
                <option key={evt.event_id} value={evt.event_id}>
                  {evt.event_id} — {evt.location?.road_name || 'Highway'} (Conf: {Math.round(evt.confidence * 100)}%)
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div className="form-group">
              <label className="form-label">Urgency Priority</label>
              <select
                className="form-control"
                value={priority}
                onChange={(e) => setPriority(e.target.value as ReportPriority)}
              >
                <option value="urgent">Urgent (Immediate Traffic Risk)</option>
                <option value="high">High (&lt; 24h Dispatch)</option>
                <option value="medium">Medium (Scheduled Batch)</option>
                <option value="low">Low (Routine Surface Plan)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Initial Resolution Status</label>
              <select
                className="form-control"
                value={resolution}
                onChange={(e) => setResolution(e.target.value as ReportResolution)}
              >
                <option value="scheduled">Scheduled for Repair</option>
                <option value="in_progress">Dispatched / In Progress</option>
                <option value="pending">Pending Field Audit</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div className="form-group">
              <label className="form-label">Reporting Authority / Inspector</label>
              <input
                type="text"
                className="form-control"
                value={submittedBy}
                onChange={(e) => setSubmittedBy(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Estimated Repair Cost (₹)</label>
              <input
                type="number"
                className="form-control"
                value={estimatedCost}
                onChange={(e) => setEstimatedCost(Number(e.target.value))}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Assigned Maintenance Squad / Contractor</label>
            <input
              type="text"
              className="form-control"
              value={assignedCrew}
              onChange={(e) => setAssignedCrew(e.target.value)}
              placeholder="e.g. Zone 4 Rapid Patch Squad"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Technical Notes &amp; Repair Instructions</label>
            <textarea
              className="form-control"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Describe road surface condition, required patch mix (cold mix / mastic asphalt), traffic diversions, etc."
            />
          </div>
        </form>
      </Modal>
    </div>
  );
};
