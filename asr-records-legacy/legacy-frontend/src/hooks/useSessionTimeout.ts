import { useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

const DEFAULT_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes
const ACTIVITY_EVENTS: (keyof WindowEventMap)[] = ['mousemove', 'keydown', 'click'];

/**
 * Monitors user activity and logs out after inactivity timeout.
 * Only call inside a component that is rendered when the user is authenticated.
 */
export const useSessionTimeout = (
  logoutFn: () => void,
  timeoutMs: number = DEFAULT_TIMEOUT_MS,
) => {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const navigate = useNavigate();

  const resetTimer = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      toast.error('Session timed out due to inactivity');
      logoutFn();
      navigate('/login');
    }, timeoutMs);
  }, [logoutFn, timeoutMs, navigate]);

  useEffect(() => {
    // Start the timer immediately
    resetTimer();

    // Reset on user activity
    const handler = () => resetTimer();
    ACTIVITY_EVENTS.forEach((evt) => window.addEventListener(evt, handler));

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      ACTIVITY_EVENTS.forEach((evt) => window.removeEventListener(evt, handler));
    };
  }, [resetTimer]);
};
