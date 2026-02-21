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

- Railway + Vercel 무료 티어 기준 설계 필수
- APScheduler In-process (별도 Worker 없음)
- Playwright + APScheduler 메모리 한도 주의 (TBD-4)
- Sentry 무료 티어 이벤트 한도 검토 필요 (TBD-5)

## 배포 문서 위치

| 문서 | 경로 |
|------|------|
| Deploy Spec | `.squad/deploy/Deploy_Spec.md` |
| Infra Map | `.squad/deploy/Infra_Map.md` |
| Runbook | `.squad/deploy/Runbook.md` |
| Env Spec | `.squad/deploy/Env_Spec.md` |
