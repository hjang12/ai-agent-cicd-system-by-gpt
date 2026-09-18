# Repository Migration

통합 기준일: 2026-09-18

## 목적

GPT 개발 프로젝트를 하나의 저장소에서 관리해 공통 Governance와 프로젝트별 Context/CI를 함께 사용할 수 있도록 통합했습니다.

## 원본

- Governance: `hjang12/ai-agent-cicd-system-by-gpt` @ `a3fd6fe90f8fe9be3a84436e7a66894d9628b5d8`
- Janggi: `hjang12/personal-ai-janggi-trainer-by-gpt` @ `83932421217f149de46e6e23b89aff9d92467a11`
- Time Dashboard: `hjang12/time-dashboard-by-gpt` @ `fb8e98baa7a81a610c2ccbf767f2995fb9af0a3f`

## 통합 후 경로

- 공통 문서 → `GOVERNANCE/`
- Janggi → `projects/personal-ai-janggi-trainer-by-gpt/`
- Time Dashboard → `projects/time-dashboard-by-gpt/`
- GitHub Actions → 저장소 루트 `.github/workflows/`

기존 프로젝트 저장소의 전체 Git history는 원본 저장소에 보존되어 있으며, 이 저장소에는 최신 상태를 스냅샷으로 가져왔습니다.

## Render 전환

Render 서비스 자체는 기존 서비스와 URL을 유지해야 하므로, 저장소 통합 후 각 서비스의 Repository를 이 저장소로 바꾸고 다음 Root Directory를 설정해야 합니다.

- Janggi: `projects/personal-ai-janggi-trainer-by-gpt`
- Time Dashboard: `projects/time-dashboard-by-gpt`

이 저장소의 루트 `render.yaml`은 위 구성을 코드로 표현한 기준안입니다.

## 파일 차이

GitHub 연결 인터페이스가 바이너리 PNG를 직접 전달하지 못해 Time Dashboard의 `assets/icon.png`는 동일한 경로를 사용하는 셀프컨테인드 SVG `assets/icon.svg`로 대체했고, manifest/HTML의 참조를 함께 갱신했습니다.
