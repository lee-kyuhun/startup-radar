# Deploy Spec: Startup Radar (PJ004)

> 작성: DevOps 에이전트 | 날짜: 2026-02-21 | 수정: 2026-02-22 | 상태: 배포 준비 완료
> 기준 문서: `.squad/03_architecture/Tech_Spec.md`, `Troubleshoot_Railway_DNS.md`

---

## 1. 환경 구성

| 환경 | 플랫폼 | URL | 트리거 | 목적 |
|------|--------|-----|--------|------|
| dev | 로컬 (Docker Compose) | localhost:8000 (BE) / localhost:3000 (FE) | 수동 | 개발/디버깅 |
| prod | Railway (BE) + Vercel (FE) | {railway-domain} / {vercel-domain} | main 브랜치 push | 서비스 운영 |

> staging 환경은 Railway 무료 티어 제약으로 MVP에서 생략. 프리뷰 배포(Vercel PR Preview)가 staging 역할 대체.

---

## 2. 플랫폼 선택 근거

### Backend -- Railway

| 항목 | 내용 |
|------|------|
| 선택 이유 | Python 자동 감지, Dockerfile 빌드 지원, PostgreSQL/Redis 플러그인 단일 프로젝트 관리 |
| 무료 티어 | $5 크레딧/월 -- MVP 트래픽 수용 가능 |
| 배포 방식 | GitHub 연동 -> main push 자동 배포 |
| 서비스 구성 | Web Service (FastAPI) + PostgreSQL Plugin + Redis Plugin |
| 빌드 방식 | Dockerfile 빌드 (Playwright Chromium 브라우저 포함) |
| 제약 사항 | 단일 프로세스 (APScheduler In-process 필수), 메모리 512MB 기본 |

### Frontend -- Vercel

| 항목 | 내용 |
|------|------|
| 선택 이유 | Next.js 14 공식 플랫폼, git push 자동 배포, PR 프리뷰 자동 생성 |
| 무료 티어 | Hobby 플랜 -- MVP 충분 |
| 배포 방식 | GitHub 연동 -> main push prod 배포, PR -> 프리뷰 URL 자동 생성 |

---

## 3. 배포 설정 파일 현황

### Backend 설정 파일

| 파일 | 경로 | 역할 | 상태 |
|------|------|------|------|
| `Dockerfile` | `backend/Dockerfile` | Railway 커스텀 빌드 (Python 3.12-slim + Playwright Chromium) | 완료 |
| `railway.toml` | `backend/railway.toml` | Railway 빌드/배포 설정 (Dockerfile builder, healthcheck 120s) | 완료 |
| `Procfile` | `backend/Procfile` | Railway Procfile (Dockerfile 사용 시 무시됨, 폴백용) | 완료 |
| `.env.example` | `backend/.env.example` | 환경변수 예시 | 완료 |

### Frontend 설정 파일

| 파일 | 경로 | 역할 | 상태 |
|------|------|------|------|
| `vercel.json` | `frontend/vercel.json` | Vercel 빌드 설정 (Next.js framework) | 완료 |
| `next.config.js` | `frontend/next.config.js` | Next.js 설정 (Vercel 표준 빌드, SSR 활성화) | 완료 |
| `.env.local.example` | `frontend/.env.local.example` | 프론트 환경변수 예시 | 완료 |

### CI/CD 설정 파일

| 파일 | 경로 | 역할 | 상태 |
|------|------|------|------|
| `backend-ci.yml` | `.github/workflows/backend-ci.yml` | Python 테스트 (pytest + PostgreSQL + Redis) | 완료 |
| `frontend-ci.yml` | `.github/workflows/frontend-ci.yml` | TypeScript 타입 체크 + ESLint + 빌드 확인 | 완료 |

---

## 4. v1.1 수정 반영 사항 (2026-02-22)

### 4-1. main.py: tenacity 기반 DB 대기 로직 추가

Railway에서 DB 연결 타이밍 문제(DNS resolve 지연)를 해결하기 위해 `_wait_for_db()` 함수를 추가했다.

- tenacity `@retry` 데코레이터: 지수 백오프(2s -> 4s -> 8s -> 10s), 최대 60초
- `SELECT 1` 쿼리로 DB 연결 확인
- DB 연결 실패 시 마이그레이션/시드 전체 건너뜀 (앱은 시작됨)
- 상세 근거: `Troubleshoot_Railway_DNS.md` 섹션 3

### 4-2. railway.toml: healthcheck 타임아웃 증가

`healthcheckTimeout`을 60초에서 120초로 증가. DB 대기(최대 60초) + Alembic 마이그레이션(최대 30초) + seed(수초) 합산 시간 확보.

### 4-3. next.config.js: static export 제거

`output: 'export'`를 제거하여 Vercel 표준 Next.js 빌드를 사용하도록 변경. SSR/ISR 지원이 가능해져 LCP < 2초 목표 달성에 유리.

### 4-4. vercel.json 신규 생성

`frontend/vercel.json`을 생성하여 Vercel에 Next.js 프레임워크와 빌드 커맨드를 명시적으로 지정.

---

## 5. CI/CD 파이프라인

```
GitHub Repository
      |
      +-- PR 생성/업데이트
      |     +-- GitHub Actions: backend-ci.yml
      |     |     +-- Python 3.12 세팅
      |     |     +-- pip install -r requirements.txt
      |     |     +-- pytest tests/ (PostgreSQL + Redis 서비스 컨테이너)
      |     |
      |     +-- GitHub Actions: frontend-ci.yml
      |     |     +-- Node.js 20 세팅
      |     |     +-- npm ci
      |     |     +-- ESLint + TypeScript type check + Build
      |     |
      |     +-- Vercel: 프리뷰 배포 자동 생성
      |           +-- Preview URL 코멘트 자동 등록
      |
      +-- main 브랜치 push
            +-- GitHub Actions: CI 재실행
            +-- Railway: 자동 빌드 시작 (Dockerfile) -> 헬스체크 통과 시 트래픽 전환
            +-- Vercel: 자동 빌드 -> prod 배포 완료
```

> Railway 배포는 GitHub 저장소 직접 연동으로 처리. 별도 Actions 배포 스텝 불필요.
> Vercel 배포는 GitHub 저장소 직접 연동으로 처리. 별도 Actions 배포 스텝 불필요.

---

## 6. 배포 절차 (정상 플로우)

```
1. 개발자: feat/* 브랜치에서 작업 완료
2. PR 생성 -> GitHub Actions CI 자동 실행 (pytest, lint, type check)
3. CI 통과 -> Vercel 프리뷰 URL 자동 생성
4. 코드 리뷰 + QA 확인
5. main 브랜치 merge
6. Railway: Dockerfile 빌드 시작 -> _wait_for_db() -> alembic upgrade head -> seed -> 헬스체크 통과 -> 트래픽 전환
7. Vercel: npm ci -> next build -> prod 배포 완료
8. 배포 완료 확인: /health 엔드포인트 + Sentry 에러율 확인
```

---

## 7. 롤백 절차

### 백엔드 (Railway) 롤백

```
1. Railway 대시보드 접속
2. Deployments 탭 -> 이전 성공 배포 선택
3. "Redeploy" 클릭 -> 즉시 이전 버전 복구
4. 예상 소요 시간: 2-3분
```

### 프론트엔드 (Vercel) 롤백

```
1. Vercel 대시보드 -> Deployments 탭
2. 이전 성공 배포 선택 -> "Promote to Production" 클릭
3. 예상 소요 시간: 30초 이내 (즉시 전환)
```

### DB 마이그레이션 롤백

```
1. alembic downgrade -1  (한 단계 롤백)
2. 또는 alembic downgrade {revision_id}  (특정 버전으로)
3. Railway 콘솔에서 실행 (SSH 또는 railway run)
```

---

## 8. 모니터링 전략

| 항목 | 도구 | 설정 |
|------|------|------|
| 에러 추적 | Sentry | Backend FastAPI SDK + Frontend Next.js SDK |
| 서버 상태 | Railway 내장 메트릭 | CPU, 메모리, 네트워크 |
| 헬스체크 | /health 엔드포인트 | Railway 자동 헬스체크 연동 (120초 타임아웃) |
| 크롤링 상태 | /api/v1/status/ | 서비스 내부 StatusBadge UI |
| 가동 시간 | Railway 대시보드 | 배포 성공/실패 알림 |

### Sentry 무료 티어 관리 (TBD-5 해결)

- Hobby 플랜: 5,000 에러 이벤트/월
- 크롤링 실패는 WARNING 레벨로 처리 (에러 이벤트 소비 절약)
- `sentry_sdk.init(traces_sample_rate=0.2)` -- 트레이스 20% 샘플링

---

## 9. 보안 체크리스트

- [x] `.env` 파일 `.gitignore` 등록 확인
- [ ] Railway 환경변수에 실제 시크릿 설정 (대시보드)
- [ ] Vercel 환경변수에 `NEXT_PUBLIC_API_BASE_URL` 설정
- [ ] CORS `ALLOWED_ORIGINS` 프로덕션 도메인만 허용
- [ ] `SECRET_KEY` 랜덤 생성값 사용 (v2 JWT 대비)
- [ ] Sentry DSN 환경변수로 관리 (코드 하드코딩 금지)

---

## 10. CORS 설정 확인

**현재 구현 (backend/app/main.py):**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,  # ALLOWED_ORIGINS 환경변수에서 로드
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**config.py의 CORS 파싱:**

```python
ALLOWED_ORIGINS: str = "http://localhost:3000"

@property
def allowed_origins_list(self) -> list[str]:
    return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
```

- 쉼표로 구분하여 여러 Origin 허용 가능
- Railway 환경변수에서 Vercel 프론트엔드 URL을 설정해야 함
- 예: `ALLOWED_ORIGINS=https://startup-radar.vercel.app`

---

## 11. TBD 항목 추적

| # | 항목 | 상태 | 해결 기한 |
|---|------|------|---------|
| TBD-4 | Railway 무료 티어 APScheduler + Playwright 메모리 한도 | 미해결 | 첫 배포 시 모니터링 |
| TBD-5 | Sentry 무료 티어 이벤트 한도 | 해결 방향 정의됨 (섹션 8) | 배포 시 |

> TBD-4 대응책: Railway에서 메모리 초과 시 Playwright 워커를 별도 Railway 서비스로 분리 고려.
> 단, MVP에서는 In-process로 먼저 시도 후 판단.

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1.0 | 2026-02-21 | 초안 작성 |
| v1.1 | 2026-02-22 | tenacity DB 대기 로직 추가, healthcheck 타임아웃 증가, next.config.js 수정, vercel.json 생성 |

---

*DevOps 에이전트 작성 | 2026-02-22 (v1.1)*
