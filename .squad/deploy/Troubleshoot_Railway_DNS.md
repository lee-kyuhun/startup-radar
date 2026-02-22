# Troubleshoot: Railway 내부 DNS 미작동 및 DB 연결 실패

> 작성: DevOps 에이전트 | 날짜: 2026-02-21
> 대상: PJ004_startup-radar 백엔드 (FastAPI + SQLAlchemy async + asyncpg)
> 증상: `socket.gaierror: [Errno -2] Name or service not known`
> 발생 지점: Alembic 마이그레이션 (`alembic/env.py`) 및 `seed_sources()` 초기화

---

## 목차

1. [Railway 환경 변수 확인 및 설정](#1-railway-환경-변수-확인-및-설정)
2. [SQLAlchemy asyncpg 연결 문자열 파싱 문제 해결](#2-sqlalchemy-asyncpg-연결-문자열-파싱-문제-해결)
3. [DB 준비 대기 및 재시도 로직 추가](#3-db-준비-대기-및-재시도-로직-추가)
4. [Ephemeral Agent 위임 작업 목록](#4-ephemeral-agent-위임-작업-목록)

---

## 1. Railway 환경 변수 확인 및 설정

### 1-1. 문제 원인

Railway PostgreSQL 플러그인은 두 종류의 호스트를 제공한다:

| 유형 | 호스트 형식 | 접근 가능 범위 |
|------|-----------|-------------|
| **Private (Internal)** | `postgres.railway.internal` | 같은 Railway 프로젝트 내 서비스 간 통신만 가능 |
| **Public (External)** | `monorail.proxy.rlwy.net:PORT` | 인터넷 어디서든 접근 가능 |

현재 `DATABASE_URL`이 `postgres.railway.internal` 호스트를 사용하고 있으나, **Railway의 Private Network DNS는 컨테이너 시작 초기에 resolve되지 않을 수 있다**. 특히 다음 시점에서 문제가 발생한다:

- Dockerfile `CMD` 실행 시점 (네트워크 준비 전)
- FastAPI lifespan 초기 단계 (서비스 디스커버리 지연)
- `subprocess.run()`으로 생성된 자식 프로세스 (부모와 별도 DNS 캐시)

### 1-2. Railway PostgreSQL 플러그인이 자동 제공하는 변수들

Railway PostgreSQL 플러그인을 추가하면 다음 변수들이 **PostgreSQL 서비스 자체**에 자동 생성된다:

```
DATABASE_URL          = postgresql://postgres:비밀번호@호스트:포트/railway
DATABASE_PRIVATE_URL  = postgresql://postgres:비밀번호@postgres.railway.internal:5432/railway
DATABASE_PUBLIC_URL   = postgresql://postgres:비밀번호@monorail.proxy.rlwy.net:외부포트/railway
PGHOST                = postgres.railway.internal (또는 외부 호스트)
PGPORT                = 5432
PGUSER                = postgres
PGPASSWORD            = {자동생성}
PGDATABASE            = railway
```

**중요**: 이 변수들은 PostgreSQL 서비스에 존재하며, 백엔드 서비스에서 사용하려면 **Reference Variable** 문법으로 연결해야 한다.

### 1-3. Railway Reference Variables로 백엔드 서비스에 연결하는 방법

Railway 대시보드에서 백엔드 서비스의 Variables 탭으로 이동한 뒤:

**단계:**

```
1. Railway 대시보드 접속 (railway.app)
2. 프로젝트: startup-radar 선택
3. 백엔드 서비스 (Web Service) 클릭
4. "Variables" 탭 클릭
5. "New Variable" 클릭
6. 이름: DATABASE_URL
7. 값: ${{Postgres.DATABASE_PUBLIC_URL}}
   (주의: DATABASE_URL이 아니라 DATABASE_PUBLIC_URL을 참조)
8. "Add" 클릭
```

**Reference Variable 문법:**

```
${{서비스이름.변수이름}}
```

예시:

| 백엔드 변수 | 값 (Reference) | 설명 |
|------------|---------------|------|
| `DATABASE_URL` | `${{Postgres.DATABASE_PUBLIC_URL}}` | Public URL 사용 (권장) |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` | Redis도 동일하게 설정 |

### 1-4. Internal vs Public 호스트 선택 기준

**권장: Public URL 사용 (`DATABASE_PUBLIC_URL`)**

| 기준 | Internal (`*.railway.internal`) | Public (`monorail.proxy.rlwy.net`) |
|------|--------------------------------|-----------------------------------|
| DNS 안정성 | **불안정** -- 컨테이너 시작 시 resolve 실패 가능 | **안정** -- 표준 DNS, 즉시 resolve |
| 지연 시간 | 이론상 더 낮음 (같은 네트워크) | 약간 높음 (프록시 경유) |
| 보안 | 내부 네트워크만 접근 | 비밀번호 + TLS로 보호 |
| 사용 조건 | Railway Private Network 활성화 필수 | PostgreSQL "Public Networking" 활성화 필수 |
| Subprocess 호환 | **비호환** -- 자식 프로세스에서 DNS 실패 | **호환** -- 표준 DNS 사용 |

**Internal DNS가 실패하는 근본 원인:**

Railway Private Network는 컨테이너에 내부 DNS resolver를 주입하는데, 이것이 준비되기 전에 애플리케이션이 DB 연결을 시도하면 `Name or service not known` 오류가 발생한다. `subprocess.run()`으로 생성한 자식 프로세스는 이 DNS resolver를 상속받지 못하는 경우도 있다.

### 1-5. Public Networking 활성화 방법

```
1. Railway 대시보드 -> startup-radar 프로젝트
2. PostgreSQL 서비스 클릭
3. "Settings" 탭 -> "Networking" 섹션
4. "Public Networking" 토글 활성화
5. 생성된 Public URL 확인: monorail.proxy.rlwy.net:XXXXX
6. "Variables" 탭에서 DATABASE_PUBLIC_URL 값이 자동 생성되었는지 확인
```

### 1-6. 최종 환경 변수 확인 절차

백엔드 서비스의 Variables 탭에서 다음을 확인:

```
[필수 확인 항목]

1. DATABASE_URL
   - 값: ${{Postgres.DATABASE_PUBLIC_URL}}
   - Resolved 값 확인 (화살표 아이콘 클릭): postgresql://postgres:XXX@monorail.proxy.rlwy.net:XXXXX/railway
   - 빈 문자열이면 PostgreSQL Public Networking 미활성화 상태

2. APP_ENV
   - 값: production (development 아닌지 반드시 확인)

3. REDIS_URL
   - 값: ${{Redis.REDIS_URL}} 또는 직접 입력
   - Redis도 Internal URL이면 같은 DNS 문제 발생 가능 -> Public URL 사용 권장

4. ALLOWED_ORIGINS
   - 값: Cloudflare Pages 실제 URL (예: https://startup-radar.pages.dev)
   - localhost가 아닌지 확인

5. SECRET_KEY
   - 값: 랜덤 생성 키 (openssl rand -hex 32)
   - 기본값 "changeme-in-production"이 아닌지 확인
```

### 1-7. Railway Private Network DNS 사용 시 주의사항 (참고)

Internal URL을 반드시 사용해야 하는 경우(예: 비용 절감, 보안 요구):

- `*.railway.internal` 호스트는 Railway Private Network 기능이 활성화된 프로젝트에서만 동작한다
- DNS resolve까지 컨테이너 시작 후 수 초에서 수십 초 걸릴 수 있다
- `subprocess`나 `os.system()`으로 실행한 프로세스에서는 DNS가 작동하지 않을 수 있다
- Internal URL 사용 시 반드시 섹션 3의 재시도 로직이 필요하다
- **현재 프로젝트에서는 Public URL 사용을 권장**한다

---

## 2. SQLAlchemy asyncpg 연결 문자열 파싱 문제 해결

### 2-1. 문제 개요

Railway가 제공하는 `DATABASE_URL`은 `postgresql://` 스킴을 사용한다. 그러나 SQLAlchemy에서 asyncpg 드라이버를 사용하려면 `postgresql+asyncpg://` 스킴이 필요하다.

```
Railway 제공:    postgresql://postgres:비밀번호@host:port/railway
코드에서 필요:   postgresql+asyncpg://postgres:비밀번호@host:port/railway
```

### 2-2. 현재 코드의 자동 변환 로직 분석

**파일: `backend/app/config.py`**

```python
# 25-31행
@property
def async_database_url(self) -> str:
    """Convert postgresql:// to postgresql+asyncpg:// for SQLAlchemy async."""
    url = self.DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url
```

진단 결과:
- 이 프로퍼티는 `postgresql://` -> `postgresql+asyncpg://` 변환을 올바르게 수행한다.
- 이미 `postgresql+asyncpg://`로 시작하는 URL은 변환하지 않는다 (정상).
- **Railway에서 `DATABASE_URL`을 원본(`postgresql://`) 그대로 넣으면 코드가 자동 변환한다.**

**파일: `backend/app/database.py`**

```python
# 18-24행
engine = create_async_engine(
    settings.async_database_url,  # <-- 자동 변환된 URL 사용
    ...
)
```

진단 결과: `database.py`는 `settings.async_database_url` 프로퍼티를 통해 변환된 URL을 사용한다. 정상.

**파일: `backend/alembic/env.py`**

```python
# 16-21행
db_url = os.environ.get("DATABASE_URL")
if db_url:
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    config.set_main_option("sqlalchemy.url", db_url)
```

진단 결과: `env.py`도 동일한 변환 로직을 가지고 있다. `os.environ`에서 직접 읽으므로 `config.py`의 프로퍼티와 독립적으로 동작한다. 정상.

### 2-3. 잠재적 함정: 이중 변환

**위험 시나리오**: Railway 환경 변수에 `DATABASE_URL`을 수동으로 `postgresql+asyncpg://`로 설정한 경우:

- `config.py`의 `async_database_url`: `startswith("postgresql://")` 체크에서 걸리지 않으므로 변환 안 함 (정상)
- `alembic/env.py`: 동일하게 변환 안 함 (정상)

하지만 **이전 배포에서 이미 겪은 실수**이므로 (`.squad/memory/devops.md` 58행 참조), 다시 반복하지 않도록 규칙을 명확히 한다:

**규칙: Railway `DATABASE_URL`에는 항상 원본 `postgresql://` 형태를 넣는다. 코드가 자동 변환한다.**

### 2-4. 확인이 필요한 수정 사항

**파일: `backend/alembic.ini` (60행)**

현재 값:
```ini
sqlalchemy.url = postgresql+asyncpg://user:password@localhost:5432/startup_radar
```

이 값은 `alembic/env.py`에서 `os.environ.get("DATABASE_URL")`이 존재하면 덮어쓰여진다. 즉, Railway에서 환경 변수가 올바르게 설정되어 있으면 무시된다. 하지만 혹시 환경 변수가 누락된 경우 이 로컬 기본값이 사용되어 혼란을 줄 수 있다.

**수정 방향**: `alembic.ini`의 `sqlalchemy.url`을 빈 문자열이나 플레이스홀더로 바꿔서, 환경 변수 없이는 명확한 오류가 나도록 한다.

```
대상 파일: backend/alembic.ini
대상 행: 60행
현재 값: sqlalchemy.url = postgresql+asyncpg://user:password@localhost:5432/startup_radar
수정 값: sqlalchemy.url = %(DATABASE_URL)s
목적: 환경 변수 없이 실행하면 즉시 오류 발생 -> 설정 누락 조기 발견
```

### 2-5. Railway Public URL과의 호환성

Railway PostgreSQL Public URL 형식:
```
postgresql://postgres:비밀번호@monorail.proxy.rlwy.net:포트번호/railway
```

이 URL은:
- `postgresql://`로 시작하므로 `config.py`와 `alembic/env.py` 모두에서 `postgresql+asyncpg://`로 자동 변환됨
- 호스트가 `monorail.proxy.rlwy.net`이므로 표준 DNS로 resolve 가능
- 포트가 5432가 아닌 Railway가 할당한 외부 포트이지만, 코드에서 포트를 하드코딩하지 않으므로 문제없음

**결론: Railway Public URL을 `DATABASE_URL`에 그대로 넣으면 모든 코드 경로에서 정상 동작한다.**

---

## 3. DB 준비 대기 및 재시도 로직 추가

### 3-1. 현재 문제점

**파일: `backend/app/main.py`**

현재 `_run_production_init()` 함수 (35-64행)에서:

1. `subprocess.run(["alembic", "upgrade", "head"])` -- DB가 준비되지 않았으면 DNS 또는 연결 오류
2. `seed_sources()` -- 내부에서 `init_db()`로 DB 연결 시도하면 동일한 오류

두 단계 모두 **재시도 없이 즉시 실행**하므로, DB가 0.1초라도 늦게 준비되면 실패한다. `try/except`로 오류를 잡아서 앱은 시작되지만, 마이그레이션과 시드 데이터가 적용되지 않는다.

### 3-2. 해결 전략 개요

세 가지 방안을 제시하며, **방안 A를 권장**한다:

| 방안 | 접근 | 코드 변경 범위 | 권장도 |
|------|------|-------------|-------|
| **A. tenacity 재시도** | `main.py`에서 tenacity `@retry`로 DB 연결 재시도 | `main.py`만 수정 | **권장** |
| B. entrypoint.sh | Dockerfile에서 wait-for-db 쉘 스크립트로 대기 후 실행 | `entrypoint.sh` 신규 + `Dockerfile` 수정 | 가능 |
| C. 수동 연결 확인 | lifespan에서 asyncpg로 직접 연결 테스트 후 진행 | `main.py` 수정 | 가능 |

### 3-3. 방안 A: tenacity 재시도 (권장)

`tenacity`는 이미 `requirements.txt`에 포함되어 있으므로 추가 설치가 필요 없다.

**수정 대상 파일: `backend/app/main.py`**

**수정 방향:**

1. `_run_production_init()` 함수를 두 단계로 분리한다:
   - `_wait_for_db()`: SQLAlchemy async engine으로 `SELECT 1`을 실행하여 DB가 준비되었는지 확인한다. tenacity `@retry`로 최대 60초간 재시도한다.
   - 기존 alembic + seed 로직은 DB 연결 확인 후 실행한다.

2. `_wait_for_db()` 함수의 설계:
   - `tenacity.retry` 데코레이터 적용
   - `wait=wait_exponential(multiplier=1, min=2, max=10)` -- 2초, 4초, 8초, 10초 간격으로 재시도
   - `stop=stop_after_delay(60)` -- 최대 60초까지 시도
   - `retry=retry_if_exception_type(Exception)` -- 모든 연결 오류에 대해 재시도
   - SQLAlchemy async engine으로 `SELECT 1` 쿼리 실행하여 연결 확인
   - 성공 시 로그 출력: `[startup] DB connection verified`

3. `_run_production_init()` 수정:
   - 먼저 `await _wait_for_db()` 호출
   - DB 연결 확인 후 alembic subprocess 실행
   - alembic 성공 후 `seed_sources()` 호출

**구체적 수정 내용 (Ephemeral Agent에게 전달):**

```
파일: backend/app/main.py

[추가할 import]
- from tenacity import retry, stop_after_delay, wait_exponential, retry_if_exception_type
- from sqlalchemy import text
- from app.database import engine

[신규 함수: _wait_for_db()]

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_delay(60),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: logger.info(
        "[startup] Waiting for DB... attempt %d", retry_state.attempt_number
    ),
)
async def _wait_for_db() -> None:
    """DB 연결 가능 여부 확인. tenacity로 최대 60초 재시도."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("[startup] DB connection verified")

[_run_production_init() 수정]
기존 코드의 첫 줄에 다음을 추가:

    try:
        await _wait_for_db()
    except Exception as exc:
        logger.error("[startup] DB not reachable after 60s: %s", exc)
        return  # DB 연결 불가 시 전체 init 건너뛰기

이후 기존 alembic subprocess + seed_sources 로직은 그대로 유지
```

### 3-4. 방안 B: entrypoint.sh (대안)

Public URL 사용 시에는 불필요하지만, Internal URL(`*.railway.internal`)을 반드시 사용해야 하는 경우에 적합하다.

**신규 파일: `backend/entrypoint.sh`**

설계:

```
#!/bin/bash
set -e

# 1. DB 호스트 추출 (DATABASE_URL에서 파싱)
# 2. pg_isready 또는 Python 스크립트로 DB 연결 대기 (최대 60초, 2초 간격)
# 3. alembic upgrade head 실행
# 4. exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

**Dockerfile 수정:**

```
대상 파일: backend/Dockerfile
현재 (45행): CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
수정:
  - COPY entrypoint.sh .
  - RUN chmod +x entrypoint.sh
  - CMD ["./entrypoint.sh"]
```

**주의사항:**
- `pg_isready` 사용 시 `apt-get install -y postgresql-client` 추가 필요 (이미지 크기 증가)
- `pg_isready` 없이 Python으로 구현 가능: `python -c "import asyncio; import asyncpg; ..."`
- entrypoint.sh에서 alembic을 실행하면 `main.py`의 `_run_production_init()`에서 alembic 부분은 제거해야 한다 (이중 실행 방지)

### 3-5. 방안 C: 수동 연결 확인 (간단한 대안)

방안 A의 간소화 버전으로, tenacity 없이 직접 루프를 돌린다.

**수정 대상: `backend/app/main.py`**

```
[_wait_for_db() 함수를 tenacity 없이 구현]
- for i in range(15):  # 최대 30초 (15회 x 2초)
-     try: SELECT 1 실행
-     except: await asyncio.sleep(2)
- else: raise ConnectionError("DB not ready after 30s")
```

tenacity가 이미 의존성에 있으므로 방안 A가 더 선언적이고 유지보수하기 좋다. 방안 C는 외부 라이브러리 의존을 줄이고 싶을 때만 사용한다.

### 3-6. Alembic subprocess 실행과 재시도

현재 `main.py`에서 alembic을 `subprocess.run()`으로 실행하는 이유:
- alembic의 `run_migrations_online()` 내부에서 `asyncio.run()`을 호출하므로, FastAPI의 이벤트 루프 안에서 직접 호출하면 `RuntimeError: This event loop is already running` 발생
- subprocess는 별도 프로세스이므로 이벤트 루프 충돌 없음

**subprocess 재시도 전략:**

`_wait_for_db()`가 DB 연결을 확인한 뒤에 subprocess를 실행하면 거의 실패하지 않는다. 그래도 안전을 위해:

```
수정 방향 (main.py의 alembic subprocess 부분):
- 현재: 1회 실행 -> 실패 시 로그만 남기고 진행
- 수정: 최대 3회 재시도 (2초 간격) -> 모두 실패 시 로그 남기고 진행
- tenacity를 subprocess 래퍼에도 적용 가능
```

### 3-7. Dockerfile CMD vs Procfile 시작 순서

**현재 상태:**

- `Dockerfile` CMD: `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`
- `Procfile`: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- `railway.toml`: builder = DOCKERFILE 이므로 **Dockerfile CMD가 사용됨** (Procfile 무시)

**권장 구조 (방안 A 적용 시):**

```
[Dockerfile CMD]
  uvicorn 실행만 담당 (현재와 동일, 변경 없음)

[main.py lifespan]
  1. _wait_for_db()  <- tenacity 재시도로 DB 대기
  2. subprocess alembic upgrade head  <- DB 준비 후 실행
  3. seed_sources()  <- 마이그레이션 완료 후 실행
  4. register_all_crawl_jobs()
  5. scheduler.start()
```

이 구조의 장점:
- Dockerfile을 변경할 필요 없음
- 모든 초기화 로직이 Python 코드에 집중되어 디버깅 용이
- Railway 로그에서 각 단계의 성공/실패를 명확히 확인 가능

**방안 B 적용 시:**

```
[entrypoint.sh]
  1. wait-for-db (쉘 스크립트)
  2. alembic upgrade head
  3. exec uvicorn  <- uvicorn으로 프로세스 교체

[main.py lifespan]
  1. seed_sources()만 실행 (alembic은 이미 완료)
  2. register_all_crawl_jobs()
  3. scheduler.start()
```

### 3-8. railway.toml 수정 사항

현재 `healthcheckTimeout`이 60초인데, tenacity 재시도(최대 60초)와 alembic 실행(최대 30초)을 합산하면 90초 이상 걸릴 수 있다. 헬스체크 타임아웃을 늘린다.

```
대상 파일: backend/railway.toml
현재 값: healthcheckTimeout = 60
수정 값: healthcheckTimeout = 120
목적: DB 대기 + 마이그레이션 + seed 완료까지 충분한 시간 확보
```

---

## 4. Ephemeral Agent 위임 작업 목록

아래 수정 작업은 전략 문서에 따라 Ephemeral Agent가 실제 코드를 작성한다.

### 작업 A: main.py에 tenacity 기반 DB 대기 로직 추가

```
파일: backend/app/main.py
수정 범위: import 추가 + _wait_for_db() 신규 함수 + _run_production_init() 수정
참조: 이 문서 섹션 3-3

구체적 변경:
1. import 추가:
   - from tenacity import retry, stop_after_delay, wait_exponential, retry_if_exception_type
   - from sqlalchemy import text
   - from app.database import engine (이미 있을 수 있음)

2. _wait_for_db() 함수 신규 작성:
   - @retry 데코레이터 적용 (wait_exponential, stop_after_delay(60))
   - async engine connect -> SELECT 1 실행
   - 성공 시 "[startup] DB connection verified" 로그

3. _run_production_init() 수정:
   - 첫 줄에 await _wait_for_db() 추가
   - 기존 로직 유지 (alembic subprocess + seed_sources)
   - _wait_for_db() 실패 시 전체 init을 건너뛰도록 try/except 추가
```

### 작업 B: railway.toml 헬스체크 타임아웃 증가

```
파일: backend/railway.toml
변경: healthcheckTimeout = 60 -> healthcheckTimeout = 120
```

### 작업 C: alembic.ini 기본 URL 안전화 (선택)

```
파일: backend/alembic.ini
변경: 60행의 sqlalchemy.url을 플레이스홀더로 변경
목적: 환경 변수 없이 실행 시 즉시 오류 발생하도록 안전장치
```

### 작업 D: .env.example 업데이트

```
파일: backend/.env.example
변경: DATABASE_URL 설명에 Railway 원본 URL 형식 명시
추가: 주석으로 "Railway에서는 postgresql:// 원본 URL 그대로 설정. 코드가 자동 변환함" 안내
```

---

## 5. 검증 체크리스트 (배포 후)

배포 후 Railway 로그에서 다음을 순서대로 확인한다:

```
[ ] "[startup] Waiting for DB... attempt 1"  <- tenacity 재시도 시작
[ ] "[startup] DB connection verified"       <- DB 연결 성공
[ ] "[startup] Running alembic upgrade head ..."
[ ] "[startup] alembic upgrade head -- OK"   <- 마이그레이션 성공
[ ] "[startup] Running seed_sources ..."
[ ] "[startup] seed_sources -- OK"           <- 시드 성공
[ ] "APScheduler started with N jobs"        <- 스케줄러 시작
```

최종 확인:

```
[ ] GET https://{railway-domain}/health -> {"status": "ok", "env": "production"}
[ ] GET https://{railway-domain}/api/v1/sources/ -> 6개 소스 데이터 반환
[ ] GET https://{railway-domain}/api/v1/status/ -> 크롤링 상태 반환
[ ] Sentry -> 새 에러 없음
```

---

## 6. 즉시 실행 요약 (Quick Action)

**가장 빠른 해결 경로 (코드 변경 없이):**

```
1. Railway 대시보드 -> PostgreSQL 서비스 -> Settings -> Public Networking 활성화
2. Railway 대시보드 -> 백엔드 서비스 -> Variables
3. DATABASE_URL 값을 ${{Postgres.DATABASE_PUBLIC_URL}} 로 변경
4. REDIS_URL도 Public URL인지 확인
5. Redeploy 트리거
6. 로그 확인
```

이것만으로도 DNS 문제는 해결될 가능성이 높다. 그래도 DB 준비 타이밍 문제를 근본적으로 해결하려면 섹션 3의 tenacity 재시도 로직을 추가하는 것이 바람직하다.

---

*DevOps 에이전트 작성 | 2026-02-21 | 대상: PJ004_startup-radar*
