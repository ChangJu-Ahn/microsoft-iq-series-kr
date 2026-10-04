# Microsoft IQ Series 한국어 실습

> **[Foundry IQ · Hosted Agent 데모 열기 ↗](https://ca-iq-demo-web.agreeabledune-2db01c8e.eastus2.azurecontainerapps.io/)** · **[CJ 전자 시나리오 먼저 보기 ↗](https://ca-iq-demo-web.agreeabledune-2db01c8e.eastus2.azurecontainerapps.io/scenario)**
>
> 완성된 서비스 흐름을 확인하는 발표자용 참고 데모입니다. 시나리오는 로그인 없이 볼 수 있으며, 질문하려면 원본 데이터 접근 권한이 있는 워크숍 계정으로 Entra ID 로그인이 필요합니다. 참가자 실습은 05 Foundry IQ의 API 테스트까지입니다.

가상 고객 **CJ전자 반도체 사업부**의 품질·설비·출하 판단 문제를 다루는 한국어 FDE 워크숍입니다. 제품 기능 나열이 아니라 고객의 질문을 정의하고, 기술로 근거를 확보해 해결 범위와 남은 불확실성을 검증합니다.

반도체 제조 시나리오의 MES(생산)·QMS(품질)·FDC(설비 센서) 데이터를 사용합니다. **01은 공통 업무 이해, 02~04는 독립적인 업무 시나리오, 05는 공정·품질 두 Knowledge Base에서 여러 원본 지식원을 조회·결합하는 통합 실습**입니다. 앞 노트북의 답변을 다음 노트북으로 전달하는 구조는 아닙니다.

## 시작하기

1. [00 고객 문제 브리프](labs/00-getting-started/README.md)에서 고객 상황·비용 압력·워크숍의 평가 기준을 확인합니다.
2. 각 랩의 메인 README에서 **업무 질문·수행 내용·산출물·해결 범위와 한계**를 먼저 읽고 실행 자료로 이동합니다.
3. [01 사내 시스템](labs/01-inhouse-system/README.md) → [02 Fabric IQ](labs/02-fabric-iq/README.md) → [03 Web IQ](labs/03-web-iq/README.md) → [04 Work IQ](labs/04-work-iq/README.md) → [05 Foundry IQ](labs/05-foundry-iq/README.md) 순서로 진행합니다.

참가자는 각자의 계정·리소스 그룹·실습 환경을 구축하는 것을 원칙으로 합니다. Web IQ만 진행자가 사용 허용된 실습 키를 제공하며 포털 접근·키 발급을 참가자에게 전제하지 않습니다. Foundry IQ의 새 리소스 구축은 [실제 화면을 따라 하는 실습 가이드](labs/05-foundry-iq/README.md)를 따릅니다. Web IQ를 포함한 기존 운영 KB와 질문 목록은 [발표자용 Hosted Agent 참고](labs/06-hostedagent/README.md#발표자용-기존-kb-구성)로 구분합니다.

실행 전 해당 실습의 계정·권한·용량·비용 조건을 확인하세요. 제공된 Mock MES 주소와 이력을 사용하고, 실제 인증키는 공유·커밋하지 않습니다. 실습 후에는 세션·예약·유료 리소스를 확인해 정리합니다.

## 실습 구성

| 순서 | 실습 | 현재 안내 |
| --- | --- | --- |
| 00 | [고객 문제 브리프](labs/00-getting-started/README.md) | 분산된 근거·불확실성·비용 압력과 FDE 접근 |
| 01 | [사내 제조 시스템](labs/01-inhouse-system/README.md) | 질문별 원장과 로트·공정·설비·시간 연결 조건 |
| 02 | [Fabric IQ](labs/02-fabric-iq/README.md) | 운영 데이터로 품질·비용·설비·측정 문제 조사 |
| 03 | [Microsoft Web IQ](labs/03-web-iq/README.md) | 제공 키로 공개 정보의 내용·출처 확인 |
| 04 | [Work IQ](labs/04-work-iq/README.md) | 협업 요청·보충 의견과 추가 운영 질문 구분 |
| 05 | [Foundry IQ](labs/05-foundry-iq/README.md) | 화면을 따라 KB·KS 신규 구축, 사용자 헤더로 API 근거 검증 |
| 참고 | [Hosted Agent 웹 데모](labs/06-hostedagent/README.md) | 발표자용 Entra ID 로그인·스트리밍·Foundry IQ 실행 기록. 참가자 실습 아님 |

개별 랩은 자신의 업무 질문에 답했는지, Foundry 랩은 근거를 결합해 추가로 무엇을 확인했는지 평가합니다. 검증된 호출 범위와 미검증 분석·신규 구축 범위는 각 안내에서 구분합니다.

## 디렉터리 구조

```text
MicrosoftIQSeries-KR/
|-- README.md
|-- .github/
|   |-- copilot-instructions.md  # 레포 공통 지침
|   `-- instructions/           # 실습 코드 및 문서별 지침
|-- labs/
|   |-- 00-getting-started/      # 고객 문제와 워크숍 흐름
|   |-- 01-inhouse-system/      # 사내 제조 시스템과 데이터 설명
|   |-- 02-fabric-iq/
|   |   |-- helper-new/        # 현재 Fabric 실습 파일
|   |   `-- helper-old/        # 이전 실습 파일 보관
|   |-- 03-web-iq/             # Microsoft Web IQ 개별 실습
|   |-- 04-work-iq/            # Work IQ 개별 실습
|   |-- 05-foundry-iq/         # 앞선 IQ들을 연결하는 Foundry IQ 데모
|   `-- 06-hostedagent/        # 발표자용 Hosted Agent 웹 데모 (참가자 실습 아님)
`-- assets/                     # 문서용 이미지와 다이어그램
```

## 콘텐츠 배치

- 폴더명은 영문으로, 실습 설명은 한국어로 작성합니다.
- 각 실습의 안내는 해당 폴더의 README에 작성하고, 코드와 설정은 해당 실습 폴더에 둡니다. Fabric 실습은 현재 `helper-new`를 사용합니다.
- 현재 실행 절차와 검증 범위는 각 랩 README를 따릅니다. 로컬 계획·작업 기록은 공개 실습 자료에 포함하지 않습니다.
- 실습 데이터는 각 랩이 안내하는 원본·노트북·데이터 폴더를 사용합니다.
- 화면 캡처는 루트 `assets/`의 실습별 폴더에 둡니다. Fabric IQ·Web IQ·Foundry IQ는 각각 `assets/fabric-iq/`, `assets/web-iq/`, `assets/foundry-iq/`를 사용합니다.
- 실행·검증의 확인 범위와 한계는 해당 실습 안내에 기록합니다. 상세 실행 로그는 각 실습의 로컬 폴더에 보관하고 Git에서 제외합니다.

## Copilot 커스텀 지침

워크숍 및 핸즈온 코드와 샘플은 학습 목표에 필요한 최소 구현으로 작성합니다.

- [레포 공통 지침](.github/copilot-instructions.md)
- [실습 코드 및 샘플 지침](.github/instructions/workshop-samples.instructions.md)
- [한국어 실습 문서 지침](.github/instructions/workshop-docs.instructions.md)