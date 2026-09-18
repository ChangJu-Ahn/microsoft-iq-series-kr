# Fabric IQ v2 화면 실습 갱신 계획

**목표:** 사용자가 요청한 16단계를 실제 브라우저에서 수행하고, 클릭 위치를 빨간색으로 강조한 화면과 참가자용 설명으로 Fabric IQ 메인 README를 갱신합니다.

**구성:** [helper-v2](../../../labs/02-fabric-iq/helper-v2/README.md)의 세 노트북을 사용합니다. MES·QMS는 `factory_lakehouse`의 `mes`·`qms` 스키마에 적재하고 FDC는 별도 `fdc_eventhouse`에 적재합니다. 온톨로지는 정적 엔터티 11개·관계 18개와 Equipment 시계열 바인딩을 사용합니다.

**도구:** Azure portal, Microsoft Fabric, 브라우저 화면 캡처, Markdown 링크 검사.

## 변경 범위

- [메인 README](../../../labs/02-fabric-iq/README.md)를 참가자용 순차 실행 가이드로 교체합니다.
- 신규 이미지는 `assets/fabric-iq/`에 저장합니다. 기존 이미지는 삭제하지 않습니다.
- helper-v2의 실행 로직·원본 이력·기존 클라우드 리소스는 임의로 변경하지 않습니다.
- 실제 키·토큰은 캡처·문서·로컬 노트북에 저장하지 않습니다. 키가 필요하면 사용자가 원격 실행 화면에 직접 입력합니다.
- 예약 실행은 비대화형 인증과 실행 종료 시각을 확인한 후 활성화합니다. 키 공급이 준비되지 않으면 미완료로 기록합니다.
- 생성 완료, 데이터 저장, Graph 관계 조회, 에이전트 응답 정확성을 각각 구분해 검증합니다.
- Git 커밋과 기존 리소스 삭제는 수행하지 않습니다.

## 실행 체크리스트

- [x] 1. 새 리소스 그룹 생성 화면과 생성 결과 촬영.
- [x] 2. 해당 그룹에 Fabric F2 용량 배포. 리전·가격·배포 완료 확인.
- [x] 3. Fabric 워크스페이스 신규 생성.
- [x] 4. 생성된 워크스페이스의 유형을 Fabric으로 변경하고 신규 F2 할당 확인.
- [x] 5. Lakehouse schemas를 활성화한 `factory_lakehouse` 생성.
- [x] 6. `01_factory_lakehouse.ipynb` 임포트, 기본 Lakehouse 연결, 입력값 설정 및 실행.
- [x] 7. `mes` 3개·`qms` 8개 테이블 목록, 저장 행 수와 샘플 확인.
- [x] 8. `fdc_eventhouse` 생성 및 읽기/쓰기 KQL Database 확인.
- [x] 9. `02_fdc_eventhouse.ipynb` 임포트, `KUSTO_URI`·`KUSTO_DATABASE` 설정 및 실행.
- [x] 10. FDC 테이블·행 수·시간 범위·중복 키와 실제 데이터 확인.
- [ ] 11. FDC 예약 실행 설정 및 실행 전후 증분 확인. 종료 시각 지정.
- [x] 12. `03_manufacturing_ontology.ipynb` 임포트, 기본 Lakehouse 연결, `KQL_DATABASE_NAME`·`ONTOLOGY_NAME` 설정 및 생성. Graph 완료 출력은 미확인.
- [ ] 13. Graph 새로 고침 완료 확인 후 새 Queryset에서 노트북이 출력한 GQL 실행. 실제 관계와 원본 기대 건수 대조.
- [x] 14. `factory_dataagent` 생성 및 이번 온톨로지 연결.
- [x] 15. `data-agent-instructions.txt` 전문 반영 및 저장 확인.
- [x] 16. Publish 후 기본 질문 0 실행 및 실제 질의·도구 반환값·최종 답변 대조. 도구 조회는 성공했으나 최종 목록 중복·누락으로 실패. 모든 필드의 원본 행별 재대조는 미완료.

## 문서 및 이미지 검증

- [ ] 단계마다 클릭 전 위치 강조 화면과 실행 후 결과 화면을 구분합니다.
- [ ] 저장된 이미지를 열어 잘림·가독성·강조 위치·비밀값 노출 여부를 확인합니다.
- [x] 메인 README의 상대 링크와 이미지 파일 존재 여부를 검사합니다.
- [x] 메인 README에 16단계, 사전 준비, 입력 변수, 예상 결과와 비용·정리가 포함됐는지 검사합니다.
- [x] 미실행·실패·부분 확인을 구분하고 과거 helper 실행 결과가 섞이지 않았는지 확인합니다.

## 진행 기록

- helper-v2 문서와 세 노트북의 입력 변수 확인 완료.
- Azure 및 Fabric 로그인 후 홈 화면 확인. 첫 클릭 위치 이미지 저장.
- Azure 탭의 숨김 상태에서 화면 갱신·클릭 안정화 대기가 멈췄습니다. 사용자가 탭을 활성화한 뒤 기존 연결 ID가 만료돼 다시 연결했으나 같은 오류가 반복됐습니다. 마지막 확인은 `visibility: hidden`, `focused: false`, `ready: complete`이며 주소는 Azure 홈입니다. `bringToFront()`와 새로 고침으로 해결되지 않았습니다.
- 재개 시 VS Code의 현재 Azure 브라우저 탭을 보이게 유지한 상태에서 Resource groups 링크의 실제 화면 이동부터 확인합니다. 일반 브라우저의 별도 Azure 탭이 아니라 에이전트가 연결한 통합 브라우저 탭이 대상입니다.
- 브라우저를 새 창으로 분리한 후 visible 상태와 정상 클릭·페이지 갱신을 확인했습니다.
- `rg-iq-fabric-v2-0917` 생성 후 목록의 Central US를 확인했습니다. `fabriciqv20917`의 F2 / Central US 배포 완료를 확인했습니다. 포털 표시 월 예상 가격은 $262.80입니다.
- 메인 README를 v2 구성과 새 이미지 12개를 사용하는 1~2단계 안내로 교체했습니다. 나머지 단계는 아직 미완료로 명시합니다.
- 워크스페이스 `IQ-Fabric-v2-0917` ID: `519a98e5-0ec5-4330-a1d2-2991af13ecb8`. Pro 생성 후 Fabric F2 할당 및 저장 성공을 확인했습니다.
- `factory_lakehouse` ID: `96101a7c-da10-4a96-bd07-4fadffbc4492`. 스키마 사용 생성, 빈 dbo 확인 완료.
- `01_factory_lakehouse` ID: `737be29d-8a50-4a16-9c6e-6667b34dff4c`. 임포트, 기본 Lakehouse 지정 완료. 사용자가 제공한 키를 원격 설정 셀 한 곳에만 입력하고 Run all을 시작했습니다. 아직 적재 완료는 미확인입니다.
- 실행 후 원격 설정 셀의 키를 예제 값으로 복원해야 합니다. 키를 저장소·캡처·이 기록에 남기지 않습니다.
- 첫 실행의 설정 셀 실패는 `FACTORY_LAKEHOUSE_NAME`의 대소문자 불일치였습니다. 원격 값을 `factory_lakehouse`로 변경한 뒤 설정 셀 성공, Run all 15개 코드 셀 성공과 11개 VERIFIED 출력 확인. 합계 1,119행입니다.
- 7단계 저장값 검증은 통과했으나 Lakehouse 화면의 테이블·샘플 조회는 미완료입니다. 이미지 36에 전체 저장값 검증 출력을 촬영했습니다. 이미지 06은 검색 결과가 빠져 재촬영이 필요합니다.
- 키 복원 직전에 페이지가 재로드되어 프레임 참조가 만료됐습니다. 2026-09-17T15:09Z 무렵 노트북 본문 로딩의 pbides.powerbi.com CORS 오류를 확인하고 원래 URL로 다시 여는 중입니다. 키 복원 성공·저장 확인은 아직 하지 못했습니다. 재개 후 최우선 확인합니다.
- 이후 새 visible 브라우저 `c7657b92-ee5e-41e9-9440-b9687e680534`에서 복구했습니다. 원격 키를 예제 값으로 복원하고 Saved 및 새로 고침 후 예제 값 유지 확인. 세션 Not connected.
- Lakehouse UI에서 mes 3개·qms 8개, 공정 91행·검사 207행의 샘플 확인. 이미지 37~39. 현재 공정 시작 샘플은 2026-06-19로 과거 helper의 6월 10일과 다릅니다.
- Eventhouse `342852a8-097c-4079-b2f1-e23e926086ce`, KQL Database `625fd4c3-3313-4bd8-8482-32cca8d41317`, 이름 모두 `fdc_eventhouse`. Query URI `https://trd-mr5spmxyvjy3ay4858.z5.kusto.fabric.microsoft.com`을 UI Copy URI 및 로컬 클립보드로 확인했습니다.
- 02 노트북 `efcd6558-cb4c-4013-8463-c05ce9a8bd39` 임포트 및 첫 설정 셀 입력 후 실행 중. 현재 코드에서 키는 MES_KEY_INPUT 직접 사용이며 README의 환경 변수·getpass 설명과 불일치합니다. 원격 키는 실행 후 비워야 합니다. 예약은 안전한 키 공급 없이 활성화하지 않습니다.
- 02 최초 실행 14개 코드 셀 성공. KQL 저장 검증: 스펙42, 판독506392, 중복0, Run93210, Alarm294. Run 2026-06-19T07:13:30~06-21T23:59:30, Idle 최신09-17T15:20 UTC. 키를 빈 문자열로 복원 후 세션 종료 성공. 15분 예약 양식은 캡처 후 Cancel, 미저장·미활성화.
- 03 노트북 ID `6840fc6d-638e-4eee-9959-c6821724e968` 임포트·factory_lakehouse 기본 연결·fdc_eventhouse/Factory_Ontology 설정 후 Run all 시작. 결과 확인 필요.

## 최신 재개 상태

- 앞선 진행 기록은 당시 상태이며 이 절이 최신입니다. 01·02 원격 키 제거 저장을 다시 열어 확인했습니다. 02 세션 종료 및 03 Not connected 확인.
- Ontology `f7e203de-0296-457f-8ffc-27537a1641e5`, Graph `60183a85-3052-44bf-8efa-6b9468af4d82` 생성. 실행 중 용량 Paused를 ARG로 확인했고 사용자가 직접 재개했습니다. Graph 편집기의 로드 실패 안내는 유지됐으나 새 Queryset의 실제 GQL은 성공했습니다.
- Queryset `factory_graph_checks` ID `06f70761-28c8-4bea-bc32-13307c9fa0b2`: NcrHasDisposition 95, EquipmentHasRuns 84, NCR/DSP 업무 ID·승인 상태 5개 샘플 확인. Graph 완료 출력·18개 관계 전체 검증은 미확인입니다.
- Data Agent `factory_dataagent` ID `96e07abb-588d-40d8-8563-45fb771557a5`: 이번 온톨로지 연결, 11개 엔터티 표시, 지침 4,003자 SHA-256 일치 확인(앞뒤 공백 제외). 게시본에도 소스·지침 확인. Microsoft 365 Copilot 추가 게시는 Off.
- 게시본 질문 0 실제 실행 66초. Steps completed의 생성 GQL은 NcrHasDisposition을 사용, 도구 결과 95행·고유95·누락0, Disp_ncr_id 일치95. 최종 답변94줄·고유92, 중복0032/0033, 누락0003/0051/0062. 표시 필드94줄은 도구 반환값과 일치. 답변 목록 검증 실패로 기록했으며 모델·지침 변경으로 임의 보정하지 않았습니다.
- 11단계 예약은 양식 촬영 후 Cancel. 키 공급 방식 미구성으로 미완료. 추가 구현·설정에 대한 사용자 결정이 필요합니다.
- README 16단계 전면 갱신 및 로컬 링크 검사 통과. 이미지06 검색결과 재촬영 완료. 이미지83은 실제 응답 로딩 완료 후 재촬영했습니다. F2 일시 중지·삭제는 하지 않았습니다.