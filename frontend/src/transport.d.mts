export class ApiError extends Error {
  status: number;
  retryAfter: number;
  constructor(message: string, status: number, retryAfter?: number);
}
export function fetchJson(url: string, options?: RequestInit, timeoutMs?: number): Promise<unknown>;
export function waitForBackend(onWait?: (message: string) => void, options?: {
  read?: () => Promise<unknown>;
  pause?: (ms: number) => Promise<void>;
  now?: () => number;
  timeoutMs?: number;
}): Promise<void>;
