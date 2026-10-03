# 보관 기록: MES Lakehouse MCP 노트북 + REST Pipeline

> **현재 참가자 실행 가이드가 아닙니다.** 현재 구성은 [helper-new 가이드](../../helper-new/README.md)의 단일 `factory_lakehouse`이며 REST Pipeline이 필요하지 않습니다. 이 폴더에는 [MES 컨텍스트 노트북](mes_lakehouse_context.ipynb)만 남아 있습니다. 아래 ZIP·Pipeline JSON·별도 원본 노트북·검증 스크립트는 현재 저장소에 없으므로 이 절차 전체를 재현할 수 없습니다.

이 문서는 2026-09-10의 Import·Validate 기록과 이후 사용자 실행 실패를 보존합니다. 당시 Copy 활동은 오류 `2015: The datasource type RestService is invalid`로 실패했습니다. Import·Validate 통과를 런타임 성공으로 해석하지 않습니다. 보관된 노트북에도 실행 출력이 없으며 이번 문서 점검에서는 원격 실행을 하지 않았습니다.

<details>
<summary>당시 절차·오류 대응·예상 스키마 (실행 안내로 사용하지 않음)</summary>

## 오류 2015 발생 시

오류는 `RestService` 데이터소스 형식이 거부됐음을 나타냅니다. 아래는 당시 제안한 수동 재연결 절차이며 성공이 확인된 해결책은 아닙니다. 오류만으로 MES 키나 대상 Lakehouse 문제를 확정하지 않습니다.

1. 기존 Pipeline의 `Copy_MES_Product`를 선택하고 **Source → Connection**에서 직접 만든 REST 클라우드 연결(예: `MES`)을 선택합니다. 목록에 없으면 Refresh 또는 Browse all로 찾습니다. `MesConnectionId` 값만 바꾸는 것으로는 기존 인라인 정의가 제거되지 않습니다.
2. Relative URL이 `api/products`, Request method가 `GET`, Additional headers의 `X-API-Key`가 동적 식 `@pipeline().parameters.MesKey`인지 확인합니다. 연결을 바꾸면서 설정이 초기화되었다면 복원합니다.
3. `Copy_MES_Material`, `Copy_MES_BOM`에도 같은 연결을 선택하고 Relative URL을 각각 `api/materials`, `api/bom`으로 유지합니다. Destination과 Mapping도 기존 값이 유지되는지 확인합니다.
4. Save 후 실행하여 각 활동의 Error와 적재 결과를 확인합니다. 이 수동 재연결 절차의 실제 성공 여부는 아직 미확인입니다. 계속 실패하면 실패 활동의 오류 코드·메시지를 확인하며, 키가 포함된 입력 전체를 공유하지 않습니다.

당시 설계는 Mock MES를 조회하여 같은 MES Lakehouse에 컨텍스트와 마스터 데이터를 저장하는 **노트북 하나와 Pipeline ZIP 하나**였습니다. Dataflow Gen2나 별도 데이터 파일 업로드를 쓰지 않는 설계였지만 Pipeline 적재 성공은 확인되지 않았습니다.

## 파일과 역할

| 파일 | 역할 |
|---|---|
| [mes_lakehouse_context.ipynb](mes_lakehouse_context.ipynb) | MCP로 LOT·공정 이력·설비 컨텍스트 수집 |
| `mes_context_pipeline.zip` (현재 없음) | 당시 REST Copy 활동 3개로 제품·자재·BOM 수집 예정 |
| `mes_lakehouse_context_old.ipynb` (현재 없음) | 당시 변경 전 원본 비교용 |
| `mes_context_pipeline/mes_context_pipeline.json` (현재 없음) | 당시 ZIP의 수정 가능한 Pipeline 정의 |
| `verify-package.mjs` (현재 없음) | 당시 작성자용 정적 검증 |

당시 문서는 원본과 새 노트북의 코드 셀이 같았고, Dataflow 호출용 ZIP을 REST Copy용으로 교체했다고 기록했습니다. 비교 원본과 ZIP이 현재 없으므로 그 동일성과 패키지 내용은 이번 점검에서 재검증하지 못했습니다.

## 사전 준비

- Fabric 용량이 연결된 작업 영역과 Notebook/Spark 및 Pipeline 실행 권한이 필요합니다. Spark와 Copy 실행에는 Fabric 용량이 사용됩니다.
- **Lakehouse schemas가 활성화된 MES 전용 Lakehouse**와 해당 Lakehouse 쓰기 권한이 필요합니다. QMS Lakehouse를 대상에 넣지 마세요.
- 실습용 MES 키와 공개 MES 주소에 대한 네트워크 접근이 필요합니다.
- 기본 MES 주소: `https://mock-mes.greenrock-bb44c93a.koreacentral.azurecontainerapps.io/`

## 1. MCP 노트북 실행

1. [노트북](mes_lakehouse_context.ipynb)을 본인 작업 영역에 Import합니다.
2. MES Lakehouse를 기본 Lakehouse로 Attach합니다.
3. 설정 셀의 `MES_KEY_INPUT`에 실습 키를 입력하고 셀을 순서대로 실행합니다.
4. `dbo.mes_equipment`, `dbo.mes_lot`, `dbo.mes_process_result`가 생성됐는지 확인합니다.

기존 스키마, MCP 호출, 원본 검증과 과거 이력 보호 동작을 유지합니다. 이 노트북은 아래 REST 테이블에 쓰지 않습니다.

## 2. REST 연결 한 번 만들기

Fabric의 **Settings → Manage connections and gateways → New**에서 클라우드 연결을 만듭니다.

| 설정 | 값 |
|---|---|
| Connection name | `mes_rest` 등 본인이 구분할 이름 |
| Connection type | `REST` |
| Base URL | 위 기본 MES 주소. 끝의 `/` 포함 |
| Authentication kind | `Anonymous` |
| Gateway | 공개 MES를 사용한다면 별도 게이트웨이 불필요 |

MES 인증은 Copy 활동이 `X-API-Key` 헤더로 전달합니다. Anonymous는 인증이 없는 MES라는 뜻이 아닙니다. 연결을 만든 뒤 연결 설정의 **Connection ID**를 확인합니다. 연결 이름이 아니라 ID가 필요하며, 실행하는 사용자가 이 연결을 사용할 권한이 있어야 합니다.

## 3. Pipeline ZIP 가져오기 및 실행

1. 작업 영역에서 **New item → Pipeline**을 만듭니다.
2. **Home → Import**에서 당시의 `mes_context_pipeline.zip`을 선택하고 **Use this template**을 누르는 절차였습니다. 현재 ZIP은 제공되지 않습니다. 당시 안내는 압축을 풀지 않고 빈 Pipeline을 사용하도록 했습니다.
3. 빈 캔버스 영역을 선택하고 아래 **Parameters**에서 다음 네 값을 설정합니다. API 경로·매핑·테이블명은 이미 들어 있으므로 Copy 활동을 개별 작성하지 않습니다.

| 매개변수 | 입력값 |
|---|---|
| `MesConnectionId` | 2단계에서 만든 REST 연결의 Connection ID |
| `MesKey` | 노트북과 같은 실습 MES 키 |
| `WorkspaceId` | MES Lakehouse가 있는 작업 영역 ID |
| `LakehouseId` | 노트북에 Attach한 MES Lakehouse ID |

Lakehouse 화면 URL의 `/groups/{WorkspaceId}/lakehouses/{LakehouseId}`에서 두 ID를 확인할 수 있습니다. SQL analytics endpoint ID를 넣지 마세요.

4. **Validate → Save → Run**을 실행합니다. 키는 가능하면 기본값에 저장하지 말고 Run의 매개변수 입력에서 전달합니다.
5. `Copy_MES_Product`, `Copy_MES_Material`, `Copy_MES_BOM` 모두 **Succeeded**인지 확인합니다.

> 당시 `MesKey`는 일반 문자열 매개변수였고 Secure input/output을 사용했다고 기록했습니다. 이는 Pipeline 매개변수·실행 이력·저장된 정의의 비밀값 보관을 보장하지 않습니다. 노트북의 `MES_KEY_INPUT`도 소스에 저장되므로 실습 전용 키만 사용하고 공유 전 소스·출력을 확인합니다. 현재 없는 ZIP의 비밀값 제거 상태는 확인할 수 없습니다.

별도 MES 서버를 사용한다면 REST 연결의 Base URL, Pipeline 정의의 `MES_REST` URL 및 노트북의 `MES_BASE_URL`을 동일한 서버로 맞춥니다.

## 당시 예상 결과 (REST 적재 미검증)

| 담당 | 테이블 | 컬럼 |
|---|---|---|
| Notebook | `mes_equipment` | `eqp_id`, `eqp_type` |
| Notebook | `mes_lot` | `lot_id`, `product_code` |
| Notebook | `mes_process_result` | `id`, `lot_id`, `eqp_id`, `step_code`, `in_time`, `out_time` |
| Pipeline | `mes_product` | `product_code`, `product_name`, `tech_node` |
| Pipeline | `mes_material` | `material_code`, `material_name`, `category`, `qty`, `uom`, `location` |
| Pipeline | `mes_bom` | `id`, `product_code`, `step_code`, `step_name`, `material_code`, `material_name`, `qty_per_wafer`, `uom` |

보관된 노트북은 앞의 MES 컨텍스트 3개 테이블만 `dbo`에 저장합니다. 나머지 REST 테이블과 타입은 당시 Pipeline 설계 기록입니다. REST의 `qty`와 `qty_per_wafer`는 DOUBLE, BOM의 `id`는 BIGINT, 나머지 REST 컬럼은 STRING으로 설계됐습니다. 행수·API 응답 계약·REST 적재 여부는 이번 점검에서 확인하지 않았습니다. 아래 SQL은 REST 테이블까지 존재할 때의 당시 대조 예시이며 현재 노트북만 실행해서는 모두 조회할 수 없습니다.

Lakehouse SQL analytics endpoint에서 동기화 후 다음을 실행합니다. 테이블이 바로 보이지 않으면 동기화 완료 후 다시 확인합니다.

```sql
SELECT 'mes_equipment' AS table_name, COUNT(*) AS row_count FROM dbo.mes_equipment
UNION ALL SELECT 'mes_lot', COUNT(*) FROM dbo.mes_lot
UNION ALL SELECT 'mes_process_result', COUNT(*) FROM dbo.mes_process_result
UNION ALL SELECT 'mes_product', COUNT(*) FROM dbo.mes_product
UNION ALL SELECT 'mes_material', COUNT(*) FROM dbo.mes_material
UNION ALL SELECT 'mes_bom', COUNT(*) FROM dbo.mes_bom;

SELECT COUNT(*) AS missing_product_count
FROM dbo.mes_lot AS lot
LEFT JOIN dbo.mes_product AS product ON lot.product_code = product.product_code
WHERE product.product_code IS NULL;

SELECT COUNT(*) AS missing_material_count
FROM dbo.mes_bom AS bom
LEFT JOIN dbo.mes_material AS material ON bom.material_code = material.material_code
WHERE material.material_code IS NULL;
```

조회 결과가 비어 있거나 참조 누락 건수가 0이 아니면 원본 MES의 데이터와 두 수집 시점을 확인합니다. 가짜 레코드를 만들어 맞추지 않습니다. 추가 마스터는 `mes_lot.product_code → mes_product.product_code → mes_bom.product_code → mes_material.material_code`로 연결할 수 있습니다. 기존 온톨로지에 이 세 테이블을 자동 등록하지는 않습니다.

## 재실행과 주의사항

- Pipeline은 **해당 REST 테이블 3개를 Overwrite**합니다. Append가 아니므로 같은 데이터로 재실행해도 행이 계속 쌓이지 않습니다. 원본에서 삭제된 행은 대상에서도 없어집니다.
- Copy 활동 3개는 독립적으로 실행되며 공통 트랜잭션이 아닙니다. 일부 실패 시 테이블별 갱신 시점이 달라질 수 있습니다. 오류를 해결하고 Pipeline 전체를 다시 실행합니다. 동일 Pipeline의 동시 실행은 피합니다.
- 원본이 수집 중 바뀌면 노트북과 REST 테이블 간 시점도 달라질 수 있습니다. 실습 중 MES 변경을 멈추고 실행합니다.
- Pipeline은 노트북의 스냅샷 비교·기존 이력 보호 검사를 대체하지 않습니다. REST 마스터 원본의 키 유일성이나 참조 무결성을 Copy 자체가 보장하지 않습니다.
- HTTP 401/403이면 실습 키와 접근 권한을, 연결 오류면 REST Connection ID와 사용 권한을, 적재 오류면 작업 영역·Lakehouse ID와 쓰기 권한을 확인합니다. 실패를 성공으로 처리하지 않습니다.

## 검증 범위와 정리

2026-09-10 작성 시 원본과 새 노트북의 코드 셀 동일성, REST 경로·컬럼 매핑·대상 테이블, ZIP 내용 일치와 압축 무결성을 검사했습니다. **Fabric Import 후 Copy 활동 3개와 매개변수를 확인했고, Validate에서 No errors were found를 확인했습니다.**

**당시 작성 시점에는 실제 키를 사용한 Notebook/Copy 실행과 저장값 대조가 미실행이었고, 이후 사용자 Copy 실행은 위 오류로 실패했습니다.** 수동 재연결 후 성공 여부, Notebook 적재 및 행수·참조 관계는 이 문서의 기록만으로 확인되지 않습니다. Import/Validate 성공을 데이터 적재 성공으로 해석하지 않습니다.

실습이 끝나고 후속 온톨로지 실습에서 더 이상 사용하지 않으면 본인이 만든 Pipeline·노트북·MES Lakehouse를 삭제합니다. 다른 실습이 사용하지 않는 REST 연결만 제거합니다. QMS/FDC 또는 공용 MES 리소스는 삭제하지 않습니다.

당시 작성자용 정적 검사는 Node.js와 `unzip`을 사용했으나 `verify-package.mjs`와 ZIP이 없어 현재 실행 명령으로 제공하지 않습니다. 현재 노트북과 보관본의 로컬 회귀 비교는 [helper-new의 검사 안내](../../helper-new/README.md#코드-구조와-로컬-회귀-확인)를 참고합니다. 이 비교도 옛 Pipeline 런타임 검증을 대신하지 않습니다.

참고: [REST Copy](https://learn.microsoft.com/en-us/fabric/data-factory/connector-rest-copy-activity), [Lakehouse Copy](https://learn.microsoft.com/en-us/fabric/data-factory/connector-lakehouse-copy-activity), [MES API 명세](https://mock-mes.greenrock-bb44c93a.koreacentral.azurecontainerapps.io/api/openapi.json).

</details>