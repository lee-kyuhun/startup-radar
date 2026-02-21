# 배포 체크리스트: 네가 직접 할 일

> PM 에이전트 작성 | 2026-02-21

---

## 사전 준비 (터미널)

- [ ] **GitHub 레포 생성 후 push**

```bash
# 프로젝트 폴더에서 실행
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/{너의_계정}/startup-radar.git
git push -u origin main
```

---

## Step 1. Railway 설정 (백엔드 + DB + Redis)

1. [ ] railway.app 접속 → **New Project** → GitHub 연결 → `startup-radar` 선택
2. [ ] **Root Directory**: `/backend` 입력
3. [ ] **Add Plugin → PostgreSQL** 추가
4. [ ] **Add Plugin → Redis** 추가
5. [ ] **환경변수 설정** (Variables 탭):

| 변수명 | 값 |
|--------|-----|
| `APP_ENV` | `production` |
| `SECRET_KEY` | 터미널에서 `openssl rand -hex 32` 실행한 값 |
| `ALLOWED_ORIGINS` | `https://startup-radar.vercel.app` (Step 3 후 실제 URL로 교체) |
| `SENTRY_DSN` | 일단 빈칸 |

> `DATABASE_URL`, `REDIS_URL`은 Plugin이 **자동 주입** — 입력 불필요

6. [ ] **Deploy** 클릭 → 배포 완료 대기 (2~5분)
7. [ ] `https://{railway-domain}/health` 접속 → `{"status": "ok"}` 확인

---

## Step 2. DB 초기화 (Railway Shell)

Railway 대시보드 → Web Service → **Shell** 탭에서:

```bash
# 테이블 생성
alembic upgrade head

# 소스 시드 데이터 삽입 (플래텀, 벤처스퀘어 등 6개)
python -m app.scripts.seed
```

- [ ] `alembic upgrade head` 실행 완료
- [ ] `python -m app.scripts.seed` 실행 완료 → `inserted=6 skipped=0` 확인

---

## Step 3. Vercel 설정 (프론트엔드)

1. [ ] vercel.com 접속 → **Add New Project** → GitHub 연결 → `startup-radar` 선택
2. [ ] **Root Directory**: `/frontend` 입력
3. [ ] **환경변수 설정**:

| 변수명 | 값 |
|--------|-----|
| `NEXT_PUBLIC_API_BASE_URL` | Railway에서 발급된 도메인 (예: `https://startup-radar-api.railway.app`) |

4. [ ] **Deploy** 클릭 → 배포 완료 대기 (1~2분)
5. [ ] 발급된 Vercel URL 확인 (예: `https://startup-radar.vercel.app`)

---

## Step 4. CORS 업데이트

- [ ] Railway 환경변수에서 `ALLOWED_ORIGINS` 값을 실제 Vercel URL로 업데이트
- [ ] Railway 자동 재배포 확인
- [ ] 프론트엔드 접속 → 피드 로딩 확인

---

## 완료 확인

- [ ] `https://{railway-domain}/health` → `{"status": "ok"}`
- [ ] `https://{railway-domain}/api/v1/feed/?tab=news` → 피드 데이터 반환
- [ ] `https://{vercel-url}` → 피드 UI 정상 표시
- [ ] 크롤러 첫 실행 대기 (최대 1시간) → 뉴스 피드 노출 확인

---

*모든 코드/설정 파일은 에이전트가 완성. 네가 할 일은 위 체크리스트 항목 클릭뿐.*
