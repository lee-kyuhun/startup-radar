# Env Spec: Startup Radar (PJ004)

> 작성: DevOps 에이전트 | 날짜: 2026-02-21
> 기준 문서: `Tech_Spec.md` 섹션 10, `backend/app/config.py`

---

## 규칙

- 실제 시크릿 값은 이 파일에 절대 기록하지 않는다
- 모든 환경변수는 Railway/Vercel 대시보드에서 직접 설정
- `.env.example` 파일이 항상 이 문서와 동기화되어야 한다
- `NEXT_PUBLIC_` 접두사 변수만 브라우저에 노출됨 (주의)

---

## Backend 환경변수 (Railway)

| 변수명 | 필수 | 기본값 (dev) | 설명 | 예시 |
|--------|------|-------------|------|------|
| `APP_ENV` | 필수 | `development` | 실행 환경 | `production` |
| `SECRET_KEY` | 필수 | `changeme-in-production` | v2 JWT 서명용. 랜덤 32자+ | `openssl rand -hex 32` 생성값 |
| `DATABASE_URL` | 필수 | `postgresql+asyncpg://...localhost...` | PostgreSQL 연결 문자열 | Railway 자동 제공 (`$DATABASE_URL`) |
| `REDIS_URL` | 필수 | `redis://localhost:6379` | Redis 연결 문자열 | Railway 자동 제공 (`$REDIS_URL`) |
| `ALLOWED_ORIGINS` | 필수 | `http://localhost:3000` | CORS 허용 Origin (쉼표 구분) | `https://startup-radar.vercel.app` |
| `SENTRY_DSN` | 권장 | `` (빈값) | Sentry 에러 추적 DSN | Sentry 프로젝트 DSN |
| `CRAWL_USER_AGENT` | 선택 | `StartupRadar/1.0 (...)` | 크롤러 User-Agent 헤더 | 기본값 사용 권장 |
| `CRAWL_RATE_LIMIT_SECONDS` | 선택 | `1.0` | 크롤링 요청 간격 (초) | `1.0` (최솟값 준수 필수) |
| `API_V1_PREFIX` | 선택 | `/api/v1` | API 경로 접두사 | 변경 불필요 |
| `DEFAULT_PAGE_SIZE` | 선택 | `20` | 기본 페이지 크기 | `20` |
| `MAX_PAGE_SIZE` | 선택 | `50` | 최대 페이지 크기 | `50` |

### Railway 자동 제공 변수 (별도 설정 불필요)

| 변수명 | 제공 주체 | 설명 |
|--------|----------|------|
| `PORT` | Railway | uvicorn 바인딩 포트 |
| `DATABASE_URL` | PostgreSQL Plugin | DB 연결 문자열 자동 주입 |
| `REDIS_URL` | Redis Plugin | Redis 연결 문자열 자동 주입 |

> Railway Plugin 연결 시 `DATABASE_URL`, `REDIS_URL`이 자동 오버라이드됨.
> config.py의 기본값은 로컬 개발용.

---

## Frontend 환경변수 (Vercel)

| 변수명 | 필수 | 기본값 (dev) | 설명 | 예시 |
|--------|------|-------------|------|------|
| `NEXT_PUBLIC_API_BASE_URL` | 필수 | `http://localhost:8000` | 백엔드 API 베이스 URL | `https://startup-radar-api.railway.app` |
| `NEXT_PUBLIC_SENTRY_DSN` | 권장 | `` (빈값) | Sentry 프론트엔드 DSN | Sentry 프로젝트 DSN (FE 전용) |

### Vercel 환경 분리

| 변수명 | Development | Preview | Production |
|--------|-------------|---------|------------|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Railway API URL | Railway API URL |
| `NEXT_PUBLIC_SENTRY_DSN` | 빈값 | Sentry DSN | Sentry DSN |

---

## 로컬 개발 설정

### backend/.env (gitignore 대상)

```
APP_ENV=development
SECRET_KEY=local-dev-secret-key-not-for-production
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/startup_radar
REDIS_URL=redis://localhost:6379
ALLOWED_ORIGINS=http://localhost:3000
SENTRY_DSN=
CRAWL_USER_AGENT=StartupRadar/1.0 (+https://startup-radar.com/about)
CRAWL_RATE_LIMIT_SECONDS=1.0
```

### frontend/.env.local (gitignore 대상)

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_SENTRY_DSN=
```

---

## .env.example 동기화 체크리스트

- [ ] `backend/.env.example` — 위 Backend 변수 전체 포함 (값은 placeholder)
- [ ] `frontend/.env.local.example` — 위 Frontend 변수 전체 포함
- [ ] 새 환경변수 추가 시 이 문서 + .env.example 동시 업데이트

---

## 시크릿 생성 가이드

```
# SECRET_KEY 생성 (터미널에서 실행)
openssl rand -hex 32

# 결과 예시 (실제 값으로 교체)
a3f8b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1
```

---

*DevOps 에이전트 작성 | 2026-02-21*
