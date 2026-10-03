# 05. Foundry IQ: 여러 영역의 근거로 복합 업무 질문에 답하기

## 고객 상황과 이 랩을 하는 이유

[CJ전자 반도체 사업부](../00-getting-started/README.md)의 담당자는 공정 원리를 이해하는 데서 그치지 않고 현장 상태와 내부 기준을 함께 보고 싶습니다. 품질 이슈를 조사할 때도 운영 상태만으로는 어떤 조치가 기록됐고 부서가 무엇을 요청했는지 알 수 없습니다. 개별 지식원을 조회할 수 있어도 근거의 역할·시점이 연결되지 않으면 판단의 불확실성이 남습니다.

이 랩은 **원본 운영 데이터·문서·협업 기록·공개 자료를 질문에 맞게 조회·결합하는 통합 실습**입니다. 앞 노트북의 답변을 복사해 모으는 실습이 아니며, 모든 개별 시나리오를 하나의 출하 미션에 종속시키지 않습니다.

## 이번 랩의 업무 질문

| 통합 시나리오 | 고객의 질문 | 필요한 근거 | 남길 산출물 |
| --- | --- | --- | --- |
| A. 공정 이해·현장 조회 | LOT0012 상태와 현재 공정 이슈를 확인하고, 이슈가 있으면 직전 공정 설비·내부 문서·공개 사례에서 무엇을 확인할 수 있는가? | MES + 내부 매뉴얼 + Web IQ | 확인 사실·원인 가설·공개 사례·미확인을 구분한 조사 요약 |
| B. 품질 이슈·후속 조치 | 지정 NCR의 상태와 관련 조치 이력·협업 요청을 대조하면 무엇이 확인되고 무엇이 남는가? | Fabric + 작업지시서 + 교대 인수인계서 + Work IQ | 운영 상태·문서 이력·요청·확인된 결정을 구분한 답변과 후속 질문 |

정확한 질문과 KS 구성은 아래 [공정 KB](#kb-1--공정-이해현장-조회)와 [품질 KB](#kb-2--품질-이슈-분석조치-판단)를 따릅니다. B의 기본 질문 대상은 LOT0004 / EQP-CMP01 / NCR-2026-0009입니다. 현재 노트북에는 기본 질문 외에 공정·품질 추가 질문도 있으며, [전체 호출 목록](#현재-노트북의-전체-호출-목록)에 작성 상태를 구분했습니다.

## 참가자가 수행할 일과 완료 기준

1. 자신의 KB와 연결할 원본·권한을 확인하고 각 소스에서 무엇을 얻어야 하는지 적습니다.
2. MSAL로 사용자 로그인한 뒤 공정 KB와 품질 KB에 각각 질문합니다.
3. 실제 호출 소스·검색 입력·오류·reference·답변 인용을 대조합니다.
4. 각 시나리오의 **확인 사실·출처·남은 불확실성·확인할 부서와 후속 질문**을 정리합니다.

**완료 기준:** HTTP 성공뿐 아니라 필요한 모든 출처의 근거가 질문을 뒷받침하는지 설명할 수 있어야 합니다. 근거가 충돌하거나 소스가 실패하면 부분 확인으로 남깁니다. 로그 분석은 고객 문제 해결을 검증하는 절차이지 실습의 업무 목적 자체가 아닙니다.

## 해결 범위와 한계

각 KB 안에서 여러 출처를 결합하지만 두 KB를 자동으로 합치는 에이전트는 없습니다. 품질 기본 질문은 지정 NCR 한 건의 후속 조사이고, 추가 질문은 메일에서 대상 로트를 찾아 품질·센서·작업·인계 이력을 대조합니다. 어느 질문도 전체 출하검사·관련 NCR 목록·최종 출하 승인을 자동 확인하지 않습니다. Fabric 확장 A~E 전체의 통합 검증이나 원인 확정·업무 조치 실행도 포함하지 않습니다.

## 참가자별 구축 원칙과 현재 제공 범위

워크숍의 목표는 **참가자 각자의 계정·리소스 그룹과 실습 리소스에 KB·KS를 구성하는 것**입니다. 자신의 모델·Search·문서 인덱스·매뉴얼 저장소·Fabric Data Agent·앱 등록과 권한을 준비해야 합니다. Fabric 작업 영역과 M365 접근 권한은 리소스 그룹 분리와 별도로 확인합니다.

Web IQ는 참가자가 서비스를 배포하거나 포털 키를 발급하지 않습니다. 진행자가 고객 실습에 사용이 허용된 키를 제공하면 참가자가 **자신의 Web IQ KS**에 설정합니다. 사용자 → KB는 각자의 MSAL 토큰, KS → Web IQ는 제공받은 키로 인증합니다. 키 하나를 공동 사용해도 KB·KS를 공유하는 구조는 아닙니다.

**현재 자료의 제한:** 호출 노트북은 생성된 v2 KB를 조회하며, 생성 도우미는 기존 KS·KB 정의와 연결 정보를 복사해 사용합니다. 아래 리소스 이름·실행 이력은 진행자 검증 환경의 기록이지 참가자의 리소스가 아닙니다. 빈 환경에서 모든 리소스와 연결을 처음부터 준비하는 참가자별 구축 절차는 아직 완결되지 않았습니다. 기존 설정을 그대로 실행하거나 02의 신규 Data Agent가 자동 연결된다고 가정하지 않습니다.

## 선행 실습

1. [Fabric IQ](../02-fabric-iq/README.md): 제조 운영 데이터와 Data Agent 조회
2. [Web IQ](../03-web-iq/README.md): 외부 웹 정보의 Playground·REST API·MCP 호출
3. [Work IQ](../04-work-iq/README.md): Microsoft 365 협업 정보 조회

## 현재 제공 자료

[v2 Knowledge Base 호출 노트북](kb_retrieve_test.ipynb)은 처음부터 공정·품질 KB 두 개만 사용합니다. **설치 → 설정 → MSAL 사용자 로그인 → 호출·로그 준비 → 공정 KB → 품질 KB** 순서입니다. 현재 호출 셀은 **공정 3개·품질 4개, 총 7개**이며, 모두 실행하면 KB retrieve도 7회 발생합니다. 기본 질문부터 실행하고, 추가 질문의 범위와 검증 상태는 아래 목록에서 먼저 확인하세요. 기존 `manufacturing-kb` 호출과 소스별 단독 테스트 셀은 없으며, Azure의 기존 리소스를 삭제하는 것은 아닙니다. 소스 호출 성공과 업무 근거 결합의 완료는 구분합니다.

## 실행 구성: 업무 목적별 v2 KB 두 개

**목표:** 공정 이해와 품질 조사를 서로 다른 KB로 실행하고, 실제 호출된 KS와 인용 근거를 확인합니다.

진행자 검증 환경에서는 기존 `manufacturing-kb`와 기존 KS 6개를 유지한 채, `ai-search-srch-vljt`에
**신규 KS 7개와 KB 2개**를 생성했습니다. 신규 KS·KB 이름은 모두 `-v2`로 끝납니다.
기존 `ks-fabriciq-factoryagent-v2`도 변경하지 않았습니다.

| KB | 신규 KS | 실제 유형·역할 |
| --- | --- | --- |
| `process-assistance-kb-v2` | `ks-process-mes-v2` | `mcpServer`: MES 공정·로트·제품·설비 조회 |
| 위와 같음 | `ks-process-webiq-v2` | `mcpServer`: **Microsoft Web IQ** 공개 기술 자료 |
| 위와 같음 | `ks-quality-manuals-v2` | `azureBlob`: 장비 운전 기준·점검 절차 |
| `quality-investigation-kb-v2` | `ks-quality-handovers-v2` | `searchIndex`: 교대 인수인계서 |
| 위와 같음 | `ks-quality-workorders-v2` | `searchIndex`: 정비 작업지시서 |
| 위와 같음 | `ks-quality-fabric-v2` | `fabricDataAgent`: 운영 수치·품질·NCR |
| 위와 같음 | `ks-quality-workiq-v2` | `workIQ`: 메일·Teams 등 협업 기록 |

기존 인덱스 2개, Blob의 `manuals` 컨테이너, Fabric Data Agent, Work IQ 앱 등록을
재사용합니다. 새 Blob KS는 매뉴얼을 별도 인덱스로 수집합니다. 서비스가 자동 생성하는
하위 리소스 이름은 `ks-quality-manuals-v2-index`, `-indexer`, `-datasource`, `-skillset`입니다.
이 하위 리소스의 서비스 지정 접미사는 KS·KB 이름 규칙과 다릅니다.

2026-10-01(KST)에 매뉴얼 KS의 연결을 품질 KB에서 공정 KB로 옮겨 **3개 / 4개**로
재배치했습니다. 재생성·재인덱싱 없이 KB 두 개의 소스 목록과 설명·조회·답변 지침만
변경했습니다. `ks-quality-manuals-v2`라는 기존 이름은 유지하지만 현재 소속은 **공정 KB**입니다.

### KB 1 — 공정 이해·현장 조회

> MES에서 LOT0012 로트 상태를 확인하고, 현재 진행 중인 공정에서 이슈가 있는지 확인해보자. 만약 이슈가 있다면, 바로 직전 공정의 설비를 확인해서 해당 설비를 내부 장비 문서를 통해서 어떤 이슈가 있을법한지 검토해 보고, 이 이슈 사항이 웹 상에서 다른 회사에서도 문제가 발생했는지 퍼블릭하게 확인해서 전체적인 요약본을 제공해

2026-10-03에 공정 기본 질문을 위 문장으로 변경했습니다. 사용자에게 상세 검색 절차나 안전 지침을 매번 붙여 넣도록 요구하지 않습니다. 실제 이력으로 직전 공정·설비를 연결하고, 확인 사실과 원인 가설을 구분하며, 공개 검색에서 내부 식별자·비공개 내용을 제외해야 합니다. [로컬 KB 정의](helper/code/knowledge_bases_v2.py)는 소스 역할·공개 검색 제한·근거 부족 표시를 지정하지만, 직전 공정 추적을 강제하는 별도 실행 로직은 아닙니다. 질문 변경만으로 원격 KB 지침이 갱신되거나 이력 연결이 검증되지는 않습니다.

이 질문은 조건부 조사입니다. 이슈가 확인되지 않아 후속 소스를 조회하지 않은 경우와 필요한 근거를 누락한 경우를 구분해 평가합니다. MES에 없는 QMS 검사 결과·FDC 센서 이상을 확인했다고 답해서는 안 됩니다. 기존 검증 로그는 이전 CMP 질문의 이력이며 새 LOT0012 질문의 성공을 증명하지 않습니다.

- 로컬 MES KS 생성 정의는 `get_lot`, `get_process_route`, `list_process_results`,
  `list_products`, `list_equipments`를 포함합니다. Hold 로트 추가 질문에는
  `list_lots`의 운영 KS 등록도 확인해야 합니다. 생성·수정·삭제 도구는 사용하지 않습니다.
  현재 등록 개수를 최대 한도로 해석하지 않으며, 도구 수 제한은 사용하는 API 버전과
  서비스의 실제 저장 결과로 확인합니다.
- Web IQ는 `https://api.microsoft.ai/v3/mcp`의 `web` 도구만 사용합니다.
  Bing Grounding 기반 `web` 유형 KS로 대체하지 않았습니다.
- 내부 장비 기준은 Blob 매뉴얼에서 확인합니다. 공개 웹의 일반적인 설명과 구분합니다.
- 외부의 일반적인 원인을 특정 로트에서 확인된 실제 원인으로 단정하지 않습니다.
- 외부 검색에는 공개 기술 용어만 사용합니다. **KB 지침은 보안 필터가 아닙니다.**
  공개 가능한 실습 질문만 입력하고, `mcpServerArguments.toolArguments`의 실제
  Web IQ 검색어를 확인합니다. 민감한 고객 데이터는 입력하지 않습니다.

**MES REST API는 별도 비교 호출로 유지합니다.** 확인한 `2026-08-01-preview` KS 계약에는
임의의 REST/OpenAPI를 직접 등록하는 유형이 없습니다. 별도 MCP 어댑터는 배포하지 않았습니다.
`GET /api/products`와 MCP `list_products`에서 같은 제품 데이터를 조회해 비교합니다.
실제 비교에서는 두 경로 모두 제품 4건을 반환했고, `product_code`로 정렬한 전체 행이 일치했습니다.

### KB 2 — 품질 이슈 분석·조치 판단

> LOT0004 / EQP-CMP01 / NCR-2026-0009의 후속 조치를 요약하세요.
> Fabric에서는 해당 NCR 한 건의 현재 상태를 확인하고, 작업지시서와 교대 인수인계서에서는
> 관련 조치 이력을, Work IQ의 IQ-DEMO-20260922 메일에서는 요청·결정·담당자를 확인하세요.
> 네 출처를 구분하고 없는 결정은 추측하지 마세요.

문서의 주장, 실제 운영 수치, 사람들의 요청·결정을 구분합니다. 같은 로트나 설비라는
이유만으로 서로 다른 시점의 사건을 합치지 않습니다. 기존 문서에는 워크숍용 합성 자료와
의미 검수 전이라는 주의가 있습니다. 검색 성공을 자료 간 의미 일치나 업무 판단의 정확성으로
간주하지 않습니다. Work IQ의 요청 메일도 승인·완료 기록으로 해석하지 않습니다.

장비 표준을 이해하는 질문은 먼저 공정 KB에, 실제 사건과 후속 조치 질문은 품질 KB에
보냅니다. 두 KB의 답변을 자동 합치는 에이전트는 추가하지 않았습니다.

### 현재 노트북의 전체 호출 목록

2026-10-03 로컬 소스 기준으로 `retrieve_v2_trace()` 호출은 다음 순서의 **7회**입니다. 이는 코드상 호출 수이지 실제 원격 성공 횟수가 아닙니다. 각 호출 뒤의 로그 셀은 추가 조회하지 않으며, 같은 KB의 다음 질문을 실행하면 `v2_process_result/trace` 또는 `v2_quality_result/trace`가 새 결과로 바뀝니다.

| 순서 | KB | 질문·상태 |
| --- | --- | --- |
| 1 | 공정 | 위 LOT0012 조건부 조사 기본 질문. 저장 답변·로그 없음 |
| 2 | 공정 | EQP-CVD01·EQP-IMPL01 매뉴얼 주의사항과 공개 해결 자료. 저장 답변·로그 없음 |
| 3 | 공정 | 현재 Hold 로트와 해당 공정의 작업 내용. 저장 답변·로그 없음 |
| 4 | 품질 | 위 LOT0004 / EQP-CMP01 / NCR-2026-0009 기본 질문. 이전 저장 출력 있음 |
| 5 | 품질 | 아래 메일에서 시작하는 품질 조사 추가 질문. 저장 출력에 과거 `SyntaxError`가 남아 있으며 현재 코드의 성공 결과가 아님 |
| 6 | 품질 | LOT0004의 품질·공정·설비·센서·문서·이메일/업무 컨텍스트 종합 조사. 저장 답변·로그 없음 |
| 7 | 품질 | 최근 품질 이슈 5건의 검사·설비 센서 근거와 원인 가설. 저장 답변·로그 없음 |

공정 추가 질문 1 — 장비 매뉴얼·공개 해결 자료:

> EQP-CVD01, EQP-IMPL01 장비 메뉴얼을 참고해서 주의할 내용이 있는지 살펴보자. 그리고 그 주의할 내용에 대해서 인터넷에서는 어떤 내용으로 해결할 수 있는지도 검색해서 인사이트를 제공해 줘

공정 추가 질문 2 — Hold 로트·공정 설명:

> MES에서 현재 상태가 Hold인 로트정보 리스트를 검색해서 어떤 공정에서 로트가 홀드 되었는지 확인하자. 그리고 해당 공정은 어떤 작업을 하는지도 웹 사이트에서 찾아서 설명해 줘.

두 질문은 사용자가 제공한 문장을 그대로 사용하며 아직 원격 실행 결과를 저장하지 않았습니다. Hold 질문은 운영 MES KS의 `list_lots` 등록과 실제 반환값을 먼저 확인합니다. 로트의 상태·공정은 MES 근거로, 공정의 일반적인 작업 내용과 해결 자료는 공개 출처로 구분하며 공개 설명만으로 내부 설비의 원인이나 조치 완료를 확정하지 않습니다.

품질 추가 질문 1 — 메일에서 시작하는 조사:

> 이메일에서 품질 불량에 대해서 요청이 온 로트가 있는지 확인해서 해당 로트의 품질 이력을 확인해서 어떤 불량이 발생했는지 확인하자. 그리고 그 불량이 발생한 장비에서 해당 시점에 발생한 장비 센서의 이력을 파악해서 무슨 문제가 발생했을지를 판단하면 좋을 것 같아. 장비에서 자체적으로 문제가 있었을수도 있지만, 실제로 그 당시 불량 기인이 작업자에서 발생했을 수 있으니 해당 작업지시서도 검토해보고 인수인계시에도 특이한 이력이 있었는지 함께 종합적으로 판단해 인사이트를 제공해.

이 질문은 특정 NCR·로트·메일 태그를 고정하지 않습니다. Work IQ에서 대상과 시점을 찾고, Fabric 품질·센서 이력과 내부 작업·인계 기록을 연결하는 확장 조사입니다. 장비·작업자 원인은 **검증할 가설**이며 작업자 책임을 추측하지 않습니다. 현재 소스의 구문 해석·모의 호출 성공과 실제 원본에서 필요한 기록을 찾는 것은 별개입니다.

품질 추가 질문 2 — LOT0004와 업무 컨텍스트:

> LOT0004 로트의 품질 이슈가 있었는지 확인해보자. 품질 이슈가 있었다면, 공정 및 사용 장비를 확인 해 해당 장비에서 발생한 센서 데이터에서 특이사항이 없었는지 확인해 보자. 마찬가지로 인수인계 교대서, 그리고 작업지시서, 그리고 내 이메일이나 업무 컨텍스트에서도 관련 내용이 없었는지 검색해서 요약해보자

품질 추가 질문 3 — 최근 품질 이슈 5건:

> 가장 최근에 발생한 5개의 품질 이슈를 확인해보자. 그리고 이 품질이슈의 검사결과, 그리고 해당 장비에서 발생했던 센서데이터를 모두 취합해서 원인이 있을법한 내용을 조합해보자.

새 두 질문은 사용자 원문 그대로이며 제품명·KS 이름·도구 호출 순서를 덧붙이지 않습니다. 아직 원격 실행 결과는 저장하지 않았습니다. 최근 5건의 기준 시각·정렬과 실제 반환 건수, 검사에 연결된 생산 실행·설비·센서 시간 구간을 대조해야 하며 가능한 원인을 확인된 원인으로 표현하지 않습니다.

## 과거 원격 검증 결과

아래 공정 검증 수치와 Web IQ 검색어는 **기본 질문 교체 전 CMP 질문**의 이력입니다. 현재 노트북의 LOT0012 질문·장비 매뉴얼 질문·Hold 로트 질문과 구분합니다. 품질 수치는 지정 NCR 기본 질문의 이력이며 메일 기반 추가 질문의 성공을 증명하지 않습니다. 이번 문서 점검에서는 원격 조회·로그인·용량 변경을 실행하지 않았습니다.

`2026-08-01-preview` REST로 실행했습니다.
[검증 기록](helper/code/v2_validation.json)은 상태·소요 시간·소스별 근거 수신 여부만 저장하며
토큰, API 키, 원본 메일·문서 본문은 포함하지 않습니다.

### 2026-10-01 재배치 검증: 공정 3개 / 품질 4개

2026-10-01(KST) 재배치 후 실제 호출 결과입니다. JSON의 `repartition.tests`에 기록했습니다.
기존 최상위 `tests`는 이전 2개 / 5개 구성의 이력입니다.

| 검증 대상 | HTTP | 소요 시간 | 근거 확인 |
| --- | --- | --- | --- |
| **공정 KB: MES + Blob 매뉴얼 + Web IQ** | **200** | **35.3초** | **세 KS 모두 확인**, reference 20건 |
| 품질 KB: 인수인계 + 작업지시 + Fabric + Work IQ | **206** | **132.8초** | 인수인계·작업지시·Work IQ 확인, **Fabric 내부 100초 타임아웃** |

공정 KB의 실제 Web IQ 검색어는 `chemical mechanical planarization process fundamentals`였으며,
내부 식별자나 매뉴얼 내용은 포함되지 않았습니다. 이 한 번의 확인이 모든 입력의 안전성을 보장하지는 않습니다.
재배치 직후에는 네 소스로 줄여도 전체 성공에 이르지 못했습니다. 이후 재검증 결과는 다음 절을 확인하세요.

### 2026-10-01 후속 재검증: Fabric 용량 재개 후

2026-10-01 09:47~09:52(KST)에 `fabriciqv20917` F2 용량을 재개했습니다.
Azure 관리 API와 Fabric API 모두 `Active`인 것을 확인한 뒤,
Fabric 단독 → 품질 KB 네 소스 조합 순서로 이전과 같은 질문을 실행했습니다.
아래 결과가 위 타임아웃 기록보다 최신이며, JSON의 `capacityResumeRetests`에 보관합니다.

| 검증 대상 | HTTP | 소요 시간 | 근거 확인 |
| --- | --- | --- | --- |
| Fabric KS 단독 | **200** | **159.5초** | Fabric 근거 1건, 오류 없음 |
| **품질 KB 네 소스 조합** | **200** | **69.2초** | **인수인계·작업지시·Fabric·Work IQ 모두 확인**, reference 32건, 오류 없음 |

각 호출 전후에 용량 `Active`를 확인했습니다. 네 소스 조합에서 Fabric 하위 호출은
약 32.3초에 완료됐습니다. 전체 요청 시간은 계획·조회·답변 생성을 포함하므로
Fabric 하위 호출 시간과 구분합니다. 두 테스트 사이에 KB·KS 설정은 바꾸지 않았으며,
전체 KS·KB 정의가 테스트 전후 동일함을 확인했습니다.

**당시 공정 3개·품질 4개 조합 모두 성공 이력을 남겼습니다.**
단, 재개 후 한 번의 조합 성공이 반복 실행의 안정성을 보장하거나 이전 타임아웃의 원인이
모두 용량 중지였음을 증명하지는 않습니다. 00:37(KST) 중지 이력은 이전 00:34경 테스트보다
뒤였습니다. 이번에는 용량을 재개한 뒤 Fabric 단독 조회를 먼저 실행했다는 조건도 다릅니다.
당시 테스트 종료 시 용량은 **Active로 유지해 과금이 계속되는 상태**였습니다. 이후 [06 데모 운영 안내](../06-hostedagent/README.md)에 중지 복원 이력이 있으므로 이 기록을 현재 Active 상태로 해석하지 마세요. 새 품질 호출 전 용량 상태를 확인하고 필요한 경우 진행자와 재개합니다.

재배치 전후 **KS 13개 전체와 기존 `manufacturing-kb`가 그대로**인지 확인했습니다.
v2 KB 두 개에서도 소스 목록·설명·조회 지침·답변 지침과 ETag 외 필드는 바뀌지 않았습니다.
매뉴얼 KS는 재생성하거나 재인덱싱하지 않았습니다.

### 재배치 전 기록: 공정 2개 / 품질 5개

아래는 2026-09-30~10-01(KST)의 **이전 구성** 결과입니다. 현재 3개 / 4개 결과와 구분합니다.

| 검증 대상 | HTTP | 소요 시간 | 결과 |
| --- | --- | --- | --- |
| MES KS 단독 | 200 | 17.0초 | MES 도구 활동과 연결된 근거 수신 |
| Web IQ KS 단독 | 200 | 19.4초 | 실제 `web` 호출, 공개 근거 3건 |
| **MES + Web IQ 조합** | **200** | **26.4초** | **두 KS의 활동·근거 확인** |
| Blob 매뉴얼 KS 단독 | 200 | 32.3초 | 근거 수신, 신규 인덱서 문서 9건 처리·실패 0건 |
| 인수인계 KS 단독 | 200 | 19.8초 | 근거 수신 |
| 작업지시 KS 단독 | 200 | 21.1초 | 근거 수신 |
| Fabric KS 단독 | 200 | 151.5초 | 품질 판정·NCR 근거 수신 |
| Work IQ KS 단독 | 200 | 63.2초 | 관련 요청 메일 근거 수신 |
| 품질 KB 다섯 소스 조합 | **206** | 155.5초 | Fabric 내부 100초 타임아웃, 나머지 네 KS 근거 수신 |
| NCR 한 건으로 좁힌 조합 재시도 | **206** | 136.0초 | Fabric 100초·Work IQ A2A 타임아웃, 문서 세 KS만 근거 수신 |

첫 조합 실패 후 질문을 좁혀 재시도했지만 전체 조합 성공을 확인하지 못했습니다.
단독 성공을 전체 조합 성공으로 표시하지 않습니다. Fabric·Work IQ 원본 설정이나
용량을 바꾸지 않았으며, 안정적인 다섯 소스 조합 시연에는 추가 진단이 필요합니다.
생성형 답변이 타임아웃을 “자료 없음”으로 설명할 수도 있으므로 **실제 `activity.error`가 우선**입니다.

기존 KS 6개와 KB 1개의 정의는 생성 전후 해시로 변경이 없음을 확인했습니다.
측정 시간은 해당 요청의 관찰값이며 서비스 지연 보장값이 아닙니다.

## 실행 준비

- Python 3.11 이상과 Jupyter/IPython 커널, `requests`, `msal`을 사용합니다. 현재 노트북 설치 셀은 `requests`, `msal`만 설치합니다. 위 MES REST/MCP 비교는 과거 별도 검증이며 현재 노트북에는 직접 비교 셀이 없습니다.
- 기존 `gpt-5.2` 모델 배포를 재사용합니다. 호출마다 모델·검색·Web IQ 사용량이 발생하고,
  신규 Blob 인덱싱은 임베딩·저장 공간을 사용합니다. Fabric capacity도 실행 중이어야 합니다.
- 생성에는 Search Service Contributor 등 KS·KB 관리 권한이 필요합니다.
  조회에는 Search Index Data Reader와 M365·Fabric 원본 접근 권한이 필요합니다.
- [v2 Foundry IQ 노트북](kb_retrieve_test.ipynb)의 설정·MSAL 사용자 로그인까지 실행해
  `SEARCH_ENDPOINT`, `search_token`, `workiq_token`을 준비합니다. 설정의 `PROCESS_KB_NAME`과
  `QUALITY_KB_NAME`으로 공정·품질 KB를 각각 지정하며, KS 이름은 3절의 `V2_SOURCES`에서 확인합니다.
  Work IQ assertion의 scope는 `api://<WORKIQ_APP_ID>/access_as_user`이며,
  직접 Work IQ API 호출용 `WorkIQAgent.Ask`와 다릅니다.
- 워크숍 로그인은 MSAL public client 방식입니다. 앱 등록의 `http://localhost` 리디렉션과
  필요한 위임 권한·동의가 먼저 준비되어야 하며, Azure CLI 로그인은 전제하지 않습니다.
- 로그인용 `WORKIQ_APP_ID` 앱에 **Azure Cognitive Search → Delegated permissions →
  user_impersonation**을 추가하고 필요한 동의를 완료합니다. 누락하면 Search 토큰 발급 단계에서
  `AADSTS650057`이 발생할 수 있습니다. 기존 Work IQ 권한을 유지하며, 사용자에게 부여하는
  Search Index Data Reader 역할과 앱의 API 권한 설정을 구분합니다.
- 위 과거 리소스 관리·검증 실행은 대상 구독을 명시한 기존 Azure CLI 사용자 세션을 사용했습니다.
  **v2 작업 중 MSAL 브라우저 로그인 자체는 다시 실행하지 않았습니다.**
- Web IQ는 승인 계정·키·할당량이 필요합니다. MES·Web IQ 키는 신규 MCP KS의
  `storedHeaders`에 저장했고 소스 조회 시 마스킹됩니다. 저장소에는 키를 넣지 않았습니다.
  이 Search 서비스의 조회 권한이 있는 사용자는 해당 저장된 연결을 사용할 수 있습니다.

## v2 노트북 실행

노트북 커널을 재시작하고 아래 순서로 준비한 뒤 기본 질문부터 실행합니다. KB 생성 코드를 실행할 필요는 없습니다. **Run All은 공정 3회·품질 4회, 총 7회 호출**하므로, 전체 질문을 실행하려는 경우가 아니라면 셀별로 실행하세요.

| 단계 | 실행 | 확인 |
| --- | --- | --- |
| 준비 | 설치 셀 → 1. 설정 | 자신의 엔드포인트·테넌트·앱 ID와 v2 KB 두 이름 |
| 인증 | 2. MSAL 사용자 로그인 | Search·Work IQ 토큰 발급 완료 |
| 도우미 | 3. KB 호출과 로그 파싱 준비 | 로그 파서 준비 완료. API 호출 없음 |
| 공정 기본 | 4. 공정 KB의 첫 호출 셀 → 바로 다음 로그 셀 | LOT0012 조사 답변, 실제 선택된 소스·근거·미확인 사항 |
| 공정 추가 1 | 4-2. 장비 매뉴얼과 공개 해결 자료 → 호출·로그 셀 | 두 장비의 내부 주의사항과 공개 해결 자료의 출처 구분 |
| 공정 추가 2 | 4-3. Hold 로트와 공정 설명 → 호출·로그 셀 | 실제 Hold 상태·공정과 공개 공정 설명의 출처 구분 |
| 품질 기본 | 5. 품질 KB의 첫 호출 셀 → 바로 다음 로그 셀 | HTTP 200 여부, Fabric·문서 두 종류·Work IQ 네 KS 근거 |
| 품질 추가 1 | `로그를 읽고 확인하기` 안내 바로 아래 호출 셀 → 로그 셀 | 메일에서 찾은 대상·시점과 품질·센서·문서 이력의 연결 |
| 품질 추가 2 | 5-3. LOT0004 품질 이슈와 업무 컨텍스트 → 호출·로그 셀 | 운영·센서·문서·협업 근거와 미확인 항목 |
| 품질 추가 3 | 5-4. 최근 품질 이슈 5건과 원인 가설 → 호출·로그 셀 | 최신순 기준·반환 건수·검사/센서 연결과 원인 가설 |

HTTP 206이나 소스 오류는 부분 실패로 봅니다. 근거 미확인은 조건에 따른 미조회와 필요한 근거 누락을 구분합니다. 남아 있는 저장 출력은 과거 실행 기록이며
현재 로그인이나 새 환경의 성공을 뜻하지 않습니다. 공정 질문을 LOT0012 조사로 교체하면서 이전 공정 저장 출력은 제거했습니다.

### 선택: REST 요청 직접 작성

아래는 노트북의 호출 구조를 살펴볼 때 사용하는 별도 예제입니다. 위 실습을 마쳤다면
다시 실행할 필요가 없으며, 실행하면 조회·사용량이 추가됩니다.

위 토큰을 준비한 뒤 **작업 디렉터리가 저장소 루트인 노트북**에서 실행합니다.
품질 시나리오는 `QUALITY_KB_NAME`과 해당 질문으로 바꿉니다. 아래 예제도 노트북 설정의 참가자별 KB 이름을 사용합니다.

```python
import sys
import requests
from IPython.display import Markdown, display

sys.path.insert(0, "labs/05-foundry-iq/helper/code")
from knowledge_bases_v2 import API_VERSION, has_evidence

kb_name = PROCESS_KB_NAME
question = (
    "MES에서 LOT0012 로트 상태를 확인하고, 현재 진행 중인 공정에서 이슈가 있는지 확인해보자. "
    "만약 이슈가 있다면, 바로 직전 공정의 설비를 확인해서 해당 설비를 내부 장비 문서를 통해서 "
    "어떤 이슈가 있을법한지 검토해 보고, 이 이슈 사항이 웹 상에서 다른 회사에서도 문제가 "
    "발생했는지 퍼블릭하게 확인해서 전체적인 요약본을 제공해"
)
members = {
    PROCESS_KB_NAME: {
        "ks-process-mes-v2": "mcpServer", "ks-process-webiq-v2": "mcpServer",
        "ks-quality-manuals-v2": "azureBlob",
    },
    QUALITY_KB_NAME: {
        "ks-quality-handovers-v2": "searchIndex", "ks-quality-workorders-v2": "searchIndex",
        "ks-quality-fabric-v2": "fabricDataAgent",
        "ks-quality-workiq-v2": "workIQ",
    },
}[kb_name]
with requests.Session() as session:
    session.params = {"api-version": API_VERSION}
    session.headers.update({
        "Authorization": f"Bearer {search_token}",
    })
    if kb_name == QUALITY_KB_NAME:
        session.headers.update({
            "x-ms-query-source-authorization": search_token,
            "x-ms-query-work-iq-source-authorization": workiq_token,
        })
    response = session.post(
        f"{SEARCH_ENDPOINT}/knowledgebases/{kb_name}/retrieve",
        json={
            "messages": [{"role": "user", "content": [{"type": "text", "text": question}]}],
            "knowledgeSourceParams": [
                {
                    "knowledgeSourceName": name, "kind": members[name],
                    "includeReferences": True, "includeReferenceSourceData": True,
                }
                for name in members
            ],
            "includeActivity": True,
            "maxRuntimeInSeconds": 300,
        },
        timeout=330,
    )
    response.raise_for_status()
    result = response.json()

print("HTTP", response.status_code)
for name in members:
    print(name, "근거 수신" if has_evidence(result, name) else "미확인 또는 실패")
for activity in result.get("activity", []):
    if activity.get("error"):
        print("소스 오류:", activity.get("knowledgeSourceName"), activity["error"])
    if activity.get("knowledgeSourceName") == "ks-process-webiq-v2":
        print("외부 조회 매개변수:", activity.get("mcpServerArguments"))
if response.status_code == 206:
    print("부분 실패입니다. 아래 생성형 답변보다 소스 오류를 우선 확인하세요.")
for message in result.get("response", []):
    for content in message.get("content", []):
        if content.get("type") == "text":
            display(Markdown(content["text"]))
```

`references[].activitySource`를 `activity[].id`와 연결해 출처를 확인합니다.
근거 수신 기준은 `count > 0`, 오류 없는 소스 활동, 그 활동에 연결된 reference입니다.
HTTP 200만으로 모든 소스를 사용했거나 업무 질문에 충분한 근거가 있다고 판단하지 않습니다.

단독 테스트에서는 `knowledgeSourceParams`의 **사용하지 않을 소스에
`neverQuerySource: True`**를 지정합니다. 특정 소스 하나만 배열에 넣는 것과 달리
나머지 소스를 이번 요청에서 명시적으로 제외하며, KB 구성을 변경하지 않습니다.

## 노트북에서 실행 로그 파싱하기

[호출 노트북](kb_retrieve_test.ipynb)의 **3. KB 호출과 로그 파싱 준비**에서 파서를 준비하고,
**4. 공정 KB / 5. 품질 KB**에서 각각 실제 응답을 분석합니다. 기존 KB 테스트를 거치거나
별도 절로 건너뛸 필요 없이 위에서 아래로 실행합니다.

1. 파서 준비 셀을 실행합니다. [파서 코드](helper/code/retrieval_trace.py)는 표준 라이브러리만 사용합니다.
2. 선택한 공정 KB 호출 셀 → 바로 다음 공정 로그 출력 셀을 실행합니다.
3. 선택한 품질 KB 호출 셀 → 바로 다음 품질 로그 출력 셀을 실행합니다.
4. 로그 출력 셀만 재실행하면 메모리에 있는 응답을 다시 파싱합니다. **추가 API 호출은 없습니다.**

출력은 다음을 구분합니다.

| 출력 | 확인할 내용 |
| --- | --- |
| 타임라인 | 계획·검색·답변 생성 활동, 시각, 소요 시간, 모델·토큰·추론 수준, warning/error |
| 실제 검색·도구 입력 | `searchIndexArguments`, `azureBlobArguments`, `mcpServerArguments`, `workIQArguments`, `fabricDataAgentArguments` 등 반환된 입력 전체 |
| 동일 소스 추가 호출 | 이전/후속 활동 ID, 결과 수와 입력 변경 여부. 상세 입력은 검색 항목에서 대조 |
| 인용 연결 | 활동 ID → KS → reference ID → 최종 답변의 `[ref_id:…]`, 점수와 원문 미리보기 |

이 로그는 **모델의 내부 추론 전문이 아닙니다.** 계획 활동이 반복돼도 후속 검색이 없으면
재검색으로 표시하지 않습니다. 같은 KS를 다시 호출해도 병렬 하위 검색·추가 검색·재시도 중
무엇인지 단정하지 않습니다. 이유가 없으면 “재조회 이유는 응답에 명시되지 않음”으로 표시합니다.
`warning`의 임계값·토큰 잘림·시간 제한 경고와 `error`는 그대로 보되 재검색의 원인이라고 추정하지 않습니다.

`count=0`은 원본에 자료가 없다는 뜻이 아닐 수 있습니다. `count`는 관련성 기준을 통과한 결과 수이며,
최종 reference 개수와도 다릅니다. `elapsedMs`가 없으면 시작·종료 시각 차이를 사용했다고
표시하고 둘 다 없으면 미제공으로 남깁니다. 시간 겹침을 표시하지만 인과관계를 만들어내지 않습니다.

원문은 500자 미리보기만 출력하며 파싱된 `v2_process_trace['references']`,
`v2_quality_trace['references']`에서 필요한 항목을 직접 펼칠 수 있습니다.
실제 본문·메타데이터가 반환되지 않으면 추측하거나 추가 네트워크 조회하지 않습니다.
인용 표식이 없거나 연결 대상이 없는 경우도 표시합니다. 원시 메일·문서 내용이 포함될 수 있으므로
노트북 출력 공유 전 검토하거나 지우세요. 알려진 인증 키 필드는 마스킹하지만 범용 개인정보 제거기는 아닙니다.

실제 응답과 파서의 활동 수·검색 입력·reference 연결을 대조한 검증은
[검증 기록](helper/code/v2_validation.json)의 `traceParsingTests`에 저장합니다.
2026-10-01(KST)에 **v2 노트북 셀 자체를 실행**하여 다음 출력을 저장했습니다.
검증에는 기존 Azure CLI 세션을 사용했고, 참가자용 MSAL 로그인 셀은 변경하지 않았습니다.
당시 v2 전용 재배치에서는 두 질문·요청 내용·저장 응답을 보존했습니다.
그때의 로컬 재배치 검증은 MSAL·HTTP 모의 응답으로 호출 2회를 확인한 것이며,
새로운 원격 호출이나 MSAL 브라우저 로그인 성공을 기록한 것은 아닙니다. 이후 공정 기본 질문 변경·추가 질문 반영으로 현재 호출 수는 4회가 되었고 공정 저장 출력은 비웠습니다.

| 실제 응답 | HTTP / 소요 시간 | 계획 활동 | 검색·도구 호출 | 반환 reference / 답변에 인용된 reference |
| --- | --- | --- | --- | --- |
| 공정 KB 3개 KS | 200 / 34.3초 | 2회 | 9회 | 20 / 11 |
| 품질 KB 4개 KS | 200 / 221.4초 | 1회 | 8회 | 28 / 5 |

두 응답 모두 기대한 KS 전체에서 근거를 받았고, 파싱된 활동·검색·reference 연결을 원본 JSON과
대조했습니다. 연결되지 않은 답변 인용 ID는 없었습니다. 응답 시간은 해당 실행의 관찰값입니다.
공정 응답에서는 `get_process_route(stage="CMP")`가 0건을 반환했고,
후속 계획 이후 `get_process_route(step_code="CMP")`가 1건을 반환했습니다.
이것은 로그에서 확인한 입력 변화이지, 모델이 재조회한 이유를 설명한 문장이 아닙니다.
품질 응답은 계획 1회에도 여러 하위 검색이 있으므로, 같은 KS의 여러 호출을 모두 재검색으로 세지 않습니다.

작성자용 회귀 테스트는 저장소 루트에서 실행합니다.
[노트북 흐름 테스트](helper/code/test_notebook_v2.py)는 기존 KB 호출이 남지 않았는지,
현재 노트북의 실제 호출 셀 전체가 두 v2 KB로 요청되는지, 사용자 토큰 헤더·부분 실패·오류 처리를 확인합니다. 현재는 공정 2회·품질 2회를 모의 실행하며 원격 소스나 질문의 업무 타당성을 검증하지 않습니다. 아래 명령은 노트북 실행에 필요한 패키지가 있는 Python에서 사용합니다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s labs/05-foundry-iq/helper/code -p 'test_*.py'
```

## 신규 생성 코드

[생성·검증 도우미](helper/code/knowledge_bases_v2.py)의 `build_definitions()`는
기존 KS 정의 맵, 기존 KB 정의, Storage 계정 ARM ID, MES 키, Web IQ 키를 받아
신규 KS·KB 정의를 반환합니다. `create_only()`에는 인증과 `api-version`이 설정된
`requests.Session`, Search 엔드포인트, 신규 정의 두 목록을 전달합니다.
키는 환경 변수 또는 `getpass.getpass()`로 받고 정의 전체를 출력하지 않습니다.
`build_bases()`로 현재 3개 / 4개 KB 정의만 만들 수도 있습니다. 실제 재배치 작업에서는
ETag의 `If-Match` 조건으로 v2 KB 두 개만 갱신했으며, 생성 전용 보호 함수는 변경하지 않았습니다.

- 기존 데이터와 참조는 재사용하지만 KS·KB 정의는 복사본에서 구성합니다.
- 생성 전에 이름 충돌을 확인하고 `If-None-Match: *` 조건부 PUT으로 덮어쓰기를 차단합니다.
  이미 만들어진 v2 리소스가 있으므로 전체 재실행은 중단됩니다.
- 실패 시 부분 생성된 신규 리소스는 유지합니다. 자동 삭제·업데이트하지 않습니다.
- Blob·모델은 기존 Search 시스템 할당 관리 ID를 사용합니다. 마스킹된 원본 키를 복사하지 않습니다.
- [단위 테스트](helper/code/test_knowledge_bases_v2.py)는 이름·읽기 도구 목록·덮어쓰기 방지·근거 판정을 확인합니다.
- [경로 회귀 테스트](helper/code/test_notebook_paths.py)는 이동된 노트북·문서의 링크와 루트·랩 폴더에서의 파서 경로 탐색을 확인합니다.

저장소 루트에서 실행:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 labs/05-foundry-iq/helper/code/test_knowledge_bases_v2.py
```

## 오류와 정리

- `401/403`: Search 역할, 사용자 테넌트·위임 권한, 원본 접근 권한, MCP 키를 각각 확인합니다.
- `412`: 동일 이름이 이미 존재합니다. 기존 리소스를 보호하기 위한 중단입니다.
- `206` + Fabric timeout: `maxRuntimeInSeconds=300`은 관찰된 Fabric 내부 100초 제한을 늘리지 않습니다.
  부분 실패를 숨기거나 나머지 소스만으로 전체 성공을 표시하지 않습니다.
- 키 회전 시 **신규 v2 MCP KS의 인증 설정만** 갱신합니다. `create_only()`는 업데이트 함수가 아닙니다.
- 실습 리소스는 재사용을 위해 유지했습니다. 정리는 신규 KB 두 개 → 이 문서의 신규 KS 7개
  순으로 진행하고, Blob KS가 만든 위 네 하위 리소스의 잔존 여부를 확인합니다.
  원본 인덱스·Blob 컨테이너·Fabric Data Agent·앱 등록·기존 KS·KB는 삭제하지 않습니다.

## 참고

- [MCP Server knowledge source](https://learn.microsoft.com/azure/search/agentic-knowledge-source-how-to-mcp-server)
- [KS REST 계약](https://learn.microsoft.com/rest/api/searchservice/knowledge-sources/create-or-update?view=rest-searchservice-2026-08-01-preview)
- [Knowledge Base retrieve](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-retrieve)
- [Web IQ 실습과 접근 조건](../03-web-iq/README.md)

[전체 실습 목록](../../README.md)