# Startup Radar

> 한국 VC/스타트업 생태계 종사자를 위한 **인물·기관 중심 정보 허브**

---

## 1. 문제 정의 (Problem Statement)

한국 VC 심사역과 스타트업 창업자는 매일 다음과 같은 문제를 겪는다:

- VC/창업자/인플루언서의 SNS가 Threads, LinkedIn, YouTube, 블로그 등 **여러 플랫폼에 분산**되어 있음
- 특정 인물의 최근 관심사·견해·행보를 파악하려면 **플랫폼을 일일이 방문**해야 함
- 스타트업 관련 뉴스가 어느 매체에서 나왔는지 파악이 어렵고 **정보 노이즈가 많음**
- VC 블로그/뉴스레터를 따로따로 구독·방문해야 하는 **정보 파편화** 문제
- 전체 생태계 트렌드를 파악하기 위해 **수십 개의 사이트를 순회**해야 함

---

## 2. 솔루션 (Solution)

**Startup Radar** — 인물과 기관을 구독하면, 그들의 모든 채널 활동이 한 피드에 모인다.

> "팔로우하면 모든 채널이 한 곳에"

---

## 3. 타겟 사용자 (Target Users)

| 사용자 | 주요 니즈 |
|---|---|
| VC 심사역 | 스타트업 트렌드 파악, 포트폴리오 모니터링 |
| 스타트업 창업자 | VC 심사역 성향/관심사 파악, 펀드레이징 준비 |
| 스타트업 관심자 | 생태계 동향 파악, 인사이트 학습 |

**1차 타겟:** 한국 VC/스타트업 생태계 종사자
**확장 방향:** 글로벌 스타트업 생태계 (영어 지원, 글로벌 VC 추가)

---

## 4. 핵심 기능 (Core Features)

### MVP (v1.0)

| 기능 | 설명 | 우선순위 |
|---|---|---|
| **인물 피드** | 특정 인물(VC, 창업자)의 Threads/LinkedIn 포스트 모아보기 | P0 |
| **기관 피드** | VC/스타트업 공식 블로그·채널 모아보기 | P0 |
| **키워드 뉴스** | 키워드 기반 국내 스타트업 뉴스 크롤링 | P0 |
| **인물/기관 검색** | 이름으로 인물·기관 검색 | P1 |
| **구독 기능** | 관심 인물·기관 구독 및 맞춤 피드 | P1 |

### v2.0 (Post-MVP)

- 리포트 발행 기능
- 스타트업 관련 행사 캘린더
- 알림 기능 (특정 인물 포스트 시 알림)
- 글로벌 확장 (영어 UI, 글로벌 VC 추가)
- 유튜브 채널 모니터링

---

## 5. 정보 소스 (Data Sources)

### SNS
- Threads (Meta)
- LinkedIn

### 뉴스 미디어 (국내)
- 플래텀 (platum.kr)
- 벤처스퀘어 (venturesquare.net)
- 스타트업투데이 (startuptoday.kr)
- 더벨 (thebell.co.kr)
- 테크M

### VC 블로그/뉴스레터
- 카카오벤처스 블로그
- 알토스벤처스
- 기타 국내 VC 공식 채널

---

## 6. 기술 스택 (Tech Stack)

### 백엔드
- **Runtime:** Python (FastAPI)
- **크롤링:** Playwright + BeautifulSoup
- **스케줄링:** APScheduler (주기적 크롤링)
- **DB:** PostgreSQL + Redis (캐싱)
- **배포:** Railway 또는 Render

### 프론트엔드
- **Framework:** Next.js (React)
- **Styling:** Tailwind CSS
- **배포:** Vercel

### 인프라
- **모니터링:** Sentry
- **CI/CD:** GitHub Actions

> **선택 이유:** 빠른 프로토타이핑 + 실제 배포 경험 + 커뮤니티 지원이 풍부한 스택

---

## 7. 프로젝트 구조 (Project Structure)

```
PJ004_startup-radar/
├── README.md               # 이 파일 (PRD + 프로젝트 개요)
├── docs/
│   ├── PRD.md              # 상세 기획서
│   ├── ARCHITECTURE.md     # 아키텍처 설계
│   └── CHANGELOG.md        # 변경 이력
├── backend/
│   ├── app/
│   │   ├── api/            # API 라우터
│   │   ├── crawlers/       # 크롤러 모듈
│   │   ├── models/         # DB 모델
│   │   └── services/       # 비즈니스 로직
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js App Router
│   │   ├── components/     # UI 컴포넌트
│   │   └── lib/            # 유틸리티
│   └── package.json
└── .github/
    └── workflows/          # CI/CD
```

---

## 8. 개발 로드맵 (Roadmap)

### Phase 1 — 기반 구축 (현재)
- [ ] 프로젝트 기획 완료 (PRD 작성)
- [ ] 기술 스택 확정 및 환경 설정
- [ ] 백엔드 기본 구조 설계

### Phase 2 — MVP 개발
- [ ] 뉴스 크롤러 개발 (플래텀, 벤처스퀘어)
- [ ] 기본 API 서버 구축
- [ ] 프론트엔드 피드 UI 구현
- [ ] 인물/기관 피드 기능

### Phase 3 — 배포
- [ ] 백엔드 Railway 배포
- [ ] 프론트엔드 Vercel 배포
- [ ] 도메인 연결
- [ ] 기본 모니터링 설정

### Phase 4 — 고도화
- [ ] SNS 크롤링 (Threads, LinkedIn)
- [ ] 구독 기능
- [ ] 검색 기능
- [ ] 리포트/행사 기능 (v2)

---

## 9. 개발 원칙 (Development Principles)

이 프로젝트는 **AI 바이브코딩으로 실제 서비스를 배포하는 과정**을 학습하는 것이 목적이다.

- **Ship fast:** 완벽함보다 동작하는 것을 먼저
- **Learn by doing:** 각 단계에서 새로운 기술/도구를 직접 경험
- **Real process:** 실제 스타트업처럼 기획 → 개발 → 배포 → 피드백 사이클
- **Clean codebase:** 일관된 폴더 구조와 컨벤션 유지

---

## 10. 배울 것들 (Learning Goals)

- [ ] MCP & Skills 활용법
- [ ] Multi-agent 아키텍처
- [ ] Zed / Ghostty 효율적 활용
- [ ] Sub-agent 활용법
- [ ] 토큰 효율적으로 쓰는 바이브코딩 방법
- [ ] 일관된 개발 프로세스 유지 방법

---

*Last updated: 2026-02-21*
