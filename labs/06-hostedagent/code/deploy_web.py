"""웹 전용 컨테이너를 빌드하고 기존 워크숍 리소스 그룹에 배포합니다."""

from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from azure.identity import AzureCliCredential
from dotenv import dotenv_values
import httpx

from questions import load_questions

ROOT = Path(__file__).resolve().parent
RESOURCE_GROUP = "rg-microsoft-iq-series"
REGISTRY = "acriqdemo8ed5b21b"
APP_NAME = "ca-iq-demo-web"


def wait_for_revision(read_state, expected_image: str) -> str:
    previous = None
    for _ in range(120):
        state = read_state()
        if state["state"] == "Failed":
            raise RuntimeError("Container App revision 배포가 실패했습니다.")
        if state["image"] != expected_image:
            raise RuntimeError("다른 이미지가 배포 대상으로 설정됐습니다. 동시 배포를 확인하세요.")
        if state["latest"] and state["latest"] == state["ready"]:
            return state["ready"]
        status = (state["latest"], state["ready"])
        if status != previous:
            print(f"revision 준비 대기: latest={status[0]} ready={status[1]}", flush=True)
            previous = status
        time.sleep(5)
    raise TimeoutError("새 이미지의 revision이 10분 안에 Ready가 되지 않았습니다. 기존 health 응답을 배포 성공으로 보지 않습니다.")


def build_context(target: Path) -> str:
    files = ["Dockerfile", ".dockerignore", "requirements-web.txt", "web.py", "catalog.py", "questions.py",
             "agent/retrieval.py"]
    files += [str(path.relative_to(ROOT)) for path in sorted((ROOT / "static").iterdir())
              if path.suffix in {".html", ".css", ".js"}]
    for filename in files:
        destination = target / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / filename, destination)
    (target / "notebook-questions.json").write_text(
        json.dumps(load_questions(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    digest = hashlib.sha256()
    for path in sorted(target.rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(target)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def main(skip_entra_update: bool = False):
    settings = {**dotenv_values(ROOT / ".env"), **os.environ}
    keys = ["AZURE_SUBSCRIPTION_ID", "TENANT_ID", "ENTRA_CLIENT_ID", "ENTRA_CLIENT_SECRET",
            "WORKIQ_APP_ID", "FOUNDRY_PROJECT_ENDPOINT", "HOSTED_AGENT_ENDPOINT", "SEARCH_ENDPOINT"]
    missing = [key for key in keys if not settings.get(key)]
    if missing:
        raise ValueError(f"배포에 필요한 설정: {', '.join(missing)}")
    subscription = settings["AZURE_SUBSCRIPTION_ID"]
    secret = settings["ENTRA_CLIENT_SECRET"]
    record = {"started_utc": datetime.now(timezone.utc).isoformat(), "status": "in_progress",
              "subscription": subscription, "resource_group": RESOURCE_GROUP, "region": "eastus2",
              "app": APP_NAME, "registry": REGISTRY, "steps": []}
    log = ROOT.parent / "logs/container-app-deployment.json"
    log.parent.mkdir(exist_ok=True)

    def save():
        log.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def az(arguments: list[str], *, json_result: bool = True):
        process = subprocess.run(["az", *arguments, "--subscription", subscription,
                                  "--only-show-errors", "-o", "json" if json_result else "none"],
                                 capture_output=True, text=True, check=False)
        if process.returncode:
            error = process.stderr.replace(secret, "[REDACTED]")
            raise RuntimeError(f"Azure CLI {arguments[0]} {arguments[1]} 실패: {error}")
        return json.loads(process.stdout) if json_result and process.stdout.strip() else None

    def deploy(template: str, parameters: dict, work: Path):
        parameter_file = work / "parameters.json"
        parameter_file.touch(mode=0o600, exist_ok=True)
        parameter_file.write_text(json.dumps({
            "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
            "contentVersion": "1.0.0.0",
            "parameters": {key: {"value": value} for key, value in parameters.items()},
        }))
        args = ["--resource-group", RESOURCE_GROUP, "--name", f"iq-web-{template}",
                "--template-file", str(ROOT / "infra" / f"{template}.bicep"),
                "--parameters", f"@{parameter_file}"]
        print(f"what-if: {template}", flush=True)
        az(["deployment", "group", "what-if", *args], json_result=False)
        print(f"deploy: {template}", flush=True)
        result = az(["deployment", "group", "create", *args])
        if result["properties"]["provisioningState"] != "Succeeded":
            raise RuntimeError(f"{template} deployment did not succeed")
        record["steps"].append(template)
        save()
        return {key: value["value"] for key, value in result["properties"]["outputs"].items()}

    save()
    try:
        with tempfile.TemporaryDirectory(prefix="iq-web-deploy-") as temporary:
            work = Path(temporary)
            context = work / "context"
            context.mkdir()
            context_hash = build_context(context)
            record["build_context_sha256"] = context_hash
            record["build_context_files"] = sorted(str(p.relative_to(context)) for p in context.rglob("*") if p.is_file())
            foundation = deploy("foundation", {}, work)
            record["foundation"] = foundation
            save()
            tag = f"iq-demo-web:{context_hash[:16]}"
            print(f"ACR build: {tag}", flush=True)
            build = az(["acr", "build", "--registry", REGISTRY, "--image", tag,
                        "--file", "Dockerfile", "--platform", "linux/amd64", "--no-logs",
                        "--query", "{runId:runId,status:status}", str(context)])
            record["build_run"] = build
            record["steps"].append("acr_build")
            save()
            image = f"{foundation['registryServer']}/{tag}"
            parameters = {
                "registryServer": foundation["registryServer"], "image": image,
                "tenantId": settings["TENANT_ID"], "clientId": settings["ENTRA_CLIENT_ID"],
                "clientSecret": secret, "workiqAppId": settings["WORKIQ_APP_ID"],
                "foundryEndpoint": settings["FOUNDRY_PROJECT_ENDPOINT"],
                "hostedAgentEndpoint": settings["HOSTED_AGENT_ENDPOINT"],
                "searchEndpoint": settings["SEARCH_ENDPOINT"],
            }
            web = deploy("web", parameters, work)
            record["url"] = web["url"]
            record["image"] = image
            save()
            record["ready_revision"] = wait_for_revision(
                lambda: az(["containerapp", "show", "--resource-group", RESOURCE_GROUP, "--name", APP_NAME,
                            "--query", "{latest:properties.latestRevisionName,ready:properties.latestReadyRevisionName,image:properties.template.containers[0].image,state:properties.provisioningState}"]),
                image,
            )
            record["readiness_verified"] = True
            save()
            if skip_entra_update:
                record["steps"].append("entra_redirect_not_modified")
                record["redirect_validation"] = "not_checked; existing callback must be verified in browser"
                print("기존 Entra 앱 설정을 변경하지 않습니다. 배포 후 실제 브라우저 로그인을 확인하세요.", flush=True)
            else:
                with AzureCliCredential(subscription=subscription) as credential:
                    graph_token = credential.get_token("https://graph.microsoft.com/.default")
                with httpx.Client(base_url="https://graph.microsoft.com/v1.0", timeout=60,
                                  headers={"Authorization": f"Bearer {graph_token.token}"}) as client:
                    response = client.get("/applications", params={
                        "$filter": f"appId eq '{settings['ENTRA_CLIENT_ID']}'", "$select": "id,web"})
                    response.raise_for_status()
                    applications = response.json()["value"]
                    if len(applications) != 1:
                        raise ValueError("웹 앱 등록을 하나로 식별하지 못했습니다.")
                    application = applications[0]
                    redirect_uris = application["web"].get("redirectUris", [])
                    callback = web["url"] + "/auth/callback"
                    if callback not in redirect_uris:
                        response = client.patch(f"/applications/{application['id']}", json={
                            "web": {"redirectUris": [*redirect_uris, callback]}})
                        response.raise_for_status()
                    verify = client.get(f"/applications/{application['id']}", params={"$select": "web"})
                    verify.raise_for_status()
                    if callback not in verify.json()["web"]["redirectUris"]:
                        raise RuntimeError("HTTPS callback 등록 검증 실패")
                    record["redirect_uri"] = callback
                record["steps"].append("entra_redirect")
            response = httpx.get(web["url"] + "/healthz", timeout=60)
            response.raise_for_status()
            if response.json() != {"status": "ok"}:
                raise RuntimeError("배포된 애플리케이션의 health 응답이 다릅니다.")
            with httpx.Client(timeout=60) as client:
                for asset in sorted((context / "static").iterdir()):
                    response = client.get(web["url"] + "/static/" + asset.name)
                    response.raise_for_status()
                    if response.content != asset.read_bytes():
                        raise RuntimeError(f"배포된 정적 파일이 빌드 context와 다릅니다: {asset.name}")
            record["static_assets_verified"] = True
            record["status"] = "deployed"
            record["health_http_status"] = response.status_code
            record["completed_utc"] = datetime.now(timezone.utc).isoformat()
            save()
            print(f"웹 배포 및 health 확인: {web['url']}", flush=True)
    except (RuntimeError, ValueError, httpx.HTTPError, OSError) as exc:
        record["status"] = "failed"
        record["error_type"] = type(exc).__name__
        save()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-entra-update", action="store_true",
                        help="동일 주소·동일 앱의 재배포에서만 사용. Graph 설정 조회·변경 없이 기존 callback을 보존합니다.")
    main(skip_entra_update=parser.parse_args().skip_entra_update)
