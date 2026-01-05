import { format, formatDistanceToNow } from "date-fns";

/**
 * Parse a UTC timestamp from the backend into a Date object.
 * Handles timestamps both with and without timezone indicators.
 */
export function parseUTCTimestamp(timestamp: string): Date {
  if (!timestamp) return new Date();
  
  // If timestamp doesn't end with Z or timezone offset, append Z to treat as UTC
  const normalizedTimestamp = timestamp.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(timestamp)
    ? timestamp
    : timestamp + 'Z';
  
  return new Date(normalizedTimestamp);
}

/**
 * Format timestamp to local date and time (e.g., "Jan 05, 17:48:49")
 */
export function formatLocalDateTime(timestamp: string): string {
  try {
    const date = parseUTCTimestamp(timestamp);
    return format(date, "MMM dd, HH:mm:ss");
  } catch {
    return timestamp;
  }
}

/**
 * Format timestamp to local date only (e.g., "Jan 05, 2026")
 */
export function formatLocalDate(timestamp: string): string {
  try {
    const date = parseUTCTimestamp(timestamp);
    return format(date, "MMM dd, yyyy");
  } catch {
    return timestamp;
  }
}

/**
 * Format timestamp to local time only (e.g., "5:48:49 PM")
 */
export function formatLocalTime(timestamp: string): string {
  try {
    const date = parseUTCTimestamp(timestamp);
    return format(date, "h:mm:ss a");
  } catch {
    return timestamp;
  }
}

/**
 * Format to full local datetime with timezone indication (e.g., "January 5, 2026 at 5:48:49 PM")
 */
export function formatFullLocalDateTime(timestamp: string): string {
  try {
    const date = parseUTCTimestamp(timestamp);
    return format(date, "PPpp");
  } catch {
    return timestamp;
  }
}

/**
 * Format relative time (e.g., "5 minutes ago", "2 hours ago")
 */
export function formatRelativeTime(timestamp: string): string {
  try {
    const date = parseUTCTimestamp(timestamp);
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return timestamp;
  }
}

/**
 * Format relative time in short form (e.g., "5m ago", "2h ago")
 */
export function formatShortRelativeTime(timestamp: string): string {
  try {
    const date = parseUTCTimestamp(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return formatLocalDateTime(timestamp);
  } catch {
    return timestamp;
  }
}

/**
 * Get the browser's timezone abbreviation (e.g., "IST", "PST", "EST")
 */
export function getTimezoneAbbr(): string {
  try {
    const date = new Date();
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const shortTz = date.toLocaleTimeString('en-US', { timeZoneName: 'short' }).split(' ').pop();
    return shortTz || timeZone;
  } catch {
    return "Local";
  }
}

/**
 * Get the browser's full timezone name (e.g., "Asia/Kolkata", "America/Los_Angeles")
 */
export function getTimezoneName(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch {
    return "Unknown";
  }
}
