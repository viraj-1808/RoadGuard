import React from 'react';
import { PotholeEventStatus, ReportPriority, ReportResolution } from '../types';

interface StatusBadgeProps {
  status: PotholeEventStatus | ReportPriority | ReportResolution | string;
  type?: 'event' | 'priority' | 'resolution';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, type = 'event' }) => {
  const norm = status.toLowerCase();

  let badgeClass = 'badge-pending';
  let label = status;

  if (type === 'priority') {
    if (norm === 'urgent') badgeClass = 'badge-urgent';
    else if (norm === 'high') badgeClass = 'badge-high';
    else if (norm === 'medium') badgeClass = 'badge-medium';
    else badgeClass = 'badge-low';
  } else if (type === 'resolution') {
    if (norm === 'repaired') badgeClass = 'badge-resolved';
    else if (norm === 'in_progress') badgeClass = 'badge-candidate';
    else if (norm === 'scheduled') badgeClass = 'badge-pending';
    else if (norm === 'rejected') badgeClass = 'badge-rejected';
    else badgeClass = 'badge-pending';
  } else {
    // Event status
    if (norm === 'confirmed' || norm === 'approved') badgeClass = 'badge-confirmed';
    else if (norm === 'candidate') badgeClass = 'badge-candidate';
    else if (norm === 'resolved' || norm === 'closed') badgeClass = 'badge-resolved';
    else if (norm === 'rejected') badgeClass = 'badge-rejected';
    else badgeClass = 'badge-pending';
  }

  return (
    <span className={`badge ${badgeClass}`}>
      {label}
    </span>
  );
};
