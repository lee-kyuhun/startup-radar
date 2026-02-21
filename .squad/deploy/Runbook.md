# Runbook: Startup Radar (PJ004)

> 작성: DevOps 에이전트 | 날짜: 2026-02-21
> 기준 문서: `Deploy_Spec.md`, `Infra_Map.md`

---

## 1. 최초 배포 절차 (First Deploy)

### 1-1. Railway 초기 설정

```
순서:
1. railway.app 접속 → 새 프로젝트 생성: "startup-radar"
2. GitHub 저장소 연결 → "startup-radar" 레포 선택
3. Web Service 설정:
   - Root Directory: /backend
   - Build Command: pip install -r requirements.txt
   - Start Command: (Procfile 자동 감지)
   - Health Check Path: /health
4. Add Plugin → PostgreSQL 추가
5. Add Plugin → Redis 추가
6. 환경변수 설정 (Env_Spec.md 참고):
   - APP_ENV=production
   - SECRET_KEY={openssl rand -hex 32 생성값}
   - ALLOWED_ORIGINS=https://startup-radar.vercel.app
   - SENTRY_DSN={Sentry 프로젝트 DSN}
   (DATABASE_URL, REDIS_URL은 플러그인이 자동 주입)
7. Deploy 클릭
```

### 1-2. DB 초기 마이그레이션

```
Railway 대시보드 → Web Service → "Connect" 탭 → Railway CLI 또는:

Railway 콘솔에서:
  alembic upgrade head

소스 시드 데이터 삽입:
  python -c "from app.scripts.seed import seed_sources; seed_sources()"
  (seed 스크립트는 Backend Lead가 별도 구현)
```

### 1-3. Vercel 초기 설정

```
순서:
1. vercel.com 접속 → "Add New Project"
2. GitHub 저장소 연결 → "startup-radar" 레포 선택
3. Root Directory: /frontend
4. Framework: Next.js (자동 감지)
5. 환경변수 설정 (Env_Spec.md 참고):
   - NEXT_PUBLIC_API_BASE_URL=https://{railway-domain}.railway.app
   - NEXT_PUBLIC_SENTRY_DSN={Sentry 프론트 DSN}
6. Deploy 클릭
```

### 1-4. CORS 최종 업데이트

```
Vercel 배포 완료 후 실제 프론트엔드 URL 확인
→ Railway 환경변수 업데이트:
  ALLOWED_ORIGINS=https://startup-radar.vercel.app
→ Railway 재배포 트리거 (환경변수 변경 시 자동 재배포)
```

---

## 2. 정상 배포 절차 (Routine Deploy)

```
1. feat/* 브랜치에서 개발 완료
2. PR 생성 → GitHub Actions CI 자동 실행
3. CI 통과 확인 (pytest, lint)
4. 코드 리뷰 완료 → main 브랜치 merge
5. Railway: 자동 배포 시작 → 2-5분 소요
6. Vercel: 자동 배포 시작 → 1-2분 소요
7. 배포 확인:
   - GET https://{railway-domain}/health → {"status": "ok"} 확인
   - 프론트엔드 접속 → 피드 로딩 확인
   - Sentry 대시보드 → 새 에러 없음 확인
```

---

## 3. 롤백 절차

### 3-1. 백엔드 롤백 (Railway)

```
긴급도: HIGH — 즉시 실행

1. Railway 대시보드 → startup-radar 프로젝트
2. Web Service → Deployments 탭
3. 이전 성공 배포 행 → "..." 메뉴 → "Redeploy"
4. 배포 로그 확인 → 헬스체크 통과 대기 (약 2-3분)
5. GET /health 응답 확인

DB 마이그레이션 포함된 경우 추가:
6. Railway 콘솔 → alembic downgrade -1
7. 코드 롤백 이후 실행 (코드-스키마 버전 맞추기)
```

### 3-2. 프론트엔드 롤백 (Vercel)

```
긴급도: LOW — Vercel이 즉시 처리

1. Vercel 대시보드 → startup-radar 프로젝트
2. Deployments 탭
3. 이전 성공 배포 → "..." 메뉴 → "Promote to Production"
4. 30초 이내 완료
```

---

## 4. 장애 대응 절차

### 4-1. 백엔드 다운 (5xx 에러)

```
확인 순서:
1. Railway 대시보드 → 배포 상태 확인 (빨간불?)
2. Railway 로그 → 에러 메시지 확인
3. Sentry → 에러 스택트레이스 확인

원인별 대응:
- 코드 버그: 섹션 3-1 롤백 실행
- DB 연결 실패: Railway PostgreSQL 플러그인 상태 확인
- Redis 연결 실패: Railway Redis 플러그인 상태 확인
- 메모리 초과 (Playwright): Railway 서비스 수동 재시작
```

### 4-2. 크롤러 미작동

```
확인:
1. GET /api/v1/status/ → last_crawled_at 타임스탬프 확인
2. Railway 로그 → APScheduler 스케줄 등록 로그 확인
3. crawl_logs 테이블 → 최근 실패 기록 확인

대응:
- 스케줄러 미등록: Railway 재배포 (앱 재시작)
- 특정 소스 크롤링 실패: crawl_logs 오류 메시지 분석 → 선택적 수정
```

### 4-3. DB 마이그레이션 실패

```
Railway 콘솔:
1. alembic current → 현재 리비전 확인
2. alembic history → 히스토리 확인
3. alembic downgrade -1 → 한 단계 롤백
4. 코드 수정 후 alembic upgrade head 재시도
```

---

## 5. 일상 운영 체크리스트

### 주간 확인 항목

- [ ] Railway 크레딧 잔여량 확인 (월 $5 기준)
- [ ] Sentry 에러 이벤트 잔여량 확인 (월 5,000개 기준)
- [ ] crawl_logs 테이블 — 지속적 크롤링 실패 소스 없는지 확인
- [ ] PostgreSQL 데이터 증가량 추이 확인

### 배포 전 필수 확인

- [ ] pytest 전체 통과
- [ ] .env.example 최신 상태
- [ ] alembic 마이그레이션 파일 존재 (스키마 변경 시)
- [ ] CHANGELOG.md 업데이트

---

## 6. Ephemeral Agent 위임 작업 목록

아래 파일들은 Runbook 작성 후 Ephemeral Agent에게 생성 위임:

| 파일 | 위치 | 역할 |
|------|------|------|
| `Dockerfile` | `backend/Dockerfile` | Railway 커스텀 빌드 (Playwright 포함) |
| `backend-ci.yml` | `.github/workflows/backend-ci.yml` | pytest CI |
| `frontend-ci.yml` | `.github/workflows/frontend-ci.yml` | TypeScript/ESLint CI |
| `docker-compose.yml` | 루트 | 로컬 개발 환경 |
| `.env.example` | `backend/.env.example` | 환경변수 예시 |
| `.env.local.example` | `frontend/.env.local.example` | 프론트 환경변수 예시 |

> Playwright 설치 필요로 인해 Nixpacks 기본 빌드가 실패할 가능성 있음.
> `backend/Dockerfile` 또는 `backend/nixpacks.toml`로 Playwright 브라우저 설치 명시 필요.

---

*DevOps 에이전트 작성 | 2026-02-21*
