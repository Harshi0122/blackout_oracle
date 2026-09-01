// In local development Vite proxies this path to FastAPI, avoiding a separate
// CORS configuration in the browser.  Deployments can override it with
// VITE_API_BASE_URL (for example, https://api.example.com).
const BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public detail?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

type QueryValue = string | number | boolean | null | undefined;
type Query = Record<string, QueryValue>;

function withQuery(path: string, query?: Query) {
  if (!query) return path;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null) params.set(key, String(value));
  }
  const suffix = params.toString();
  return suffix ? `${path}?${suffix}` : path;
}

async function request<T>(
  method: string,
  path: string,
  options: { body?: unknown; signal?: AbortSignal; query?: Query } = {},
): Promise<T> {
  const url = `${BASE}${withQuery(path, options.query)}`;
  const response = await fetch(url, {
    method,
    signal: options.signal,
    headers: {
      Accept: 'application/json',
      ...(options.body !== undefined ? { 'Content-Type': 'application/json' } : {}),
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    let detail: unknown;
    try { detail = await response.json(); } catch { detail = await response.text().catch(() => undefined); }
    const message = typeof detail === 'object' && detail && 'detail' in detail
      ? String((detail as { detail: unknown }).detail)
      : `${method} ${path} failed (${response.status})`;
    throw new ApiError(message, response.status, detail);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const apiGet = <T>(path: string, signal?: AbortSignal, query?: Query) =>
  request<T>('GET', path, { signal, query });

export const apiPost = <T>(path: string, body?: unknown, signal?: AbortSignal, query?: Query) =>
  request<T>('POST', path, { body, signal, query });

export const apiPatch = <T>(path: string, body?: unknown, signal?: AbortSignal) =>
  request<T>('PATCH', path, { body, signal });

export const apiDelete = <T>(path: string, signal?: AbortSignal) =>
  request<T>('DELETE', path, { signal });

export const apiBaseUrl = BASE;
