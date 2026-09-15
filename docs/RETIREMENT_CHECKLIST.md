# Project Retirement Checklist

사용하지 않는 프로젝트·Repository·Deployment 자산을 정리할 때 사용하는 체크리스트다.

## 1. Retirement decision

- [ ] 프로젝트 종료 사유 기록
- [ ] 사용자 결정 기록
- [ ] 최종 Active 기능/서비스 확인
- [ ] 종료 대상 Repository 확인
- [ ] 종료 대상 Render Project / Environment / Service 확인

## 2. Dependency and data review

- [ ] Database 확인
- [ ] Persistent Disk / Object Storage 확인
- [ ] 사용자 데이터 보존 필요 여부 확인
- [ ] Export / Backup 필요 여부 확인
- [ ] 다른 프로젝트가 호출하는 API 확인
- [ ] Cron / Worker / Webhook 확인
- [ ] OAuth / external API integration 확인
- [ ] Domain / DNS 확인
- [ ] TLS / certificate 확인
- [ ] Environment Variables / Secrets 확인
- [ ] CI/CD workflow 및 deploy hook 확인

## 3. Cutover / shutdown

- [ ] 신규 사용 유입 차단
- [ ] 서비스 URL의 외부 참조 확인
- [ ] 필요한 데이터/코드 보존
- [ ] Render Service 중지 또는 삭제
- [ ] 삭제 후 URL/API 접근 확인
- [ ] Domain/DNS 제거 또는 변경
- [ ] 외부 연동 제거

## 4. Repository disposition

Repository는 상황에 따라 다음 중 하나를 선택한다.

- Archive: history를 유지하고 활성 개발을 종료
- Delete: 모든 필요한 자료를 별도로 보존한 후 완전 삭제
- Keep: 코드나 기록을 향후 참고용으로 계속 유지

- [ ] 최종 선택 기록
- [ ] 마지막 Commit 기록
- [ ] 필요한 Release/Artifact 보존
- [ ] Repository 삭제/Archive 실행
- [ ] 조직/팀/권한에서 제거 또는 정리

## 5. Post-retirement verification

- [ ] Render에서 삭제/비활성화 상태 확인
- [ ] GitHub에서 Archive/Delete 상태 확인
- [ ] 다른 서비스 영향 없음 확인
- [ ] DNS/Domain 영향 없음 확인
- [ ] 비용 발생 자산 없음 확인
- [ ] Secrets / credentials 폐기 필요 여부 확인
- [ ] Monitoring / Alert 제거
- [ ] Inventory 갱신
- [ ] DEVELOPMENT_HISTORY 기록
- [ ] Issue 종료

## 6. Evidence

최소한 다음을 남긴다.

```text
Retirement Date
Project
Repository
Render Project / Environment / Service
Reason
Preserved Assets
Deleted Assets
External Dependencies Checked
Verification Result
Evidence / Links
```
