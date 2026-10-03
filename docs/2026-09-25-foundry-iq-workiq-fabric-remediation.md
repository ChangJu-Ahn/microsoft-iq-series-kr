# Foundry IQ Work IQ 및 Fabric IQ 호출 오류 조치 리포트

- 조치 일자: 2026-09-25
- 대상 Knowledge Base: `manufacturing-kb`
- Azure AI Search: `ai-search-srch-vljt`
- 최종 상태: `2026-08-01-preview` REST retrieve에서 Work IQ 및 Fabric IQ 호출 성공

## 결론

| 구분 | 확인된 원인 | 조치 | 최종 검증 |
| --- | --- | --- | --- |
| 공통 모델 호출 | 로컬 키 인증이 비활성화된 모델 리소스에 API key 인증을 시도함 | Knowledge Base 모델 인증을 Azure AI Search 시스템 할당 관리 ID로 전환 | 모델 계획 단계 정상 실행 |
| Work IQ | 일반 Knowledge Base 호출 클라이언트가 Work IQ 전용 사용자 assertion 헤더를 전달하지 않음 | `access_as_user` assertion을 발급하고 전용 헤더로 전달 | HTTP 200, Work IQ 활동 및 참조 각 1건 |
| Fabric IQ | 지식 소스가 삭제된 이전 Data Agent를 가리키고, 현재 Data Agent의 F2 capacity가 일시 중지됨 | 현재 workspace/Data Agent ID로 교체하고 F2 capacity 재개 | HTTP 200, Fabric Data Agent 활동 및 참조 각 1건 |

## 대상 구성

| 항목 | 값 |
| --- | --- |
| Foundry account | `foundry-changju-kr-v2` |
| Foundry project | `proj-default` |
| Knowledge Base | `manufacturing-kb` |
| Work IQ knowledge source | `ks-workiq-changju` |
| Fabric knowledge source | `ks-fabriciq-factoryagent-v2` |
| 현재 Fabric workspace | `IQ-Fabric-v2-0917` (`519a98e5-0ec5-4330-a1d2-2991af13ecb8`) |
| 현재 Fabric Data Agent | `factory_dataagent` (`96e07abb-588d-40d8-8563-45fb771557a5`) |
| Fabric capacity | `fabriciqv20917` (F2) |

## 확인된 증상과 원인

### 1. 공통 모델 인증

최초 검색에서는 모델 호출이 HTTP 403으로 실패했고 다음 메시지가 반환되었습니다.

```text
Key based authentication is disabled for this resource.
```

모델 리소스는 로컬 키 인증이 비활성화되어 있었지만 Knowledge Base는 API key 인증을 시도하고 있었습니다. Azure AI Search 관리 ID에는 이미 `Cognitive Services OpenAI User` 역할이 있으므로 새 역할 추가 없이 시스템 할당 관리 ID를 사용하도록 모델 인증을 변경했습니다.

최종 확인 시 `apiKey`와 `authIdentity`는 모두 `null`이며, 시스템 할당 관리 ID 경로로 모델 계획 단계가 정상 실행되었습니다.

### 2. Work IQ

Work IQ 소스의 앱 등록, federated credential 및 tenant 설정은 정상적으로 저장되어 있었습니다. 문제는 일반 MCP 검색 호출이 다음 Work IQ 전용 헤더를 전달하지 않는 것이었습니다.

```http
x-ms-query-work-iq-source-authorization: <user-assertion>
```

사용자 assertion은 다음 정확한 delegated scope로 발급해야 합니다.

```text
api://12beac79-cff2-47e0-9fc3-4b60e3b33540/access_as_user
```

검증한 assertion에는 다음 조건이 모두 충족되었습니다.

- `aud`: Work IQ 앱 등록
- `scp`: `access_as_user`
- `oid`: 로그인 사용자
- `tid`: Work IQ 앱과 동일한 tenant

Azure CLI는 진단용으로만 사용했습니다. 실제 애플리케이션에서는 MSAL authorization code flow와 PKCE로 사용자 assertion을 발급해야 합니다.

#### 포털 테스트 제한

2026-09-25 기준 공식 문서의 Work IQ 사용 지원표에서 Azure portal과 Microsoft Foundry portal은 모두 지원되지 않습니다. 지원되는 질의 경로는 .NET SDK, Python SDK 및 REST API입니다.

따라서 Azure portal의 Knowledge Base **New chat**은 사용자 assertion을 발급하거나 다음 헤더를 채우지 못합니다.

```text
Invalid header: 'x-ms-query-work-iq-source-authorization' is null or empty.
```

이 오류는 Work IQ 지식 소스 설정 실패가 아니라 현재 포털 테스트 클라이언트의 기능 제한입니다. 지식 소스 설정만 변경해서 포털 채팅을 동작하게 만들 수 없으며, 사용자 로그인과 assertion 전달을 구현한 SDK 또는 REST 클라이언트로 검증해야 합니다.

### 3. Fabric IQ

기존 지식 소스는 다음 삭제된 이전 항목을 가리키고 있었습니다.

| 항목 | 이전 값 |
| --- | --- |
| Workspace ID | `4177bef9-1c57-440b-a918-d46c9ec677e9` |
| Data Agent ID | `0e3c2dbc-a1ad-44b5-9e85-d1bd4aa1800a` |

이전 workspace의 Items API 결과는 0건이었고, 이전 Data Agent 조회는 `EntityNotFound`를 반환했습니다. 현재 capacity가 연결된 workspace에서 `factory_dataagent`를 확인하고 지식 소스의 두 ID만 교체했습니다.

교체 후에도 직접 Data Agent 호출은 다음 오류를 반환했습니다.

```text
CapacityNotActive
```

연결된 `fabriciqv20917` F2 capacity의 상태가 `Paused`였으므로 재개했습니다. 최종 상태는 `provisioningState: Succeeded`, `state: Active`입니다.

## 호출 요구사항

### 공통 서비스 인증

Knowledge Base retrieve 요청 자체에는 Azure AI Search 서비스 인증이 필요합니다.

```http
Authorization: Bearer <search-service-access-token>
```

### Work IQ 사용자 인증

```http
x-ms-query-work-iq-source-authorization: <work-iq-app-audience-user-assertion>
```

### Fabric 사용자 인증

Fabric Data Agent OBO 호출에는 Azure AI Search audience 사용자 토큰을 별도로 전달합니다.

```http
x-ms-query-source-authorization: <search-audience-user-token>
```

혼합 질문에서는 서비스 인증과 두 사용자 헤더를 모두 전달해야 합니다. 헤더가 하나라도 없으면 플래너가 해당 소스를 선택했을 때 전체 또는 부분 실패가 발생할 수 있습니다.

요청 본문의 핵심 설정은 다음과 같습니다.

```json
{
  "knowledgeSourceParams": [
    {
      "knowledgeSourceName": "<knowledge-source-name>",
      "kind": "<workIQ-or-fabricDataAgent>",
      "includeReferences": true,
      "includeReferenceSourceData": true
    }
  ],
  "includeActivity": true,
  "maxRuntimeInSeconds": 300
}
```

Work IQ는 40초 이상 걸릴 수 있고, 이번 Fabric 질의는 120초 제한을 초과했습니다. 이 워크숍 구성에서는 `maxRuntimeInSeconds: 300`을 권장합니다.

## 최종 검증 결과

### Work IQ 질문

실제 검증에 사용한 질문은 다음과 같습니다.

```text
Microsoft 365의 메일, Teams 대화, 회의 및 공유 문서에서 EQP-CMP01과 LOT0004에 관련된 논의, 의사결정 배경, 담당자와 후속 조치를 찾아서 근거별로 정리해 주세요. Fabric 운영 수치나 장비 매뉴얼이 아니라 Microsoft 365 협업 기록만 사용해 주세요.
```

| 검증 항목 | 결과 |
| --- | --- |
| HTTP 상태 | 200 |
| Work IQ 활동 | 1건, 오류 없음 |
| Work IQ 소요 시간 | 52.722초 |
| Work IQ 참조 | 1건 |
| `sourceData.parts` | 2개 |

### Fabric IQ 질문

실제 검증에 사용한 질문은 다음과 같습니다.

```text
Fabric 운영 데이터에서 EQP-CMP01이 LOT0004를 처리한 시점의 PAD_PRESSURE 측정값, 경고 또는 알람 횟수와 관련 품질 판정을 조회해 주세요. 문서나 Microsoft 365 기록이 아니라 Fabric Data Agent의 운영 데이터만 사용해 주세요.
```

| 검증 항목 | 결과 |
| --- | --- |
| Data Agent 직접 MCP 초기화 | 성공 |
| HTTP 상태 | 200 |
| Fabric Data Agent 활동 | 1건, 오류 없음 |
| Fabric Data Agent 참조 | 1건 |
| `sourceData.fabricAnswer` | 반환됨 |
| `sourceData.fabricEmbeddedResources` | 필드 반환됨 |

M365 원문과 실제 응답 내용은 이 리포트에 저장하지 않았습니다.

## 운영 주의사항

- F2 capacity를 재개했으므로 Fabric 과금도 다시 시작되었습니다. 실습이 끝난 뒤 capacity 중지 정책을 별도로 결정해야 합니다.
- `knowledgeSourceParams`에 한 소스만 넣어도 모델 플래너가 다른 연결 소스를 선택할 수 있습니다. 성공 여부는 HTTP 상태뿐 아니라 `activity[].type`, `activity[].error`, `references[].type`을 함께 확인합니다.
- Azure portal, Microsoft Foundry portal 및 일반 `search_knowledge_base_retrieve` 도구는 Work IQ 사용자 assertion 헤더를 전달하지 못합니다. 이 클라이언트들로는 Work IQ 소스 성공을 검증할 수 없으며, 사용자 헤더를 설정할 수 있는 `2026-08-01-preview` REST 또는 지원 SDK 클라이언트를 사용해야 합니다.
- 진단 중 `ks-azureblob-manual`의 벡터화 인증 403도 관찰했습니다. Work IQ와 Fabric IQ 검증 범위 밖이므로 이번 조치에는 포함하지 않았습니다.
- access token과 M365/Fabric 응답 본문은 로그나 문서에 기록하지 않습니다.

## 참고 문서

- [Work IQ knowledge source](https://learn.microsoft.com/azure/search/agentic-knowledge-source-how-to-work-iq)
- [Fabric Data Agent knowledge source](https://learn.microsoft.com/azure/search/agentic-knowledge-source-how-to-fabric-data-agent)
- [Knowledge Base retrieve](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-retrieve)
- [Fabric data agent MCP server](https://learn.microsoft.com/fabric/data-science/data-agent-mcp-server)
- [Fabric capacity 일시 중지 및 재개](https://learn.microsoft.com/fabric/enterprise/pause-resume)