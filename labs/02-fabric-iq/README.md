# Fabric IQ

Fabric F2 용량과 워크스페이스를 준비하고, 생산·품질·센서 데이터를 온톨로지로 연결하여 Data Agent에서 조회하는 한국어 핸즈온입니다. [helper-v2](helper-v2/README.md)의 세 노트북을 순서대로 사용합니다.

> 2026-09-17~18 실제 화면으로 작성한 v2 실습 가이드입니다. MES·QMS·FDC 적재와 저장값 검증, 온톨로지 생성, 일부 GQL 관계 조회, Data Agent 지침 반영·게시·질문 테스트를 진행했습니다. **예약 실행은 키 공급 미구성으로 미완료이며, 에이전트 답변 목록에는 중복·누락이 확인됐습니다.** Graph 새로 고침 완료 출력과 18개 관계 전체 검증도 미확인입니다. 아래에서 실행 결과와 한계를 구분합니다.

## 목표

- 하나의 `factory_lakehouse`에 MES·QMS 데이터를 적재하고 저장값을 확인합니다.
- `fdc_eventhouse`에 센서 시계열을 적재하고 예약 실행의 증분을 확인합니다.
- 정적 엔터티 11개·관계 18개와 Equipment 시계열 바인딩을 가진 온톨로지를 구성합니다.
- Graph에서 GQL을 실행하고, `factory_dataagent`에 지침을 반영한 뒤 업무 질문을 시험합니다.

## 사전 준비

- Azure 구독과 리소스 그룹·Microsoft Fabric 용량 생성 권한이 필요합니다.
- Fabric 조직 계정, 워크스페이스 생성·용량 할당 권한, 실습 작업 영역의 Contributor 이상 권한이 필요합니다. 온톨로지에 필요한 테넌트 Preview 사용 설정도 확인합니다.
- 유료 Fabric F2 용량을 새로 만듭니다. 생성 직전 본인의 구독·리전에 표시되는 가격을 확인합니다.
- 제공된 Mock MES에 접근할 수 있어야 하며, 실습용 인증키를 준비합니다. 실제 키는 문서·캡처·공유 파일에 남기지 않습니다.
- 세 노트북은 같은 작업 영역과 같은 MES 주소·이력을 사용합니다. 실행 중 MES 원본 이력을 재시드하지 않습니다.
- 화면은 영문 UI 기준입니다. 빨간 테두리는 선택하거나 확인할 위치이며, 회색 영역은 구독·계정 정보를 가린 부분입니다.

### 사용할 파일

| 순서 | 파일 | 주요 설정 |
| --- | --- | --- |
| 1 | [01_factory_lakehouse.ipynb](helper-v2/01_factory_lakehouse.ipynb) | 기본 Lakehouse 연결, `MES_KEY_INPUT`, `FACTORY_LAKEHOUSE_NAME` |
| 2 | [02_fdc_eventhouse.ipynb](helper-v2/02_fdc_eventhouse.ipynb) | `KUSTO_URI`, `KUSTO_DATABASE`, `MES_KEY_INPUT` |
| 3 | [03_manufacturing_ontology.ipynb](helper-v2/03_manufacturing_ontology.ipynb) | 기본 Lakehouse 연결, `KQL_DATABASE_NAME`, `ONTOLOGY_NAME` |
| 지침 | [data-agent-instructions.txt](helper-v2/data-agent-instructions.txt) | Data Agent에 전문 반영 |
| 질문 | [비즈니스 시나리오](helper-v2/README-ontology-business-scenarios.md) | 게시 후 새 대화에서 한 질문씩 실행 |

첫 번째·세 번째 노트북의 Lakehouse ID는 기본 연결에서 읽습니다. 두 번째의 `KUSTO_DATABASE`와 세 번째의 `KQL_DATABASE_NAME`은 동일한 **KQL Database 이름**을 사용하며, 부모 Eventhouse 이름으로 대신하지 않습니다.

### 리소스 이름

| 항목 | 이번 실행 이름 | 상태 |
| --- | --- | --- |
| Azure 리소스 그룹 | `rg-iq-fabric-v2-0917` | 생성 확인 |
| Fabric 용량 | `fabriciqv20917` | F2 / Central US 배포 완료 |
| Fabric 워크스페이스 | `IQ-Fabric-v2-0917` | 생성 및 신규 F2 할당 확인 |
| Lakehouse | `factory_lakehouse` | 스키마 활성화 생성 및 기본 연결 확인 |
| Eventhouse / KQL Database | `fdc_eventhouse` / `fdc_eventhouse` | 생성 및 Query URI 확인 |
| 온톨로지 | `Factory_Ontology` | 생성 및 GQL 일부 관계 조회 확인 |
| Data Agent | `factory_dataagent` | 게시본 질의 실행, 조회 성공·답변 목록 오류 확인 |

참가자는 Azure 리소스와 워크스페이스 이름이 기존 항목과 겹치지 않도록 정합니다. 이번 실행의 기존 리소스를 변경하거나 다른 참가자의 항목을 선택하지 않습니다.

## 1. 리소스 그룹 생성

### 1-1. Resource groups 열기

[Azure portal](https://portal.azure.com/)에 로그인하고 홈의 **Azure services > Resource groups**를 선택합니다. 홈에 보이지 않으면 상단 검색에서 `Resource groups`를 찾습니다.

![Azure services의 Resource groups 선택](../../assets/fabric-iq/01-azure-resource-groups.png)

목록 상단의 **Create**를 선택합니다.

![리소스 그룹 목록의 Create](../../assets/fabric-iq/02-resource-group-create.png)

### 1-2. 구독·이름·리전 입력

**Subscription**에서 사용할 구독을 확인합니다. **Resource group name**에 `rg-iq-fabric-v2-0917`, **Region**에 **(US) Central US**를 지정하고 **Review + create**를 선택합니다.

![새 리소스 그룹 이름과 리전 및 검토 버튼](../../assets/fabric-iq/03-resource-group-basics.png)

### 1-3. 검토 후 생성

검증이 끝나고 **Create**가 활성화되면 그룹 이름과 리전을 다시 확인한 뒤 **Create**를 선택합니다.

![리소스 그룹 검토와 Create](../../assets/fabric-iq/04-resource-group-review.png)

생성 알림 후 목록으로 돌아옵니다. **Refresh**를 누르고 필터에 그룹 이름을 입력합니다. 새 그룹이 **Central US**로 표시되는지 확인합니다. 이 단계는 그룹만 만든 것이며 Fabric 용량은 다음 단계에서 배포합니다.

![생성된 리소스 그룹과 Central US 확인](../../assets/fabric-iq/05-resource-group-created.png)

## 2. 생성된 그룹에 Fabric F2 배포

### 2-1. Microsoft Fabric 검색

Azure 상단 검색에 `Microsoft Fabric`을 입력하고 **Services > Microsoft Fabric**을 선택합니다. Marketplace 검색 결과와 구분합니다.

![Services의 Microsoft Fabric 검색 결과](../../assets/fabric-iq/06-search-fabric.png)

용량 목록 상단의 **Create**를 선택합니다.

![Microsoft Fabric 용량 목록의 Create](../../assets/fabric-iq/07-fabric-create.png)

### 2-2. 배포 대상과 F2 선택

| 입력 항목 | 설정 |
| --- | --- |
| Subscription | 1단계에서 사용한 구독 |
| Resource group | **기존 그룹** `rg-iq-fabric-v2-0917` 선택 |
| Capacity name | `fabriciqv20917` |
| Region | **(US) Central US** |
| Fabric capacity administrator | Fabric에서 사용할 본인 관리 계정 |

이번 확인에서 기본 **Size**는 **F64**였습니다. 그대로 생성하지 말고 **Change size**를 선택합니다.

![Fabric 기본 입력과 Change size 위치](../../assets/fabric-iq/08-fabric-change-size.png)

**F2 / 2 Capacity units** 행을 선택하고 **Select**를 누릅니다. 이번 화면의 월 예상 가격은 **$262.80**이며, 참가자는 실행 당시 표시되는 가격을 기준으로 확인합니다.

![F2 행과 예상 비용 및 Select](../../assets/fabric-iq/09-select-f2.png)

기본 화면에서 **Size: F2 / 2 Capacity units**, 그룹·용량 이름·리전을 확인하고 **Review + create**를 선택합니다.

![F2 적용 후 기본 설정 검토](../../assets/fabric-iq/10-fabric-basics-f2.png)

### 2-3. 검증 후 배포

**Validation succeeded**를 확인합니다. 검토 화면에서 **F2**, **Central US**, 새 그룹과 용량 이름, 표시 비용을 확인한 후 **Create**를 선택합니다. 이 버튼부터 유료 용량 배포가 시작됩니다.

![검증 성공과 F2 배포 Create](../../assets/fabric-iq/11-fabric-review-create.png)

배포 요청과 배포 완료는 다릅니다. **Your deployment is complete**를 확인한 뒤 다음 단계로 진행합니다. **Go to resource**로 생성한 용량의 개요를 열 수 있습니다.

![Fabric 배포 완료와 Go to resource](../../assets/fabric-iq/12-fabric-deployment-complete.png)

## 3. 워크스페이스 신규 생성

### 3-1. Workspaces 열기

[Microsoft Fabric](https://app.fabric.microsoft.com/)에 로그인합니다. Azure에서 용량 관리자로 지정한 계정 또는 해당 용량의 할당 권한이 있는 계정을 사용합니다. 왼쪽 **Workspaces**를 선택합니다.

![Fabric Workspaces 메뉴](../../assets/fabric-iq/13-fabric-workspaces.png)

패널 아래 **New workspace**를 선택합니다. 기존 작업 영역이나 My workspace에 실습 항목을 추가하지 않습니다.

![Workspaces 패널 New workspace](../../assets/fabric-iq/14-new-workspace.png)

### 3-2. 이름과 초기 유형 지정

**Name**에 `IQ-Fabric-v2-0917`을 입력하고 **This name is available**을 확인합니다. 이번 실습은 생성 후 용량 변경 과정을 따라 하기 위해 **Advanced > Workspace type > Power BI Pro**를 선택합니다. 생성 양식이 Fabric 용량을 자동 선택했다면 Pro로 바꿉니다. Pro로 만든 상태에서는 다음 절의 Fabric 할당을 마치기 전 Lakehouse를 만들지 않습니다.

![워크스페이스의 초기 Power BI Pro 선택](../../assets/fabric-iq/15-workspace-pro.png)

**Advanced**를 접고 이름을 확인한 뒤 **Apply**를 누릅니다.

![워크스페이스 이름과 Apply](../../assets/fabric-iq/16-workspace-create.png)

생성된 작업 영역의 이름과 **Showing 0 item**을 확인합니다. 화면 폭에 따라 상단 버튼이 아이콘으로만 표시될 수 있습니다. **Workspace settings**를 선택합니다.

![빈 워크스페이스 생성과 Workspace settings](../../assets/fabric-iq/17-workspace-created-settings.png)

## 4. Workspace type을 Fabric으로 변경

**Workspace settings > Workspace type**에서 **Current workspace type: Power BI Pro**를 확인하고 **Edit**를 선택합니다.

![현재 Pro 유형과 Workspace type Edit](../../assets/fabric-iq/18-workspace-type-edit.png)

**Fabric**을 선택합니다. **Details > Select a capacity**에서 2단계에 만든 **fabriciqv20917 - Central US**를 선택하고 **Select**를 누릅니다. 기존 용량이나 Fabric Trial로 대신하지 않습니다. **Semantic model storage format**은 기본값을 유지합니다.

![Fabric 유형과 신규 용량 선택](../../assets/fabric-iq/19-workspace-fabric-capacity.png)

**Your changes were successfully saved**와 다음 값을 확인합니다.

- Current workspace type: **Fabric**
- Details: **fabriciqv20917**
- SKU / Region: **F2 / Central US**

![저장된 Fabric F2 Central US 할당](../../assets/fabric-iq/20-workspace-f2-confirmed.png)

설정 창 오른쪽 위 **Close**를 눌러 작업 영역으로 돌아옵니다.

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

## 6. Factory 노트북 임포트·설정·실행

### 6-1. 워크스페이스에서 Import 열기

왼쪽의 **IQ-Fabric-v2-0917**을 선택합니다. 탐색 패널만 열리면 패널 안의 워크스페이스 이름을 한 번 더 선택해 항목 목록으로 이동합니다. 상단 **Import**를 누릅니다. Lakehouse의 Upload files는 데이터 파일용이므로 사용하지 않습니다.

![워크스페이스의 Notebook Import 시작](../../assets/fabric-iq/25-import-notebook.png)

**Notebook**을 선택합니다.

![Import Notebook 메뉴](../../assets/fabric-iq/26-import-notebook-menu.png)

**From this computer**를 선택합니다.

![노트북 From this computer](../../assets/fabric-iq/27-import-from-computer.png)

**Import status > Upload**를 누르고 [01_factory_lakehouse.ipynb](helper-v2/01_factory_lakehouse.ipynb)를 선택합니다. OS 파일 선택창에서 `helper-v2`의 파일인지 확인합니다.

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

카탈로그에서 **factory_lakehouse**, 위치 **IQ-Fabric-v2-0917**, 유형 **Lakehouse**인 행을 선택하고 **Add**를 누릅니다. 이름이 같아도 SQL analytics endpoint는 선택하지 않습니다. 유형 아이콘에 마우스를 올려 확인할 수 있습니다.

![작업 영역과 Lakehouse 유형을 확인하고 Add](../../assets/fabric-iq/32-attach-factory-lakehouse.png)

Explorer의 **OneLake > factory_lakehouse**를 오른쪽 클릭하고 **Set as default lakehouse**를 선택합니다. 연결만 하는 것과 기본 대상으로 지정하는 것은 구분합니다. 기본 Lakehouse를 바꾸라는 세션 종료 안내가 나오면 데이터 실행 전에 연결을 마칩니다.

![factory_lakehouse Set as default lakehouse](../../assets/fabric-iq/33-set-default-lakehouse.png)

### 6-3. 입력값과 실행

첫 코드 셀인 **셀 2**에서 `MES_KEY_INPUT`에 제공받은 실습용 키를 입력합니다. 이번 노트북은 이 변수에서 키를 읽으며 별도 숨김 입력창은 없습니다.

```python
MES_KEY_INPUT = "<YOUR_MES_KEY>"
FACTORY_LAKEHOUSE_NAME = "factory_lakehouse"
```

이 변수에 실제 키를 입력하면 원격 노트북 소스에 저장됩니다. 실습 완료 후 예제 값으로 되돌리고, 공유·내보내기 전에 소스와 출력을 확인합니다. 이 문서와 캡처에는 실제 키를 넣지 않습니다.

Lakehouse ID·작업 영역 ID는 기본 연결에서 자동으로 읽습니다. **`FACTORY_LAKEHOUSE_NAME`은 연결된 대상의 이름을 검증하는 값이므로 실제 이름과 대소문자까지 맞춥니다.** 이 실습에서는 원본의 `"Factory_Lakehouse"`를 `"factory_lakehouse"`로 변경합니다. 공통 MES 주소와 `ALLOW_CONTEXT_RESET = False`는 유지합니다.

이름을 바꾸지 않으면 `Expected this workspace's schema-enabled Factory_Lakehouse. No data was written.` 오류가 날 수 있습니다. 이름·기본 연결·스키마를 확인하고 설정 셀을 다시 실행합니다. 이번 실행은 이름 수정 후 아래 대상 확인을 통과했습니다.

![올바른 factory_lakehouse ID와 기본 연결 확인](../../assets/fabric-iq/35-factory-connection-verified.png)

**Run all**을 한 번 누릅니다. Spark 세션 준비 후 설정·MES 조회·QMS 생성·사전 검사·적재·저장값 검증이 순서대로 진행됩니다. 키가 없거나 대상이 잘못 연결되면 오류를 해결한 뒤 다시 실행하며 검증을 우회하지 않습니다. 대상 테이블 11개를 덮어쓰므로 실행을 겹치지 않습니다.

![기본 Lakehouse와 키를 가린 설정 셀 및 Run all](../../assets/fabric-iq/34-factory-settings-run.png)

이번 실행에서 **15 executions succeeded**와 마지막 셀의 **11 tables verified**를 확인했습니다. 테이블별 결과는 다음 절과 같습니다.

## 7. 테이블 생성 및 저장값 확인

### 7-1. 마지막 적재 셀 확인

노트북 마지막 셀의 실행이 끝날 때까지 기다립니다. **11개 테이블 모두 `VERIFIED`**와 **11 tables verified**가 출력됐는지 확인합니다. 중간의 `context rows written`만으로 전체 성공으로 판단하지 않습니다.

![MES QMS 테이블 11개의 저장값 검증 결과](../../assets/fabric-iq/36-factory-tables-verified.png)

아래는 이번 실행의 실제 결과입니다. 노트북은 생성한 행과 저장된 행의 건수 및 양방향 차집합을 비교했습니다. 다음 표는 다른 참가자의 MES 데이터에도 동일한 건수를 강제하는 기준이 아닙니다.

| 테이블 | 저장 검증 행 수 |
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

`mes.process_result`를 선택합니다. **Showing 91 rows**와 `id`, `lot_id`, `eqp_id`, `step_code`, `in_time`, `out_time`을 확인했습니다. 설비가 없는 METRO 이력의 `eqp_id = NULL`은 보존됩니다. 이번 샘플의 공정 시작일은 2026-06-19이며, 과거 실행의 날짜를 사용하지 않습니다.

![MES 공정이력 91행의 실제 미리보기](../../assets/fabric-iq/38-mes-process-preview.png)

`qms.inspection`을 선택합니다. **Showing 207 rows**와 검사 ID·검사 유형·로트·제품·공정·설비를 확인했습니다. 오른쪽의 긴 컬럼은 가로 스크롤해 확인합니다. 샘플 미리보기는 7-1의 전체 저장값 검증과 구분합니다.

![QMS 검사 207행의 실제 미리보기](../../assets/fabric-iq/39-qms-inspection-preview.png)

실행이 끝나면 원격 노트북의 `MES_KEY_INPUT`을 예제 값으로 되돌리고 **Saved**를 확인합니다. 이번에는 새로 고침 후에도 예제 값이 유지되는 것을 확인했습니다. 자신의 Spark 세션을 종료한 뒤 FDC 실습을 진행합니다. 현재 세션은 **Not connected** 상태입니다.

## 8. fdc_eventhouse 생성

워크스페이스 목록의 **New item > Store data > Eventhouse**를 선택합니다.

![Store data의 Eventhouse 선택](../../assets/fabric-iq/40-select-eventhouse.png)

**Eventhouse name**에 `fdc_eventhouse`를 입력하고 **Create**를 선택합니다.

![fdc_eventhouse 이름 입력 후 Create](../../assets/fabric-iq/41-create-fdc-eventhouse.png)

생성 후 Welcome 안내는 **Get started**, 이어지는 기능 안내는 **Close**로 닫습니다. 왼쪽 **KQL databases > fdc_eventhouse**를 선택합니다. 이번 생성에서는 같은 이름의 KQL Database가 함께 만들어졌습니다.

![생성된 Eventhouse와 KQL Database 선택](../../assets/fabric-iq/42-eventhouse-created.png)

오른쪽 **Database details**가 접혀 있으면 제목 옆 펼치기 아이콘을 누릅니다. **Overview > Query URI** 행의 **Copy URI**를 선택합니다. **MCP Server URI**나 **Ingestion URI**를 복사하지 않습니다. 적재 전에는 **Tables > No tables**, **Last ingestion: Data was not ingested** 상태입니다.

![Database details의 Query URI 복사 버튼](../../assets/fabric-iq/43-fdc-query-uri.png)

## 9. FDC 노트북 임포트 및 실행

### 9-1. 노트북 임포트

워크스페이스 목록으로 돌아와 6-1과 같이 **Import > Notebook > From this computer > Upload**를 선택합니다. 이번에는 [02_fdc_eventhouse.ipynb](helper-v2/02_fdc_eventhouse.ipynb)를 선택합니다.

![02번 FDC 노트북 Upload](../../assets/fabric-iq/44-upload-fdc-notebook.png)

**Imported successfully** 후 목록에서 **02_fdc_eventhouse**, 유형 **Notebook**을 확인하고 엽니다. Eventhouse·KQL Database 항목과 구분합니다.

![임포트된 02_fdc_eventhouse Notebook](../../assets/fabric-iq/45-fdc-notebook-imported.png)

### 9-2. 연결 변수 입력

첫 코드 셀인 셀 2에 다음 값을 설정합니다. 이 노트북은 KQL Database에 적재하므로 기본 Lakehouse를 연결하지 않습니다.

```python
KUSTO_URI = "<본인의 Query URI>"
KUSTO_DATABASE = "fdc_eventhouse"
MES_KEY_INPUT = "<YOUR_MES_KEY>"
```

- `KUSTO_URI`: 8단계에서 복사한 Query URI. `https://`부터 전체 주소를 입력합니다.
- `KUSTO_DATABASE`: 생성한 **KQL Database 이름**. 이번에는 `fdc_eventhouse`입니다.
- `MES_KEY_INPUT`: 01번과 같은 Mock MES의 실습용 키입니다.

현재 파일은 `MES_KEY_INPUT`을 `MesProbe`에 직접 전달합니다. helper-v2 README의 환경 변수·비밀번호 프롬프트 설명만 보고 자동으로 키가 공급된다고 가정하지 않습니다. 이 실행에서는 소스에 임시 입력하고, 완료 후 제거합니다. 캡처의 키 행은 가렸습니다.

### 9-3. 최초 실행

**Run all**을 한 번 선택하고 실행이 시작됐는지 확인합니다. MES 조회·센서 생성·기존 워터마크 확인·사전 검사·적재가 순서대로 진행됩니다. 첫 실행은 과거 공정 구간부터 채우는 백필이며, 완료하기 전 예약 실행을 켜지 않습니다.

![FDC 연결 변수와 키 가림 및 Run all](../../assets/fabric-iq/46-fdc-settings-run.png)

이번 최초 실행에서 **14 executions succeeded**, 센서 스펙 **42행**, 판독값 **506,392행** 적재를 확인했습니다. 판독값 수는 실행 시각에 따라 달라집니다. 실패했다고 곧바로 테이블을 삭제하거나 동시에 재실행하지 않습니다.

![FDC 센서 스펙과 판독값 적재 완료](../../assets/fabric-iq/47-fdc-ingestion-complete.png)

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

이번 실제 저장 결과는 **42 / 506,392 / 0 / 93,210 / 294**입니다. 스펙 42행과 중복 키 0건을 확인합니다. 판독값 건수는 9-3의 해당 실행 출력과 비교합니다. 중복이 있으면 예약을 켜지 말고 겹친 실행 여부부터 확인합니다.

![KQL 저장 건수와 중복 키 0건](../../assets/fabric-iq/49-fdc-stored-counts.png)

### 10-3. 시간 범위 확인

```kusto
fdc_sensor_reading
| summarize rows = count(), first_ts = min(reading_ts), last_ts = max(reading_ts) by run_status
```

이번 결과의 시각은 UTC입니다. 최근 24시간만 조회하면 과거 생산 구간의 경보를 놓칠 수 있으므로 전체 범위를 먼저 확인합니다.

| run_status | rows | first_ts | last_ts |
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

검증 후 02번 소스의 `MES_KEY_INPUT`을 빈 문자열로 복원합니다. 이번에는 **Stop session** 후 **Session stopped successfully**를 확인했습니다.

## 11. 15분 예약 실행 설정

> **현재 미완료:** 예약 양식까지 확인했으나 저장하지 않고 취소했습니다. 현재 02번 코드는 소스의 `MES_KEY_INPUT`을 직접 사용하고, 비대화형 실행에 키를 공급하는 구성이 없습니다. 키를 비운 상태로 예약을 켜거나 일반 예약 파라미터에 실제 키를 남기지 않습니다. 예약 실행·증분 검증은 안전한 키 공급 방식을 준비한 뒤 진행해야 합니다.

### 11-1. Schedule 열기

02번 노트북에서 **Run > Schedule**을 선택합니다. 최초 적재가 완료됐고 10-2의 중복 키가 0건인지 먼저 확인합니다.

![FDC Run 탭의 Schedule](../../assets/fabric-iq/52-fdc-schedule-button.png)

**Add schedule**을 선택합니다. 기존 예약이 있다면 중복 생성하지 않습니다.

![예약 목록의 Add schedule](../../assets/fabric-iq/53-fdc-add-schedule.png)

### 11-2. 간격·종료 시각 확인

| 설정 | 이번 양식 확인값 |
| --- | --- |
| Repeat | By the minute |
| Interval | 15 minutes |
| Start date and time | 2026-09-18 00:45 |
| End date and time | 2026-09-18 01:45 |
| Time zone | (UTC+09:00) Osaka, Sapporo, Tokyo |

참가자는 시작 시각을 현재 이후로, 종료 시각을 실습 종료 시간으로 지정합니다. 날짜를 그대로 복사하지 않습니다. 아래는 **저장 전 양식**이며 예약이 활성화된 화면이 아닙니다. 이번에는 키 공급 미구성으로 **Cancel**을 선택했습니다.

![15분 예약 양식 확인 후 미저장](../../assets/fabric-iq/54-fdc-schedule-settings-unsaved.png)

키 공급이 준비된 환경에서만 **Save** 후 예약의 간격·상태·종료 시각을 확인합니다. **Run > View recent runs**의 예약 실행 성공과 아래 저장값의 증가를 함께 확인해야 합니다. 실행 시간이 간격보다 길면 예약을 끄고 주기를 조정합니다.

```kusto
fdc_sensor_reading
| summarize rows = count(), latest_reading = max(reading_ts)
```

예약 실행 전후 값을 비교하고 10-2의 스펙 42행·중복 키 0건을 다시 검사합니다. 이번 최초 적재 기준은 **506,392행 / 2026-09-17 15:20:00 UTC**이며, 예약 증분 결과는 아직 없습니다.

## 12. 온톨로지 노트북 준비 및 실행

### 12-1. 임포트와 기본 연결

01·02번 데이터 검증을 마친 뒤 워크스페이스의 **Import > Notebook > From this computer > Upload**에서 [03_manufacturing_ontology.ipynb](helper-v2/03_manufacturing_ontology.ipynb)를 선택합니다.

![03번 온톨로지 노트북 Upload](../../assets/fabric-iq/60-upload-ontology-notebook.png)

목록의 **03_manufacturing_ontology** Notebook을 엽니다.

![임포트된 온톨로지 Notebook](../../assets/fabric-iq/61-ontology-imported.png)

**Add data items > From OneLake catalog**에서 본인의 `factory_lakehouse`를 선택하고 **Add**를 누릅니다. 6-2와 같이 **Set as default lakehouse**를 확인합니다. 이미 기본 대상이면 해당 메뉴가 비활성화됩니다.

![온톨로지에 동일 Factory Lakehouse 연결](../../assets/fabric-iq/62-ontology-attach-lakehouse.png)

### 12-2. 입력과 실행

패키지 설치 셀 다음의 셀 4에서 두 값을 확인합니다. 이번에는 최신 helper-v2의 기본값을 그대로 사용합니다.

```python
KQL_DATABASE_NAME = "fdc_eventhouse"
ONTOLOGY_NAME = "Factory_Ontology"
```

Lakehouse ID와 작업 영역 ID는 기본 연결에서, KQL Database ID는 현재 작업 영역의 정확한 DB 이름에서 찾습니다. 테이블 위치 `mes`·`qms`는 01번 적재 결과와 같아야 합니다.

![온톨로지 입력값과 Run all](../../assets/fabric-iq/63-ontology-settings.png)

**Run all**을 선택합니다. 패키지 설치·인증·원본 검사·정의 게시·Graph 새로 고침을 순서대로 실행합니다. 원본 검사 실패 시 안전장치를 끄거나 원본을 임의로 변경하지 않습니다.

이번에는 MES·QMS 원본 읽기와 온톨로지 생성까지 확인했습니다. 패키지 설치 셀에 기존 PyJWT 버전 충돌 경고가 출력됐지만 후속 인증·생성은 진행됐습니다. 이 경고를 모든 환경에서 무시해도 된다는 뜻은 아닙니다.

![온톨로지 원본 테이블 읽기 결과](../../assets/fabric-iq/64-ontology-preflight.png)

| 항목 | 이번 생성 결과 |
| --- | --- |
| Ontology ID | `f7e203de-0296-457f-8ffc-27537a1641e5` |
| Graph ID | `60183a85-3052-44bf-8efa-6b9468af4d82` |
| 모델 | 노드 유형 11개·관계 유형 18개 |

실행 도중 용량이 Paused 상태가 되어 사용자가 다시 재개했습니다. 이후 Graph 편집 화면에는 로드 실패 안내가 남았지만, 새 Queryset에서 13절의 관계 건수와 업무 속성 조회는 성공했습니다. **노트북의 Graph 완료 출력·18개 관계 전체 대조까지 확인한 상태는 아닙니다.** 실패 안내만으로 데이터가 없거나 관계가 지원되지 않는다고 단정하지 않습니다.

## 13. Graph에서 GQL 조회

### 13-1. 생성된 Graph 열기

워크스페이스 목록에서 이번 온톨로지의 **Graph model** 항목을 엽니다. 이번 이름은 `Factory_Ontology_graph_f7e203de0296457f8ffc27537a1641e5`입니다. 기존 실습의 비슷한 이름과 혼동하지 않습니다.

왼쪽 **Nodes (11)**, **Edges (18)**에서 모델 구성을 확인합니다. `Data load is in progress`는 완료가 아닙니다. 다음 캡처는 로드 중 상태를 기록한 것입니다.

![온톨로지 Graph의 노드 관계 목록과 로드 중 상태](../../assets/fabric-iq/67-graph-model-loading.png)

용량 재개 후 로드 실패 안내가 남아 있으면 **Retry**로 최신 상태를 확인할 수 있습니다. 이번에는 Retry 후에도 안내가 남았으므로, 아래 실제 Queryset 결과와 구분하여 기록합니다. 다른 실행에서 로드가 실패하면 오류를 확인하고 임의로 원본이나 모델을 바꾸지 않습니다.

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

이번 결과는 **95**입니다. 단순히 두 테이블의 ID를 나란히 표시한 것이 아니라 등록된 `NcrHasDisposition` 관계를 조회한 결과입니다.

![NcrHasDisposition 실제 GQL 관계 95건](../../assets/fabric-iq/71-gql-ncr-disposition-count.png)

```gql
MATCH (equipment:Equipment)-[:EquipmentHasRuns]->(run:ProcessRun)
RETURN count(*) AS edge_count
```

이번 결과는 **84**입니다. 전체 공정 91행에는 설비가 없는 공정도 있으므로 전체 공정 수와 같다고 가정하지 않습니다.

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

`NCR-2026-0001`~`0005`, 연결된 `DSP-2026-0001`~`0005`와 승인 상태를 확인했습니다. 실제 속성명은 모델의 접두사와 축약 규칙을 따르므로 원본 컬럼 이름만으로 임의 작성하지 않습니다. **Save**로 Queryset을 저장합니다.

![부적합 ID 처리 ID 승인 상태의 실제 GQL 샘플](../../assets/fabric-iq/73-gql-business-sample.png)

이 실습에서 확인한 관계는 위 두 종류입니다. 18개 관계 전체 검증은 03번 마지막 셀에서 출력하는 관계별 기대 건수와 새 Queryset의 실제 결과를 각각 대조해야 합니다. 샘플 성공으로 전체 검증을 대신하지 않습니다.

## 14. factory_dataagent 생성 및 소스 연결

워크스페이스 목록의 **New item > Data agent**를 선택합니다.

![새 항목에서 Data agent 선택](../../assets/fabric-iq/75-select-data-agent.png)

이름에 `factory_dataagent`를 입력하고 **Create**를 선택합니다.

![factory_dataagent 생성](../../assets/fabric-iq/76-create-factory-dataagent.png)

상단 **Add data > Data source**를 선택합니다. Azure AI Search 소스를 추가하는 단계가 아닙니다.

![Data Agent Add data](../../assets/fabric-iq/77-agent-add-data.png)

OneLake catalog에서 **Factory_Ontology**, 유형 **Ontology**, 위치 **IQ-Fabric-v2-0917**인 항목을 선택하고 **Add**를 누릅니다. 같은 이름이 여러 개라면 위치나 항목 상세를 확인합니다. Graph model·Lakehouse를 대신 선택하지 않습니다.

![이번 워크스페이스의 Factory_Ontology 선택](../../assets/fabric-iq/78-agent-select-ontology.png)

Explorer에서 **Factory_Ontology**를 펼쳐 엔터티 11개를 확인합니다. 최초에는 `No tables selected yet` 안내가 잠시 나타났습니다. 소스의 메뉴에서 **Refresh**하고 로딩이 끝난 뒤 해당 안내가 사라지는지 확인합니다. 소스가 표시된 것만으로 게시본에 연결됐다고 가정하지 않고 16절의 게시본도 확인합니다.

## 15. Data Agent 지침 반영

상단 **Agent instructions**를 선택하고 가운데 기본 예제 문장을 클릭해 편집합니다. 기존 예제를 모두 지운 뒤 [data-agent-instructions.txt](helper-v2/data-agent-instructions.txt)의 **전문**을 넣습니다. Markdown 미리보기 영역을 선택해 저장합니다.

![제공된 한국어 Data Agent 지침 입력](../../assets/fabric-iq/79-agent-instructions.png)

이번에는 입력한 지침의 앞뒤 공백을 제외한 **4,003자와 SHA-256**을 로컬 파일과 비교해 일치함을 확인했습니다. 지침은 한국어 답변·실제 관계와 조회 근거·센서별 단위·공정 시간 구간·합성 데이터의 한계를 포함합니다. 문서의 질문이나 진행자용 설명을 지침에 추가하지 않습니다.

## 16. 게시 후 비즈니스 질문 테스트

### 16-1. Publish

상단 **Publish**를 선택합니다. 화면이 좁으면 **More items > Publish**에 있습니다. **Draft / Published** 전환 메뉴 자체는 게시 명령이 아닙니다.

![More items의 Publish](../../assets/fabric-iq/80-agent-publish-menu.png)

게시 확인창에서 이름과 설명을 확인합니다. 이번 실습에서는 **Also publish to Microsoft 365 Copilot: Off**를 유지하고 **Publish**를 선택합니다. 별도 Microsoft 365 배포는 수행하지 않습니다.

![Fabric Data Agent 게시 확인](../../assets/fabric-iq/81-agent-publish-confirm.png)

게시가 끝나면 상단 **Draft > Published**를 선택합니다. Explorer의 이번 온톨로지와 반영된 한국어 지침을 확인합니다. 이번 에이전트 ID는 `96e07abb-588d-40d8-8563-45fb771557a5`입니다.

![Published 버전과 온톨로지 및 지침 확인](../../assets/fabric-iq/82-agent-published.png)

### 16-2. 질문 0 실행

[비즈니스 시나리오](helper-v2/README-ontology-business-scenarios.md)의 기본 질문 0을 새 대화에서 전달합니다. 입력란은 **Ask a question about your data**입니다.

```text
처리 결정이 등록된 부적합을 찾아줘.
각 부적합의 ID·발생 출처·담당 부서와,
연결된 처리 결정의 종류·승인 상태를 함께 보여줘.
```

**Send** 후 응답을 기다립니다. 게시 성공과 답변 정확성은 별도이며, 실제 조회에서 `NcrHasDisposition`을 사용했는지, ID·부서·처리·승인 상태가 원본과 맞는지 확인합니다. 결과가 일부만 반환됐다면 전체 95건이라고 표현하지 않습니다.

이번 게시본은 **66초** 후 응답을 반환했습니다. **Expand response > Data**에서 목록을 크게 볼 수 있습니다. 아래는 실제 답변의 일부이며, 성공 예시가 아니라 검증 대상입니다.

![게시본 질문 0의 실제 응답 목록](../../assets/fabric-iq/83-agent-scenario-response.png)

### 16-3. 실행 근거와 답변 대조

**Expand response > Steps completed**에서 분석 단계를 펼치고 **Execution and output**을 확인합니다. 이번 생성 질의는 `Nonconformance`에서 `NcrHasDisposition`으로 `Disposition`을 연결하여 요청한 다섯 필드를 조회했습니다.

![실제 GQL 관계 질의와 도구 반환 데이터](../../assets/fabric-iq/84-agent-query-evidence.png)

| 검증 항목 | 이번 결과 |
| --- | --- |
| 실제 관계 사용 | `NcrHasDisposition` 사용 확인 |
| 도구 반환 데이터 | 95행·고유 NCR 95개·누락 없음 |
| 반환된 처리 결정의 참조 | 반환 JSON의 `Disp_ncr_id`와 NCR ID가 95행 모두 일치 |
| 자연어 응답 목록 | 94줄·고유 NCR 92개 |
| 중복 | `NCR-2026-0032`, `NCR-2026-0033` 각각 2회 |
| 응답에 없는 ID | `NCR-2026-0003`, `NCR-2026-0051`, `NCR-2026-0062` |
| 응답에 표시한 다섯 필드 | 표시된 94줄 모두 도구 반환 필드와 일치 |
| 판정 | **도구 조회 성공, 최종 답변 목록 정확성 실패** |

응답은 일부 발췌라고 밝혔지만 중복 제거 기준을 지키지 못했습니다. 도구 결과의 95건을 자연어 목록으로 옮기는 단계와 실제 관계 조회를 구분하여 판단합니다. 이 대조는 도구 반환값과 답변의 비교이며, 모든 필드의 원본 Lakehouse 행별 재대조나 모든 비즈니스 시나리오 통과를 뜻하지 않습니다. 이번 테스트를 통과시키기 위해 데이터·지침·시나리오를 임의로 변경하지 않았습니다.

## 검증 상태

| 범위 | 상태 |
| --- | --- |
| 리소스 생성·F2 할당 | 확인 완료 |
| MES·QMS 11개 테이블 | 적재·전체 저장값 대조 및 UI 샘플 확인 완료 |
| FDC | 적재·건수·중복·시간 범위·샘플 확인 완료 |
| 15분 예약·증분 | 양식만 확인, 미저장·미활성화 |
| 온톨로지·Graph | 생성 완료, 두 관계와 업무 속성 GQL 확인. Graph 완료 출력·18개 관계 전체 대조 미확인 |
| Data Agent | 소스·지침·게시 확인. 질문 0 도구 조회 성공, 최종 목록 오류 확인 |

## 비용 및 정리

- 용량을 일시 중지하거나 삭제하기 전까지 비용이 발생할 수 있습니다. 실제 청구는 사용 시간·계약 조건·별도 저장 비용 등에 따라 달라집니다.
- 실습 종료 시 예약 실행을 끄고 자신의 Spark 세션을 종료합니다. 세션 종료와 Fabric 용량 일시 중지는 별도 작업입니다.
- 실습용 항목의 사용 여부를 확인한 뒤 이번에 만든 리소스만 정리합니다. 기존 용량·워크스페이스·원본 데이터는 삭제하지 않습니다.
- 노트북을 공유하거나 내보내기 전에 실제 키를 제거하고 셀 출력·캡처에도 비밀값이 없는지 확인합니다.
- 이번 작업의 01·02번 원격 소스는 키 제거 후 다시 열어 저장 상태를 확인했습니다. 02번 세션 종료 성공 및 이후 03번 Not connected 상태도 확인했습니다. **용량 일시 중지·삭제는 수행하지 않았으므로 사용자가 재개한 F2의 비용 정리는 별도로 필요합니다.**

[전체 실습 목록](../../README.md)