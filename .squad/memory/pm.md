# PM 에이전트 세션 기록

> 이번 세션에서 선택한 스킬과 컨텍스트

---

## 활성 스킬

| 스킬 | 이유 |
|------|------|
| prd-writing | PRD 작성 세션 |
| brainstorming | 기능 우선순위 정리에 활용 |

## 현재 작업

- PRD.md 초안 작성 중
- 기준: README.md의 문제 정의 + 기능 목록

## 세션 날짜

2026-02-21

---

## 장기 기억: 에이전트 병렬 작업 워크플로우

> 2026-02-21 습득

### Git Worktree + 멀티 에이전트 패턴

다음 프로젝트에서 에이전트 병렬 작업 시 worktree 구조 도입할 것.

**폴더 구조 예시:**
```
project/                    ← main (PM 관리, 프로덕션)
project-backend/            ← feat/backend (backend-lead 에이전트)
project-frontend/           ← feat/frontend (frontend-lead 에이전트)
project-fix/                ← fix/qa-bugs (qa 에이전트)
```

**PM 역할:**
- main 브랜치 감시
- 각 에이전트 브랜치를 PR로 받아서 검토 후 main 머지 승인
- 에이전트 간 충돌 방지

**도입 시점:**
- 에이전트 2명 이상이 동시에 같은 레포 파일을 수정할 가능성이 있을 때
- 피처 개발과 버그 수정이 병렬로 진행될 때

**이번 프로젝트(PJ004)의 교훈:**
- DevOps 에이전트와 PM이 동시에 `manager.py` 수정 → 충돌 위험 발생
- worktree였으면 각자 다른 폴더에서 작업 후 PR 머지로 깔끔하게 처리 가능했음

---

## 배포 디버깅 기록: Railway DNS + DB 초기화 (2026-02-21)

### 문제 요약

Railway에 FastAPI 백엔드 배포 시 `socket.gaierror: [Errno -2] Name or service not known` 에러로 DB 연결 불가.
`postgres.railway.internal` 내부 DNS가 컨테이너 시작 시점에 resolve 안 됨.

### 시도 이력 (6회 연속 실패)

| # | 시도 | 결과 | 원인 |
|---|------|------|------|
| 1 | lifespan에서 `asyncio.run(alembic)` 직접 호출 | RuntimeWarning: coroutine never awaited | 이벤트 루프 충돌 |
| 2 | lifespan에서 `asyncio.to_thread(alembic)` | hang → 타임아웃 | 같은 이벤트 루프 문제 |
| 3 | Dockerfile CMD에서 `alembic upgrade head && uvicorn` | psycopg2 에러 | asyncpg URL 변환 누락 |
| 4 | env.py에 URL 자동 변환 추가 | DNS 에러 (`Name or service not known`) | CMD 시점에 Railway 내부 DNS 미준비 |
| 5 | lifespan에서 `subprocess.run(["alembic", ...])` | alembic DNS 에러 (rc=1) | subprocess도 같은 시점에 DNS 안 됨 |
| 6 | 5번과 동일 + seed도 실행 | 둘 다 DNS 에러, 앱은 시작됨 | lifespan 초기 시점에도 DNS 미준비 |

### 현재 상태 (세션 종료 시점)

- **앱 자체는 정상 시작**: `Application startup complete` + `/health` 200 OK
- **DB 연결 실패**: alembic, seed, crawl jobs 모두 `socket.gaierror`
- **핵심 원인**: `postgres.railway.internal` DNS가 컨테이너 라이프사이클 전체에서 resolve 안 됨

### 다음 세션 해결 방안 (DevOps + Backend 에이전트 협업 필요)

**방안 A (권장): DATABASE_URL을 외부(Public) URL로 변경**
- Railway PostgreSQL의 Public Networking URL 사용
- 형태: `postgresql://postgres:비밀번호@monorail.proxy.rlwy.net:포트/railway`
- 장점: DNS 문제 완전 회피, 코드 변경 불필요
- 단점: 약간의 레이턴시 증가 (무시할 수준)

**방안 B: retry 로직 추가**
- DNS 준비될 때까지 최대 N초 대기 후 재시도
- 장점: 내부 URL 유지
- 단점: 코드 복잡도 증가, 근본 해결 아님

**방안 C: entrypoint.sh 스크립트**
- DNS 체크 → 대기 → alembic → uvicorn 순서 실행
- 장점: 확실한 순서 보장
- 단점: Dockerfile 수정 필요

### 영향 받는 파일

| 파일 | 현재 상태 | 수정 필요 여부 |
|------|-----------|---------------|
| `backend/app/main.py` | subprocess 기반 alembic + seed (DNS 에러) | 방안에 따라 다름 |
| `backend/Dockerfile` | CMD uvicorn만 | 방안 C면 entrypoint.sh 추가 |
| `backend/alembic/env.py` | URL 자동 변환 포함 | 변경 불필요 |
| `backend/app/database.py` | `settings.async_database_url` 사용 | 변경 불필요 |
| Railway 환경변수 | `DATABASE_URL=postgresql://...@postgres.railway.internal:5432/railway` | 방안 A면 외부 URL로 변경 |

### 사용자 수동 작업 (다음 세션 시작 전)

- [ ] Railway PostgreSQL Public URL 확인 (Settings → Networking → Public Networking 활성화)
- [ ] `ALLOWED_ORIGINS`를 Cloudflare Pages 실제 URL로 변경
