# 사내 제조 시스템 데이터 관계 문서 설계

## 목적

Microsoft IQ Series 제조 시나리오의 시작점으로 Mock MES, QMS, FDC가 각각
무엇을 담당하고 어떻게 연결되는지 설명한다. 참가자가 이후 Fabric IQ와 Foundry IQ
실습에서 교차 질의를 해야 하는 이유를 이해하는 것이 목표다.

## 대상 문서

| 문서 | 역할 |
| --- | --- |
| `labs/01-inhouse-system/README.md` | 시스템의 업무 역할, 전체 연계도, Foundry IQ를 통한 통합 목표 |
| `labs/01-inhouse-system/data-relationship.md` | 비즈니스 키와 시간축, FDC에서 시작하는 3단 교차 분석 흐름 |

## 확인한 사실

- Mock MES는 로트, 공정실적, WIP, 자재, 제품, BOM, 설비를 제공하며 REST/OpenAPI와 MCP Tools를 함께 제공한다.
- QMS는 Fabric Lakehouse의 Delta 테이블에 검사, 측정, 부적합 및 처리 결정을 저장한다.
- FDC는 Fabric Eventhouse의 KQL DB에 설비 센서 시계열을 저장한다.
- QMS와 MES는 `lot_id`, `product_code`, `step_code`, `material_code`로 연결한다.
- FDC와 MES는 `eqp_id`와 공정실적의 시간 범위로 연결한다.
- 세 시스템은 외래 키를 공유하지 않으며, QMS와 FDC는 같은 MES 시간축에 맞춰 적재해야 한다.
- 로그인 계정에서 `fabriccjmenufacturing` Fabric Capacity는 Central US, F2, Succeeded 상태로 확인했다. Fabric 포털에서는 `QMS-Workspace`를 확인했다.

## 표현 방식

- 첫 문서에 시스템 간 데이터 생성과 질의 경로를 보여 주는 Mermaid 다이어그램 1개를 둔다.
- 상세 문서에 데이터 키·시간축 다이어그램과 FDC 이상 분석의 3단 흐름 다이어그램을 둔다.
- Fabric 포털에서 실제 항목 이름을 확인하지 못한 Lakehouse와 Eventhouse는 역할명으로만 쓴다.
- 기존 Lakehouse/FDC 헬퍼 문서의 데이터 건수와 동작 제약을 반복하지 않고, 해당 문서로 연결한다.

## 검증

- Mermaid 코드 블록이 3개인지, 문서 간 상대 링크가 존재하는지 확인한다.
- 시스템 역할, 연결 키, 시간축 규칙이 기존 Lakehouse와 Eventhouse 안내의 설명과 일치하는지 확인한다.