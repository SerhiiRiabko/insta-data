/**
 * "Open the bot, then wait until the user confirms there" - shared by the
 * Telegram login, Telegram linking and Stars payment flows.
 *
 * The bot tab is opened *before* the API call: browsers only allow
 * window.open inside the click handler itself, and an awaited request in
 * between would get the popup blocked.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

export type FlowState = 'idle' | 'waiting' | 'done' | 'failed' | 'expired';

const POLL_MS = 2000;
const TIMEOUT_MS = 5 * 60 * 1000;

export function openPendingTab(): Window | null {
  if (typeof window === 'undefined') return null;
  return window.open('about:blank', '_blank');
}

export function sendTabTo(tab: Window | null, url: string): void {
  if (tab && !tab.closed) tab.location.href = url;
  else window.location.href = url;
}

/**
 * `check` resolves to 'pending' | 'done' | 'failed'; polling stops on
 * anything but 'pending', on timeout, or on unmount.
 */
export function useTelegramPoll(check: () => Promise<'pending' | 'done' | 'failed'>) {
  const [state, setState] = useState<FlowState>('idle');
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const started = useRef(0);
  const checkRef = useRef(check);
  checkRef.current = check;

  const stop = useCallback(() => {
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
  }, []);

  const start = useCallback(() => {
    stop();
    started.current = Date.now();
    setState('waiting');
    timer.current = setInterval(async () => {
      if (Date.now() - started.current > TIMEOUT_MS) {
        stop();
        setState('expired');
        return;
      }
      try {
        const result = await checkRef.current();
        if (result !== 'pending') {
          stop();
          setState(result);
        }
      } catch {
        stop();
        setState('expired');
      }
    }, POLL_MS);
  }, [stop]);

  useEffect(() => stop, [stop]);

  const reset = useCallback(() => {
    stop();
    setState('idle');
  }, [stop]);

  return { state, start, reset };
}
