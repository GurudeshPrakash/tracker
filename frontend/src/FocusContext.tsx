import React, { createContext, useContext, useState, useEffect, ReactNode, useRef } from 'react';

export interface FocusContextType {
  isFocusMode: boolean;
  isRunning: boolean;
  seconds: number;
  activeTopic: string;
  setActiveTopic: (topic: string) => void;
  startFocus: (topic?: string) => void;
  pauseFocus: () => void;
  resumeFocus: () => void;
  toggleRunning: () => void;
  resetTimer: () => void;
  stopFocus: () => void;
  isTabAllowed: (tabId: string) => boolean;
  toastMessage: string | null;
  clearToast: () => void;
  triggerLockedNotice: (tabLabel?: string) => void;
  formatTime: (totalSeconds: number) => string;
}

const STORAGE_KEY = 'flux_focus_session_state';

export const formatFocusTime = (totalSeconds: number): string => {
  const hrs = Math.floor(totalSeconds / 3600);
  const mins = Math.floor((totalSeconds % 3600) / 60);
  const secs = totalSeconds % 60;
  if (hrs > 0) {
    return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
};

const FocusContext = createContext<FocusContextType | undefined>(undefined);

export const FocusProvider: React.FC<{ children: ReactNode; onNavigateToTab?: (tab: string) => void }> = ({
  children,
  onNavigateToTab,
}) => {
  const [isFocusMode, setIsFocusMode] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        return Boolean(parsed.isFocusMode);
      }
    } catch (e) {
      // ignore parse errors
    }
    return false;
  });

  const [isRunning, setIsRunning] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        return Boolean(parsed.isRunning && parsed.isFocusMode);
      }
    } catch (e) {
      // ignore
    }
    return false;
  });

  const [seconds, setSeconds] = useState<number>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.isFocusMode) {
          let extra = 0;
          if (parsed.isRunning && parsed.lastSavedTimestamp) {
            extra = Math.max(0, Math.floor((Date.now() - parsed.lastSavedTimestamp) / 1000));
          }
          return (parsed.seconds || 0) + extra;
        }
      }
    } catch (e) {
      // ignore
    }
    return 0;
  });

  const [activeTopic, setActiveTopic] = useState<string>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        return parsed.activeTopic || 'Deep Study Session';
      }
    } catch (e) {
      // ignore
    }
    return 'Deep Study Session';
  });

  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const toastTimeoutRef = useRef<number | null>(null);

  // Sync to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          isFocusMode,
          isRunning,
          seconds,
          activeTopic,
          lastSavedTimestamp: Date.now(),
        })
      );
    } catch (e) {
      // ignore
    }
  }, [isFocusMode, isRunning, seconds, activeTopic]);

  // Timer tick
  useEffect(() => {
    let interval: any = null;
    if (isRunning && isFocusMode) {
      interval = setInterval(() => {
        setSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRunning, isFocusMode]);

  const clearToast = () => {
    setToastMessage(null);
    if (toastTimeoutRef.current) {
      window.clearTimeout(toastTimeoutRef.current);
      toastTimeoutRef.current = null;
    }
  };

  const triggerLockedNotice = (tabLabel?: string) => {
    clearToast();
    setToastMessage(
      `🔒 Focus Mode Active: Only Goals and Learning tabs work right now. End or pause focus mode to open ${tabLabel || 'other tabs'}.`
    );
    toastTimeoutRef.current = window.setTimeout(() => {
      setToastMessage(null);
      toastTimeoutRef.current = null;
    }, 4000);
  };

  const startFocus = (topic?: string) => {
    setIsFocusMode(true);
    setIsRunning(true);
    if (topic && topic.trim()) {
      setActiveTopic(topic.trim());
    }
    if (onNavigateToTab) {
      onNavigateToTab('learning');
    }
  };

  const pauseFocus = () => {
    setIsRunning(false);
  };

  const resumeFocus = () => {
    setIsFocusMode(true);
    setIsRunning(true);
  };

  const toggleRunning = () => {
    if (!isFocusMode) {
      startFocus();
    } else {
      setIsRunning((prev) => !prev);
    }
  };

  const resetTimer = () => {
    setSeconds(0);
    setIsRunning(false);
  };

  const stopFocus = () => {
    setIsFocusMode(false);
    setIsRunning(false);
    setSeconds(0);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      // ignore
    }
  };

  const isTabAllowed = (tabId: string): boolean => {
    if (!isFocusMode) return true;
    return tabId === 'learning' || tabId === 'goals';
  };

  return (
    <FocusContext.Provider
      value={{
        isFocusMode,
        isRunning,
        seconds,
        activeTopic,
        setActiveTopic,
        startFocus,
        pauseFocus,
        resumeFocus,
        toggleRunning,
        resetTimer,
        stopFocus,
        isTabAllowed,
        toastMessage,
        clearToast,
        triggerLockedNotice,
        formatTime: formatFocusTime,
      }}
    >
      {children}
    </FocusContext.Provider>
  );
};

export const useFocusMode = (): FocusContextType => {
  const context = useContext(FocusContext);
  if (!context) {
    throw new Error('useFocusMode must be used within a FocusProvider');
  }
  return context;
};
