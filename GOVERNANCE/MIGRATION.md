# Repository Migration

통합 기준일: 2026-09-18

## 목적

GPT 개발 프로젝트를 하나의 저장소에서 관리해 공통 Governance와 프로젝트별 Context/CI를 함께 사용할 수 있도록 통합했습니다.

이 문서 이후의 신규 개발은 canonical Workspace Repository만 대상으로 합니다.

## Canonical Workspace

- Repository: `hjang12/ai-agent-cicd-system-by-gpt`
- Default branch: `main`
- Common Governance: `GOVERNANCE/`
- Projects: `projects/<project>/`

## 원본 Snapshot

- Governance: `hjang12/ai-agent-cicd-system-by-gpt` @ `a3fd6fe90f8fe9be3a84436e7a66894d9628b5d8`
- Janggi: `hjang12/personal-ai-janggi-trainer-by-gpt` @ `83932421217f149de46e6e23b89aff9d92467a11`
- Time Dashboard: `hjang12/time-dashboard-by-gpt` @ `fb8e98baa7a81a610c2ccbf767f2995fb9af0a3f`

## 통합 후 경로

- 공통 문서 → `GOVERNANCE/`
- Janggi → `projects/personal-ai-janggi-trainer-by-gpt/`
- Time Dashboard → `projects/time-dashboard-by-gpt/`
- GitHub Actions → 저장소 루트 `.github/workflows/`
- Render Blueprint → 저장소 루트 `render.yaml`

기존 프로젝트 저장소의 전체 Git history는 원본 저장소에 보존되어 있으며, 이 저장소에는 최신 상태를 스냅샷으로 가져왔습니다.

Janggi와 Time Dashboard의 원본 HEAD 트리와 중앙 monorepo subtree를 비교한 결과, 의도된 migration 변경 외의 project file 누락은 확인되지 않았습니다.

## GitHub CI 변경

프로젝트별 기존 workflow는 monorepo root로 이동했습니다.

- Janggi validation → `.github/workflows/janggi-validation.yml`
- Janggi search benchmark → `.github/workflows/janggi-search-benchmark.yml`
- Time Dashboard CI → `.github/workflows/time-dashboard-ci.yml`

각 workflow는 해당 프로젝트와 공통 Governance 경로를 기준으로 path filter를 사용합니다.

초기 monorepo Janggi validation/benchmark 실패는 migration 과정에서 발생한 test/benchmark 의미 불일치를 후속 commit에서 수정했고, 현재 `main`의 두 workflow는 성공 상태입니다.

## Render 전환

Root `render.yaml`은 두 서비스를 같은 Git Repository에서 운영하되 프로젝트별 Root Directory로 경계를 유지하도록 정의합니다.

- Janggi Root Directory: `projects/personal-ai-janggi-trainer-by-gpt`
- Time Dashboard Root Directory: `projects/time-dashboard-by-gpt`

### 실제 상태 확인 — 2026-09-18

Render `My Workspace`에서 확인한 현재 Service 설정:

- `personal-ai-janggi-trainer-by-gpt`
  - Repository: `hjang12/personal-ai-janggi-trainer-by-gpt`
  - Root Directory: empty
  - Branch: `main`
  - Auto Deploy: enabled
  - Latest live deploy: `83932421217f149de46e6e23b89aff9d92467a11`
  - URL: `https://personal-ai-janggi-trainer.onrender.com`

- `time-dashboard-by-gpt`
  - Repository: `hjang12/time-dashboard-by-gpt`
  - Root Directory: empty
  - Branch: `main`
  - Auto Deploy: enabled
  - Latest live deploy: `fb8e98baa7a81a610c2ccbf767f2995fb9af0a3f`
  - URL: `https://time-dashboard.onrender.com`

따라서 현재 Render는 **아직 monorepo로 전환되지 않았습니다**. `render.yaml`은 목표 상태를 정의하지만 기존 Service의 Repository / Root Directory를 자동으로 변경하지 않습니다.

기존 서비스 설정을 Render에서 위 목표 상태로 변경한 뒤, 최신 `main` commit을 배포하고 post-deployment verification을 수행해야 합니다.

## 파일 차이

GitHub 연결 인터페이스가 바이너리 PNG를 직접 전달하지 못해 Time Dashboard의 `assets/icon.png`는 self-contained SVG `assets/icon.svg`로 대체했고, `manifest.json` 및 관련 HTML 참조를 함께 갱신했습니다.

## 원본 Repository 운영

기존 `-by-gpt` 프로젝트 Repository는 historical snapshot으로 취급합니다.

- 신규 개발은 canonical monorepo에서 수행
- 기존 원본 Repository에는 신규 기능을 추가하지 않음
- Archive/Delete는 별도의 destructive lifecycle action으로 수행
- Archive/Delete 전에 필요한 history/evidence/운영 기록을 보존하고 실제 플랫폼 결과를 재확인


## Safe cleanup order

기존 프로젝트 Repository는 현재 Render Service가 직접 참조하고 있으므로 Render cutover 이전에 삭제하지 않는다.

권장 순서는 다음과 같다.

```text
Render Repository 변경
→ Root Directory 변경
→ monorepo commit 배포
→ Deployment live 확인
→ health / smoke 확인
→ post-deployment 결과 문서화
→ 기존 -by-gpt Repository Archive/Delete
```

현재 연결된 Render 도구에는 기존 Service의 Repository / Root Directory를 수정하는 작업이 노출되어 있지 않다. 따라서 해당 변경은 Render Dashboard에서 수행해야 하며, 실제 변경 전까지 기존 Repository를 유지한다.
