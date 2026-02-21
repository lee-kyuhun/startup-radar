# Open Questions: Backend Lead 검토 필요

> 작성: PM 에이전트 | 날짜: 2026-02-21 | 대상: Backend Lead 에이전트

PRD 작성 중 기술 결정이 필요한 질문들. Tech Spec 작성 전에 이 질문들에 대한 답을 확정해야 한다.

---

## Q1. 뉴스 미디어 RSS 피드 제공 여부 [High]

**질문:** 아래 미디어들이 RSS 피드를 제공하는가?

| 미디어 | URL | RSS 여부 | 수집 방식 결정 |
|--------|-----|----------|------|
| 플래텀 | platum.kr | 미확정 (서버 직접 확인 필요) | feedparser 시도 → 실패 시 BeautifulSoup 크롤링 |
| 벤처스퀘어 | venturesquare.net | 미확정 (서버 직접 확인 필요) | feedparser 시도 → 실패 시 BeautifulSoup 크롤링 |
| 스타트업투데이 | startuptoday.kr | 미확정 | BeautifulSoup 크롤링 (기본 방식) |

**[Backend Lead 답변]:**
- 플래텀, 벤처스퀘어 모두 WordPress 기반 사이트로 RSS 엔드포인트(`/feed`, `/?feed=rss2`)가 있을 가능성이 높으나, WebFetch 환경에서 403 차단됨.
- 실제 백엔드 서버(Python feedparser + 적절한 User-Agent)에서 동작할 가능성이 있으므로, 구현 시 feedparser를 1순위로 시도.
- **전략: Dual-mode 수집기** — RSS 성공 시 feedparser, 실패 시 자동으로 BeautifulSoup HTML 크롤링으로 fallback.
- 스타트업투데이(startuptoday.kr)는 오마이뉴스 계열 CMS 구조로 추정되며, HTML 크롤링을 기본으로 설계.

**[결정일]:** 2026-02-21

---

## Q2. Threads/LinkedIn 크롤링 가능 여부 [High → P1 결정에 영향]

**질문:** 인물 SNS 포스트 수집이 기술적으로 가능한가?

| 플랫폼 | 결론 | 근거 |
|--------|------|------|
| LinkedIn | **불가** | ToS 명시적 금지, 법적 집행 사례 다수. MVP 제외. |
| Threads | **API로 가능** | Meta 공식 Threads API 제공 (2023 출시, 2025 기능 확장). 공개 프로필 포스트 조회 지원. |

**[Backend Lead 답변]:**

**LinkedIn:** 크롤링 완전 불가. LinkedIn 이용약관이 모든 자동화 수집을 금지하며, 실제 계정 차단 및 법적 조치 사례가 존재함. P1-3에서 LinkedIn 지원 제외, v2에서도 공식 API 심사 통과 전까지는 불가.

**Threads:** Meta 공식 Threads API를 통해 공개 프로필의 포스트 수집 가능. 다만:
- 앱 등록 및 API 키 발급 필요 (Meta Developer Console)
- 공개 프로필만 접근 가능 (비공개 계정 제외)
- Rate limit 준수 필요

→ **P1-3 범위 재정의:** LinkedIn 제외, Threads API 기반으로만 인물 SNS 포스트 수집 지원.
→ PM 에이전트에 통보 완료 (이 파일 업데이트로 갈음).

**[결정일]:** 2026-02-21

---

## Q3. VC 블로그 크롤링 가능 여부 확인 [Medium]

**질문:** P0-3 대상 VC 블로그들의 robots.txt가 크롤링을 허용하는가?

| 기관 | 블로그 URL | 플랫폼 | 수집 방식 |
|------|-----------|--------|----------|
| 카카오벤처스 | brunch.co.kr/@kakaoventures | Brunch | BeautifulSoup 크롤링 또는 비공식 RSS |
| 알토스벤처스 | altos.vc | 자체 웹사이트 | 사이트 직접 확인 후 결정 |

**[Backend Lead 답변]:**

**카카오벤처스:**
- 공식 블로그가 brunch.co.kr/@kakaoventures로 이전 완료 (Medium 블로그에서 마이그레이션).
- Brunch는 공식 RSS 미제공이나, 서드파티 RSS 생성 URL 패턴이 알려져 있음.
- 1순위: 비공식 Brunch RSS URL 패턴 시도, 실패 시 Playwright + BeautifulSoup 크롤링.
- robots.txt 준수: 구현 시 brunch.co.kr/robots.txt 최우선 확인 필요.

**알토스벤처스:**
- altos.vc 메인 사이트에서 블로그/인사이트 섹션 존재 여부 확인 필요.
- Medium 블로그 운영 여부 불확실 (검색 결과에서 확인 안 됨).
- robots.txt 확인 및 블로그 URL 확정은 첫 번째 크롤러 구현 ephemeral agent에게 위임.

**[결정일]:** 2026-02-21

---

## 추가 발견: 소스 확장 가능 후보

Q3 조사 중 발견한 추가 VC 블로그 소스 (PM 검토 후 P0-3에 포함 여부 결정):

| 기관 | 채널 | 비고 |
|------|------|------|
| 카카오벤처스 | kakaovc.stibee.com (뉴스레터) | Stibee 기반, 아카이브 크롤링 가능할 수 있음 |

---

## 답변 방식

Backend Lead는 이 파일에 직접 답변을 추가하거나, Tech_Spec.md 작성 시 반영한다.

```
각 질문 아래에:
**[Backend Lead 답변]**: {결론}
**[결정일]**: YYYY-MM-DD
```

---

*PM 에이전트 작성 | Backend Lead 답변 추가: 2026-02-21 | 참고: `.squad/01_planning/PRD.md` 섹션 10 (열린 질문)*
