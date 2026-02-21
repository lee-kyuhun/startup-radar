// API 클라이언트: fetch 래퍼 + Envelope 파싱
// 기준: API_Contract.md (Base URL: NEXT_PUBLIC_API_BASE_URL)

import { ApiEnvelope } from '@/types/api';

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export class ApiClientError extends Error {
  constructor(
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = 'ApiClientError';
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });

  if (!res.ok && res.status !== 200) {
    throw new ApiClientError('HTTP_ERROR', `HTTP ${res.status}: ${res.statusText}`);
  }

  const envelope: ApiEnvelope<T> = await res.json();

  if (envelope.error) {
    throw new ApiClientError(envelope.error.code, envelope.error.message);
  }

  return envelope.data as T;
}

export function buildSearchParams(params: Record<string, string | number | boolean | undefined | null>): string {
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      sp.set(key, String(value));
    }
  }
  const str = sp.toString();
  return str ? `?${str}` : '';
}

// --- Feed API ---

import type { FeedItem, SourceWithStatus, StatusData } from '@/types/api';
import type { ApiEnvelope as Envelope, PaginationMeta } from '@/types/api';

export interface FeedResponse {
  items: FeedItem[];
  meta: PaginationMeta;
}

export async function fetchFeed(params: {
  tab?: string;
  cursor?: string;
  limit?: number;
  keyword?: string;
}): Promise<FeedResponse> {
  const qs = buildSearchParams({
    tab: params.tab ?? 'news',
    cursor: params.cursor,
    limit: params.limit ?? 20,
    keyword: params.keyword,
  });
  const url = `/api/v1/feed/${qs}`;
  const res = await fetch(`${BASE_URL}${url}`, {
    headers: { 'Content-Type': 'application/json' },
  });
  const envelope: Envelope<FeedItem[]> = await res.json();
  if (envelope.error) throw new ApiClientError(envelope.error.code, envelope.error.message);
  return {
    items: envelope.data ?? [],
    meta: envelope.meta ?? { next_cursor: null, has_more: false, total_count: null },
  };
}

export async function fetchSearch(params: {
  q: string;
  cursor?: string;
  limit?: number;
}): Promise<FeedResponse> {
  const qs = buildSearchParams({
    q: params.q,
    cursor: params.cursor,
    limit: params.limit ?? 20,
  });
  const res = await fetch(`${BASE_URL}/api/v1/search/${qs}`, {
    headers: { 'Content-Type': 'application/json' },
  });
  const envelope: Envelope<FeedItem[]> = await res.json();
  if (envelope.error) throw new ApiClientError(envelope.error.code, envelope.error.message);
  return {
    items: envelope.data ?? [],
    meta: envelope.meta ?? { next_cursor: null, has_more: false, total_count: 0 },
  };
}

export async function fetchStatus(): Promise<StatusData> {
  return request<StatusData>('/api/v1/status/');
}

export async function fetchSources(): Promise<SourceWithStatus[]> {
  return request<SourceWithStatus[]>('/api/v1/sources/');
}
