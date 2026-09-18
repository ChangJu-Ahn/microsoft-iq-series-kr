# Microsoft IQ Series 한국어 실습

WorkIQ, Foundry IQ, Fabric IQ, WebIQ를 각각 시나리오별로 실습하고, 마지막에 네 IQ를 하나의 시나리오로 통합하는 한국어 레포입니다.

현재는 디렉터리 구조만 준비되어 있으며, 실습 콘텐츠와 실행 코드는 추후 추가합니다.

## 실습 구성

| 구분 | 디렉터리 |
| --- | --- |
| 환경 준비 | [00-getting-started](labs/00-getting-started/README.md) |
| WorkIQ | [01-work-iq](labs/01-work-iq/README.md) |
| Foundry IQ | [02-foundry-iq](labs/02-foundry-iq/README.md) |
| Fabric IQ | [03-fabric-iq](labs/03-fabric-iq/README.md) |
| WebIQ | [04-web-iq](labs/04-web-iq/README.md) |
| 네 IQ 통합 | [05-capstone](labs/05-capstone/README.md) |

## 디렉터리 구조

```text
MicrosoftIQSeries-KR/
|-- README.md
|-- .github/
|   |-- copilot-instructions.md  # 레포 공통 지침
|   `-- instructions/           # 실습 코드 및 문서별 지침
|-- docs/                       # 공통 문서
|-- labs/
|   |-- 00-getting-started/      # 공통 환경 준비
|   |-- 01-work-iq/             # WorkIQ 시나리오별 실습
|   |-- 02-foundry-iq/          # Foundry IQ 시나리오별 실습
|   |-- 03-fabric-iq/           # Fabric IQ 시나리오별 실습
|   |-- 04-web-iq/              # WebIQ 시나리오별 실습
|   `-- 05-capstone/            # 네 IQ 통합 실습
|-- datasets/                   # 실습 데이터
|-- shared/
|   `-- contracts/              # 통합 시 사용하는 입출력 규약
`-- assets/                     # 문서용 이미지와 다이어그램
```

## 콘텐츠 배치

- 폴더명은 영문으로, 실습 설명은 한국어로 작성합니다.
- 각 IQ 폴더 아래에 `01-<scenario-name>`, `02-<scenario-name>` 형태로 시나리오를 추가합니다.
- 각 시나리오의 안내는 해당 폴더의 README에 작성하고, 코드와 설정은 해당 실습 폴더에 둡니다.
- 공통 문서는 `docs/`, 실습 데이터는 `datasets/`, 여러 실습에서 재사용하는 코드는 `shared/`에 둡니다.
- 문서용 이미지는 `assets/`에 둡니다.
- 시나리오, 기술 스택, 실행 방식은 콘텐츠를 추가할 때 정합니다.

## Copilot 커스텀 지침

워크숍 및 핸즈온 코드와 샘플은 학습 목표에 필요한 최소 구현으로 작성합니다.

- [레포 공통 지침](.github/copilot-instructions.md)
- [실습 코드 및 샘플 지침](.github/instructions/workshop-samples.instructions.md)
- [한국어 실습 문서 지침](.github/instructions/workshop-docs.instructions.md)