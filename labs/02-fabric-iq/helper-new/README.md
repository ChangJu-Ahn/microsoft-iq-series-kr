# Fabric helper-v2

한 개의 `factory_lakehouse`에 MES·QMS 데이터를 적재하고, `fdc_eventhouse`의 센서 시계열을 온톨로지에 연결하는 실습 파일입니다. 기존 helper 파일이나 기존 실습 리소스 없이 실행할 수 있습니다.

2026-09-18 기준 V2 안내입니다. 화면별 준비·실행 단계와 실제 검증 결과는 [Fabric IQ 실습 가이드](../README.md)를 따릅니다.

## 사전 준비

- Fabric 용량이 할당된 작업 영역과 Contributor 이상 권한, 온톨로지·Data Agent에 필요한 테넌트 사용 설정을 준비합니다.
- 같은 작업 영역에 스키마를 활성화한 `factory_lakehouse`와 Eventhouse 및 읽기/쓰기 KQL Database `fdc_eventhouse`를 직접 생성합니다.
- 제공된 Mock MES 주소와 실습용 키를 사용합니다. 세 노트북은 같은 MES 이력을 사용하며 실행 중 재시드하지 않습니다.

## 실행 순서

Fabric에 노트북을 임포트하고 아래 순서로 설정한 뒤 각 노트북의 셀을 위에서부터 실행합니다.

| 순서 | 노트북 | 설정 | 결과 |
|---|---|---|---|
| 1 | [01_factory_lakehouse.ipynb](01_factory_lakehouse.ipynb) | `factory_lakehouse`를 기본 Lakehouse로 연결, `FACTORY_LAKEHOUSE_NAME = "factory_lakehouse"`, `MES_KEY_INPUT` 입력 | `mes` 3개·`qms` 8개 테이블 적재 및 저장값 검증 |
| 2 | [02_fdc_eventhouse.ipynb](02_fdc_eventhouse.ipynb) | 실제 Query URI를 `KUSTO_URI`에 입력, `KUSTO_DATABASE = "fdc_eventhouse"`, `MES_KEY_INPUT` 입력 | `fdc_sensor_spec`·`fdc_sensor_reading` 적재 |
| 3 | [03_manufacturing_ontology.ipynb](03_manufacturing_ontology.ipynb) | 같은 기본 Lakehouse 연결, `KQL_DATABASE_NAME = "fdc_eventhouse"`, `ONTOLOGY_NAME = "Factory_Ontology"` | 정적 엔터티 11개·관계 18개와 Equipment 시계열 바인딩 생성 |

01·03번의 Lakehouse ID는 기본 연결에서 자동으로 읽습니다. 02번은 기본 Lakehouse 연결이 필요하지 않습니다. `mes`·`qms` 스키마는 01번이 생성하며 `dbo`는 사용하지 않습니다.

`KUSTO_DATABASE`와 `KQL_DATABASE_NAME`은 동일한 **KQL Database 이름**입니다. 03번은 현재 작업 영역에서 정확히 일치하는 이름의 ID를 찾으며, 부모 Eventhouse 이름으로 대신 조회하지 않습니다.

01·02번은 소스의 `MES_KEY_INPUT`을 직접 사용합니다. 환경 변수나 비밀번호 프롬프트에서 자동으로 읽지 않습니다. 입력한 키는 노트북에 저장되므로 완료 후 제거하고 공유·내보내기·커밋 전에 소스와 출력을 확인합니다.

## Data Agent 질문

생성한 온톨로지를 Data Agent 소스로 연결하고 [에이전트 지침](data-agent-instructions.txt) 전문을 적용합니다. 게시 후 [비즈니스 시나리오](README-ontology-business-scenarios.md)의 질문을 새 대화에서 하나씩 실행합니다.

## 실행 확인

- 01번: 마지막 셀의 `11 tables verified`와 테이블별 저장값 검증을 확인합니다.
- 02번: 센서 스펙 42행, 해당 실행의 판독값 건수와 중복 키 0건을 확인합니다. 판독값 수는 실행 시각에 따라 달라집니다.
- 03번: Graph 로드 완료와 관계별 기대 건수를 실제 GQL 결과에 대조합니다. 생성 성공만으로 조회 성공을 판단하지 않습니다.

메인 가이드에는 MES·QMS·FDC 적재 검증, 온톨로지 생성, 일부 GQL 관계 조회와 Data Agent 게시·질문 실행 결과가 기록돼 있습니다. 해당 실행의 **예약·증분 검증, Graph 완료 출력 및 18개 관계 전체 대조는 미완료 또는 미확인**이며, Data Agent 최종 목록의 중복·누락도 기록돼 있습니다. 상세 결과는 [메인 가이드의 검증 상태](../README.md#검증-상태)를 확인합니다.

## 재실행과 정리

- MES·QMS는 대상 테이블을 덮어쓰고, FDC는 기존 워터마크 이후를 이어서 적재합니다. 동시 실행과 부분 실패 상태에서의 후속 실행을 피합니다.
- 예약 실행은 안전한 비대화형 키 공급을 준비한 뒤 사용합니다. 키를 비운 상태로 예약을 켜거나 일반 예약 파라미터에 실제 키를 남기지 않습니다.
- 종료 후 키를 제거하고 자신의 Spark 세션·예약을 중지합니다. 세션 종료와 유료 Fabric 용량의 일시 중지는 별개입니다.
- 리소스 정리는 실제 ID와 사용 여부를 확인하고 이번 실습에서 만든 항목만 대상으로 합니다. 세부 절차는 [메인 가이드의 비용 및 정리](../README.md#비용-및-정리)를 따릅니다.