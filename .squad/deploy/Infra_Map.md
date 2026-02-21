# Infra Map: Startup Radar (PJ004)

> 작성: DevOps 에이전트 | 날짜: 2026-02-21
> 기준 문서: `Deploy_Spec.md`, `Tech_Spec.md`

---

## 1. 전체 인프라 구성도

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                        │
│                    startup-radar (monorepo)                     │
│                                                                 │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐ │
│  │  .github/workflows/      │  │  브랜치 전략                  │ │
│  │  ├── backend-ci.yml      │  │  main   → prod 자동 배포      │ │
│  │  └── frontend-ci.yml     │  │  dev    → 개발 통합           │ │
│  └──────────────────────────┘  │  feat/* → PR → 프리뷰         │ │
│                                └──────────────────────────────┘ │
└──────────────────┬──────────────────────┬───────────────────────┘
                   │                      │
         main push │                      │ main push
                   │                      │
┌──────────────────▼──────────┐  ┌────────▼───────────────────────┐
│         RAILWAY             │  │           VERCEL                │
│   (Backend 플랫폼)           │  │    (Frontend 플랫폼)            │
│                             │  │                                 │
│  ┌─────────────────────┐    │  │  ┌─────────────────────────┐   │
│  │   Web Service       │    │  │  │   Next.js 14 App         │   │
│  │   FastAPI + uvicorn │    │  │  │   (App Router)           │   │
│  │   Python 3.12       │    │  │  │                          │   │
│  │   Port: $PORT       │    │  │  │   Prod: startup-radar    │   │
│  │   Procfile 기반     │    │  │  │         .vercel.app      │   │
│  └──────┬──────────────┘    │  │  │                          │   │
│         │                   │  │  │   PR Preview: 자동 생성  │   │
│  ┌──────▼──────┐            │  │  └─────────────────────────┘   │
│  │ PostgreSQL  │            │  └────────────────────────────────┘
│  │ Plugin      │            │
│  │ (Railway)   │            │
│  └──────┬──────┘            │
│         │                   │
│  ┌──────▼──────┐            │
│  │   Redis     │            │
│  │   Plugin    │            │
│  │  (Railway)  │            │
│  └─────────────┘            │
└─────────────────────────────┘

                   │ HTTPS REST API
                   │ /api/v1/*
                   ▼

┌─────────────────────────────┐
│    사용자 브라우저           │
│  (Vercel 프론트에서 호출)    │
└─────────────────────────────┘
```

---

## 2. Railway 서비스 구성 상세

```
Railway Project: startup-radar
│
├── Web Service (FastAPI)
│   ├── Build: Nixpacks (Python 자동 감지)
│   ├── Start Command: Procfile → uvicorn app.main:app --host 0.0.0.0 --port $PORT
│   ├── Root Directory: /backend
│   ├── Health Check: GET /health
│   ├── Memory: 512MB (기본, Playwright 사용 시 모니터링 필요)
│   └── Environment Variables: Railway 대시보드 설정
│
├── PostgreSQL Plugin
│   ├── 버전: PostgreSQL 16
│   ├── 자동 제공 변수: $DATABASE_URL (Railway 내부 연결)
│   └── 백업: Railway 내장 (무료 티어: 1일 보관)
│
└── Redis Plugin
    ├── 버전: Redis 7
    ├── 자동 제공 변수: $REDIS_URL (Railway 내부 연결)
    └── 용도: 피드 캐시 (TTL 5분), 크롤링 Lock
```

---

## 3. Vercel 프로젝트 구성 상세

```
Vercel Project: startup-radar
│
├── Framework: Next.js 14
├── Root Directory: /frontend
├── Build Command: next build
├── Output Directory: .next
├── Node.js: 20.x
│
├── Domains
│   ├── Production: startup-radar.vercel.app (기본)
│   └── Custom: 추후 설정 (TBD)
│
└── Environment Variables
    ├── NEXT_PUBLIC_API_BASE_URL (Production)
    └── NEXT_PUBLIC_SENTRY_DSN (Production)
```

---

## 4. 네트워크 흐름

```
사용자 요청 플로우:

1. 사용자 브라우저
   └── GET https://startup-radar.vercel.app
         └── Vercel Edge Network (CDN)
               └── Next.js SSR (서버 컴포넌트)
                     └── fetch https://api.startup-radar.com/api/v1/feed/
                           └── Railway (FastAPI)
                                 ├── Redis (캐시 HIT → 즉시 반환)
                                 └── PostgreSQL (캐시 MISS → DB 조회)

2. 크롤링 플로우 (APScheduler, 1시간 주기):
   Railway FastAPI 프로세스 내
   └── APScheduler 트리거
         └── CrawlerManager
               ├── feedparser (RSS)  → PostgreSQL INSERT
               ├── BeautifulSoup     → PostgreSQL INSERT
               └── Playwright        → PostgreSQL INSERT
```

---

## 5. 로컬 개발 환경

```
docker-compose.yml (Ephemeral Agent 위임 대상)

services:
  postgres:
    image: postgres:16
    port: 5432

  redis:
    image: redis:7
    port: 6379

개발 실행:
  backend:  cd backend && uvicorn app.main:app --reload
  frontend: cd frontend && npm run dev
```

---

## 6. 도메인 계획

| 환경 | 현재 | 목표 (추후) |
|------|------|------------|
| Frontend Prod | startup-radar.vercel.app | startup-radar.com |
| Backend Prod | startup-radar-api.railway.app | api.startup-radar.com |
| Frontend Preview | 자동 생성 (PR별) | - |

> MVP에서는 기본 제공 도메인 사용. 사용자 유입 확인 후 커스텀 도메인 연결.

---

*DevOps 에이전트 작성 | 2026-02-21*
