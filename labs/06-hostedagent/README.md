# 06. Foundry IQ Hosted Agent 웹 데모

> **발표자용 참고 구현입니다. 참가자가 직접 만드는 실습이 아닙니다.**
> 참가자는 [05 Foundry IQ](../05-foundry-iq/README.md)에서 KB를 구성하고 API로 검증합니다.
> 이 데모는 그 결과를 **Entra ID 로그인 → 웹 사이트 → Microsoft Foundry Hosted Agent → Foundry IQ**의 서비스 흐름으로 보여줍니다.

**[배포된 웹 데모 열기](https://ca-iq-demo-web.agreeabledune-2db01c8e.eastus2.azurecontainerapps.io)**

상단의 **CJ 전자 시나리오**에서 고객 배경을 먼저 읽고 질문을 시작할 수 있습니다. [시나리오 페이지](https://ca-iq-demo-web.agreeabledune-2db01c8e.eastus2.azurecontainerapps.io/scenario)는 로그인 없이 열리며, **GitHub 레포** 링크로 원본 실습 자료에 이동할 수 있습니다.

질문 실행·질문 목록·KB 설명 조회에는 Entra ID 로그인이 필요합니다. 시작 화면과 공개 시나리오 읽기에는 필요하지 않습니다. **품질 질문을 실행하기 전에는 `fabriciqv20917` 용량을 확인하고, Paused이면 Active로 재개**해야 합니다. 이전 검증 후 비용 방지를 위해 Paused로 복원했으며, 이 문서 점검에서 현재 용량을 다시 조회하지는 않았습니다.

## 1. 무엇을 보여주는 데모인가

- 한 번의 질문을 Foundry IQ가 어떻게 계획하고 여러 원본에 나누어 조회하는지 확인합니다.
- 근거 기반 답변을 스트리밍하고, 답변과 별도로 실제 검색·도구 호출·인용 연결을 보여줍니다.
- 답변의 Markdown 제목·강조·목록·표·인용문·코드 블록을 읽기 쉬운 서식으로 표시합니다. 원문 인용 ID는 유지합니다.
- 같은 질문을 Low/Medium으로 실행해 계획·검색 횟수와 지연을 비교합니다.
- 선택한 Knowledge Base(KB)와 연결된 Knowledge Source(KS)의 역할을 설명으로 확인합니다.
- 상단 연결도에서 Entra 인증·웹·Foundry Hosted Agent·Foundry IQ와 각 지식원의 데이터 역할을 확인합니다. 선택한 KB만 강조하며 실제 호출 완료를 뜻하지는 않습니다.

이 구현은 **커스텀 코드 기반 Microsoft Foundry Hosted Agent**입니다. `azure-ai-agentserver-invocations`의 `InvocationAgentServerHost`를 사용하며 **Microsoft Agent Framework(MAF) 구현이 아닙니다.** 로컬 배포 기록에는 `iq-workshop-demo` **버전 5**의 `active` 전환과 업로드·다운로드 ZIP 해시 일치가 남아 있습니다. 일반 API 서버에 Agent라는 이름만 붙이거나 Prompt Agent로 대체하지 않았습니다. 두 KB를 자동 결합하거나 원인 확정·출하 승인·업무 조치를 실행하지는 않습니다.

## 2. 아키텍처와 실행 흐름

```text
사용자 브라우저
  ├─ Entra ID 로그인
  └─ 웹: Container Apps HTTPS / 로컬 localhost:8000
       ├─ 로그인 세션·사용자 토큰 관리
       ├─ KB·KS 설명 GET → Azure AI Search
       └─ SSE 중계 → Microsoft Foundry Hosted Agent
                       ├─ Foundry IQ KB retrieve
                       │   ├─ 공정: MES + 내부 매뉴얼 + Web IQ
                       │   └─ 품질: Fabric + 작업지시서 + 인수인계서 + Work IQ
                       ├─ activity·references 파싱 → 디버그 trace
                       └─ KB 답변에 근거한 모델 생성 → 실제 텍스트 delta
```

1. 웹에서 로그인한 사용자의 Search·Work IQ 위임 토큰을 취득합니다.
2. 웹의 서비스 호출 자격 증명(클라우드 Managed Identity / 로컬 Azure CLI)으로 Hosted Agent에 인증합니다. KB·질문·추론 강도를 보내고, 로그인 사용자의 위임 토큰은 질문과 분리된 전용 헤더로 전달합니다.
3. Agent가 기존 KB를 조회합니다. **KB retrieve 자체는 비스트리밍**이며 계획·검색·답변 합성이 끝난 응답을 받습니다.
4. 같은 응답에서 소스별 근거 상태와 디버그 정보를 파싱합니다. 이를 위해 추가 모델/검색을 호출하지 않습니다.
5. 별도 모델 호출이 KB 답변의 사실·인용을 바탕으로 최종 답변을 **실제 토큰 스트리밍**합니다. 완성된 답변을 잘라 보내는 방식이 아닙니다.

이벤트는 `status → evidence → trace → status → delta* → done` 순서로 전달됩니다. 오류는 `error`로 종결하며, 완료 이벤트 없이 끊긴 응답은 미완료로 표시합니다. KB 합성 외에 최종 모델 호출 비용이 추가됩니다.

## 3. 폴더와 소스코드

**모든 소스·테스트·배포 정의는 [code/](code/)에 있습니다.** GitHub에는 아래 실행 자료와 이 README를 올립니다. 개인 설정·실행 로그·작업 이력은 공개 파일에 포함하지 않습니다.

```text
06-hostedagent/
├── README.md                  # 이 문서: 기능·구조·실행·배포·운영
├── .gitignore                 # 로컬 설정·로그·환경·작업 이력 제외
└── code/
    ├── web.py                 # Entra 로그인·세션·SSE 중계
    ├── catalog.py             # 실제 KB·KS 설명 조회
    ├── questions.py           # 05 노트북의 질문 추출
    ├── scenario.py            # 00 고객 브리프·기존 도식의 로컬/컨테이너 경로
    ├── setup_identity.py      # 전용 웹 앱 등록
    ├── deploy.py              # Foundry Hosted Agent 배포
    ├── deploy_web.py          # Container Apps 웹 배포
    ├── evaluate.py            # 모든 노트북 질문 회귀
    ├── requirements.txt       # 개발·배포·검증 의존성
    ├── requirements-web.txt   # 웹 이미지 전용 의존성
    ├── package.json          # Markdown 파서 버전·브라우저 자산 생성·JS 테스트
    ├── package-lock.json
    ├── .npmrc                 # 특정 조직 registry에 고정되지 않는 잠금 파일
    ├── .env.example           # 로컬 설정 예제
    ├── Dockerfile
    ├── .dockerignore
    ├── agent/                 # Hosted Agent와 KB 호출·근거·trace 처리
    ├── static/                # HTML/CSS/JavaScript UI
    ├── infra/                 # Container Apps·ACR·identity Bicep
    ├── scripts/               # 고정 버전 Markdown 브라우저 번들 생성
    └── tests/                 # Python / JavaScript 회귀 테스트
```

제작 중 사용한 계획서·작업 보고서는 참고 자료에 포함하지 않습니다. 기능·실행·배포 안내는 이 README에서 확인합니다. `logs/`, `.copilot-azure/`, `.azure/`, `.venv/`, `node_modules/`, `code/.env`는 [.gitignore](.gitignore)로 제외하며, `logs/`는 배포·평가 스크립트가 필요할 때 생성합니다.

테스트, `package-lock.json`, [Markdown 브라우저 번들](code/static/markdown-it.js)은 불필요한 산출물이 아닙니다. 각각 회귀 검증, 의존성 재현, CDN 없는 웹 실행에 필요하므로 유지합니다.

GitHub 업로드 전 저장소 루트에서 `git add --dry-run labs/06-hostedagent`로 포함할 파일을 확인하세요. `.env`, 로그, 가상환경 또는 `node_modules`가 보이면 먼저 제외 규칙을 확인하고, 무시된 파일을 `git add -f`로 포함하지 마세요.

| 읽을 파일 | 확인할 내용 |
| --- | --- |
| [web.py](code/web.py) | 로그인, 세션 만료·CSRF·동시 요청 제한, Managed Identity, SSE 중계 |
| [agent/main.py](code/agent/main.py) | Invocations 입력, KB 호출, 상태·trace·모델 delta 전송 |
| [agent/retrieval.py](code/agent/retrieval.py) | 3/4개 KS 요청, Low/Medium, 소스 근거·인용 판정 |
| [agent/trace_view.py](code/agent/trace_view.py) | 05 파서 재사용, trace 집계·비밀값 마스킹·실제 본문 필드 추출 |
| [catalog.py](code/catalog.py) | KB의 실제 연결 목록을 따라 KS 설명 조회, 반환 필드 제한 |
| [static/app.js](code/static/app.js), [static/trace.js](code/static/trace.js), [static/comparison.js](code/static/comparison.js) | 질문·KB 설명 사이드바·토글·디버그·동일 질문 비교 UI |
| [static/markdown.js](code/static/markdown.js), [scripts/vendor-markdown.mjs](code/scripts/vendor-markdown.mjs) | 안전한 Markdown 렌더링과 오프라인 브라우저 라이브러리 생성 |
| [static/references.js](code/static/references.js) | 출처 이름·실제 reference 연결·인용 근거 카드·안전한 원문 링크 |
| [static/question-picker.js](code/static/question-picker.js) | 모든 05 실습 질문의 팝업 목록, Knowledge Base 연결, 직접 입력 구분 |
| [static/scenario.html](code/static/scenario.html), [static/scenario-render.js](code/static/scenario-render.js), [scenario.py](code/scenario.py) | 00 README 기반 공개 시나리오 페이지, 목차·도식·원본 링크 |
| [questions.py](code/questions.py) | 원본 노트북을 실행하지 않고 AST로 질문 추출 |
| [deploy.py](code/deploy.py), [deploy_web.py](code/deploy_web.py), [infra/](code/infra/) | Agent 배포와 웹 배포의 차이, 패키징·권한·리소스 정의 |
| [evaluate.py](code/evaluate.py), [tests/](code/tests/) | 실제 질문 회귀와 로컬 자동 검증 |

의존하는 원본은 [05 노트북](../05-foundry-iq/kb_retrieve_test.ipynb), [기존 trace 파서](../05-foundry-iq/helper/code/retrieval_trace.py), [00 고객 브리프](../00-getting-started/README.md)와 [도식](../00-getting-started/assets/)입니다. 이 폴더를 단독 복사하기보다 저장소 구조를 유지하세요. Agent 배포 ZIP에는 파서를 포함하고, 웹 이미지에는 추출한 질문 JSON과 공개 시나리오 README·SVG 도식 2개를 포함합니다.

## 4. 화면 사용법

### CJ 전자 시나리오

상단의 **CJ 전자 시나리오** 링크는 별도 페이지를 새 탭으로 열어 현재 작성 중인 질문을 유지합니다. 00 README의 고객 상황·페인포인트·실습 흐름·완료 기준·주의사항을 생략하지 않고 HTML로 표시합니다.

- 목차에서 원하는 절로 이동하고, 기존 SVG 도식 2개는 클릭해 크게 볼 수 있습니다.
- 원문 Markdown의 상대 문서 링크는 GitHub의 해당 파일로 연결합니다.
- **질문하러 가기** 버튼으로 웹의 질문 화면에 돌아옵니다.
- 시나리오 문서 읽기에는 로그인이 필요 없으며, 모델·Knowledge Base 조회는 실행하지 않습니다.
- 문서의 사실·시나리오를 별도로 복제하지 않습니다. 00 README를 변경한 뒤 웹을 재배포하면 본문과 도식에 반영됩니다. 실제 실행 질문은 05 질문 팝업을 기준으로 합니다.

### 질문·답변과 모드 비교

1. Entra ID로 로그인합니다.
2. **05 실습 질문 보기** 버튼을 누르면 팝업에서 공정·품질 질문의 전문을 볼 수 있습니다. 원하는 항목의 **이 질문 사용**을 누르면 해당 Knowledge Base와 입력란이 함께 바뀝니다.
3. 선택한 질문을 수정하거나 입력란에 직접 작성합니다. 팝업은 **닫기** 또는 Esc로 닫을 수 있으며, 닫기만 하면 작성 중인 내용은 바뀌지 않습니다.
4. 추론 강도를 선택하고 **근거 조회 & 답변 생성**을 누릅니다.
5. 소스별 응답·인용과 답변의 미확인 항목을 확인합니다.

목록은 [05 노트북](../05-foundry-iq/kb_retrieve_test.ipynb)의 실제 조회 질문 전부를 사용합니다. 같은 Knowledge Base에 질문이 추가되어도 첫 질문만 남기지 않습니다. 팝업에서는 긴 문장을 줄이지 않고 전문을 표시하며, 선택 후 입력란에도 같은 원문을 넣습니다.

현재 소스에서 추출되는 목록은 **공정 2개·품질 2개, 총 4개**입니다. LOT0012 조건부 조사, 제품창고 로트·수량 비교, 지정 NCR 후속 조치, 메일에서 시작하는 품질·센서·작업·인계 조사 순서입니다. [05의 전체 호출 목록](../05-foundry-iq/README.md#현재-노트북의-전체-호출-목록)에 원문과 상태를 기록했습니다. 특히 공정 두 번째 질문은 **`찾은 뒤`에서 끝나는 작성 중 문장**입니다. 팝업은 이를 임의로 완성하거나 검증 완료 질문으로 선별하지 않으므로 실행 전 수정·도구 범위 확인이 필요합니다.

팝업을 열거나 질문을 선택하는 것만으로 채팅·모델 호출을 실행하지 않습니다. 선택한 질문을 편집하면 직접 입력으로 표시합니다. Knowledge Base를 직접 변경할 때 실습 질문을 선택 중이면 해당 KB의 첫 질문으로 맞추고, 직접 작성 중인 내용은 유지합니다. 질문 목록 조회가 실패해도 직접 입력은 사용할 수 있습니다.

공정 KB의 기본 질문은 [05 노트북](../05-foundry-iq/kb_retrieve_test.ipynb)에 있는 다음 문장을 그대로 사용합니다.

> MES에서 LOT0012 로트 상태를 확인하고, 현재 진행 중인 공정에서 이슈가 있는지 확인해보자. 만약 이슈가 있다면, 바로 직전 공정의 설비를 확인해서 해당 설비를 내부 장비 문서를 통해서 어떤 이슈가 있을법한지 검토해 보고, 이 이슈 사항이 웹 상에서 다른 회사에서도 문제가 발생했는지 퍼블릭하게 확인해서 전체적인 요약본을 제공해

사용자가 상세 절차·안전 지침을 질문마다 반복해서 입력하는 방식이 아닙니다. KB 지침에는 소스 역할·공개 검색 제한이 있고, Agent의 최종 모델 지침에는 확인 사실·미확인 구분과 인용 유지가 있습니다. **직전 공정 추적을 강제하는 코드나 외부 검색어 보안 필터는 아닙니다.** 실제 이력 연결과 공개 가능한 검색어인지는 반환 로그로 확인해야 합니다. 질문을 수정할 때는 노트북을 변경하고 웹을 재배포하면 패키징되는 질문 JSON도 함께 갱신됩니다. 이 작업이 원격 KB 지침을 변경하는 것은 아닙니다.

답변은 스트리밍 중에도 누적 Markdown을 화면 프레임 단위로 렌더링합니다. 생성 중 아직 닫히지 않은 서식은 후속 토큰이 오면 완성됩니다. 중지·실패 시에는 그때까지 받은 답변을 남기고 미완료 상태를 표시합니다.

`markdown-it`의 원시 HTML 기능은 끄고, 링크는 HTTP(S)만 허용합니다. 새 창 링크에는 `noopener noreferrer`를 적용하고 외부 이미지를 자동 로드하지 않습니다. 모델이 만든 HTML·스크립트를 실행하지 않으며, CSP도 유지합니다.

답변의 `[ref_id:…]`는 **MES·내부 매뉴얼·Web IQ 등 출처 이름과 ID가 있는 배지**로 표시합니다. 배지를 선택하면 답변 아래의 해당 근거 카드가 펼쳐집니다. 제목·본문·직접 원문 URL은 API에 실제 반환된 것만 사용합니다. URL이 없으면 없다고 표시하고, 미연결·중복 ID는 **근거 미확인**으로 표시합니다. 코드 블록이나 기존 링크 안의 인용 문자열은 배지로 바꾸지 않습니다.

근거 본문은 JSON 앞부분이 아니라 `sourceData.snippet`, `chunk`, `content`, `text` 등 **실제 텍스트 필드를 먼저 추출**해 표시합니다. GUID·문서 ID·Blob URL은 접힌 메타데이터로 분리합니다. reference당 최대 12,000자를 표시하며, 이를 넘으면 원래 본문 길이와 잘림을 명시합니다. 본문 필드가 없으면 메타데이터를 대신 보여주지 않습니다. 이는 검색 결과에 반환된 청크 본문이며, 문서 전체 또는 모델이 실제 사용한 정확한 문장 범위를 뜻하지 않습니다. 추가 모델 요약이나 별도 문서 재조회는 하지 않습니다.

근거 카드는 최종 답변에 실제 등장한 인용만 보여주며, 디버그 토글을 켜지 않아도 확인할 수 있습니다. 같은 질문의 모드 비교 표는 답변·근거 카드 뒤에 배치했습니다.

**Low / Medium은 Foundry IQ 검색 추론 강도**입니다. 최종 스트리밍 모델 설정은 변경하지 않습니다.

| 모드 | 동작 |
| --- | --- |
| Low | LLM으로 한 번 계획하고 하위 쿼리를 만들어 소스를 선택·검색합니다. Low도 쿼리 분할을 합니다. |
| Medium — 기본 | 최초 결과를 평가하고 필요할 때 후속 계획·검색을 수행합니다. 항상 재검색하거나 항상 느린 것은 아닙니다. |

`retrievalReasoningEffort.kind`를 요청별로 지정하므로 KB 저장 설정은 바뀌지 않습니다. 같은 KB·같은 질문을 각각 실행하면 비교 표에 결과가 남습니다. **모드 변경만으로 자동 재호출하지 않습니다.**

최근 완료 실행 10개를 브라우저 메모리에만 유지합니다. 다른 질문·KB를 섞지 않으며 새로고침하면 기록을 지웁니다.

| 측정값 | 기준 |
| --- | --- |
| KB 조회 | Agent의 retrieve 호출 직전부터 응답 수신까지. 계획·검색·KB 합성과 왕복 통신 포함 |
| 모델 생성 구간 | KB 응답 후 별도 모델 호출부터 생성·수신 완료까지 |
| 첫 답변 / 전체·Agent | Agent handler 시작 기준, 첫 텍스트 delta / 전체 완료 |
| 첫 답변 / 전체·브라우저 | 버튼을 누른 시점 기준. 인증·네트워크·기동·스트림 수신 포함 |

병렬 활동 시간을 합산하지 않습니다. 캐시·원본 상태·콜드 스타트·답변 길이도 지연에 영향을 주므로 단일 실행으로 성능 우열을 단정하지 마세요.

### Foundry IQ 실행 기록 — Debug 토글

답변 아래 토글을 켜면 **동일 KB 응답**의 `activity`와 `references`를 확인합니다. 토글 변경은 추가 조회·모델 호출을 발생시키지 않습니다.

- **요청/API 보고 강도:** 요청한 모드와 `agenticReasoning.retrievalReasoningEffort`의 실제 보고값. 미반환이면 “미제공”.
- **요약·타임라인:** 계획 패스·검색/도구 호출·동일 소스 추가 호출·KB 합성 수, 시각·소요 시간·결과 수·토큰.
- **fan-out 배지:** 다른 소스 조회 활동(같은 지식원 호출 포함)과 `startedAt`~`completedAt` 구간이 겹치는 행의 ID 옆에 표시합니다. 기존 `overlaps` 관찰값을 사용하며 모델 계획·합성 활동이나 시각이 누락된 조회에는 붙이지 않습니다. 서버의 fan-out 그룹 ID나 인과관계를 뜻하지 않으며, 활동 ID 순서나 배지 유무만으로 직렬 실행을 단정하지 않습니다.
- **실제 하위 쿼리:** 소스별 `*Arguments`를 공통 형식으로 파싱해 검색문·도구·필터·결과 수·경고/오류를 먼저 표시합니다. MCP의 로트 ID 같은 실제 도구 입력도 읽을 수 있고, 각 카드 아래의 상세 JSON은 기본적으로 접혀 있습니다.
- **추가 호출:** 같은 소스의 이전/후속 activity ID, 검색문·입력·관련 결과 수를 나란히 비교합니다. 원본 상세 필드는 아래에서 펼쳐 볼 수 있습니다. 해석하지 못하는 새 유형은 추측하지 않고 상세 JSON 확인을 안내합니다.
- **인용 연결:** `activity.id → reference.activitySource → reference.id → [ref_id:…]`, 해당 reference의 실제 본문과 접힌 상세 JSON.

**내부 추론 전문은 아닙니다.** 계획 패스 수나 같은 소스 추가 호출 수를 재검색 루프 횟수로 단정하지 않습니다. 추가 호출에는 병렬 하위 검색도 포함됩니다. 반환되지 않은 재조회 이유는 추측하지 않으며, KB 답변 인용과 최종 Agent 답변 인용도 구분합니다.

2번 실행 과정은 **1차 계획·조회 → 2차 계획·조회 → KB 답변 합성**처럼 반환된 계획 활동을 기준으로 묶어 보여줍니다. 각 단계의 시간·입력/출력 토큰·검색문·결과 수는 먼저 읽을 수 있고 **‘근거 · 활동별 반환 JSON’**은 접혀 있습니다. 이는 시간순 표시용 묶음이며 서버가 제공한 iteration ID나 인과관계를 새로 만들어 낸 것이 아닙니다. 계획 활동이 없으면 계획 연결 미제공으로 표시합니다. 검색 추론 활동은 API에 있을 때만 표시하며 이를 임의로 별도의 결과 평가 단계라고 부르지 않습니다.

요약의 계획·합성 I/O 토큰은 해당 활동의 명시된 입력/출력 토큰만 합산합니다. 별도 `agenticReasoning`의 추론 토큰을 중복 합산하지 않으며 전체 청구 토큰으로 해석하지 않습니다.

디버그에는 로그인 사용자가 접근 가능한 내부 문서·메일 발췌가 포함될 수 있습니다. 화면 공유 대상을 확인하세요.

### 오른쪽 Knowledge Base 패널

질문·답변을 보면서 오른쪽 패널에서 선택한 KB의 **이름·설명·기본 추론 강도**와 실제 연결된 KS 각각의 **이름·유형·설명**을 함께 확인합니다. 넓은 화면에서는 패널이 스크롤을 따라가며, 모바일에서는 질문·답변 아래로 배치됩니다.

- 로그인 직후와 KB 선택 변경 시 자동으로 갱신합니다. 접두사가 아니라 실제 `knowledgeSources` 연결을 따릅니다.
- 모델·검색 생성은 실행하지 않지만 정의 GET 호출은 발생합니다.
- 연결 주소·키·인증·모델 자격 증명은 브라우저에 보내지 않습니다.
- 정의 조회 권한은 retrieve 권한과 다를 수 있습니다. 403이면 권한을 확인하며, 가상의 설명으로 대체하지 않습니다.
- 설명 조회 오류는 오른쪽 패널에 표시하고 질문·답변 영역은 그대로 유지합니다. 패널 갱신은 채팅/모델 호출을 실행하지 않습니다.

## 5. 인증과 필수 조건

**Entra 로그인만으로 Work IQ/Fabric 원본 권한이 생기지는 않습니다.**

| 경계 | 필요한 인증 |
| --- | --- |
| 사용자 → 웹 | 전용 single-tenant Entra 웹 앱의 authorization code + PKCE |
| 웹 → Hosted Agent | 로컬은 Azure CLI 사용자, Container Apps는 Managed Identity. `https://ai.azure.com/.default` |
| Agent → KB | 로그인한 사용자의 Search 토큰 |
| KB → Fabric | 같은 Search 토큰을 `x-ms-query-source-authorization`에 전달 |
| KB → Work IQ | `api://<WORKIQ_APP_ID>/access_as_user` 토큰을 별도 헤더로 전달 |
| Agent → 모델 | Foundry가 제공한 Agent 런타임 자격 증명 |

웹은 Work IQ → Search 순서로 같은 사용자에게 로그인·동의를 받습니다. 사용자 토큰은 서버 메모리의 MSAL 캐시에 보관하고 `x-client-search-authorization`, `x-client-workiq-authorization` 헤더로 Agent에 전달합니다. 질문·모델 입력·브라우저 저장소·평가 로그에는 넣지 않습니다. 브라우저에는 불투명 HttpOnly 세션 ID만 전달합니다.

준비할 항목:

- Python 3.11 이상, Azure CLI와 올바른 워크숍 구독 로그인. 배포 런타임은 Python 3.13입니다.
- 기존 Foundry 프로젝트·모델·공정/품질 KB·7개 KS. 이 데모가 원본 구성을 처음부터 만들지는 않습니다.
- 사용자에게 Search Index Data Reader, 필요한 M365 라이선스·Fabric 원본 접근 권한·위임 동의. 오른쪽 Knowledge Base 패널에는 정의 읽기 권한도 필요합니다.
- 품질 질문용 Fabric capacity **Active** 상태.
- 배포 수행 계정에 리소스·역할 할당 생성과 Entra 앱 설정 권한.
- JavaScript 테스트에는 Node.js 22.7 이상. 웹 실행 자체에는 Node.js가 필요하지 않습니다.

## 6. 로컬 준비·실행

명령은 **저장소 루트**에서 시작합니다. 소스는 `code/`, 가상환경은 상위 `.venv/`, 로컬 설정은 `code/.env`, 로그는 상위 `logs/`에 둡니다. 기존 가상환경은 경로를 옮기지 않고 재사용합니다.

```bash
cd labs/06-hostedagent
python3 -m venv .venv
.venv/bin/python -m pip install -r code/requirements.txt
cd code
test -f .env || cp .env.example .env
chmod 600 .env
```

이미 `.venv`가 준비돼 있으면 생성 단계를 생략하고, 기존 `.env`를 덮어쓰지 않습니다. 구조 정리 시 기존 로컬 설정도 `code/.env`로 이동했습니다. 실제 비밀값은 출력·커밋하지 마세요.

[설정 예제](code/.env.example)는 진행자 검증 환경입니다. 다음 값을 자신의 환경에 맞게 확인합니다.

| 환경 변수 | 용도 |
| --- | --- |
| `TENANT_ID` | 사용자 로그인 테넌트 |
| `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET` | 전용 웹 앱과 비밀값 |
| `WORKIQ_APP_ID` | 기존 Work IQ KS용 API 앱 ID |
| `SEARCH_ENDPOINT` | 기존 KB가 있는 Search 서비스 |
| `FOUNDRY_PROJECT_ENDPOINT` | 기존 Foundry 프로젝트 |
| `HOSTED_AGENT_NAME`, `HOSTED_AGENT_ENDPOINT` | 배포/호출할 Hosted Agent |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | Agent의 최종 스트리밍 모델 |
| `AZURE_SUBSCRIPTION_ID` | 로컬 CLI 및 배포 구독. Container Apps에서는 Managed Identity를 우선 사용 |
| `WEB_ORIGIN` | 로컬 `http://localhost:8000`, 클라우드는 배포된 HTTPS origin |
| `OTEL_SDK_DISABLED` | 검증 구성은 `true`, 요청/토큰 tracing 수집 비활성화 |

Container Apps의 `AZURE_CLIENT_ID`는 배포 identity의 client ID입니다. `QUESTION_SET_PATH`는 컨테이너에 패키징된 질문 JSON 경로이며 로컬 노트북 조회에는 설정하지 않습니다. `SCENARIO_CONTENT_DIR`는 컨테이너의 공개 시나리오 파일 경로로 Dockerfile에서 지정하며, 로컬에서는 00 폴더를 그대로 읽습니다.

### Entra 웹 앱 등록

기존 앱이 있으면 새로 만들지 않습니다. Web redirect URI `http://localhost:8000/auth/callback`, Azure Cognitive Search delegated `user_impersonation`, 기존 Work IQ API의 delegated `access_as_user`와 필요한 동의를 확인합니다.

**새 전용 앱이 필요할 때만**, `code/`에서:

```bash
../.venv/bin/python setup_identity.py
```

같은 이름의 앱·기존 로컬 자격 증명이 있으면 중복 생성하지 않습니다. 비밀키는 30일 만료, `code/.env`에 권한 0600으로만 저장합니다. 생성 이력은 로컬 `logs/identity.json`에 기록하며 기존 Work IQ 앱을 변경하지 않습니다.

### 웹 서버 시작

`code/`에서:

```bash
../.venv/bin/python -m uvicorn web:app --host 127.0.0.1 --port 8000 --no-access-log
```

[localhost:8000](http://localhost:8000)에서 로그인합니다. `--no-access-log`는 callback URL의 authorization code가 접근 로그에 남지 않게 합니다. 로그인 세션은 최대 1시간, 미완료 로그인은 10분이며 서버 재시작 시 재로그인합니다.

## 7. Agent 배포와 웹 배포

**두 배포는 별개입니다.** 아래 명령은 모두 `code/`에서 실행하며 Azure 리소스 변경·과금이 발생합니다.

### Microsoft Foundry Hosted Agent

```bash
../.venv/bin/python deploy.py
```

- 공식 `azure-ai-projects` SDK로 기존 프로젝트에 새 Agent 버전을 만듭니다.
- Agent 코드와 05의 기존 trace 파서를 ZIP에 포함합니다. `.env`·노트북 출력·평가 로그는 제외합니다.
- `active`와 다운로드 ZIP 해시 일치를 확인합니다. 결과는 로컬 `logs/deployment.json`에 기록합니다.
- Foundry/Search/모델을 새로 만들지 않습니다. 검증 환경의 azd 기본 계정 불일치 때문에, 공유 기본 계정은 바꾸지 않고 구독을 지정한 SDK 경로를 사용합니다.

### Azure Container Apps 웹

```bash
../.venv/bin/python deploy_web.py
```

foundation what-if/배포 → ACR 원격 빌드 → 웹 what-if/배포 → **새 이미지의 Ready revision 확인** → Entra HTTPS callback 추가 → `/healthz`와 **정적 파일·시나리오 원본·도식의 빌드 context 일치** 확인 순서입니다. 기존 revision의 health 응답만으로 새 버전 배포 성공으로 보지 않습니다. 재배포도 같은 명령입니다. 로컬 Docker 설치는 필요하지 않습니다.

2026-10-03 20:05(KST)의 **과거 배포 기록**은 `ca-iq-demo-web--0000011` Ready, 정적 파일·시나리오 원본·도식 일치를 확인했습니다. 당시 revision에는 상단 GitHub/시나리오 링크와 MES 소개·링크가 포함됐습니다. **재배포하면 revision이 바뀌므로 이 번호를 현재 배포 버전으로 사용하지 마세요.** 이는 당시 웹 배포 검증이며 새 질문 4개의 KB·모델 호출 성공 또는 현재 Fabric 상태를 뜻하지 않습니다.

**이미 등록한 동일 URL·동일 Entra 앱의 소스만 재배포**하는 경우에는 다음 명령으로 기존 앱 등록을 건드리지 않을 수 있습니다. 이 옵션은 Graph 조회·변경을 하지 않으며, 신규 URL/앱 최초 배포에는 사용하지 않습니다. 실행 후 실제 브라우저 로그인을 확인합니다.

```bash
../.venv/bin/python deploy_web.py --skip-entra-update
```

| 리소스 | 현재 구성 |
| --- | --- |
| 구독 / 리소스 그룹 | `8ed5b21b-07a5-4a49-a2a6-0f09bb704ca3` / `rg-microsoft-iq-series` |
| 웹 / 환경 | `ca-iq-demo-web` / `cae-iq-demo-eus2`, East US 2 |
| 웹 실행 | Consumption 0.5 vCPU / 1 GiB, replica 1·worker 1, single revision |
| ACR | `acriqdemo8ed5b21b`, Basic, East US, admin 계정 비활성화 |
| Identity | `id-iq-demo-web`, East US. 전용 ACR의 AcrPull + 기존 Foundry 프로젝트의 Foundry User |

최초 East US 환경은 용량 부족으로 실패해 웹만 East US 2로 전환했습니다. 기존 ACR·identity는 재사용하고 실패한 환경만 삭제했습니다.

[Dockerfile](code/Dockerfile)과 [allowlist](code/.dockerignore)를 사용하며, [배포 스크립트](code/deploy_web.py)가 웹 파일·추출한 질문 JSON·00 공개 README·SVG 도식 2개를 담은 임시 context를 만듭니다. **노트북 원본·저장 출력·`.env`·로그·Agent 서버 코드는 이미지에 넣지 않습니다.** 소스 폴더에서 직접 `docker build .`를 하는 대신 위 스크립트를 사용합니다.

컨테이너는 non-root, HTTPS only, readiness/liveness probe, Secure 세션 쿠키·HSTS로 실행됩니다. Entra 비밀값은 secure ARM parameter → Container Apps secret → `secretRef`로 주입합니다. 기존 localhost callback은 보존하고 배포 HTTPS callback만 추가합니다.

위 배포 이름과 리소스는 진행자 환경의 값입니다. 다른 환경에 배포할 때는 설정 예제뿐 아니라 [배포 스크립트의 대상 이름](code/deploy_web.py)과 [Bicep 기본값](code/infra/foundation.bicep)도 검토하세요. 테스트 명령은 리소스를 생성하지 않으며, 배포 명령은 Azure 리소스를 변경합니다.

## 8. 테스트·로그·결과 해석

### 비용 없는 로컬 검증

`code/`에서:

```bash
OTEL_SDK_DISABLED=true ../.venv/bin/python -m unittest discover -s tests -v
npm test
../.venv/bin/python -m pip check
```

고정 버전 Markdown 브라우저 번들 [static/markdown-it.js](code/static/markdown-it.js)는 소스와 함께 제공하므로 일반 웹 실행·Docker 배포 시 Node.js나 외부 CDN이 필요하지 않습니다. 파서 버전을 갱신하거나 번들을 재생성할 때만 `code/`에서 다음을 실행합니다.

```bash
npm ci --ignore-scripts
npm run build
npm test
```

생성 파일에는 라이브러리의 MIT 라이선스를 포함합니다. `node_modules/`는 git과 컨테이너 context에서 제외합니다.

잠금 파일은 버전·무결성 값을 유지하되 특정 조직의 패키지 미러 URL을 저장하지 않습니다. `npm ci`는 각 개발자의 npm registry 설정을 사용합니다.

### 원격 Hosted Agent 회귀

```bash
# 현재 노트북 질문 4개, 기본 Medium: Hosted Agent 호출 4회
../.venv/bin/python evaluate.py
# 현재 노트북 질문 4개 × Low/Medium: Hosted Agent 호출 8회
../.venv/bin/python evaluate.py --efforts low medium --output ../logs/reasoning-comparison.json
```

명령은 앞 절과 같이 **`code/`에서** 실행합니다. 이는 **유료 실환경 호출**이며 CLI 사용자 위임 토큰을 사용합니다. 브라우저 로그인 테스트를 대신하지 않습니다. 작성 중인 공정 질문도 자동 포함하므로 먼저 원문을 검토하세요. 출력 상대 경로는 실행 위치와 무관하게 `code/` 기준이며, 기본 출력은 `../logs/evaluation.json`입니다. 재실행하면 지정한 로그 파일을 갱신하므로 이전 결과를 보존하려면 새 파일명을 지정하세요.

Agent/웹 배포·앱 등록 스크립트도 상위 `logs/`를 자동 생성해 결과를 기록합니다. **새로 clone한 저장소에는 과거 로그가 없어도 됩니다.** 실행 결과는 Git에서 제외하며, 공유하려면 토큰·원문·식별자를 검토해 별도 전달하세요.

진행자 환경에서는 로그인 전 데이터 API의 401, 실제 Entra 로그인, Markdown·인용·디버그·Knowledge Base 패널, 약 219초의 스트림 완료를 확인했습니다. Low에서는 일부 소스를 선택하지 않아 부분 확인이 된 실행도 있었습니다. 이 이력은 새 환경에서의 성공이나 답변의 정답을 보증하지 않으므로 자신의 실행 결과로 판단합니다.

이번 문서 점검은 현재 소스·노트북 질문·기존 배포 기록을 대조하는 로컬 검증입니다. 과거 로그인·스트리밍 결과를 재실행하지 않았으며, 현재 질문 4개 전체의 원격 성공을 주장하지 않습니다. 로컬 모의 테스트 통과도 실제 Entra 동의·KS 권한·원본 데이터·Fabric capacity 가용성을 대신 검증하지 않습니다.

**HTTP 200·reference 반환·인용 연결은 업무 정답을 보증하지 않습니다.** “검색 결과 없음”도 reference로 반환될 수 있습니다. 실제 Work IQ 조회에서 지정 메일을 찾지 못한 사례가 있으므로 요청·결정·담당자를 미확인으로 남깁니다. 근거 누락·HTTP 206·소스 오류·미해결 인용을 성공으로 바꾸지 않습니다.

LOT0012 질문은 조건부 조사입니다. 현재 자동 소스 검사는 3개 소스의 reference·인용을 기준으로 하므로, 이슈가 없어 후속 소스를 조회하지 않은 정상적인 분기도 “부분 확인”으로 표시될 수 있습니다. 이 표시는 기술적 소스 충족 여부이며, 실제 질문 해결 여부는 조건과 답변을 함께 검토합니다. 과거 CMP 질문의 로그를 새 질문의 검증 결과로 해석하지 않습니다.

## 9. 운영·비용·정리

- **웹은 계속 실행 중**입니다. 메모리 세션이므로 revision 교체·재시작 시 재로그인합니다. replica/worker를 늘리려면 공유 세션 저장소가 필요합니다.
- Container Apps 기본 HTTP ingress timeout은 **240초**입니다. 약 219초 요청은 검증했지만 240초 초과 동작은 보장하지 않습니다. heartbeat가 전체 요청 제한을 해제한다고 가정하지 않습니다.
- 웹 compute + Basic ACR은 730시간·무료 제공량 적용 전 단순 추정으로 월 약 **US$17~45**입니다. 모델·Foundry·Fabric·전송·빌드 비용은 별도입니다.
- Entra 앱 비밀키는 **2026-11-01 12:27 UTC(21:27 KST) 만료**입니다. 만료 전에 안전하게 갱신하고 웹을 재배포합니다. 실제 값은 문서·명령줄에 출력하지 마세요.
- 품질 데모 전에 Fabric을 재개하고 종료 후 기존 운영 정책에 따라 중지합니다. 웹 실행과 Fabric 상태는 별개입니다.
- 브라우저 중지는 연결을 취소하지만, 이미 진행 중인 원본 검색과 과금까지 즉시 취소된다고 보장하지 않습니다.
- 로그아웃/서버 종료는 앱 메모리의 토큰·세션을 제거합니다. Entra SSO 브라우저 쿠키 전체를 로그아웃시키지는 않습니다.
- 데모 종료 후 Foundry 포털에서 **`iq-workshop-demo`의 테스트 세션만** 중지합니다. Agent 정의·KB·KS·모델은 재사용할 수 있습니다.

### 웹 리소스만 정리

**공유 리소스 그룹 전체를 삭제하지 마세요.** 원본 Foundry·Search·Storage도 들어 있습니다. 아래 명령은 웹이 더 이상 필요 없을 때만 실행합니다.

```bash
SUBSCRIPTION=8ed5b21b-07a5-4a49-a2a6-0f09bb704ca3
GROUP=rg-microsoft-iq-series
az containerapp delete --subscription "$SUBSCRIPTION" -g "$GROUP" -n ca-iq-demo-web --yes
az containerapp env delete --subscription "$SUBSCRIPTION" -g "$GROUP" -n cae-iq-demo-eus2 --yes
az acr delete --subscription "$SUBSCRIPTION" -g "$GROUP" -n acriqdemo8ed5b21b --yes
```

이후 `id-iq-demo-web`의 프로젝트 범위 역할 할당을 확인해 제거하고 해당 identity만 삭제합니다. Entra 앱의 HTTPS callback만 제거하면 로컬 데모는 유지할 수 있습니다. 로컬 데모도 폐기할 때는 자신이 생성한 로컬 `logs/identity.json` 또는 Entra 포털에서 **전용 웹 앱**의 ID를 확인하고 앱과 `code/.env`를 정리합니다. 기존 Work IQ 앱·Foundry Agent·KB·KS는 삭제하지 않습니다.

운영 수준의 다중 사용자 부하·고가용성·종합 보안 검증·자동 업무 승인은 범위 밖입니다. 이 폴더는 워크숍 결과를 설명하기 위한 단일 replica POC입니다.

## 공식 자료

- [Hosted agents](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents)
- [Hosted Agent 소스 코드 배포](https://learn.microsoft.com/azure/foundry/agents/how-to/deploy-hosted-agent-code)
- [Work IQ knowledge source](https://learn.microsoft.com/azure/search/agentic-knowledge-source-how-to-work-iq)
- [Retrieve API](https://learn.microsoft.com/rest/api/searchservice/knowledge-retrieval/retrieve?view=rest-searchservice-2026-08-01-preview)
- [검색 추론 강도와 요청별 override](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-set-retrieval-reasoning-effort)
- [Container Apps ingress](https://learn.microsoft.com/azure/container-apps/ingress-overview)
