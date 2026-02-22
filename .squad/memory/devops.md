# DevOps Agent — PJ004 세션 메모리

> 생성: 2026-02-21 | DevOps 에이전트

---

## 이번 세션에서 선택한 스킬

| 스킬 | 용도 |
|------|------|
| railway-deploy | FastAPI 백엔드 + PostgreSQL + Redis Railway 배포 |
| vercel-deploy | Next.js 14 프론트엔드 Vercel 배포 |
| github-actions-ci | 테스트 + 자동 배포 파이프라인 |

---

## 프로젝트 컨텍스트 요약

- **프로젝트:** Startup Radar (PJ004)
- **현재 단계:** Phase 4 Build 게이트 진입 (모든 설계 승인 완료)
- **CI/CD 현황:** .github/workflows 없음 — 신규 구성 필요
- **백엔드 기반:** FastAPI + Procfile 존재, 미배포 상태
- **프론트엔드:** Next.js 14 — 구조 미생성 상태

## 핵심 제약 조건

- Railway + Cloudflare Pages 기준 설계
- APScheduler In-process (별도 Worker 없음)
- Playwright + APScheduler 메모리 한도 주의
- Sentry 무료 티어 이벤트 한도 검토 필요

## 첫 배포 교훈 (2026-02-21)

10건 연쇄 실패 경험에서 도출한 핵심 교훈:
- **push 확인 필수**: 로컬 수정 후 반드시 `git log origin/main..HEAD` 확인
- **배포 로그 커밋 해시 대조**: 의도한 커밋이 빌드되는지 확인
- **Railway startCommand 금지**: Dockerfile CMD에서 `${PORT:-8000}` 사용
- **DATABASE_URL 자동 변환**: `postgresql://` → `postgresql+asyncpg://` 코드에서 처리
- **Playwright --with-deps 금지**: Debian에서 Ubuntu 패키지 없음, 수동 apt-get 사용
- 상세 체크리스트: `~/.claude/agents-memory/devops/learnings.md` 참조

---

## PM 피드백: 배포 환경변수 및 DB 초기화 장애 (2026-02-21)

> PM 에이전트로부터 전달된 사후 분석 및 시정 요구사항

### 발생한 문제

DevOps가 설정한 Railway 환경변수가 부정확하여 **배포 후 4회 연속 실패**함.
PM이 직접 디버깅 및 수정을 대신해야 했음.

### 오류 원인 및 해결

| # | 문제 | 원인 | 해결 |
|---|------|------|------|
| 1 | `APP_ENV=development`로 설정됨 | 프로덕션 환경에 개발 값 그대로 복사 | `production`으로 변경 |
| 2 | `DATABASE_URL`을 수동으로 `postgresql+asyncpg://`로 변경 | `config.py`에 자동 변환 로직(`async_database_url`)이 이미 있는데 중복 변환 시도 | Railway 플러그인 원본 `postgresql://` 유지 |
| 3 | alembic을 FastAPI lifespan에서 프로그래매틱 실행 시도 | `asyncio.run()` 이벤트 루프 충돌로 hang | Dockerfile CMD에서 실행하도록 이동 |
| 4 | `ALLOWED_ORIGINS=http://localhost:3000` | 프로덕션에 로컬 값 그대로 | Cloudflare Pages URL로 변경 필요 |
| 5 | Railway Shell 미제공으로 DB 초기화 불가 | Shell 없이 seed/migration 실행 방법 미확보 | auto-seed를 lifespan에, alembic을 Dockerfile CMD에 추가 |

### 시정 사항: 다음 프로젝트부터 반드시 준수

**1. 환경변수 배포 전 체크리스트 필수 실행:**
- [ ] `APP_ENV`이 프로덕션 환경에 맞는 값(`production`)인지 확인
- [ ] `DATABASE_URL`은 Railway/Supabase 플러그인 원본 URL 그대로 사용 (코드 자동 변환 확인)
- [ ] `ALLOWED_ORIGINS`에 실제 프론트엔드 프로덕션 URL 설정
- [ ] `SECRET_KEY`에 랜덤 생성된 프로덕션 키 사용
- [ ] `REDIS_URL`이 올바른 프로덕션 값인지 확인

**2. DB 초기화 파이프라인 사전 구축:**
- Dockerfile CMD 또는 entrypoint에서 `alembic upgrade head` 실행
- FastAPI lifespan에서 alembic 직접 호출 금지 (이벤트 루프 충돌)
- seed 스크립트는 lifespan에서 호출 가능 (async 네이티브)

**3. 코드 내 자동 변환 로직 확인 후 환경변수 설정:**
- `config.py`의 `async_database_url` 프로퍼티처럼 자동 변환이 있는지 반드시 확인
- 있으면 원본 값 그대로 유지, 없으면 직접 변환

**4. 배포 전 로컬 검증:**
- `railway run` 또는 Docker 로컬 빌드로 환경변수 + 마이그레이션 + seed 전체 흐름 사전 테스트

---

---

## [긴급] Railway 내부 DNS 미작동 문제 (2026-02-21, PM 전달)

> 다음 세션에서 최우선으로 해결할 것

### 문제

Railway 컨테이너에서 `postgres.railway.internal` DNS가 resolve 되지 않음.
Dockerfile CMD, lifespan(subprocess), lifespan(직접 호출) — **모든 시점에서 실패**.

```
socket.gaierror: [Errno -2] Name or service not known
```

### 시도한 것 (모두 실패)

1. Dockerfile CMD에서 `alembic upgrade head` → DNS 에러
2. lifespan에서 `asyncio.run()` → 이벤트 루프 충돌
3. lifespan에서 `subprocess.run()` → DNS 에러 (별도 프로세스에서도 동일)

### 해결 지침 (PM 지시)

**방안 A (권장): DATABASE_URL을 외부(Public) URL로 변경**
- Railway PostgreSQL에서 Public Networking 활성화
- `DATABASE_URL`을 `postgresql://postgres:비밀번호@monorail.proxy.rlwy.net:포트/railway` 형태로 변경
- 코드 변경 없이 환경변수만 바꾸면 됨
- **주의**: `config.py`의 `async_database_url` 프로퍼티가 `postgresql://` → `postgresql+asyncpg://` 자동 변환하므로 원본 URL 그대로 넣을 것

**방안 B: entrypoint.sh로 DNS 대기 + alembic 실행**
```bash
#!/bin/bash
# wait for DNS
until pg_isready -h postgres.railway.internal -p 5432; do
  echo "Waiting for postgres..."
  sleep 2
done
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```
- Dockerfile에 `ENTRYPOINT ["./entrypoint.sh"]` 추가
- pg_isready가 없으면 `apt-get install postgresql-client` 필요

### 현재 코드 상태

| 파일 | 상태 |
|------|------|
| `backend/app/main.py` | lifespan에서 subprocess로 alembic + seed 실행 (DNS 에러로 둘 다 실패, 앱은 시작됨) |
| `backend/Dockerfile` | CMD는 uvicorn만 실행 |
| `backend/alembic/env.py` | `DATABASE_URL` postgresql:// → postgresql+asyncpg:// 자동 변환 포함 |

### 작업 순서

1. Railway PostgreSQL Public Networking URL 확인
2. Railway Variables에서 `DATABASE_URL`을 외부 URL로 변경
3. Redeploy → 로그 확인
4. `[startup] alembic upgrade head — OK` + `[startup] seed_sources — OK` 확인
5. `/health` 200 OK 확인

### 추가 해결 필요 사항

- `ALLOWED_ORIGINS`: Cloudflare Pages 실제 URL로 변경
- `REDIS_URL`: Redis 서비스도 내부 URL이면 같은 문제 발생 가능 → 확인 필요

---

## Railway DNS 문제 해결 문서 작성 완료 (2026-02-22)

> 긴급 이슈 대응 — 상세 트러블슈팅 문서 작성

### 작성한 문서

`.squad/deploy/Troubleshoot_Railway_DNS.md` — 6개 섹션, Ephemeral Agent 위임 작업 4건 포함

### 핵심 결론

1. **즉시 해결**: Railway DATABASE_URL을 `${{Postgres.DATABASE_PUBLIC_URL}}`로 변경 (코드 변경 불필요)
2. **근본 해결**: `main.py`에 tenacity 기반 `_wait_for_db()` 재시도 로직 추가
3. **railway.toml**: healthcheckTimeout 60 -> 120 증가 필요

### Ephemeral Agent 위임 작업

| 작업 | 파일 | 상태 |
|------|------|------|
| A. tenacity DB 대기 로직 | `backend/app/main.py` | 미완료 |
| B. 헬스체크 타임아웃 증가 | `backend/railway.toml` | 미완료 |
| C. alembic.ini URL 안전화 | `backend/alembic.ini` | 미완료 (선택) |
| D. .env.example 업데이트 | `backend/.env.example` | 미완료 |

---

## 배포 문서 위치

| 문서 | 경로 |
|------|------|
| Deploy Spec | `.squad/deploy/Deploy_Spec.md` |
| Infra Map | `.squad/deploy/Infra_Map.md` |
| Runbook | `.squad/deploy/Runbook.md` |
| Env Spec | `.squad/deploy/Env_Spec.md` |
| **Troubleshoot DNS** | **`.squad/deploy/Troubleshoot_Railway_DNS.md`** |
