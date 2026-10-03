"""기존 Foundry 프로젝트에 전용 Hosted Agent 버전만 코드 배포합니다."""

import hashlib
import io
import json
import os
from pathlib import Path
import time
import tempfile
import zipfile

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import CodeConfiguration, HostedAgentDefinition, ProtocolVersionRecord
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent


def main():
    load_dotenv(ROOT / ".env")
    credential = AzureCliCredential(subscription=os.environ["AZURE_SUBSCRIPTION_ID"])
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    name = os.environ["HOSTED_AGENT_NAME"]
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as archive:
        for filename in ["main.py", "retrieval.py", "trace_view.py", "requirements.txt"]:
            archive.write(ROOT / "agent" / filename, filename)
        archive.write(ROOT.parents[1] / "05-foundry-iq/helper/code/retrieval_trace.py", "retrieval_trace.py")
    code = payload.getvalue()
    digest = hashlib.sha256(code).hexdigest()
    environment = {key: os.environ[key] for key in [
        "FOUNDRY_PROJECT_ENDPOINT", "AZURE_AI_MODEL_DEPLOYMENT_NAME", "SEARCH_ENDPOINT",
    ]}
    environment["OTEL_SDK_DISABLED"] = "true"
    with AIProjectClient(endpoint=endpoint, credential=credential, allow_preview=True) as project, \
            tempfile.NamedTemporaryFile(suffix=".zip") as upload:
        upload.write(code)
        upload.seek(0)
        created = project.agents.create_version_from_code(
            agent_name=name,
            definition=HostedAgentDefinition(
                cpu="0.5", memory="1Gi",
                code_configuration=CodeConfiguration(
                    runtime="python_3_13", entry_point=["python", "main.py"],
                    dependency_resolution="remote_build",
                ),
                protocol_versions=[ProtocolVersionRecord(protocol="invocations", version="2.0.0")],
                environment_variables=environment,
            ),
            code=upload, code_zip_sha256=digest,
            description="Foundry IQ reference demo; delegated retrieval and genuine SSE generation.",
        )
        record = {"agent": name, "version": created.version, "zip_sha256": digest,
                  "endpoint": endpoint, "states": []}
        log = ROOT.parent / "logs/deployment.json"
        log.parent.mkdir(exist_ok=True)
        for _ in range(180):
            version = project.agents.get_version(agent_name=name, agent_version=created.version)
            state = str(version.get("status"))
            if not record["states"] or record["states"][-1] != state:
                record["states"].append(state)
                print(f"version={created.version} status={state}", flush=True)
                log.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            if state == "active":
                downloaded = b"".join(project.agents.download_code(
                    agent_name=name, agent_version=created.version))
                record["download_hash_matches"] = hashlib.sha256(downloaded).hexdigest() == digest
                log.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
                if not record["download_hash_matches"]:
                    raise RuntimeError("배포 ZIP 해시가 일치하지 않습니다.")
                print("Deployed code verified.", flush=True)
                return
            if state in {"failed", "deleted", "archived"}:
                error = version.get("error") or {}
                record["error"] = dict(error)
                log.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
                raise RuntimeError(f"배포 실패. 오류: {error}")
            time.sleep(5)
        raise TimeoutError("배포가 15분 내 active가 되지 않았습니다.")


if __name__ == "__main__":
    main()
