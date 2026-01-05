import { useEffect, useRef, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';

interface UseInactivityTimeoutOptions {
  timeoutMinutes: number;
  warningMinutes?: number;
  onTimeout: () => void;
  enabled: boolean;
}

export function useInactivityTimeout({
  timeoutMinutes,
  warningMinutes = 1,
  onTimeout,
  enabled
}: UseInactivityTimeoutOptions) {
  const { toast } = useToast();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const warningRef = useRef<NodeJS.Timeout | null>(null);
  const lastActivityRef = useRef<number>(Date.now());
  const hasWarnedRef = useRef<boolean>(false);

  const clearTimers = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (warningRef.current) {
      clearTimeout(warningRef.current);
      warningRef.current = null;
    }
  }, []);

  const handleTimeout = useCallback(() => {
    console.log('[Inactivity] Session timeout - logging out user');
    toast({
      title: "Session Expired",
      description: "You have been logged out due to inactivity.",
      variant: "destructive",
    });
    onTimeout();
  }, [onTimeout, toast]);

  const showWarning = useCallback(() => {
    if (!hasWarnedRef.current) {
      hasWarnedRef.current = true;
      toast({
        title: "Session Expiring Soon",
        description: `Your session will expire in ${warningMinutes} minute${warningMinutes > 1 ? 's' : ''} due to inactivity.`,
        duration: 30000,
      });
    }
  }, [warningMinutes, toast]);

  const resetTimer = useCallback(() => {
    if (!enabled) return;

    lastActivityRef.current = Date.now();
    hasWarnedRef.current = false;
    
    // Store last activity in localStorage for cross-tab sync
    localStorage.setItem('last_activity', lastActivityRef.current.toString());

    clearTimers();

    const timeoutMs = timeoutMinutes * 60 * 1000;
    const warningMs = (timeoutMinutes - warningMinutes) * 60 * 1000;

    // Set warning timer
    if (warningMs > 0) {
      warningRef.current = setTimeout(showWarning, warningMs);
    }

    // Set logout timer
    timeoutRef.current = setTimeout(handleTimeout, timeoutMs);
  }, [enabled, timeoutMinutes, warningMinutes, clearTimers, showWarning, handleTimeout]);

  // Check for activity in other tabs
  const checkCrossTabActivity = useCallback(() => {
    const storedActivity = localStorage.getItem('last_activity');
    if (storedActivity) {
      const storedTime = parseInt(storedActivity, 10);
      if (storedTime > lastActivityRef.current) {
        // Activity happened in another tab, reset our timer
        lastActivityRef.current = storedTime;
        resetTimer();
      }
    }
  }, [resetTimer]);

  useEffect(() => {
    if (!enabled) {
      clearTimers();
      return;
    }

    // Activity events to track
    const events = [
      'mousedown',
      'mousemove',
      'keydown',
      'scroll',
      'touchstart',
      'click',
      'wheel'
    ];

    // Throttle reset to avoid excessive timer resets
    let throttleTimeout: NodeJS.Timeout | null = null;
    const throttledReset = () => {
      if (!throttleTimeout) {
        throttleTimeout = setTimeout(() => {
          throttleTimeout = null;
          resetTimer();
        }, 1000); // Only reset once per second max
      }
    };

    // Add event listeners
    events.forEach(event => {
      document.addEventListener(event, throttledReset, { passive: true });
    });

    // Listen for storage events (cross-tab sync)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'last_activity') {
        checkCrossTabActivity();
      }
    };
    window.addEventListener('storage', handleStorageChange);

    // Initial timer setup
    resetTimer();

    // Periodic check for cross-tab activity
    const crossTabInterval = setInterval(checkCrossTabActivity, 10000);

    return () => {
      clearTimers();
      events.forEach(event => {
        document.removeEventListener(event, throttledReset);
      });
      window.removeEventListener('storage', handleStorageChange);
      if (throttleTimeout) clearTimeout(throttleTimeout);
      clearInterval(crossTabInterval);
    };
  }, [enabled, resetTimer, clearTimers, checkCrossTabActivity]);

  return {
    resetTimer,
    lastActivity: lastActivityRef.current
  };
}
