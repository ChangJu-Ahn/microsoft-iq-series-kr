# 02. Fabric IQ: 생산·품질·설비 기록으로 운영 문제를 조사하기

**바로 따라 하기:** [사전 준비와 16단계 목차](#walkthrough) · [1단계: 기존 리소스 그룹 선택](#step-01) · [16단계: 게시와 업무 질문 11개](#step-16) · [산출물과 완료 기준](#산출물과-완료-기준)

## 고객 상황과 이 랩을 하는 이유

[CJ전자 반도체 사업부](../00-getting-started/README.md)의 품질·설비 담당자는 검사 결과를 생산 공정과 연결하고 싶습니다. 출하검사 합격 로트에 품질 조치가 남아 있는지, 재작업 실패 비용이 어디에 집중되는지, 어떤 설비를 먼저 점검할지도 알아야 합니다. 별도 표에서 같은 로트·설비를 찾는 것만으로는 공정·검사·처리 관계와 센서 관측 시점을 구분하기 어렵습니다.

이 랩은 **등록된 업무 관계와 운영 데이터를 근거로 질문에 답하는 독립 분석 실습**입니다. 모든 질문을 LOT0004 출하 검토 하나의 하위 작업으로 취급하지 않습니다. 데이터는 기존 MES 이력과 그에 맞춘 합성 품질·센서 자료이며 실제 공장의 실적이나 인과관계를 증명하지 않습니다.

[01 사내 제조 시스템](../01-inhouse-system/README.md)은 공통 배경입니다. 02~04는 서로의 실행 결과를 선행 조건으로 삼지 않으며, 이 랩도 Web IQ·Work IQ 실습 없이 실행합니다.

## 이번 랩의 업무 질문

먼저 기본 질문으로 근거를 연결할 수 있는지 확인합니다. 질문 전문과 결과 판정 기준은 [비즈니스 시나리오](helper-new/README-ontology-business-scenarios.md)를 사용합니다.

| 기본 질문 | 확인하려는 업무 사실 |
| --- | --- |
| 0. 부적합 처리·승인 현황 | NCR과 연결된 처리 종류·승인 상태·담당 부서 |
| 1. 검사·측정 담당 역할 | 검사 결과와 측정값, 검사 담당자와 측정 기록자의 소속·자격 |
| 2. 검사의 생산 공정·설비 | 기본 검사·재검사가 어떤 생산 실행과 설비에 연결되는지 |
| 3. 부적합 발견 근거 | 문제가 발견된 검사·생산 공정·설비와 심각도·추정 비용 |
| 4. 경보 이력 설비의 생산 | 가동 중 경보 이력이 있는 설비와 그 설비의 생산 목록 |

기본 질문 4는 **각 생산 공정에서 경보가 발생했다는 뜻이 아닙니다.** 경보 당시의 영향 로트를 조사하려면 같은 설비의 실제 생산 시간 구간과 센서 관측을 추가 대조해야 합니다.

기본 관계를 확인한 뒤에는 목적에 맞는 확장 질문을 별도로 수행합니다.

| 확장 시나리오 | 해결하려는 문제 | 남길 산출물 |
| --- | --- | --- |
| A. 생산 온도와 불량 비교 | 특정 불량의 평균 온도만 보고 조사 방향을 좁히는 문제 | 비교 가능한 제품·공정의 온도와 다른 불량 관측, 집계 기준 |
| B. 출하검사와 미완료 조치 | 검사 합격을 모든 품질 조치의 완료로 혼동하는 문제 | 대상 로트·관련 NCR·담당 부서·기한·처리 및 승인 상태 |
| C. 재작업 실패·폐기 비용 | 반복 불량과 비용의 집중 지점을 알기 어려운 문제 | 공정·설비별 처리 건수·비용·승인 상태와 중복 제거 기준 |
| D. 설비 점검 우선순위 | 경보 횟수만으로 설비를 단순 비교하는 문제 | 같은 제품·공정의 불합격률·센서별 경보 표본 비율과 점검 후보 |
| E. 측정 판정 근거 | 제품 문제와 측정·판정의 추가 확인 사항을 구분하기 어려운 문제 | 재검사·측정값·적용 규격·담당자 정보와 미확인 항목 |

확장 A~E는 현재 실행 미검증입니다. 질문이 준비되어 있다는 사실과 결과가 원본에 맞는다는 검증을 구분합니다.

## 참가자가 수행할 일

각자 권한이 있는 Fabric 작업 영역에 리소스를 준비합니다. 참가자가 20명이면 작업 영역과 실습 항목도 참가자별로 구분하며, 진행자의 기존 작업 영역을 기본값으로 사용하지 않습니다. Fabric 작업 영역은 Azure 리소스 그룹만 분리한다고 자동으로 분리되지 않습니다.

**사전 준비:** Fabric 용량이 할당된 작업 영역, Contributor 이상 권한, 온톨로지·Data Agent에 필요한 테넌트 설정, 제공된 Mock MES 주소·키가 필요합니다.

| 순서 | 수행 내용 | 실행 자료·확인 결과 |
| --- | --- | --- |
| 1 | 스키마가 활성화된 `factory_lakehouse`를 만들고 기본 Lakehouse로 연결 | [Lakehouse 노트북](helper-new/01_factory_lakehouse.ipynb): MES 3개·QMS 8개 테이블과 저장값 검증 |
| 2 | Eventhouse와 읽기/쓰기 KQL Database `fdc_eventhouse`를 준비하고 Query URI 설정 | [Eventhouse 노트북](helper-new/02_fdc_eventhouse.ipynb): 센서 스펙 42행·판독값·중복 키 확인 |
| 3 | 같은 소스의 온톨로지와 시계열 바인딩 생성·Graph 새로 고침 | [온톨로지 노트북](helper-new/03_manufacturing_ontology.ipynb): 엔터티 11개·관계 18개의 실제 조회 대조 |
| 4 | 자신의 온톨로지를 Data Agent 소스로 연결하고 지침 적용·게시 | [Data Agent 지침](helper-new/data-agent-instructions.txt): 게시된 소스와 버전 확인 |
| 5 | 기본 질문을 새 대화에서 실행하고, 필요한 확장 질문을 선택 | [업무 질문과 판정 기준](helper-new/README-ontology-business-scenarios.md): ID·관계·시간·집계를 원본과 대조 |

노트북별 설정·재실행 주의점은 [상세 실행 가이드](helper-new/README.md)를 따릅니다. 같은 MES 이력으로 순서대로 적재하고, 실습 중 MES를 재시드하거나 동시 적재하지 않습니다. 보관용 `helper-old`는 참가자의 실행 대상이 아닙니다.

현재 물리 테이블은 `factory_lakehouse`의 `mes.equipment`·`mes.lot`·`mes.process_result`와 `qms` 8개 테이블입니다. 보관본의 `dbo.mes_*`·`dbo.qms_*` 테이블이나 REST Pipeline 마스터 테이블을 준비하지 않습니다. MES 생산 판정·수량·현재 WIP, 제품·자재·BOM 원장 전체를 온톨로지에 복제하는 구성이 아닙니다.

<a id="walkthrough"></a>

## 스크린샷으로 따라 하는 16단계

> 아래 스크린샷은 **2026-09-17~18에 기록한 과거 실행 화면**입니다. 새 배포·적재·조회 성공의 증거가 아닙니다. 화면의 리소스 이름·ID·날짜·실행 시간·행 수·가격은 당시 예시이며 현재 환경의 보장값으로 사용하지 않습니다. 현재 UI와 메뉴 위치가 다를 수 있습니다. 영문 UI의 빨간 테두리는 선택·확인 위치이고 회색 영역은 계정 정보를 가린 부분입니다.
>
> **이번 재실행은 기존 Azure 리소스 그룹 `rg-microsoft-iq-series`를 선택합니다.** 이 그룹을 새로 만들거나 이동·삭제하지 않습니다. **2026-10-03 읽기 전용 ARM 조회**에서 이 그룹의 `Microsoft.Fabric/capacities` 리소스 **`fabricchangjuv2`는 F2, Korea Central, Active, `provisioningState: Succeeded`**로 확인됐습니다. 이는 해당 시점의 관측이며 소유·현재 워크로드·실습 격리 가능 여부와 기능·리전 적합성은 아직 미확인입니다. 바로 재사용하거나 중복 용량을 만들지 않습니다.
>
> **이번 재실행은 MES 키 미준비로 중단된 상태이며 새 리소스나 데이터는 생성하지 않았습니다.** 작업 영역 생성 양식에는 **`fabricchangjuv2 - Korea Central`**이 자동 선택됐지만 양식을 취소했으며 새 작업 영역 생성이나 리소스 변경은 하지 않았습니다. 아래 생성·적재 절차는 키 등 사전 조건과 용량 선택을 마친 뒤 진행할 안내입니다. 키를 받기 전에는 01·02번 적재를 실행하지 않고, 안전한 비대화형 키 공급이 없으면 예약을 활성화하지 않습니다.

### 사전 준비와 실행 파일

- Azure 구독에서 기존 그룹·Fabric 용량을 조회할 권한, Fabric 조직 계정과 작업 영역 생성·용량 할당 권한이 필요합니다. 새 용량이 필요한 경우에만 해당 생성·관리 권한을 추가로 확인합니다.
- Fabric 작업 영역 Contributor 이상 권한과 온톨로지·Data Agent에 필요한 테넌트 사용 설정을 확인합니다. 화면의 Power BI Pro 생성 경로를 사용할 경우 해당 라이선스·권한도 확인합니다.
- 기존 용량의 소유·SKU·리전·상태·사용 현황을 먼저 확인하고 실습용으로 격리해 사용할 수 있는 적절한 용량을 선택합니다. 새 유료 F2 용량이 필요한 경우 배포 전에 현재 가격과 사용할 수 있는 기능을 확인합니다. 지원 여부나 권한 오류를 우회하기 위해 공용 데이터의 보안을 낮추지 않습니다.
- 제공된 Mock MES 주소·실습용 키를 준비합니다. 01·02번은 `MES_KEY_INPUT`을 직접 사용하며, 입력한 실제 키는 원격 노트북 소스에 저장됩니다. 환경 변수나 숨김 프롬프트에서 자동 공급된다고 가정하지 않습니다.
- 실행 설정과 재실행 안전장치는 [현재 실행 도우미](helper-new/README.md)를 기준으로 합니다. 과거 화면의 코드·셀 번호보다 현재 파일의 변수와 설명을 우선합니다.

| 순서 | 파일 | 주요 설정 |
| --- | --- | --- |
| 1 | [01_factory_lakehouse.ipynb](helper-new/01_factory_lakehouse.ipynb) | 기본 Lakehouse 연결, `MES_KEY_INPUT`, `FACTORY_LAKEHOUSE_NAME` |
| 2 | [02_fdc_eventhouse.ipynb](helper-new/02_fdc_eventhouse.ipynb) | `KUSTO_URI`, `KUSTO_DATABASE`, `MES_KEY_INPUT` |
| 3 | [03_manufacturing_ontology.ipynb](helper-new/03_manufacturing_ontology.ipynb) | 같은 기본 Lakehouse 연결, `KQL_DATABASE_NAME`, `ONTOLOGY_NAME` |
| 지침 | [data-agent-instructions.txt](helper-new/data-agent-instructions.txt) | Data Agent에 현재 파일 전문 반영 |
| 질문 | [비즈니스 시나리오](helper-new/README-ontology-business-scenarios.md) | 기본 0~4·선택적 승인 후속·확장 A~E |

01·03번의 Lakehouse ID는 기본 연결에서 읽습니다. 02번의 `KUSTO_DATABASE`와 03번의 `KQL_DATABASE_NAME`은 동일한 **KQL Database 이름**이며 부모 Eventhouse 이름으로 대신하지 않습니다.

### 이번에 사용할 이름과 리소스 경계

| 항목 | 이번 재실행에서 사용할 값 | 과거 화면의 예시 |
| --- | --- | --- |
| Azure 리소스 그룹 | **기존** `rg-microsoft-iq-series` | `rg-iq-fabric-v2-0917` |
| Fabric 용량 | 기존 `fabricchangjuv2`(2026-10-03 관측: F2 / Korea Central / Active)의 적합성 확인 후 선택; 새로 만들어야 할 때만 `<사용 가능한 고유 용량 이름>` | `fabriciqv20917`, F2 / Central US |
| Fabric 워크스페이스 | `<본인이 정한 고유 작업 영역 이름>` | `IQ-Fabric-v2-0917` |
| Lakehouse | `factory_lakehouse` | 같은 이름 |
| Eventhouse / KQL Database | `fdc_eventhouse` / `fdc_eventhouse` | 같은 이름 |
| 온톨로지 | `Factory_Ontology` | 같은 이름 |
| Data Agent | `factory_dataagent` | 같은 이름 |

`<...>`는 직접 정할 값을 표시한 것으로 그대로 입력하지 않습니다. 용량 이름은 포털의 이름 규칙·사용 가능 여부 검사를 따릅니다. 이후 화면에서 과거 용량·작업 영역 이름이 보이면 **자신이 이번에 정한 이름**으로 대체합니다. 이미 동일 항목을 준비했다면 실제 ID와 소유·사용 범위를 확인하며, 무조건 중복 생성하거나 덮어쓰지 않습니다.

Azure 리소스 그룹에 속하는 것은 **Fabric 용량 리소스**입니다. Fabric 워크스페이스는 이 용량에 할당되고 Lakehouse·Eventhouse·온톨로지·Data Agent는 그 작업 영역 안에 생성됩니다. 작업 영역과 항목은 Azure RG의 자식 리소스가 아니므로 그룹 선택만으로 생성·이동·참가자별 격리가 되지 않습니다.

### 적재 전 꼭 확인할 사항

- 세 노트북은 같은 MES 주소·이력을 사용합니다. 01번의 환경 변수 변경이 02번에 전파되지 않으므로 양쪽의 실제 `MES_BASE_URL`을 확인합니다.
- MES·QMS의 순차 조회는 단일 스냅샷 트랜잭션이 아닙니다. 01번의 두 번 읽기 검사도 QMS부터 FDC까지 원본 전체를 잠그지 않습니다. 실습 중 재시드·동시 적재를 하지 않습니다.
- 01번은 11개 테이블을 덮어쓰며 단일 트랜잭션으로 저장하지 않습니다. 기본 `ALLOW_CONTEXT_RESET = False`를 유지하고 키·시간축 불일치나 부분 실패를 해결한 뒤 후속 단계로 진행합니다.
- FDC는 최초 백필 후 워터마크 뒤를 추가합니다. 기존 데이터·워터마크를 지워 불일치를 숨기지 않습니다. 30일 보존 정책 DDL은 출력만 하므로 자동 적용·자동 정리를 가정하지 않습니다.
- 날짜·생성 규칙을 현재 날짜나 원하는 답변에 맞게 바꾸지 않습니다. 자세한 기준은 [원본 계약과 시간 기준](helper-new/README.md#원본-계약과-시간-기준), [재실행과 정리](helper-new/README.md#재실행과-정리)를 따릅니다.

### 목차

| 단계 | 따라 할 작업 |
| --- | --- |
| [1](#step-01) | 기존 리소스 그룹 선택 — 과거 생성 화면은 건너뛰기 |
| [2](#step-02) | 기존 용량 확인·선택, 필요한 경우에만 Fabric F2 배포 |
| [3](#step-03) | 워크스페이스 신규 생성 |
| [4](#step-04) | Fabric 용량 할당 |
| [5](#step-05) | factory_lakehouse 생성 |
| [6](#step-06) | 01번 노트북 임포트·설정·실행 |
| [7](#step-07) | MES·QMS 테이블과 저장값 확인 |
| [8](#step-08) | fdc_eventhouse 생성 |
| [9](#step-09) | 02번 FDC 노트북 실행 |
| [10](#step-10) | FDC 저장 데이터 검증 |
| [11](#step-11) | 예약 양식 확인 — 키 공급 미구성 시 미저장 |
| [12](#step-12) | 03번 온톨로지 노트북 실행 |
| [13](#step-13) | Graph에서 GQL 조회 |
| [14](#step-14) | Data Agent 생성·소스 연결 |
| [15](#step-15) | 지침 반영 |
| [16](#step-16) | 게시·기본 질문·선택적 후속·확장 질문 |

<a id="step-01"></a>

## 1. 기존 리소스 그룹 선택

### 1-1. Resource groups 열기

[Azure portal](https://portal.azure.com/)에 로그인하고 홈의 **Azure services > Resource groups**를 선택합니다. 홈에 보이지 않으면 상단 검색에서 `Resource groups`를 찾습니다.

![Azure services의 Resource groups 선택](../../assets/fabric-iq/01-azure-resource-groups.png)

목록에서 사용할 구독 필터를 확인하고 `rg-microsoft-iq-series`를 검색해 선택합니다. **이번에는 목록 상단의 Create를 누르지 않습니다.** 그룹이 보이지 않으면 구독·디렉터리·조회 권한을 확인하며 동명 그룹을 새로 만들지 않습니다.

아래는 과거에 목록 상단 **Create**를 선택했던 위치입니다. 생성 절차의 화면을 보존한 것이며 이번 실행 지시가 아닙니다.

![리소스 그룹 목록의 Create](../../assets/fabric-iq/02-resource-group-create.png)

### 1-2. 과거 구독·이름·리전 입력 화면 — 건너뛰기

과거 실행은 **Subscription**, **Resource group name: rg-iq-fabric-v2-0917**, **Region: (US) Central US**를 입력하고 **Review + create**를 선택했습니다. **이 양식 입력과 버튼 클릭은 이번 재실행에서 건너뜁니다.** 기존 그룹의 위치를 바꾸지 않습니다.

![새 리소스 그룹 이름과 리전 및 검토 버튼](../../assets/fabric-iq/03-resource-group-basics.png)

### 1-3. 과거 검토·생성 화면 — 기존 그룹 확인으로 대체

과거 화면에서는 검증 후 **Create**로 새 그룹을 만들었습니다. **이번에는 이 Create도 실행하지 않습니다.**

![리소스 그룹 검토와 Create](../../assets/fabric-iq/04-resource-group-review.png)

**Resource groups** 목록으로 돌아가 **Refresh**를 누르고 `rg-microsoft-iq-series`로 필터링합니다. 그룹 이름·구독·실제 위치를 확인합니다. 다음 캡처의 과거 그룹 이름과 Central US를 현재 값으로 오인하지 않습니다. 현재 그룹 목록에서 확인된 `fabricchangjuv2`의 존재와 사용 가능 여부는 별개이므로 다음 단계에서 상세를 확인합니다.

![생성된 리소스 그룹과 Central US 확인](../../assets/fabric-iq/05-resource-group-created.png)

<a id="step-02"></a>

## 2. 기존 용량 확인 및 필요한 경우 Fabric F2 배포

### 2-1. Microsoft Fabric 검색과 기존 용량 확인

Azure 상단 검색에 `Microsoft Fabric`을 입력하고 **Services > Microsoft Fabric**을 선택합니다. Marketplace 검색 결과와 구분합니다.

![Services의 Microsoft Fabric 검색 결과](../../assets/fabric-iq/06-search-fabric.png)

**Create보다 먼저** 목록의 기존 `fabricchangjuv2`를 열어 다음을 확인합니다. 2026-10-03 읽기 전용 ARM 조회에서 **F2 / Korea Central / Active / `provisioningState: Succeeded`**를 확인했지만, Active나 작업 영역 양식의 자동 선택이 유휴 상태·사용 승인·실습 적합성을 뜻하지는 않습니다.

- 리소스 ID·구독·그룹과 소유·관리 담당자, 본인의 사용·할당 권한
- 관측 이후 실제 SKU·리전·용량 상태의 변경 여부와 아직 미확인인 이 실습의 기능·리전 적합성
- 연결된 작업 영역·기존 사용자·진행 중 작업·사용 현황과 실습 부하의 영향
- 기존 업무와 분리된 작업 영역에서 실습용으로 격리해 사용할 수 있는 적절한 용량인지 여부

적합한 기존 용량을 사용할 수 있다면 **2-2·2-3의 생성을 건너뛰고 3단계로 진행**합니다. `fabricchangjuv2`가 적합하지 않거나 사용 승인이 없으면 임의로 선택·재개·일시 중지·크기 변경하지 않습니다. 다른 적절한 격리 용량을 사용할 수 있는지 먼저 확인하고, **새 용량이 필요하다고 확인한 경우에만** 비용·권한·사전 조건을 확인한 뒤 목록 상단의 **Create**를 선택합니다. 이번 재실행은 MES 키 미준비로 아직 생성 단계에 진입하지 않았습니다.

![Microsoft Fabric 용량 목록의 Create](../../assets/fabric-iq/07-fabric-create.png)

### 2-2. 새 용량이 필요한 경우: 배포 대상과 F2 선택

아래는 새 용량 생성 경로입니다. 기존 용량을 선택했다면 이 양식을 사용하거나 기존 SKU를 F2로 바꾸지 않습니다.

| 입력 항목 | 설정 |
| --- | --- |
| Subscription | 1단계에서 기존 그룹을 확인한 구독 |
| Resource group | **기존 그룹 `rg-microsoft-iq-series` 선택**, Create new 사용 안 함 |
| Capacity name | 본인이 정한 사용 가능한 고유 용량 이름 |
| Region | 본인 환경의 사용 가능 리전 확인 후 선택; 과거 화면은 **(US) Central US** |
| Fabric capacity administrator | Fabric에서 사용할 본인 관리 계정 |

과거 화면의 기본 **Size**는 **F64**였습니다. 기본값을 그대로 생성하지 말고 **Change size**를 선택합니다.

![Fabric 기본 입력과 Change size 위치](../../assets/fabric-iq/08-fabric-change-size.png)

**F2 / 2 Capacity units** 행을 선택하고 **Select**를 누릅니다. 화면의 월 예상 가격 **$262.80은 2026-09-17 당시 예시**이며 현재 가격·월 청구액 보장이 아닙니다. 실행 당시 본인의 구독·리전·계약 조건에 표시되는 가격을 확인합니다.

![F2 행과 예상 비용 및 Select](../../assets/fabric-iq/09-select-f2.png)

기본 화면에서 **Size: F2 / 2 Capacity units**, **기존 그룹 `rg-microsoft-iq-series`**, 자신의 용량 이름·선택 리전을 확인하고 **Review + create**를 선택합니다.

![F2 적용 후 기본 설정 검토](../../assets/fabric-iq/10-fabric-basics-f2.png)

### 2-3. 새 용량이 필요한 경우: 검증 후 배포

**Validation succeeded**를 확인합니다. 검토 화면에서 **F2**, 선택한 리전, 기존 그룹과 새 용량 이름, 현재 표시 비용을 확인한 후 **Create**를 선택합니다. 이 버튼부터 유료 용량 배포가 시작됩니다.

![검증 성공과 F2 배포 Create](../../assets/fabric-iq/11-fabric-review-create.png)

배포 요청과 배포 완료는 다릅니다. 자신의 배포에서 **Your deployment is complete**를 확인한 뒤 다음 단계로 진행합니다. **Go to resource**로 생성한 용량의 개요를 엽니다. 다음은 과거 배포 완료 화면이며 이번 배포의 성공 증거가 아닙니다.

![Fabric 배포 완료와 Go to resource](../../assets/fabric-iq/12-fabric-deployment-complete.png)

<a id="step-03"></a>

## 3. 워크스페이스 신규 생성

### 3-1. Workspaces 열기

[Microsoft Fabric](https://app.fabric.microsoft.com/)에 로그인합니다. Azure에서 용량 관리자로 지정한 계정 또는 해당 용량의 할당 권한이 있는 계정을 사용합니다. 왼쪽 **Workspaces**를 선택합니다.

![Fabric Workspaces 메뉴](../../assets/fabric-iq/13-fabric-workspaces.png)

패널 아래 **New workspace**를 선택합니다. 다른 참가자의 작업 영역이나 My workspace에 실습 항목을 추가하지 않습니다.

![Workspaces 패널 New workspace](../../assets/fabric-iq/14-new-workspace.png)

### 3-2. 이름과 초기 유형 지정

**Name**에 본인이 정한 고유 작업 영역 이름을 입력하고 **This name is available**을 확인합니다. 과거 화면의 `IQ-Fabric-v2-0917`은 그대로 복사하지 않습니다.

과거 실습은 생성 후 용량 변경 과정을 보여 주기 위해 **Advanced > Workspace type > Power BI Pro**를 선택했습니다. 이 경로를 사용할 권한·라이선스가 있으면 같은 순서로 진행할 수 있습니다. 생성 양식에서 자신의 Fabric 용량을 바로 선택했다면 굳이 Pro로 바꾸지 않고 다음 절에서 할당 결과를 확인합니다. **Pro 상태에서는 Fabric 할당을 마치기 전 Lakehouse를 만들지 않습니다.**

![워크스페이스의 초기 Power BI Pro 선택](../../assets/fabric-iq/15-workspace-pro.png)

**Advanced**를 접고 이름을 확인한 뒤 **Apply**를 누릅니다.

![워크스페이스 이름과 Apply](../../assets/fabric-iq/16-workspace-create.png)

생성된 작업 영역의 이름과 **Showing 0 item**을 확인합니다. 화면 폭에 따라 상단 버튼이 아이콘으로만 표시될 수 있습니다. **Workspace settings**를 선택합니다.

![빈 워크스페이스 생성과 Workspace settings](../../assets/fabric-iq/17-workspace-created-settings.png)

<a id="step-04"></a>

## 4. Workspace type을 Fabric으로 변경

**Workspace settings > Workspace type**에서 현재 유형을 확인합니다. **Current workspace type: Power BI Pro**라면 **Edit**를 선택합니다. 이미 Fabric이면 이번 용량에 연결되었는지 확인합니다.

![현재 Pro 유형과 Workspace type Edit](../../assets/fabric-iq/18-workspace-type-edit.png)

**Fabric**을 선택합니다. **Details > Select a capacity**에서 2단계에 준비한 **자신의 용량 이름과 리전**을 선택하고 **Select**를 누릅니다. 과거 화면의 `fabriciqv20917 - Central US`, 다른 참가자의 용량이나 Fabric Trial로 대신하지 않습니다. **Semantic model storage format**은 기본값을 유지합니다.

![Fabric 유형과 신규 용량 선택](../../assets/fabric-iq/19-workspace-fabric-capacity.png)

**Your changes were successfully saved**와 다음 값을 확인합니다.

- Current workspace type: **Fabric**
- Details: **자신의 용량 이름**
- SKU / Region: **선택한 용량의 실제 SKU / 리전** — 신규 생성 예시는 F2이며 기존 용량은 2단계의 적합성 확인 결과와 대조합니다.

![저장된 Fabric F2 Central US 할당](../../assets/fabric-iq/20-workspace-f2-confirmed.png)

설정 창 오른쪽 위 **Close**를 눌러 작업 영역으로 돌아옵니다.

<a id="step-05"></a>

## 5. factory_lakehouse 생성

### 5-1. Lakehouse 항목 선택

워크스페이스 상단 **New item**을 선택합니다.

![작업 영역 New item](../../assets/fabric-iq/21-new-item.png)

새 항목 목록의 **Store data > Lakehouse**를 선택합니다. Sample lakehouse를 선택하지 않습니다.

![새 항목에서 Lakehouse 선택](../../assets/fabric-iq/22-select-lakehouse.png)

### 5-2. 이름과 스키마 설정

**Name**에 `factory_lakehouse`를 입력합니다. **Location**이 본인의 실습 작업 영역인지 확인하고 **Lakehouse schemas 체크를 유지**한 채 **Create**를 누릅니다.

![factory_lakehouse 이름과 Lakehouse schemas 활성화](../../assets/fabric-iq/23-create-factory-lakehouse.png)

### 5-3. 생성 결과 확인

로딩이 끝나면 Explorer의 **factory_lakehouse > Tables > dbo**, **Files**를 확인합니다. 이때는 아직 MES·QMS 테이블이 없습니다. `mes`·`qms` 스키마는 01번 노트북의 적재 셀이 생성합니다. SQL analytics endpoint 생성 안내가 표시될 수 있으며, Lakehouse와 별도 유형의 항목입니다.

![노트북 실행 전 Tables dbo와 Files](../../assets/fabric-iq/24-empty-factory-lakehouse.png)

<a id="step-06"></a>

## 6. Factory 노트북 임포트·설정·실행

### 6-1. 워크스페이스에서 Import 열기

왼쪽에서 **본인의 작업 영역 이름**을 선택합니다. 탐색 패널만 열리면 패널 안의 워크스페이스 이름을 한 번 더 선택해 항목 목록으로 이동합니다. 상단 **Import**를 누릅니다. Lakehouse의 Upload files는 데이터 파일용이므로 사용하지 않습니다.

![워크스페이스의 Notebook Import 시작](../../assets/fabric-iq/25-import-notebook.png)

**Notebook**을 선택합니다.

![Import Notebook 메뉴](../../assets/fabric-iq/26-import-notebook-menu.png)

**From this computer**를 선택합니다.

![노트북 From this computer](../../assets/fabric-iq/27-import-from-computer.png)

**Import status > Upload**를 누르고 [01_factory_lakehouse.ipynb](helper-new/01_factory_lakehouse.ipynb)를 선택합니다. OS 파일 선택창에서 [현재 실행 폴더](helper-new/)의 파일인지 확인합니다.

![Factory 노트북 Upload 버튼](../../assets/fabric-iq/28-upload-factory-notebook.png)

임포트 성공 후 목록의 **01_factory_lakehouse**, 유형 **Notebook**을 확인하고 엽니다. 같은 이름으로 다시 임포트하지 않습니다.

![임포트된 01_factory_lakehouse Notebook](../../assets/fabric-iq/29-factory-notebook-imported.png)

첫 방문 기능 안내가 화면을 가리면 **Skip for now**로 닫습니다.

![노트북 첫 방문 안내 Skip for now](../../assets/fabric-iq/30a-notebook-skip-tour.png)

### 6-2. 기본 Lakehouse 연결

왼쪽 **Explorer > Data items**에서 **Add data items**를 선택합니다.

![No data sources added와 Add data items](../../assets/fabric-iq/30-notebook-add-data-items.png)

**From OneLake catalog**를 선택합니다. 이미 생성했으므로 New lakehouse를 선택하지 않습니다.

![From OneLake catalog 선택](../../assets/fabric-iq/31-onelake-catalog.png)

카탈로그에서 **factory_lakehouse**, 위치 **본인의 작업 영역**, 유형 **Lakehouse**인 행을 선택하고 **Add**를 누릅니다. 이름이 같아도 SQL analytics endpoint는 선택하지 않습니다. 유형 아이콘에 마우스를 올려 확인할 수 있습니다.

![작업 영역과 Lakehouse 유형을 확인하고 Add](../../assets/fabric-iq/32-attach-factory-lakehouse.png)

Explorer의 **OneLake > factory_lakehouse**를 오른쪽 클릭하고 **Set as default lakehouse**를 선택합니다. 연결만 하는 것과 기본 대상으로 지정하는 것은 구분합니다. 기본 Lakehouse를 바꾸라는 세션 종료 안내가 나오면 데이터 실행 전에 연결을 마칩니다.

![factory_lakehouse Set as default lakehouse](../../assets/fabric-iq/33-set-default-lakehouse.png)

### 6-3. 입력값과 실행

[현재 설정 안내](helper-new/README.md#실행-순서)에 따라 `MES_KEY_INPUT`과 `FACTORY_LAKEHOUSE_NAME`이 있는 설정 셀을 찾습니다. 과거 화면에서는 첫 코드 셀인 셀 2였습니다. 제공받은 키가 없으면 이 단계의 실행을 멈춥니다.

```python
MES_KEY_INPUT = "<YOUR_MES_KEY>"
FACTORY_LAKEHOUSE_NAME = "factory_lakehouse"
```

실제 키를 입력하면 원격 노트북 소스에 저장됩니다. 실습 완료 후 예제 값으로 되돌리고, 공유·내보내기 전에 소스와 출력을 확인합니다. 문서와 캡처에는 실제 키를 넣지 않습니다.

Lakehouse ID·작업 영역 ID는 기본 연결에서 자동으로 읽습니다. **`FACTORY_LAKEHOUSE_NAME`은 연결 대상의 이름을 검증하는 값이므로 실제 이름과 대소문자까지 맞춥니다.** 과거에는 `"Factory_Lakehouse"`를 `"factory_lakehouse"`로 수정했지만 현재 파일은 소문자 기본값을 확인하면 됩니다. 공통 MES 주소와 `ALLOW_CONTEXT_RESET = False`는 유지합니다.

이름이 맞지 않아 `Expected this workspace's schema-enabled Factory_Lakehouse. No data was written.` 같은 오류가 나면 이름·기본 연결·스키마를 확인하고 설정 셀을 다시 실행합니다. 다음은 과거 이름 수정 후 대상 확인을 통과한 화면입니다. 자신의 실행에서 표시되는 대상 ID를 확인합니다.

![올바른 factory_lakehouse ID와 기본 연결 확인](../../assets/fabric-iq/35-factory-connection-verified.png)

**Run all**을 한 번 누릅니다. Spark 세션 준비 후 설정·MES 조회·QMS 생성·사전 검사·적재·저장값 검증이 순서대로 진행됩니다. 키가 없거나 대상이 잘못 연결되면 오류를 해결한 뒤 다시 실행하며 검증을 우회하지 않습니다. 대상 테이블 11개를 덮어쓰므로 실행을 겹치지 않습니다.

![기본 Lakehouse와 키를 가린 설정 셀 및 Run all](../../assets/fabric-iq/34-factory-settings-run.png)

과거 화면에서는 **15 executions succeeded**와 마지막 셀의 **11 tables verified**가 확인됐습니다. 현재 실행의 셀 개수나 성공을 이 숫자로 대신 판단하지 말고, 마지막 저장값 검증을 다음 절에서 확인합니다.

<a id="step-07"></a>

## 7. 테이블 생성 및 저장값 확인

### 7-1. 마지막 적재 셀 확인

노트북 마지막 셀의 실행이 끝날 때까지 기다립니다. **11개 테이블 모두 `VERIFIED`**와 **11 tables verified**가 출력됐는지 확인합니다. 중간의 `context rows written`만으로 전체 성공으로 판단하지 않습니다.

![MES QMS 테이블 11개의 저장값 검증 결과](../../assets/fabric-iq/36-factory-tables-verified.png)

아래는 **2026-09-17 당시 저장 검증 결과**입니다. 노트북은 생성한 행과 저장된 행의 건수 및 양방향 차집합을 비교했습니다. 이 표는 현재 클라우드 상태나 다른 MES 데이터에서 동일 건수를 보장하는 기준이 아닙니다.

| 테이블 | 과거 저장 검증 행 수 |
| --- | ---: |
| `mes.equipment` | 8 |
| `mes.lot` | 16 |
| `mes.process_result` | 91 |
| `qms.defect_code` | 24 |
| `qms.inspection_spec` | 108 |
| `qms.inspector` | 15 |
| `qms.inspection` | 207 |
| `qms.measurement` | 260 |
| `qms.incoming_inspection` | 200 |
| `qms.nonconformance` | 95 |
| `qms.disposition` | 95 |
| **합계** | **1,119** |

### 7-2. Lakehouse 화면 확인

워크스페이스 목록에서 Lakehouse 유형의 `factory_lakehouse`를 엽니다. **Refresh** 후 **Tables > mes**, **Tables > qms**의 왼쪽 화살표를 눌러 각각 3개·8개 테이블을 확인합니다.

![mes 3개 qms 8개 테이블 목록](../../assets/fabric-iq/37-factory-table-list.png)

`mes.process_result`를 선택합니다. 과거 화면의 **Showing 91 rows**와 `id`, `lot_id`, `eqp_id`, `step_code`, `in_time`, `out_time`을 참고해 자신의 저장값을 확인합니다. 설비가 없는 METRO 이력의 `eqp_id = NULL`은 보존됩니다. 과거 샘플의 공정 시작일은 2026-06-19였으며, 이번 실행에서도 실제 MES 이력의 날짜를 사용하고 현재 날짜로 옮기지 않습니다.

![MES 공정이력 91행의 실제 미리보기](../../assets/fabric-iq/38-mes-process-preview.png)

`qms.inspection`을 선택합니다. 과거 화면의 **Showing 207 rows**와 검사 ID·검사 유형·로트·제품·공정·설비를 참고합니다. 오른쪽의 긴 컬럼은 가로 스크롤해 확인합니다. 샘플 미리보기는 7-1의 전체 저장값 검증과 구분합니다.

![QMS 검사 207행의 실제 미리보기](../../assets/fabric-iq/39-qms-inspection-preview.png)

실행이 끝나면 원격 노트북의 `MES_KEY_INPUT`을 예제 값으로 되돌리고 **Saved**를 확인합니다. 다시 열어 실제 키가 남지 않았는지 확인하고 자신의 Spark 세션을 종료한 뒤 FDC 실습을 진행합니다. **Not connected** 상태도 확인합니다. 이는 이번 실행에서 직접 수행할 정리이며 과거 정리 기록으로 대신하지 않습니다.

<a id="step-08"></a>

## 8. fdc_eventhouse 생성

워크스페이스 목록의 **New item > Store data > Eventhouse**를 선택합니다.

![Store data의 Eventhouse 선택](../../assets/fabric-iq/40-select-eventhouse.png)

**Eventhouse name**에 `fdc_eventhouse`를 입력하고 **Create**를 선택합니다.

![fdc_eventhouse 이름 입력 후 Create](../../assets/fabric-iq/41-create-fdc-eventhouse.png)

생성 후 Welcome 안내는 **Get started**, 이어지는 기능 안내는 **Close**로 닫습니다. 왼쪽 **KQL databases > fdc_eventhouse**를 선택합니다. 과거 생성에서는 같은 이름의 KQL Database가 함께 만들어졌습니다. 이번에도 실제 DB 이름과 읽기/쓰기 대상을 확인합니다.

![생성된 Eventhouse와 KQL Database 선택](../../assets/fabric-iq/42-eventhouse-created.png)

오른쪽 **Database details**가 접혀 있으면 제목 옆 펼치기 아이콘을 누릅니다. **Overview > Query URI** 행의 **Copy URI**를 선택합니다. **MCP Server URI**나 **Ingestion URI**를 복사하지 않습니다. 새 대상의 적재 전 화면은 **Tables > No tables**, **Last ingestion: Data was not ingested**입니다.

![Database details의 Query URI 복사 버튼](../../assets/fabric-iq/43-fdc-query-uri.png)

<a id="step-09"></a>

## 9. FDC 노트북 임포트 및 실행

### 9-1. 노트북 임포트

워크스페이스 목록으로 돌아와 6-1과 같이 **Import > Notebook > From this computer > Upload**를 선택합니다. 이번에는 [02_fdc_eventhouse.ipynb](helper-new/02_fdc_eventhouse.ipynb)를 선택합니다.

![02번 FDC 노트북 Upload](../../assets/fabric-iq/28-upload-factory-notebook.png)

**Imported successfully** 후 목록에서 **02_fdc_eventhouse**, 유형 **Notebook**을 확인하고 엽니다. Eventhouse·KQL Database 항목과 구분합니다.

![임포트된 02_fdc_eventhouse Notebook](../../assets/fabric-iq/45-fdc-notebook-imported.png)

### 9-2. 연결 변수 입력

[현재 설정 안내](helper-new/README.md#실행-순서)에 따라 아래 변수가 있는 설정 셀에 값을 입력합니다. 과거 화면에서는 첫 코드 셀인 셀 2였습니다. KQL Database에 적재하므로 기본 Lakehouse를 연결하지 않습니다.

```python
KUSTO_URI = "<본인의 Query URI>"
KUSTO_DATABASE = "fdc_eventhouse"
MES_KEY_INPUT = "<YOUR_MES_KEY>"
```

- `KUSTO_URI`: 8단계에서 복사한 Query URI. `https://`부터 전체 주소를 입력합니다.
- `KUSTO_DATABASE`: 생성한 **KQL Database 이름**. 이 실습은 `fdc_eventhouse`를 사용합니다.
- `MES_KEY_INPUT`: 01번과 같은 Mock MES의 실습용 키입니다. 키가 없으면 실행하지 않습니다.

현재 파일은 `MES_KEY_INPUT`을 직접 사용합니다. 노트북 도입부에 남은 환경 변수·비밀번호 프롬프트 설명만 보고 자동으로 키가 공급된다고 가정하지 않습니다. 실제 키는 소스에 임시 입력하고 완료 후 제거합니다. 과거 캡처의 키 행은 가렸습니다.

### 9-3. 최초 실행

**Run all**을 한 번 선택하고 실행이 시작됐는지 확인합니다. MES 조회·센서 생성·기존 워터마크 확인·사전 검사·적재가 순서대로 진행됩니다. 첫 실행은 과거 공정 구간부터 채우는 백필이며, 완료하기 전 예약 실행을 켜지 않습니다.

![FDC 연결 변수와 키 가림 및 Run all](../../assets/fabric-iq/46-fdc-settings-run.png)

과거 최초 실행에서는 **14 executions succeeded**, 센서 스펙 **42행**, 판독값 **506,392행** 적재가 확인됐습니다. 판독값 수는 MES 이력·실행 시각에 따라 달라지며 현재 기대값이 아닙니다. 실패했다고 곧바로 테이블을 삭제하거나 동시에 재실행하지 않습니다.

![FDC 센서 스펙과 판독값 적재 완료](../../assets/fabric-iq/47-fdc-ingestion-complete.png)

<a id="step-10"></a>

## 10. FDC 저장 데이터 검증

### 10-1. 테이블과 Queryset 열기

`fdc_eventhouse`의 KQL Database로 돌아와 **Refresh**합니다. **Tables** 아래 `fdc_sensor_spec`, `fdc_sensor_reading`을 확인하고 왼쪽 **fdc_eventhouse_queryset**을 선택합니다.

![생성된 FDC 테이블과 Queryset](../../assets/fabric-iq/48-fdc-tables-queryset.png)

Queryset의 예제 쿼리를 지우고 아래 쿼리를 **한 블록씩** 입력하여 **Run**을 선택합니다. 노트북용 `%%sql`은 붙이지 않습니다.

### 10-2. 건수·중복·경보 확인

```kusto
print specs = toscalar(fdc_sensor_spec | count),
readings = toscalar(fdc_sensor_reading | count),
duplicate_keys = toscalar(fdc_sensor_reading | summarize copies = count() by reading_ts, eqp_id, sensor_code | where copies > 1 | count),
run_rows = toscalar(fdc_sensor_reading | where run_status == "Run" | count),
run_alarms = toscalar(fdc_sensor_reading | where run_status == "Run" and status == "Alarm" | count)
```

과거 실제 저장 결과는 **42 / 506,392 / 0 / 93,210 / 294**였습니다. 현재 실행에서는 기본 센서 스펙 42행과 판독값 중복 키 0건을 확인하고, 판독값 건수는 9-3의 **자신의 실행 출력**과 비교합니다. 중복이 있으면 예약을 켜지 말고 겹친 실행 여부부터 확인합니다.

![KQL 저장 건수와 중복 키 0건](../../assets/fabric-iq/49-fdc-stored-counts.png)

### 10-3. 시간 범위 확인

```kusto
fdc_sensor_reading
| summarize rows = count(), first_ts = min(reading_ts), last_ts = max(reading_ts) by run_status
```

아래는 과거 실행의 UTC 시각입니다. 최근 24시간만 조회하면 과거 생산 구간의 경보를 놓칠 수 있으므로 자신의 전체 범위를 먼저 확인합니다.

| run_status | 과거 rows | 과거 first_ts (UTC) | 과거 last_ts (UTC) |
| --- | ---: | --- | --- |
| Run | 93,210 | 2026-06-19 07:13:30 | 2026-06-21 23:59:30 |
| Idle | 413,182 | 2026-06-19 07:15:00 | 2026-09-17 15:20:00 |

![FDC 가동 유휴별 시간 범위](../../assets/fabric-iq/50-fdc-time-range.png)

### 10-4. 샘플 확인

```kusto
fdc_sensor_reading
| project reading_ts, eqp_id, sensor_code, value, unit, status, run_status
| take 10
```

같은 설비에도 여러 센서·단위가 존재합니다. `value`만 비교하지 말고 `sensor_code`, `unit`, 시각과 상태를 함께 확인합니다. `take 10`은 정렬하지 않은 샘플이며 전체 건수 확인을 대신하지 않습니다.

![센서 코드 단위 상태를 포함한 실제 FDC 샘플](../../assets/fabric-iq/51-fdc-reading-sample.png)

검증 후 02번 소스의 `MES_KEY_INPUT`을 빈 문자열로 복원하고 저장·재열기로 키 제거를 확인합니다. **Stop session** 후 **Session stopped successfully**를 확인합니다. 과거에도 세션 종료를 확인했지만 현재 세션의 종료를 보장하지는 않습니다.

<a id="step-11"></a>

## 11. 15분 예약 실행 설정 — 키 공급 전에는 활성화하지 않기

> **현재 미완료·미활성화:** 과거 실행은 예약 양식까지 확인했으나 저장하지 않고 취소했습니다. 현재 02번 코드는 소스의 `MES_KEY_INPUT`을 직접 사용하며 안전한 비대화형 키 공급이 준비되지 않았습니다. **이번에도 Save하지 말고 Cancel합니다.** 키를 비운 상태로 예약을 켜거나 일반 예약 파라미터에 실제 키를 남기지 않습니다. 아래 저장·증분 확인 절차는 안전한 키 공급을 별도로 준비·검증한 환경에서만 수행할 조건부 안내입니다.

### 11-1. Schedule 열기

02번 노트북에서 **Run > Schedule**을 선택합니다. 최초 적재가 완료됐고 10-2의 중복 키가 0건인지 먼저 확인합니다. 아직 적재하지 않았다면 아래 화면을 참고만 하고 예약을 만들지 않습니다.

![FDC Run 탭의 Schedule](../../assets/fabric-iq/52-fdc-schedule-button.png)

**Add schedule**을 선택해 양식을 확인합니다. 기존 예약이 있다면 중복 생성하지 않습니다.

![예약 목록의 Add schedule](../../assets/fabric-iq/53-fdc-add-schedule.png)

### 11-2. 간격·종료 시각 확인

| 설정 | 과거 양식 확인값 — 그대로 복사하지 않음 |
| --- | --- |
| Repeat | By the minute |
| Interval | 15 minutes |
| Start date and time | 2026-09-18 00:45 |
| End date and time | 2026-09-18 01:45 |
| Time zone | (UTC+09:00) Osaka, Sapporo, Tokyo |

조건이 준비되어 실제 예약을 구성할 때는 시작 시각을 현재 이후로, 종료 시각을 실습 종료 시간으로 지정합니다. 날짜를 그대로 복사하지 않습니다. 아래는 **저장 전 양식**이며 예약이 활성화된 화면이 아닙니다. 키 공급 미구성인 이번 재실행에서는 **Cancel**을 선택합니다.

![15분 예약 양식 확인 후 미저장](../../assets/fabric-iq/54-fdc-schedule-settings-unsaved.png)

안전한 키 공급이 준비·검증된 환경에서만 **Save** 후 예약의 간격·상태·종료 시각을 확인할 수 있습니다. **Run > View recent runs**의 예약 실행 성공과 아래 저장값의 증가를 함께 확인해야 합니다. 실행 시간이 간격보다 길면 예약을 끄고 주기를 조정합니다.

```kusto
fdc_sensor_reading
| summarize rows = count(), latest_reading = max(reading_ts)
```

실제 예약 실행 전후 값을 비교하고 10-2의 스펙 42행·중복 키 0건을 다시 검사합니다. 과거 최초 적재 기준은 **506,392행 / 2026-09-17 15:20:00 UTC**였으며 예약 증분 결과는 없습니다. 키 공급이 없는 현재는 이 검증을 완료로 표시하지 않고, 수동 적재 검증을 마쳤다면 12단계로 진행합니다.

<a id="step-12"></a>

## 12. 온톨로지 노트북 준비 및 실행

### 12-1. 임포트와 기본 연결

01·02번 데이터 검증을 마친 뒤 워크스페이스의 **Import > Notebook > From this computer > Upload**에서 [03_manufacturing_ontology.ipynb](helper-new/03_manufacturing_ontology.ipynb)를 선택합니다.

![03번 온톨로지 노트북 Upload](../../assets/fabric-iq/28-upload-factory-notebook.png)

목록의 **03_manufacturing_ontology** Notebook을 엽니다.

![임포트된 온톨로지 Notebook](../../assets/fabric-iq/61-ontology-imported.png)

**Add data items > From OneLake catalog**에서 본인의 `factory_lakehouse`를 선택하고 **Add**를 누릅니다. 6-2와 같이 **Set as default lakehouse**를 확인합니다. 이미 기본 대상이면 해당 메뉴가 비활성화됩니다.

![온톨로지에 동일 Factory Lakehouse 연결](../../assets/fabric-iq/62-ontology-attach-lakehouse.png)

### 12-2. 입력과 실행

패키지 설치 셀 다음의 설정 셀에서 두 값을 확인합니다. 과거에는 셀 4였으며, 현재는 [현재 실행 도우미](helper-new/README.md#실행-순서)의 설정을 따릅니다.

```python
KQL_DATABASE_NAME = "fdc_eventhouse"
ONTOLOGY_NAME = "Factory_Ontology"
```

Lakehouse ID와 작업 영역 ID는 기본 연결에서, KQL Database ID는 현재 작업 영역의 정확한 DB 이름에서 찾습니다. 테이블 위치 `mes`·`qms`는 01번 적재 결과와 같아야 합니다.

![온톨로지 입력값과 Run all](../../assets/fabric-iq/63-ontology-settings.png)

**Run all**을 선택합니다. 패키지 설치·인증·원본 검사·정의 게시·Graph 새로 고침을 순서대로 실행합니다. 런타임 재시작 안내가 나오면 재시작 후 설정 셀부터 계속합니다. 원본 검사 실패 시 안전장치를 끄거나 원본을 임의로 변경하지 않습니다. 동명 온톨로지 정의가 달라 중단되면 실제 ID·정의를 확인하며 무조건 삭제하지 않습니다.

과거 실행에서는 MES·QMS 원본 읽기와 온톨로지 생성까지 확인했습니다. 패키지 설치 셀에 기존 PyJWT 버전 충돌 경고가 출력됐지만 후속 인증·생성은 진행됐습니다. 이 경고를 모든 환경에서 무시해도 된다는 뜻은 아닙니다.

![온톨로지 원본 테이블 읽기 결과](../../assets/fabric-iq/64-ontology-preflight.png)

| 항목 | 과거 생성 결과 — 이번 연결 대상으로 사용하지 않음 |
| --- | --- |
| Ontology ID | `f7e203de-0296-457f-8ffc-27537a1641e5` |
| Graph ID | `60183a85-3052-44bf-8efa-6b9468af4d82` |
| 모델 | 노드 유형 11개·관계 유형 18개 |

과거 실행 도중 용량이 Paused 상태가 되어 사용자가 재개했습니다. 이후 Graph 편집 화면에는 로드 실패 안내가 남았지만 새 Queryset에서 다음 절의 일부 조회는 성공했습니다. **Graph 완료 출력·18개 관계 전체 대조까지 확인한 상태는 아닙니다.** 자신의 용량 상태·현재 오류를 확인하며 실패 안내만으로 데이터가 없거나 관계가 지원되지 않는다고 단정하지 않습니다.

<a id="step-13"></a>

## 13. Graph에서 GQL 조회

### 13-1. 생성된 Graph 열기

워크스페이스 목록에서 **이번 노트북이 생성한 Graph model** 항목을 엽니다. 과거 이름은 `Factory_Ontology_graph_f7e203de0296457f8ffc27537a1641e5`였으며 이번 이름·ID는 자신의 실행 출력에서 확인합니다. 기존 실습의 비슷한 이름과 혼동하지 않습니다.

왼쪽 **Nodes (11)**, **Edges (18)**에서 모델 구성을 확인합니다. `Data load is in progress`는 완료가 아닙니다. 다음 캡처는 과거 로드 중 상태를 기록한 것입니다.

![온톨로지 Graph의 노드 관계 목록과 로드 중 상태](../../assets/fabric-iq/67-graph-model-loading.png)

로드 실패 안내가 남아 있으면 실제 오류·용량 상태를 확인하고 **Retry**로 최신 상태를 확인할 수 있습니다. 과거에는 Retry 후에도 안내가 남았으므로 아래 실제 Queryset 결과와 구분하여 기록했습니다. 이번 실행에서도 로드가 실패하면 원본이나 모델을 임의로 바꾸지 않습니다.

![Graph 로드 실패 안내와 Retry](../../assets/fabric-iq/68-graph-retry-load.png)

### 13-2. 새 Queryset과 Code editor

Graph 상단 **Query > Create queryset**을 선택합니다.

![Graph Query 메뉴](../../assets/fabric-iq/69-graph-query.png)

이름에 `factory_graph_checks`를 입력하고 실습 워크스페이스 위치를 확인한 뒤 **Create**를 선택합니다.

![Graph queryset 생성](../../assets/fabric-iq/70-create-graph-queryset.png)

새 Queryset 상단의 **Query builder** 드롭다운을 열고 **Code editor**로 전환합니다. 아래 GQL을 한 블록씩 입력하고 재생 아이콘 **Run query**를 선택합니다. 쿼리를 바꿀 때는 편집기 전체를 선택하고 기존 내용을 지운 뒤 입력합니다.

### 13-3. 실제 관계 건수 확인

```gql
MATCH (ncr:Nonconformance)-[:NcrHasDisposition]->(decision:Disposition)
RETURN count(*) AS edge_count
```

과거 결과는 **95**였습니다. 단순히 두 테이블의 ID를 나란히 표시한 것이 아니라 등록된 `NcrHasDisposition` 관계를 조회한 결과입니다. 이번에는 현재 원본의 관계별 기대 건수와 비교합니다.

![NcrHasDisposition 실제 GQL 관계 95건](../../assets/fabric-iq/71-gql-ncr-disposition-count.png)

```gql
MATCH (equipment:Equipment)-[:EquipmentHasRuns]->(run:ProcessRun)
RETURN count(*) AS edge_count
```

과거 결과는 **84**였습니다. 당시 전체 공정 91행에는 설비가 없는 공정도 있었으므로 전체 공정 수와 관계 건수가 같다고 가정하지 않습니다.

![EquipmentHasRuns 실제 GQL 관계 84건](../../assets/fabric-iq/72-gql-equipment-runs-count.png)

### 13-4. 업무 속성 샘플 확인

```gql
MATCH (ncr:Nonconformance)-[:NcrHasDisposition]->(decision:Disposition)
RETURN ncr.Ncr_ncr_id AS ncr_id,
       decision.Disp_disposition_id AS disposition_id,
       decision.Disp_approval_status AS approval_status
ORDER BY ncr_id
LIMIT 5
```

과거에는 `NCR-2026-0001`~`0005`, 연결된 `DSP-2026-0001`~`0005`와 승인 상태를 확인했습니다. 실제 속성명은 모델의 접두사와 축약 규칙을 따르므로 원본 컬럼 이름만으로 임의 작성하지 않습니다. 현재 게시된 스키마와 비교하고 **Save**로 Queryset을 저장합니다.

![부적합 ID 처리 ID 승인 상태의 실제 GQL 샘플](../../assets/fabric-iq/73-gql-business-sample.png)

과거에 확인한 관계는 위 두 종류입니다. **18개 관계 전체 검증은 03번 마지막 셀에서 출력하는 관계별 기대 건수와 새 Queryset의 실제 결과를 각각 대조**해야 합니다. Graph 로드 완료, 샘플 조회, 전체 관계 검증을 구분하며 샘플 성공으로 전체 검증을 대신하지 않습니다.

<a id="step-14"></a>

## 14. factory_dataagent 생성 및 소스 연결

워크스페이스 목록의 **New item > Data agent**를 선택합니다.

![새 항목에서 Data agent 선택](../../assets/fabric-iq/75-select-data-agent.png)

이름에 `factory_dataagent`를 입력하고 **Create**를 선택합니다.

![factory_dataagent 생성](../../assets/fabric-iq/76-create-factory-dataagent.png)

상단 **Add data > Data source**를 선택합니다. Azure AI Search 소스를 추가하는 단계가 아닙니다.

![Data Agent Add data](../../assets/fabric-iq/77-agent-add-data.png)

OneLake catalog에서 **Factory_Ontology**, 유형 **Ontology**, 위치 **자신의 작업 영역**인 항목을 선택하고 **Add**를 누릅니다. 같은 이름이 여러 개라면 위치·항목 상세·이번 실행 ID를 확인합니다. Graph model·Lakehouse를 대신 선택하지 않습니다.

![이번 워크스페이스의 Factory_Ontology 선택](../../assets/fabric-iq/78-agent-select-ontology.png)

Explorer에서 **Factory_Ontology**를 펼쳐 엔터티 11개를 확인합니다. 과거 최초 연결에서는 `No tables selected yet` 안내가 잠시 나타났습니다. 소스의 메뉴에서 **Refresh**하고 로딩이 끝난 뒤 해당 안내가 사라지는지 확인합니다. 소스가 표시된 것만으로 게시본에 연결됐다고 가정하지 않고 16절의 게시본도 확인합니다.

<a id="step-15"></a>

## 15. Data Agent 지침 반영

상단 **Agent instructions**를 선택하고 가운데 기본 예제 문장을 클릭해 편집합니다. 기존 예제를 모두 지운 뒤 [data-agent-instructions.txt](helper-new/data-agent-instructions.txt)의 **현재 전문**을 넣습니다. Markdown 미리보기 영역을 선택해 저장합니다.

![제공된 한국어 Data Agent 지침 입력](../../assets/fabric-iq/79-agent-instructions.png)

과거에는 앞뒤 공백을 제외한 **4,003자와 SHA-256**을 당시 로컬 파일과 비교했습니다. **현재 지침의 길이나 해시가 그 값과 같아야 한다는 뜻은 아닙니다.** 이번에는 현재 파일의 처음·끝과 전문이 누락 없이 반영됐는지 비교합니다. 지침은 한국어 답변·실제 관계와 조회 근거·센서별 단위·공정 시간 구간·합성 데이터의 한계를 포함합니다. 문서의 질문이나 진행자용 설명을 지침에 추가하지 않습니다. 로컬 파일만 확인해 원격 설정이 바뀌었다고 판단하지 않습니다.

<a id="step-16"></a>

## 16. 게시 후 비즈니스 질문 테스트

### 16-1. Publish

상단 **Publish**를 선택합니다. 화면이 좁으면 **More items > Publish**에 있습니다. **Draft / Published** 전환 메뉴 자체는 게시 명령이 아닙니다.

![More items의 Publish](../../assets/fabric-iq/80-agent-publish-menu.png)

게시 확인창에서 이름과 설명을 확인합니다. 이 실습에서는 **Also publish to Microsoft 365 Copilot: Off**를 유지하고 **Publish**를 선택합니다. 별도 Microsoft 365 배포는 수행하지 않습니다.

![Fabric Data Agent 게시 확인](../../assets/fabric-iq/81-agent-publish-confirm.png)

게시가 끝나면 상단 **Draft > Published**를 선택합니다. Explorer의 **이번 온톨로지**와 반영된 한국어 지침을 확인합니다. 과거 에이전트 ID `96e07abb-588d-40d8-8563-45fb771557a5`를 연결 대상으로 복사하지 말고 현재 에이전트 이름·ID를 확인합니다.

![Published 버전과 온톨로지 및 지침 확인](../../assets/fabric-iq/82-agent-published.png)

### 16-2. 현재 비즈니스 시나리오의 질문 11개

[비즈니스 시나리오](helper-new/README-ontology-business-scenarios.md)의 **기본 질문 0~4 다섯 개 + 선택적 승인 후속 한 개 + 확장 A~E 다섯 개**를 아래에 그대로 제공합니다. 각 블록만 **Ask a question about your data**에 붙여 넣고 **Send**합니다. 각 질문은 새 대화에서 실행하되 질문 0의 후속 필터는 같은 대화에서 이어 사용할 수 있습니다. 설명·확인 기준은 질문에 함께 붙여 넣지 않습니다.

기본 질문으로 관계를 먼저 확인하고 목적에 맞는 확장 질문을 선택합니다. 질문이 준비되어 있다는 사실은 실행 성공을 뜻하지 않습니다. **확장 A~E는 실행 미검증**이며 실제 판정은 [시나리오별 확인 기준](helper-new/README-ontology-business-scenarios.md#기본-질문)과 [기간과 답변 판정](helper-new/README-ontology-business-scenarios.md#기간과-답변-판정)을 따릅니다.

#### 기본 질문 0. 부적합 처리·승인 현황

```text
처리 결정이 등록된 부적합을 찾아줘.
각 부적합의 ID·발생 출처·담당 부서와,
연결된 처리 결정의 종류·승인 상태를 함께 보여줘.
```

`NcrHasDisposition` 사용과 NCR·처리의 실제 참조를 확인합니다. 처리 등록을 승인 완료로 해석하지 않고 동일 `(ncr_id, disposition_id)` 쌍의 중복·누락을 대조합니다.

#### 선택적 후속 필터. 승인 검토가 남은 부적합

```text
처리 결정의 승인 상태가 대기 또는 반려인 부적합을 찾아줘.
부적합 ID·담당 부서·조치 기한과,
연결된 처리 결정의 ID·종류·승인 상태를 함께 보여줘.
```

처리의 `approval_status`가 대기·반려인지 확인합니다. NCR 자체 상태로 대신 필터링하지 않으며 조치 기한은 추가 원본 조회로 확인합니다.

#### 기본 질문 1. 검사·측정 담당 역할

```text
검사별 측정 결과와 검사 담당자·측정 기록자의 소속 및 자격을 함께 조회해서 같이 보여줘.
```

`InspectorDoesInspection`, `InspectionHasMeasures`, `InspectorRecordsMeasure`를 확인합니다. 검사 담당자와 측정 기록자를 역할별로 구분하며 같은 사람이어도 정상입니다.

#### 기본 질문 2. 검사의 생산 공정과 사용 설비

```text
공정검사와 재검사 결과를 생산 이력 및 사용 설비와 함께 결과만 표 형태로 보여줘
```

`RunHasInspection`, `EquipmentHasRuns`로 해당 생산 실행·설비를 확인합니다. 같은 로트·공정 코드만으로 실행을 대체하지 않습니다.

#### 기본 질문 3. 부적합의 발견 검사와 생산 공정·설비

```text
공정검사에서 발견된 부적합은 어떤 검사와 생산 공정·설비에서 확인됐고, 심각도와 추정 비용은 어땠어?
```

`InspectionHasNcr`, `RunHasInspection`, `EquipmentHasRuns`를 따라 발견 근거를 확인합니다. 생산 연결이 없는 기록을 임의로 연결하거나 `EquipmentHasNcr`로 경로를 대신하지 않습니다.

#### 기본 질문 4. 센서 경보 이력이 있는 설비의 생산 공정

```text
가동 중 센서 경보가 있었던 설비의 생산 이력을 보여줘.
```

동일 센서 관측 행의 `run_status = Run`, `status = Alarm`으로 설비를 선별하고 `EquipmentHasRuns`로 생산 이력을 확인합니다. **반환된 각 공정에서 경보가 났다는 뜻이 아니며**, 일부 표시를 전체 이력으로 표현하지 않습니다.

#### 확장 A. 불량 코드별 생산 온도와 함께 관측된 불량

```text
기본 공정검사에서 발견된 불량 유형별로 생산 당시 평균 챔버 온도를 비교하고, 각 유형에서 관측된 온도 범위에 다른 불량도 있었는지 보여줘.
```

같은 제품·공정·설비 유형·센서·단위 안에서 공정별 Run 관측 평균을 먼저 구합니다. 코드별 고유 공정 평균·공정 수·관측 수·비교 범위를 확인하며 `CHAMBER_TEMP`가 없는 설비를 주변 온도로 대신하지 않습니다.

#### 확장 B. 출하검사 합격 로트의 미완료 품질 조치

```text
출하검사에 합격한 로트 중 아직 마무리되지 않은 품질 조치가 있는 로트를 찾아줘. 어떤 문제가 어느 생산 공정·설비와 관련됐고, 담당 부서와 조치 기한·처리 및 승인 상태는 어떤지 함께 보여줘.
```

OQC 합격 후보의 다른 검사·품질 조치도 확인하고 직접 연결·검사 경유 NCR을 `ncr_id`로 중복 제거합니다. NCR 상태와 처리 승인 상태를 구분하며 최종 출하 승인·홀드를 이 답변만으로 확정하지 않습니다.

#### 확장 C. 재작업 실패 비용과 반복 불량

```text
재작업에 실패해 폐기된 사례의 비용은 어느 생산 공정·설비에 집중돼 있어? 처리 승인 상태와 반복된 불량 유형, 기록된 원인·즉시조치도 함께 보여줘.
```

`rework_result`·처리 종류를 확인하고 `scrap_cost_krw`는 고유 `disposition_id`마다 한 번만 합산합니다. NCR 추정 비용과 합치지 않으며 승인 상태·귀속 불명·비용 누락을 분리합니다.

#### 확장 D. 품질과 센서 경보를 함께 보는 설비 점검

```text
같은 제품을 같은 공정에서 생산한 설비들의 공정검사 불합격률과 가동 중 센서별 경보 비율을 비교해줘. 관련 불량 유형을 근거로 점검이 필요한 설비를 최대 3개 추천해줘.
```

기본 IPQC 고유 불합격 검사 수 / 고유 검사 수를 확인하고 IPQC-RT는 분리합니다. 센서 경보 비율은 해당 생산 구간의 Run·Alarm 행수 / Run 관측 행수로서 지속시간 비율·수율이 아닙니다. 분자·분모를 표시하며 조회 실패를 0%로 채우거나 후보를 억지로 3개 만들지 않습니다.

#### 확장 E. 측정 문제로 기록된 불합격의 판정 근거

```text
측정 문제로 공정검사에서 불합격 처리된 사례의 판정 근거를 확인해줘. 재검사 결과와 측정값·적용 규격, 담당자의 자격을 대조하고 추가로 확인할 내용을 정리해줘.
```

연결된 NCR의 `root_cause_category = 측정`인 기본 IPQC 불합격을 확인합니다. 같은 ProcessRun의 IPQC-RT가 기본 검사와 직접 후속 관계를 가진다고 가정하지 않습니다. 규격은 `spec_id`로 대조하고 담당자 역할·자료 부족을 구분하며 실제 계측 오류나 과실을 단정하지 않습니다.

확장 A·D의 공정별 센서는 동일 `eqp_id`, `in_time <= reading_ts < out_time`, `run_status = Run` 조건으로 원본 Eventhouse와 대조합니다. 시계열 조회·집계가 실패하면 정적 관계 성공만으로 전체 질문을 통과 처리하지 않습니다. 전체 기록을 기본으로 하며 최근 기간을 추가했다면 실제 기간·시간대와 자료 없음도 그대로 기록합니다.

### 16-3. 과거 질문 0의 실행 근거와 답변 대조

아래 화면은 **2026-09-17 게시본의 질문 0 실패 사례**입니다. 질문 11개의 테스트를 이 사례 하나로 대체하지 않으며, 별도로 제공된 사용자 답변 확인 기록과 합쳐 성공으로 처리하지 않습니다.

당시 게시본은 **66초** 후 응답을 반환했습니다. 현재 응답 시간 보장이 아닙니다. **Expand response > Data**에서 목록을 크게 볼 수 있습니다. 다음은 당시 답변의 일부이며 성공 예시가 아니라 검증 대상입니다.

![게시본 질문 0의 실제 응답 목록](../../assets/fabric-iq/83-agent-scenario-response.png)

**Expand response > Steps completed**에서 분석 단계를 펼치고 **Execution and output**을 확인합니다. 당시 생성 질의는 `Nonconformance`에서 `NcrHasDisposition`으로 `Disposition`을 연결하여 요청한 다섯 필드를 조회했습니다.

![실제 GQL 관계 질의와 도구 반환 데이터](../../assets/fabric-iq/84-agent-query-evidence.png)

| 검증 항목 | 과거 질문 0 실행 결과 |
| --- | --- |
| 실제 관계 사용 | `NcrHasDisposition` 사용 확인 |
| 도구 반환 데이터 | 95행·고유 NCR 95개·누락 없음 |
| 반환된 처리 결정의 참조 | 반환 JSON의 `Disp_ncr_id`와 NCR ID가 95행 모두 일치 |
| 자연어 응답 목록 | 94줄·고유 NCR 92개 |
| 중복 | `NCR-2026-0032`, `NCR-2026-0033` 각각 2회 |
| 응답에 없는 ID | `NCR-2026-0003`, `NCR-2026-0051`, `NCR-2026-0062` |
| 응답에 표시한 다섯 필드 | 표시된 94줄 모두 도구 반환 필드와 일치 |
| 판정 | **도구 조회 성공, 최종 답변 목록 정확성 실패** |

당시 응답은 일부 발췌라고 밝혔지만 중복 제거 기준을 지키지 못했습니다. 도구 결과를 자연어 목록으로 옮기는 단계와 실제 관계 조회를 구분하여 판단합니다. 이 대조는 도구 반환값과 답변의 비교이며 모든 필드의 원본 Lakehouse 행별 재대조나 모든 비즈니스 시나리오 통과를 뜻하지 않습니다. 실패를 통과시키기 위해 데이터·지침·시나리오를 임의로 변경하지 않습니다.

이번 실행에서도 각 질문의 실제 이름·ID, 시각·시간대, 질문·필터, 생성 질의·도구 오류, 기대값·실제값을 비밀값 없이 기록합니다. **확인됨 / 조건 해당 없음 / 부분 확인 / 조회 실패**를 구분하고 아래 완료 기준으로 판정합니다.

## 산출물과 완료 기준

질문별로 **확인된 운영 사실 + 근거 ID·관계 + 기간·집계 기준 + 미확인 항목**을 남깁니다.

- 데이터 생성·저장 성공과 Graph 관계 조회 성공, Data Agent 답변의 정확성을 각각 확인합니다.
- 비용은 NCR의 추정 비용과 처리의 폐기 비용을 합산하지 않고 고유 ID 기준으로 집계합니다.
- 비율은 분자·분모를 함께 제시하고, 미관측·조회 실패를 0%로 채우지 않습니다.
- 결과가 일부만 반환되면 전체 목록·총계·순위를 확인했다고 표현하지 않습니다.
- 확인됨 / 조건 해당 없음 / 부분 확인 / 조회 실패를 구분합니다. 상관관계를 실제 원인으로 단정하지 않습니다.

## 해결 범위와 Foundry에서의 연결

이 랩은 생산·품질·설비 기록을 관계와 시간 기준으로 조사하는 문제를 다룹니다. 이메일의 요청·결정, 정비 작업 문서, 내부 매뉴얼이나 공개 공정 원리까지 함께 확인하는 실습은 아닙니다. 점검 추천은 검토 후보이며 설비 정지·출하 승인·폐기를 실행하지 않습니다.

[05 Foundry IQ](../05-foundry-iq/README.md)는 공정 지원 KB(MES·Web IQ·매뉴얼)와 품질 조사 KB(작업지시서·인수인계서·Fabric IQ·Work IQ)를 분리합니다. 품질 시나리오는 지정 NCR 한 건을 원본 소스에서 조회·대조하며, 이 랩의 확장 A~E 전체를 자동 실행하거나 앞 답변을 복사해 취합하는 방식이 아닙니다. [06 Hosted Agent](../06-hostedagent/README.md)는 두 KB를 활용하는 참고 데모이며 참가자 필수 배포 단계가 아닙니다.

## 검증 상태

- [업무 시나리오의 검증 기록](helper-new/README-ontology-business-scenarios.md#검증-상태)은 기본 질문 1~4의 사용자 확인과 질문 0의 제공 답변 확인을 기록합니다. 원본 데이터·실행 질의를 모두 대조했다는 뜻은 아닙니다.
- 별도로 기록된 2026-09-17 실행에서는 `NcrHasDisposition` 95건·`EquipmentHasRuns` 84건의 GQL 조회와 질문 0 최종 목록의 중복·누락 실패가 있었습니다. 질문 0의 사용자 제공 답변 확인과 이 실행을 같은 성공 기록으로 합치지 않습니다.
- 예약·증분 검증, Graph 완료 출력, 18개 관계 전체 대조는 미완료·미확인입니다. 저장소의 세 현재 노트북에는 실행 출력이 없으며, 기록된 당시 행수·시각은 현재 클라우드 상태나 재실행 기대값을 보장하지 않습니다. 이번 문서는 새 원격 실행 결과를 추가하지 않습니다.
- 과거 로컬 회귀 검사는 보관본과 생성값·요청·오류 동작을 비교했으며, 해당 테스트 스크립트는 현재 배포 자료에서 제외했습니다. [검증 범위](helper-new/README.md#코드-구조와-로컬-회귀-확인)를 참고하세요. Spark 적재·Eventhouse 증분·온톨로지 게시의 실제 환경 재검증과는 별개입니다.

## 비용 및 정리

- Spark, 저장소, 수집·조회, Graph·Data Agent는 Fabric 용량을 사용합니다. 자신의 용량·사용 조건을 먼저 확인합니다.
- 노트북 공유 전 입력한 키와 민감한 출력을 제거하고, 종료 후 자신의 Spark 세션·예약을 중지합니다.
- 세션 종료와 유료 용량 일시 중지는 별개입니다. 공유 용량을 다른 참가자가 사용 중이면 임의로 중지하지 않습니다.
- 삭제할 때는 자신이 만든 항목의 실제 ID와 사용 여부를 확인합니다. Data Agent 연결, 온톨로지·Graph, Eventhouse·KQL DB, Lakehouse의 의존성을 확인하고 실습 항목만 정리합니다. 전체 작업 영역이나 공용 리소스를 일괄 삭제하지 않습니다.
- **기존 `rg-microsoft-iq-series`는 이번 실습의 생성·이동·삭제 대상이 아닙니다.** 자신의 새 용량을 정리할 때도 연결된 다른 작업 영역·사용자를 먼저 확인합니다. 과거 스크린샷의 리소스 이름·ID를 정리 대상으로 복사하지 않습니다.

[전체 고객 시나리오](../00-getting-started/README.md) · [별도 실습: Web IQ](../03-web-iq/README.md) · [전체 실습 목록](../../README.md)
