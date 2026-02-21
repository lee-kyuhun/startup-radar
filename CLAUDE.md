# CLAUDE.md — Startup Radar 개발 가이드

이 파일은 Claude Code가 이 프로젝트를 열 때 자동으로 읽는 컨텍스트 파일이다.
새 세션을 시작할 때마다 이 파일을 먼저 읽고 프로젝트 컨텍스트를 파악한다.

---

## 프로젝트 개요

**Startup Radar** — 한국 VC/스타트업 생태계 종사자를 위한 인물·기관 중심 정보 허브.
인물과 기관을 구독하면, 그들의 모든 채널(SNS, 블로그, 뉴스)이 한 피드에 모인다.

상세 기획: `README.md` 참고

---

## 기술 스택

- **Backend:** Python + FastAPI
- **Crawling:** Playwright + BeautifulSoup
- **Database:** PostgreSQL + Redis
- **Frontend:** Next.js + Tailwind CSS
- **Deploy:** Backend → Railway, Frontend → Vercel
- **CI/CD:** GitHub Actions

---

## 프로젝트 구조 규칙

```
PJ004_startup-radar/
├── CLAUDE.md           ← 이 파일 (항상 최신 상태 유지)
├── README.md           ← PRD + 프로젝트 개요
├── docs/               ← 설계 문서
├── backend/            ← Python FastAPI 서버
├── frontend/           ← Next.js 앱
└── .github/workflows/  ← CI/CD
```

**규칙:**
- 새 폴더/파일 생성 전 반드시 기존 구조 확인
- 임시 파일, 테스트 스크립트는 루트에 두지 않음
- 모든 환경변수는 `.env` (gitignore됨), 예시는 `.env.example`에 작성

---

## 개발 프로세스 (바이브코딩 워크플로우)

### 새 기능 개발 시
1. README.md 로드맵에서 현재 Phase 확인
2. 작업 전 `TodoWrite`로 할 일 목록 작성
3. 기존 코드 먼저 읽기 (절대 새 파일 생성 전 기존 파일 확인)
4. 작은 단위로 구현 → 테스트 → 커밋
5. CHANGELOG.md 업데이트

### 커밋 컨벤션
```
feat: 새 기능
fix: 버그 수정
docs: 문서 변경
refactor: 리팩토링
test: 테스트
chore: 빌드/설정 변경
```

### 브랜치 전략
- `main`: 배포 가능한 상태만
- `dev`: 개발 통합 브랜치
- `feat/기능명`: 기능 개발

---

## 토큰 절약 규칙

- 파일 탐색 시 Glob → Grep → Read 순서로 (전체 읽기 최소화)
- 큰 파일은 필요한 라인만 Read (offset + limit 활용)
- 반복 작업은 sub-agent에 위임
- 이미 파악한 컨텍스트는 재탐색하지 않음
- CLAUDE.md를 항상 최신으로 유지해서 매 세션 재탐색 방지

---

## 크롤링 주의사항

- robots.txt 확인 필수
- rate limiting 준수 (요청 간격 최소 1초)
- User-Agent 명시
- SNS 크롤링 시 API 우선 검토, 없으면 Playwright

---

## MAS (Multi-Agent System) 연동

이 프로젝트는 SYS002 Persistent + Ephemeral MAS 구조로 개발된다.

### 에이전트 구조
```
[영속 에이전트] ~/.claude/agents/  ← 코드 작성 금지, 마크다운 문서만 작성
  ├── orchestrator.md  — 총괄, 게이트 관리
  ├── pm.md            — 기획, PRD 작성
  ├── designer.md      — UI/UX 스펙
  ├── tech-lead.md     — 기술 방향, API 계약, 통합
  ├── frontend-lead.md — 프론트 아키텍처, 임시 에이전트 지시
  ├── backend-lead.md  — 백엔드 아키텍처, 임시 에이전트 지시
  ├── qa-reviewer.md   — 스펙 검증, 테스트 전략
  └── devops.md        — 배포 전략, CI/CD 설계

[임시 에이전트] Task tool로 즉석 호출  ← 실제 코드 작성 담당
  — 단일 구현 작업 후 즉시 소멸
  — 최소 컨텍스트로 토큰 효율 극대화
  — 산출물은 파일로 저장 (코드 자체가 영속성)
```

### 에이전트 메모리
- 글로벌: `~/.claude/agents-memory/{role}/learnings.md`
- 프로젝트: `.squad/memory/{role}.md`
- 새 세션 시작 시 에이전트는 반드시 메모리 먼저 로드

### 워크플로우 게이트
`.squad/hired_agents.json`의 `gates` 필드로 현재 단계 추적
```
PRD 승인 → UI 스펙 승인 → Tech Spec 승인 → 빌드
```

### 에이전트 호출 예시
```
"pm 에이전트로 PRD 작성해줘"
"backend-lead가 Tech Spec 작성해줘"
"ephemeral agent로 플래텀 크롤러 구현해줘"
```

---

## 현재 상태 (2026-02-21)

**Phase 4 — Build 게이트 진입 (모든 설계 문서 승인 완료)**

### 게이트 현황
- [x] PRD 승인 (2026-02-21) — `.squad/01_planning/PRD.md`
- [x] UI Spec 승인 (2026-02-21) — `.squad/02_design/UI_Specs.md`
- [x] Tech Spec 승인 (2026-02-21) — `.squad/03_architecture/Tech_Spec.md`
- [ ] Build 완료

### 설계 문서 위치
- PRD: `.squad/01_planning/PRD.md`
- UI Spec: `.squad/02_design/UI_Specs.md`
- Tech Spec: `.squad/03_architecture/Tech_Spec.md`
- API Contract: `.squad/03_architecture/API_Contract.md`
- DB Schema: `.squad/03_architecture/DB_Schema.md`
- Tech Decisions: `.squad/03_architecture/Tech_Decisions.md`

### 백엔드 진행 현황 (Backend Lead)
- [x] Open Questions 기술 검토 완료 (2026-02-21) — `.squad/03_architecture/Open_Questions.md`
- [x] 백엔드 기반 구축 완료 (2026-02-21) — `backend/` (46개 파일)
  - FastAPI 앱, SQLAlchemy 모델, Pydantic 스키마, API 4개, RSS 크롤러, Alembic 마이그레이션
- [ ] 스타트업투데이 HTML 크롤러 구체 구현
- [ ] 카카오벤처스 Playwright 크롤러 구체 구현
- [ ] 알토스벤처스 HTML 크롤러 구체 구현

### 다음 할 일
1. Backend Lead → 잔여 크롤러 구현 (스타트업투데이, 카카오벤처스, 알토스벤처스)
2. Frontend Lead → 프론트엔드 기반 구축 지시 (Next.js 초기화, Tailwind 토큰)
3. Ephemeral Agent → 피드 UI 구현 (FeedList, FeedItem, TabNav, StatusBadge)
4. DevOps → Railway + Vercel 배포 설정
