# Fabric IQ 현재 실행 도우미 (helper-new)

한 개의 `factory_lakehouse`에 MES·QMS 데이터를 적재하고, `fdc_eventhouse`의 센서 시계열을 온톨로지에 연결하는 실습 파일입니다. 기존 helper 파일이나 기존 실습 리소스 없이 실행할 수 있습니다.

현재 실행용 V2 노트북의 기술 안내입니다. 먼저 [Fabric IQ 메인 시나리오](../README.md)에서 고객의 업무 질문·산출물·해결 범위를 확인하고 이 문서로 진행합니다.

## 사전 준비

- Fabric 용량이 할당된 작업 영역과 Contributor 이상 권한, 온톨로지·Data Agent에 필요한 테넌트 사용 설정을 준비합니다.
- 같은 작업 영역에 스키마를 활성화한 `factory_lakehouse`와 Eventhouse 및 읽기/쓰기 KQL Database `fdc_eventhouse`를 직접 생성합니다.
- 제공된 Mock MES 주소와 실습용 키를 사용합니다. 세 노트북은 같은 MES 이력을 사용하며 실행 중 재시드하지 않습니다.
- 온톨로지 바인딩용 MES·QMS는 관리형 Delta 테이블을 사용합니다. 노트북이 안내하는 OneLake 보안·Delta column mapping 제약에 맞는 별도 실습 대상을 준비하고, 공용 데이터의 보안 설정을 낮추지 않습니다.

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

**02번 노트북의 도입부에는 환경 변수·프롬프트로 키를 전달한다는 이전 설명이 남아 있지만 실제 코드는 `MES_KEY_INPUT`을 사용합니다.** 이 가이드의 설정을 따릅니다. 별도 MES 서버를 사용할 때도 01번의 환경 변수만 바꾸면 02번에 전파되지 않으므로 두 노트북의 실제 `MES_BASE_URL`을 같은 주소로 맞춥니다.

03번은 Fabric 런타임에서 `microsoft-fabric-api==0.1.0b24`와 `azure-identity>=1.17,<2`를 설치하는 셀을 포함합니다. 런타임 재시작 안내가 나오면 재시작 후 설정 셀부터 계속합니다. 동명 온톨로지의 정의가 다르면 기본 설정에서 덮어쓰지 않고 중단하므로, 기존 항목을 무조건 삭제하지 말고 실제 ID와 정의를 확인합니다.

## 원본 계약과 시간 기준

| 소스 | 현재 저장·연결 범위 |
|---|---|
| `mes.equipment` | `eqp_id STRING`, `eqp_type STRING`. 공정이력과 공정경로에서 도출하며 전체 설비 마스터 복제본이 아님 |
| `mes.lot` | `lot_id STRING`, `product_code STRING`. 현재 WIP·로트 상태·수량은 저장하지 않음 |
| `mes.process_result` | `id INT`, `lot_id STRING`, `eqp_id STRING`, `step_code STRING`, `in_time TIMESTAMP`, `out_time TIMESTAMP`. 설비 미지정 행도 보존 |
| `qms` 8개 테이블 | `defect_code`·`inspection_spec`·`inspector`·`inspection`·`measurement`·`incoming_inspection`·`nonconformance`·`disposition` |
| KQL Database | `fdc_sensor_spec`과 `fdc_sensor_reading`. 온톨로지에는 판독값의 6개 속성만 Equipment 시계열로 바인딩 |

노트북 내부의 `mes_process_result`·`qms_inspection` 같은 계약 키와 실제 물리 테이블명을 구분합니다. 실제 생산 실행 연결은 `qms.inspection.mes_process_result_id → mes.process_result.id`입니다. 로트·공정 코드만으로 개별 실행을 대체하지 않습니다. PK/FK는 논리적 관계이며 물리적인 외래 키 제약을 생성하지 않습니다.

기본 생성 목표는 QMS 순서대로 24·108·15·207·260·200·95·95행, 합계 **1,004행**입니다. 이는 현재 클라우드 행수나 임의의 MES 입력에서 보장되는 결과가 아닙니다. NCR·처리는 기본 생성에서 95:95이고, NCR 출처 목표는 공정검사 43·출하검사 6·입고검사 40·고객제기 6건입니다. 참조 컬럼은 배타적이지 않으며 입고검사와 로트를 잇는 일부 기록도 합성 연결이지 실제 자재 투입 증거가 아닙니다.

QMS 날짜는 MES 공정의 최대 `out_time`(UTC 앵커)에서 계산하며 실행일로 옮기지 않습니다. MES와 QMS는 별도로 조회하므로 순차 실행만으로 단일 스냅샷 트랜잭션이 보장되지는 않습니다. 01번 MES 컨텍스트 조회는 두 번 읽어 변경을 검사하지만, QMS 조회부터 FDC 조회까지 전체 원본을 잠그지는 않습니다.

FDC 최초 실행은 MES 시작부터 실행 시각까지 백필하고 이후에는 워터마크 뒤를 추가합니다. 가동 표본은 30초, 유휴 표본은 5분 간격이며 MES 이력 종료 뒤에는 유휴 데이터가 이어집니다. 생산 관측은 동일 설비의 `in_time <= reading_ts < out_time`에서 찾습니다. `fdc_sensor_reading`에는 `lot_id`·제품·불량코드·검사 판정이 없고, `eqp_type`·`step_code`는 있지만 로트 귀속에는 MES 실행과 시간이 필요합니다.

## Data Agent 질문

생성한 온톨로지를 Data Agent 소스로 연결하고 [에이전트 지침](data-agent-instructions.txt) 전문을 적용합니다. 게시 후 [비즈니스 시나리오](README-ontology-business-scenarios.md)의 질문을 새 대화에서 하나씩 실행합니다.

## 실행 확인

- 01번: 마지막 셀의 `11 tables verified`와 테이블별 저장값 검증을 확인합니다.
- 02번: 센서 스펙 42행, 해당 실행의 판독값 건수와 중복 키 0건을 확인합니다. 판독값 수는 실행 시각에 따라 달라집니다.
- 03번: Graph 로드 완료와 관계별 기대 건수를 실제 GQL 결과에 대조합니다. 생성 성공만으로 조회 성공을 판단하지 않습니다.

02번의 저장 후 건수·중복 확인과 03번의 GQL 대조는 출력된 안내에 따라 별도 Queryset에서 수행합니다. 셀 실행 성공이 이 조회를 자동 수행했다는 뜻은 아닙니다. FDC 스펙 키는 `(eqp_type, sensor_code)`, 판독값 중복 확인 키는 `(reading_ts, eqp_id, sensor_code)`입니다.

기존 안내에는 **예약·증분 검증, Graph 완료 출력 및 18개 관계 전체 대조의 미완료·미확인**과 Data Agent 목록의 중복·누락이 기록되어 있었습니다. [검증 상태](../README.md#검증-상태)는 이 기록과 사용자 제공 답변 확인을 구분합니다. 세 노트북의 저장된 실행 출력은 비어 있으므로 현재 클라우드 실행 증거로 사용할 수 없습니다.

## 재실행과 정리

- MES·QMS는 대상 테이블을 덮어쓰고, FDC는 기존 워터마크 이후를 이어서 적재합니다. 동시 실행과 부분 실패 상태에서의 후속 실행을 피합니다.
- 01번은 기본 `ALLOW_CONTEXT_RESET=False`로 기존 MES 키·시간축 변경을 거부합니다. 11개 테이블 저장은 단일 트랜잭션이 아니므로 부분 실패를 해결하고 저장값 검증을 마친 뒤 다음 단계로 진행합니다. 키·앵커 불일치를 없애려고 재시드·초기화를 임의로 수행하지 않습니다.
- 예약 실행은 안전한 비대화형 키 공급을 준비한 뒤 사용합니다. 키를 비운 상태로 예약을 켜거나 일반 예약 파라미터에 실제 키를 남기지 않습니다.
- FDC 노트북의 30일 보존 정책 DDL은 **출력만 하고 적용하지 않습니다.** 실제 보존 정책을 확인하지 않고 30일 뒤 자동 정리된다고 가정하지 않습니다. 오류 메시지의 재배포·테이블 삭제 예시는 자동 복구 절차가 아니며, 이력·ID·공유 사용 여부를 먼저 확인합니다.
- 종료 후 키를 제거하고 자신의 Spark 세션·예약을 중지합니다. 세션 종료와 유료 Fabric 용량의 일시 중지는 별개입니다.
- 리소스 정리는 실제 ID와 사용 여부를 확인하고 이번 실습에서 만든 항목만 대상으로 합니다. 세부 절차는 [메인 가이드의 비용 및 정리](../README.md#비용-및-정리)를 따릅니다.

## 코드 구조와 로컬 회귀 확인

MES 조회는 클라이언트 객체를 따로 만들지 않고 `fetch_mes_snapshot()`, `fetch_mes_context()`, `fetch_mes_facts()`를 직접 호출합니다. 요청 ID는 표준 반복자로 만들며, 응답 검증·연결 종료·조회 함수의 키 참조 정리는 유지합니다. 검사 ID도 같은 순서의 표준 반복자를 사용합니다.

생성 데이터의 이름·타입을 나타내는 작은 데이터 클래스와, SDK 토큰 갱신·장기 작업 대기·오류 구분에 필요한 객체는 유지합니다. 이를 없애기 위해 사전 키 접근이나 전역 상태를 늘리지 않습니다. 데이터 생성 규칙·난수 시드·스키마·워터마크·저장 동작도 변경하지 않습니다.

[로컬 회귀 테스트](test_notebook_refactor.py)는 보관용 노트북을 변경 전 기준으로 사용합니다. 테스트 전용 입력으로 QMS 8개 테이블의 전체 행·순서·스키마·검증 보고서, FDC 센서값·스키마, MES 요청·오류·연결 정리를 비교합니다. 테스트 입력은 실제 워크숍 데이터나 실행 결과를 대신하지 않습니다. 실행 노트북 자체는 보관본을 불러오지 않습니다.

저장소 루트에서 Python 3.10 이상으로 실행합니다. 표준 라이브러리만 사용하며 외부 로그인·API 호출·데이터 적재·의존성 설치는 하지 않습니다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s labs/02-fabric-iq/helper-new -p 'test_*.py'
```

로컬 비교가 실제 Fabric 실행을 대신하지는 않습니다. 리팩토링 후 Spark 적재·Eventhouse 증분 적재·온톨로지 게시를 원격에서 재실행한 것은 아니며, 실제 진행 전에는 위 실행 확인 기준으로 해당 환경에서 검증해야 합니다.