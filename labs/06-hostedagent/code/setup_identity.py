"""전용 웹 앱 등록. 기존 Work IQ 앱은 변경하지 않으며 비밀값은 .env에만 씁니다."""

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path

from azure.identity import AzureCliCredential
from dotenv import dotenv_values, set_key
import httpx

ROOT = Path(__file__).resolve().parent


def main():
    settings = {**dotenv_values(ROOT / ".env.example"), **dotenv_values(ROOT / ".env")}
    env_file = ROOT / ".env"
    if settings.get("ENTRA_CLIENT_SECRET"):
        raise RuntimeError("이미 .env에 웹 앱 자격 증명이 있습니다. 새 비밀키를 자동 생성하지 않습니다.")
    with AzureCliCredential(subscription=settings["AZURE_SUBSCRIPTION_ID"]) as credential:
        token = credential.get_token("https://graph.microsoft.com/.default")
    with httpx.Client(
        base_url="https://graph.microsoft.com/v1.0",
        headers={"Authorization": f"Bearer {token.token}"}, timeout=60,
    ) as client:
        def call(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            if not response.is_success:
                error = response.json().get("error", {})
                raise RuntimeError(f"Graph {method} {path}: HTTP {response.status_code} {error.get('code')}")
            return response.json() if response.content else {}

        sources = []
        for app_id, scope_name in [
            ("https://search.azure.com", "user_impersonation"),
            (settings["WORKIQ_APP_ID"], "access_as_user"),
        ]:
            # Resolve Search by its servicePrincipalName rather than assuming its app ID.
            query = ("servicePrincipalNames/any(n:n eq 'https://search.azure.com')"
                     if scope_name == "user_impersonation" else f"appId eq '{app_id}'")
            found = call("GET", "/servicePrincipals", params={"$filter": query})["value"]
            if len(found) != 1:
                raise RuntimeError(f"{scope_name}: 대상 서비스 주체가 하나가 아닙니다.")
            sp = found[0]
            scope = next(s for s in sp["oauth2PermissionScopes"] if s["value"] == scope_name and s["isEnabled"])
            sources.append((sp, scope))
        name = "iq-hostedagent-demo-web"
        existing = call("GET", "/applications", params={"$filter": f"displayName eq '{name}'"})["value"]
        if existing:
            raise RuntimeError("같은 이름의 앱 등록이 있습니다. 중복 생성하지 않습니다.")
        app = call("POST", "/applications", json={
            "displayName": name, "signInAudience": "AzureADMyOrg",
            "web": {"redirectUris": [settings["WEB_ORIGIN"] + "/auth/callback"]},
            "requiredResourceAccess": [
                {"resourceAppId": sp["appId"], "resourceAccess": [{"id": scope["id"], "type": "Scope"}]}
                for sp, scope in sources
            ],
        })
        service = call("POST", "/servicePrincipals", json={"appId": app["appId"]})
        record = {"application_id": app["appId"], "object_id": app["id"],
                  "service_principal_id": service["id"], "redirect_uri": settings["WEB_ORIGIN"] + "/auth/callback"}
        (ROOT.parent / "logs").mkdir(exist_ok=True)
        (ROOT.parent / "logs/identity.json").write_text(json.dumps(record, indent=2) + "\n")
        secret = call("POST", f"/applications/{app['id']}/addPassword", json={
            "passwordCredential": {"displayName": "local-demo-30-days",
                                   "endDateTime": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()}
        })["secretText"]
        env_file.touch(mode=0o600, exist_ok=True)
        os.chmod(env_file, 0o600)
        for key, value in settings.items():
            if value is not None:
                set_key(str(env_file), key, value)
        set_key(str(env_file), "ENTRA_CLIENT_ID", app["appId"])
        set_key(str(env_file), "ENTRA_CLIENT_SECRET", secret)
        print(json.dumps(record, indent=2))
        print("비밀값은 권한 0600의 .env에만 저장했습니다. 위임 동의는 브라우저 로그인에서 수행합니다.")


if __name__ == "__main__":
    main()
