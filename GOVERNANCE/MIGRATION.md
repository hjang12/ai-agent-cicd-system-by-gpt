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

초기 monorepo Janggi validation/benchmark 실패는 migration 과정에서 발생한 test/benchmark 의미 불일치를 후속 commit에서 수정했고, migration sequence 동안 검증을 통과했습니다.

## Render 운영 원칙

GitHub Repository 통합과 Render Service 통합은 동일한 작업이 아닙니다.

- GitHub Source of Truth: `hjang12/ai-agent-cicd-system-by-gpt` 하나
- Render deploy units: 프로젝트별 Web Service를 유지
- Janggi Service Root Directory: `projects/personal-ai-janggi-trainer-by-gpt`
- Time Dashboard Service Root Directory: `projects/time-dashboard-by-gpt`

Render는 동일 Git Repository에 여러 Service를 연결하고 Service별 Root Directory를 지정하는 monorepo 배포 방식을 지원합니다. 따라서 프로젝트별 서비스 격리를 유지하면서 Repository 수를 줄이는 구조를 사용합니다.

## Render 전환

Root `render.yaml`은 현재 운영 중인 Service 이름을 그대로 사용하여 기존 Service를 Blueprint 대상과 일치시키도록 구성했습니다.

- Janggi
  - Service name: `personal-ai-janggi-trainer-by-gpt`
  - Repository target: canonical monorepo
  - Root Directory: `projects/personal-ai-janggi-trainer-by-gpt`
  - Branch: `main`
  - Region: Singapore
  - Build: `python -m compileall janggi tests`
  - Start: `python app.py`
  - Desired health check: `/api/health`

- Time Dashboard
  - Service name: `time-dashboard-by-gpt`
  - Repository target: canonical monorepo
  - Root Directory: `projects/time-dashboard-by-gpt`
  - Branch: `main`
  - Region: Oregon
  - Build: `pip install -r requirements.txt`
  - Start: `python timefolio_server.py`

### 실제 상태 확인 — 2026-09-18

Render `My Workspace`에서 확인한 현재 Service 설정:

- `personal-ai-janggi-trainer-by-gpt`
  - Repository: `hjang12/ai-agent-cicd-system-by-gpt`
  - Root Directory: `projects/personal-ai-janggi-trainer-by-gpt`
  - Branch: `main`
  - Auto Deploy: enabled
  - Latest live deploy: `51fc3322121167f1c48eb339bbe91bf69858c551`
  - Deploy: `dep-damckfad0e5s73eu325g`
  - URL: `https://personal-ai-janggi-trainer.onrender.com`

- `time-dashboard-by-gpt`
  - Repository: `hjang12/ai-agent-cicd-system-by-gpt`
  - Root Directory: `projects/time-dashboard-by-gpt`
  - Branch: `main`
  - Auto Deploy: enabled
  - Latest live deploy: `51fc3322121167f1c48eb339bbe91bf69858c551`
  - Deploy: `dep-damckue7bikc73b4p7ng`
  - URL: `https://time-dashboard.onrender.com`

따라서 **Render monorepo 전환은 완료되었습니다**. 두 기존 Service가 동일한 canonical GitHub Repository를 사용하고, 각 프로젝트의 Root Directory로 배포 경계를 유지합니다.

배포 검증:
- Janggi: build 성공, `python app.py` 시작, Render `live`.
- Time Dashboard: 첫 전환 빌드는 `requirements.txt`를 찾지 못해 실패했으나, 설정이 적용된 재배포에서 build 성공, `python timefolio_server.py` 시작, `HEAD /` 및 `GET /`가 HTTP 200으로 확인되었고 Render `live`.
- 두 Service 모두 현재 Render `healthCheckPath`는 비어 있습니다. Janggi 애플리케이션에는 `/api/health`가 존재하며, Time Dashboard는 root 응답으로 기동 여부를 확인할 수 있습니다. 명시적 Render health-check 설정은 후속 운영 개선사항으로 남깁니다.

## 파일 차이

GitHub 연결 인터페이스가 바이너리 PNG를 직접 전달하지 못해 Time Dashboard의 `assets/icon.png`는 self-contained SVG `assets/icon.svg`로 대체했고, `manifest.json` 및 관련 HTML 참조를 함께 갱신했습니다.

## 원본 Repository 운영

기존 프로젝트 `-by-gpt` Repository는 historical snapshot으로 취급합니다.

- 신규 개발은 canonical monorepo에서 수행
- 기존 원본 Repository에는 신규 기능을 추가하지 않음
- Archive/Delete는 별도의 destructive lifecycle action으로 수행
- Archive/Delete 전에 필요한 history/evidence/운영 기록을 보존하고 실제 플랫폼 결과를 재확인

## Safe cleanup order

기존 프로젝트 Repository는 현재 Render Service가 직접 참조하고 있으므로 Render cutover 이전에 삭제하지 않는다.

권장 순서는 다음과 같다.

```text
Render Service Source Repository 변경
→ Root Directory 변경
→ monorepo commit 배포
→ Deployment live 확인
→ health / smoke 확인
→ post-deployment 결과 문서화
→ 기존 -by-gpt Repository Archive/Delete
```

현재 연결된 Render MCP 도구에는 기존 Service의 backing Repository / Root Directory를 수정하는 작업이 노출되어 있지 않습니다. Render 공식 문서상 이 설정은 Dashboard/API/Blueprint로 변경할 수 있습니다. 따라서 현재 연결된 도구만으로는 기존 Service 자체의 source 전환을 직접 실행할 수 없으며, Dashboard에서 Source와 Root Directory를 변경하거나 Blueprint를 연결/동기화해야 합니다.

중요: 기존 Service를 삭제하고 새 Service를 만드는 방식으로 대체하지 않습니다. 기존 Service를 유지한 채 source를 monorepo로 전환하여 서비스 URL과 운영 리소스를 유지하는 것을 원칙으로 합니다.
