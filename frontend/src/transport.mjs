import { COMPANY_QUESTION_GUIDANCE } from './queryInput.mjs';

// Network recovery for read-only readiness checks. Business POSTs are never replayed.
export class ApiError extends Error {
  constructor(message, status, retryAfter = 0) {
    super(message);
    this.status = status;
    this.retryAfter = retryAfter;
  }
}

export async function fetchJson(url, options = {}, timeoutMs = 45000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    let data;
    try {
      data = await response.json();
    } catch {
      throw new ApiError(
        'The service is starting or temporarily unavailable. Reconnect in a moment.',
        response.ok ? 503 : response.status,
      );
    }
    if (!response.ok) {
      let message = typeof data.detail === 'string' ? data.detail : 'The request could not be completed. Please retry shortly.';
      if (response.status === 422 && Array.isArray(data.detail)) {
        const fields = data.detail.map((item) => item.loc?.[1]);
        if (fields.every((field) => field === 'question') && fields.length) {
          message = data.detail.some((item) => item.type === 'string_too_long')
            ? 'Please keep your question under 1,500 characters.'
            : COMPANY_QUESTION_GUIDANCE;
        } else if (fields.some((field) => field === 'effective_at' || field === 'known_at')) {
          message = 'Choose valid dates for “Effective on” and “Known by”, then try again.';
        } else {
          message = 'Some request details are missing or invalid. Review your question, dates, and workspace.';
        }
      }
      throw new ApiError(
        message,
        response.status,
        Number(response.headers.get('Retry-After')) || 0,
      );
    }
    return data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    const investigation = String(url).endsWith('/company/ask');
    throw new ApiError(
      investigation
        ? 'The investigation connection was interrupted. It may still finish; check Saved investigations before submitting it again.'
        : 'The connection was interrupted. Please reconnect and try again.',
      0,
    );
  } finally {
    clearTimeout(timer);
  }
}

export async function waitForBackend(onWait = () => {}, options = {}) {
  const read = options.read || (() => fetchJson('/readyz', {}, 6000));
  const pause = options.pause || ((ms) => new Promise((resolve) => setTimeout(resolve, ms)));
  const now = options.now || Date.now;
  const deadline = now() + (options.timeoutMs || 105000);
  let attempt = 0;
  while (true) {
    onWait(attempt === 0 ? 'Connecting to company memory…' : 'Starting the database. Free hosting can take about a minute to wake…');
    try {
      const result = await read();
      if (result?.status === 'ready') return;
    } catch (error) {
      if (error instanceof ApiError && error.status === 403) throw error;
    }
    if (now() >= deadline) {
      throw new ApiError('The service is taking longer to start. Please reconnect shortly.', 503);
    }
    await pause(Math.min(1500 + attempt++ * 500, 5000));
  }
}
