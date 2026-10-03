# Web IQ 데모 구현 계획

> 2026-09-30 진행자 시연 자료를 만들 때의 구현·검증 이력입니다. 현재 워크숍의 참가자 직접 호출과 키 제공 조건은 [메인 README](README.md)를 따릅니다.

**목표:** 승인된 계정으로 실제 검색 결과를 캡처하고, 고객은 설명 자료와 실행 결과를 살펴본다. 접근 권한이 있는 진행자는 REST와 MCP 노트북을 재실행한다.

**구성:** [README](README.md)에 실습 안내, [assets](assets/)에 실제 포털 캡처, 이 폴더에 REST와 MCP Python 노트북을 둔다. 검색어는 Microsoft Foundry와 Microsoft Copilot이다.

## 제약

- 고객의 직접 접근을 전제로 하지 않는다. Limited Access 표기와 API 문서의 GA 표기를 구분한다.
- Web IQ 포털과 공식 API 문서를 사용한다. 일반 웹 검색으로 결과를 대체하지 않는다.
- 기존 README의 공식 문서 링크를 보존한다. 다른 IQ 폴더는 수정하지 않는다.
- 키, 쿠키, 인증 토큰을 소스·캡처·실행 출력에 저장하지 않는다.
- 사용자 허락 없이 기존 키를 회전하거나 삭제하지 않는다.
- 실제 실행 결과만 보존하며, 실행하지 못한 항목은 명시한다.

## 실행과 검증

- [x] Playground에서 두 검색어를 Web, Images, Videos로 조회한다. Videos 결과의 YouTube 출처를 확인한다.
- [x] 검색어·카테고리·결과가 보이는 캡처 6개를 저장하고 로컬 OCR로 내용을 확인한다.
- [x] Profile Management에서 데모 전용 API 키를 발급하고 키를 제외한 발급 흐름을 캡처한다.
- [x] `01_rest_api.ipynb`에서 공식 REST 엔드포인트를 직접 호출한다. HTTP 상태와 각 결과 목록을 검사한다.
- [x] `02_mcp.ipynb`에서 공식 MCP SDK로 초기화, 도구 목록 조회, 도구 호출을 수행한다. 도구 권한과 오류 여부를 검사한다.
- [x] README에 목표, 접근 조건, 실행 단계, 실제 결과 설명, 비용·키 정리 방법을 작성한다.
- [x] 노트북 구문·실행 출력, 문서 상대 링크, 캡처 파일, 비밀값 노출 여부를 검증한다.

## 검증 기록

- 2026-09-30: 저장소 루트의 공용 가상환경으로 두 노트북의 모든 코드 셀을 실행했다. Web IQ 하위에 만들었던 가상환경은 삭제했다.
- REST 6회 모두 HTTP 200, MCP 6회 모두 `isError=False`, 각각 결과 3건을 확인했다.
- 키 값과 저장된 노트북 내용을 비교해 키가 포함되지 않았음을 확인했다. 로컬 클립보드는 비웠다.
- 검색 캡처 6개와 키 이름 입력 양식 1개를 저장했다. 최소화된 창의 오래된 화면이 찍힌 키 발급 캡처는 실제 창 복원 후 교체했다. 양식 재촬영 중에는 키를 추가 발급하지 않았다.
- Copilot 이미지 첨부 다운로드 오류 때문에 최종 캡처 검증은 이미지 재첨부 대신 로컬 OCR로 수행했다.
- 데모 키는 자동 폐기하지 않았다. 재실행 종료 후 해당 키만 폐기하는 절차를 README에 명시했다.

## 공식 근거

- https://webiq.microsoft.ai/documentation/overview/
- https://webiq.microsoft.ai/documentation/authentication/
- https://webiq.microsoft.ai/documentation/api-reference/web/
- https://webiq.microsoft.ai/documentation/api-reference/images/
- https://webiq.microsoft.ai/documentation/api-reference/videos/
- https://webiq.microsoft.ai/documentation/mcp/