# Deploy Spec: Startup Radar (PJ004)

> 작성: DevOps 에이전트 | 날짜: 2026-02-21 | 상태: 초안
> 기준 문서: `.squad/03_architecture/Tech_Spec.md`

---

## 1. 환경 구성

| 환경 | 플랫폼 | URL | 트리거 | 목적 |
|------|--------|-----|--------|------|
| dev | 로컬 (Docker Compose) | localhost:8000 (BE) / localhost:3000 (FE) | 수동 | 개발/디버깅 |
| prod | Railway (BE) + Vercel (FE) | api.startup-radar.com / startup-radar.vercel.app | main 브랜치 push | 서비스 운영 |

> staging 환경은 Railway 무료 티어 제약으로 MVP에서 생략. 프리뷰 배포(Vercel PR Preview)가 staging 역할 대체.

---

## 2. 플랫폼 선택 근거

### Backend — Railway

| 항목 | 내용 |
|------|------|
| 선택 이유 | Python 자동 감지, Procfile 지원, PostgreSQL/Redis 플러그인 단일 프로젝트 관리 |
| 무료 티어 | $5 크레딧/월 — MVP 트래픽 수용 가능 |
| 배포 방식 | GitHub 연동 → main push 자동 배포 |
| 서비스 구성 | Web Service (FastAPI) + PostgreSQL Plugin + Redis Plugin |
| 제약 사항 | 단일 프로세스 (APScheduler In-process 필수), 메모리 512MB 기본 |

### Frontend — Vercel

| 항목 | 내용 |
|------|------|
| 선택 이유 | Next.js 14 공식 플랫폼, git push 자동 배포, PR 프리뷰 자동 생성 |
| 무료 티어 | Hobby 플랜 — MVP 충분 |
| 배포 방식 | GitHub 연동 → main push prod 배포, PR → 프리뷰 URL 자동 생성 |

---

## 3. CI/CD 파이프라인

```
GitHub Repository
      │
      ├── PR 생성/업데이트
      │     ├── GitHub Actions: backend-ci.yml
      │     │     ├── Python 3.12 세팅
      │     │     ├── pip install -r requirements.txt
      │     │     └── pytest tests/
      │     │
      │     └── Vercel: 프리뷰 배포 자동 생성
      │           └── Preview URL 코멘트 자동 등록
      │
      └── main 브랜치 push
            ├── GitHub Actions: backend-ci.yml
            │     ├── pytest 통과 확인
            │     └── Railway 자동 배포 트리거 (GitHub 연동)
            │
            └── Vercel: prod 자동 배포
```

### GitHub Actions 워크플로우 구성 (위임 대상)

| 파일 | 트리거 | 역할 |
|------|--------|------|
| `.github/workflows/backend-ci.yml` | PR, main push | Python 테스트 실행 |
| `.github/workflows/frontend-ci.yml` | PR, main push | TypeScript 타입 체크, ESLint |

> Railway 배포는 GitHub 저장소 직접 연동으로 처리. 별도 Actions 배포 스텝 불필요.
> Vercel 배포는 GitHub 저장소 직접 연동으로 처리. 별도 Actions 배포 스텝 불필요.

---

## 4. 배포 절차 (정상 플로우)

```
1. 개발자: feat/* 브랜치에서 작업 완료
2. PR 생성 → GitHub Actions CI 자동 실행 (pytest, lint)
3. CI 통과 → Vercel 프리뷰 URL 자동 생성
4. 코드 리뷰 + QA 확인
5. main 브랜치 merge
6. Railway: 자동 빌드 시작 → 헬스체크 통과 시 트래픽 전환
7. Vercel: 자동 빌드 → prod 배포 완료
8. 배포 완료 확인: /health 엔드포인트 + Sentry 에러율 확인
```

---

## 5. 롤백 절차

### 백엔드 (Railway) 롤백

```
1. Railway 대시보드 접속
2. Deployments 탭 → 이전 성공 배포 선택
3. "Redeploy" 클릭 → 즉시 이전 버전 복구
4. 예상 소요 시간: 2-3분
```

### 프론트엔드 (Vercel) 롤백

```
1. Vercel 대시보드 → Deployments 탭
2. 이전 성공 배포 선택 → "Promote to Production" 클릭
3. 예상 소요 시간: 30초 이내 (즉시 전환)
```

### DB 마이그레이션 롤백

```
1. alembic downgrade -1  (한 단계 롤백)
2. 또는 alembic downgrade {revision_id}  (특정 버전으로)
3. Railway 콘솔에서 실행 (SSH 또는 railway run)
```

---

## 6. 모니터링 전략

| 항목 | 도구 | 설정 |
|------|------|------|
| 에러 추적 | Sentry | Backend FastAPI SDK + Frontend Next.js SDK |
| 서버 상태 | Railway 내장 메트릭 | CPU, 메모리, 네트워크 |
| 헬스체크 | /health 엔드포인트 | Railway 자동 헬스체크 연동 |
| 크롤링 상태 | /api/v1/status/ | 서비스 내부 StatusBadge UI |
| 가동 시간 | Railway 대시보드 | 배포 성공/실패 알림 |

### Sentry 무료 티어 관리 (TBD-5 해결)

- Hobby 플랜: 5,000 에러 이벤트/월
- 크롤링 실패는 WARNING 레벨로 처리 (에러 이벤트 소비 절약)
- `sentry_sdk.init(traces_sample_rate=0.1)` — 트레이스 10% 샘플링

---

## 7. 보안 체크리스트

- [ ] `.env` 파일 `.gitignore` 등록 확인
- [ ] Railway 환경변수에 실제 시크릿 설정 (대시보드)
- [ ] Vercel 환경변수에 `NEXT_PUBLIC_API_BASE_URL` 설정
- [ ] CORS `ALLOWED_ORIGINS` 프로덕션 도메인만 허용
- [ ] `SECRET_KEY` 랜덤 생성값 사용 (v2 JWT 대비)
- [ ] Sentry DSN 환경변수로 관리 (코드 하드코딩 금지)

---

## 8. TBD 항목 추적

| # | 항목 | 상태 | 해결 기한 |
|---|------|------|---------|
| TBD-4 | Railway 무료 티어 APScheduler + Playwright 메모리 한도 | 미해결 | 첫 배포 시 |
| TBD-5 | Sentry 무료 티어 이벤트 한도 | 해결 방향 정의됨 | 배포 시 |

> TBD-4 대응책: Railway에서 메모리 초과 시 Playwright 워커를 별도 Railway 서비스로 분리 고려.
> 단, MVP에서는 In-process로 먼저 시도 후 판단.

---

*DevOps 에이전트 작성 | 2026-02-21 | 다음: Infra_Map.md, Runbook.md, Env_Spec.md 작성*
