import test from 'node:test';
import assert from 'node:assert/strict';
import { ApiError, fetchJson, waitForBackend } from '../src/transport.mjs';

test('a waking-host HTML response becomes a recoverable service error', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => new Response('<html>Starting</html>'));
  await assert.rejects(fetchJson('/api/company/session'), (e) => e instanceof ApiError && e.status === 503);
});

test('a failed business POST is never automatically submitted twice', async (t) => {
  const mock = t.mock.method(globalThis, 'fetch', async () => { throw new TypeError('network'); });
  await assert.rejects(fetchJson('/api/company/ask', { method: 'POST', body: '{}' }), /Saved investigations/);
  assert.equal(mock.mock.callCount(), 1);
});

test('provider admission errors retain Retry-After for the caller', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify({ detail: 'Busy, please retry.' }), { status: 429, headers: { 'Retry-After': '15' } }));
  await assert.rejects(fetchJson('/api/company/ask', { method: 'POST' }), (e) => e.status === 429 && e.retryAfter === 15);
});

test('readiness recovers across a cold start and stops when ready', async () => {
  let calls = 0;
  const states = [];
  await waitForBackend((s) => states.push(s), {
    read: async () => { if (++calls === 1) throw new ApiError('Starting', 503); return { status: 'ready' }; },
    pause: async () => {},
  });
  assert.equal(calls, 2);
  assert.equal(states.length, 2);
});

test('readiness retries end instead of leaving an indefinite loading state', async () => {
  let time = 0;
  await assert.rejects(waitForBackend(() => {}, {
    read: async () => { throw new ApiError('Starting', 503); },
    now: () => time,
    pause: async (ms) => { time += ms; },
    timeoutMs: 3000,
  }), /taking longer to start/);
});

test('a stalled request is aborted without replay', async (t) => {
  const mock = t.mock.method(globalThis, 'fetch', (_url, { signal }) => new Promise((_resolve, reject) => {
    signal.addEventListener('abort', () => reject(new Error('Aborted')), { once: true });
  }));
  await assert.rejects(fetchJson('/api/company/ask', { method: 'POST' }, 5), /interrupted/);
  assert.equal(mock.mock.callCount(), 1);
});
