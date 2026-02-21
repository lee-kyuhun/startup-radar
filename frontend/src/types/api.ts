// API Contract TypeScript 타입 정의
// 기준 문서: .squad/03_architecture/API_Contract.md

export interface ApiEnvelope<T> {
  data: T | null;
  error: ApiError | null;
  meta: PaginationMeta | null;
}

export interface ApiError {
  code: string;
  message: string;
}

export interface PaginationMeta {
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}

export type SourceType = 'news' | 'vc_blog';

export interface Source {
  id: number;
  name: string;
  slug: string;
  source_type: SourceType;
}

export interface SourceWithStatus extends Source {
  is_active: boolean;
}

export interface FeedItem {
  id: number;
  source: Source;
  title: string;
  url: string;
  summary: string | null;
  author: string | null;
  published_at: string; // ISO 8601 UTC
}

export interface StatusData {
  last_updated_at: string; // ISO 8601 UTC
  status: 'ok' | 'warning' | 'error';
  sources: SourceStatus[];
}

export interface SourceStatus {
  source_id: number;
  source_name: string;
  last_crawled_at: string;
  crawl_status: 'success' | 'failed' | 'running' | 'unknown';
}

export type TabType = 'news' | 'vc_blog';
