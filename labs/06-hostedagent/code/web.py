import asyncio
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
import secrets
import time
from urllib.parse import urlparse

from azure.identity.aio import AzureCliCredential, DefaultAzureCredential, ManagedIdentityCredential
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import httpx
import msal
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from questions import load_questions
from agent.retrieval import ReasoningEffort
from catalog import fetch_catalog

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
logger = logging.getLogger("iq-web")
sessions: dict[str, dict] = {}


def origin() -> str:
    value = os.getenv("WEB_ORIGIN", "http://localhost:8000").rstrip("/")
    parsed = urlparse(value)
    if (parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}
    )) or parsed.path or parsed.query or parsed.fragment or parsed.username:
        raise RuntimeError("WEB_ORIGIN은 HTTPS origin 또는 로컬 개발 origin이어야 합니다.")
    return value


def sweep_sessions():
    for sid, session in list(sessions.items()):
        if session["expires"] <= time.time():
            sessions.pop(sid, None)


@asynccontextmanager
async def lifespan(app):
    async def sweep():
        while True:
            await asyncio.sleep(60)
            sweep_sessions()
    task = asyncio.create_task(sweep())
    yield
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    sessions.clear()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/healthz")
async def health():
    return {"status": "ok"}


def backend_credential():
    if os.getenv("IDENTITY_ENDPOINT"):
        return ManagedIdentityCredential(client_id=os.getenv("AZURE_CLIENT_ID"))
    if os.getenv("AZURE_SUBSCRIPTION_ID"):
        return AzureCliCredential(subscription=os.environ["AZURE_SUBSCRIPTION_ID"])
    return DefaultAzureCredential()


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.update({
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY",
        "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; "
        "connect-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
    })
    if origin().startswith("https://"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


def session_for(request: Request) -> dict:
    sweep_sessions()
    session = sessions.get(request.cookies.get("iq_session", ""))
    if not session or not session.get("account"):
        raise HTTPException(401, "Entra ID 로그인이 필요합니다.")
    return session


def check_csrf(request: Request, session: dict):
    if request.headers.get("origin") != origin() or not secrets.compare_digest(
        request.headers.get("x-csrf-token", ""), session["csrf"]
    ):
        logger.warning("csrf_rejected")
        raise HTTPException(403, "요청 출처 또는 CSRF 토큰이 올바르지 않습니다.")


def auth_client(session: dict):
    required = ["ENTRA_CLIENT_ID", "ENTRA_CLIENT_SECRET", "TENANT_ID", "WORKIQ_APP_ID"]
    if any(not os.getenv(key) for key in required):
        raise HTTPException(503, "Entra 앱 설정이 없습니다. README의 앱 등록 단계를 확인하세요.")
    return msal.ConfidentialClientApplication(
        os.environ["ENTRA_CLIENT_ID"],
        client_credential=os.environ["ENTRA_CLIENT_SECRET"],
        authority=f"https://login.microsoftonline.com/{os.environ['TENANT_ID']}",
        token_cache=session["cache"],
    )


def scopes(resource: str) -> list[str]:
    return (["https://search.azure.com/.default"] if resource == "search"
            else [f"api://{os.environ['WORKIQ_APP_ID']}/access_as_user"])


def begin_flow(session: dict, resource: str):
    session["resource"] = resource
    session["flow"] = auth_client(session).initiate_auth_code_flow(
        scopes(resource), redirect_uri=origin() + "/auth/callback",
        login_hint=session.get("account", {}).get("username"),
    )
    return RedirectResponse(session["flow"]["auth_uri"])


def set_cookie(response, sid: str):
    response.set_cookie("iq_session", sid, httponly=True, secure=origin().startswith("https"),
                        samesite="lax", max_age=3600, path="/")


@app.get("/")
async def home():
    return FileResponse(ROOT / "static/index.html")


@app.get("/auth/login")
def login(request: Request):
    sweep_sessions()
    sessions.pop(request.cookies.get("iq_session", ""), None)
    sid = secrets.token_urlsafe(32)
    session = {"expires": time.time() + 600, "cache": msal.TokenCache(),
               "csrf": secrets.token_urlsafe(32)}
    response = begin_flow(session, "workiq")
    sessions[sid] = session
    set_cookie(response, sid)
    return response


@app.get("/auth/callback")
def callback(request: Request):
    sweep_sessions()
    sid = request.cookies.get("iq_session", "")
    session = sessions.get(sid)
    if not session or "flow" not in session:
        raise HTTPException(400, "로그인 상태가 만료됐습니다. 다시 로그인하세요.")
    client = auth_client(session)
    try:
        result = client.acquire_token_by_auth_code_flow(session.pop("flow"), dict(request.query_params))
    except ValueError:
        sessions.pop(sid, None)
        logger.warning("oauth_state_rejected")
        raise HTTPException(400, "로그인 응답 검증에 실패했습니다.") from None
    if "access_token" not in result:
        sessions.pop(sid, None)
        logger.warning("oauth_failed code=%s", result.get("error", "unknown"))
        raise HTTPException(401, {"message": "로그인 또는 위임 동의가 실패했습니다.",
                                  "code": result.get("error", "unknown")})
    claims = result.get("id_token_claims", {})
    user_id = (claims.get("tid"), claims.get("oid"))
    if not all(user_id) or user_id[0] != os.environ["TENANT_ID"] or (
        "user_id" in session and tuple(session["user_id"]) != user_id
    ):
        sessions.pop(sid, None)
        raise HTTPException(403, "두 리소스에 같은 테넌트·사용자로 로그인해야 합니다.")
    session["user_id"] = user_id
    accounts = client.get_accounts()
    account = next((a for a in accounts if a.get("local_account_id") == user_id[1]), None)
    if not account:
        sessions.pop(sid, None)
        raise HTTPException(401, "로그인한 사용자의 토큰 캐시를 찾을 수 없습니다.")
    session["account"] = account
    if session["resource"] == "workiq":
        return begin_flow(session, "search")
    session["expires"] = time.time() + 3600
    new_sid = secrets.token_urlsafe(32)
    sessions[new_sid] = sessions.pop(sid)
    response = RedirectResponse("/")
    set_cookie(response, new_sid)
    return response


@app.get("/api/me")
def me(request: Request):
    session = session_for(request)
    return {"name": session["account"]["username"], "csrf": session["csrf"]}


@app.get("/api/questions")
def questions(request: Request):
    session_for(request)
    return load_questions()


@app.post("/auth/logout")
def logout(request: Request):
    session = session_for(request)
    check_csrf(request, session)
    sessions.pop(request.cookies.get("iq_session", ""), None)
    response = JSONResponse({"logged_out": True})
    response.delete_cookie("iq_session", path="/")
    return response


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    kb: Literal["process", "quality"]
    question: str = Field(min_length=1, max_length=6000)
    reasoning_effort: ReasoningEffort = "medium"


def user_token(session: dict, resource: str) -> str:
    result = auth_client(session).acquire_token_silent(
        scopes(resource), account=session["account"])
    if not result or "access_token" not in result:
        raise HTTPException(401, "사용자 위임 토큰을 갱신하지 못했습니다. 다시 로그인하세요.")
    return result["access_token"]


@app.get("/api/knowledge-base")
async def knowledge_base(request: Request, kb: Literal["process", "quality"]):
    session = session_for(request)
    token = await asyncio.to_thread(user_token, session, "search")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            return await fetch_catalog(kb, token, client)
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        logger.warning("catalog_failed status=%s", status)
        raise HTTPException(status if status in (401, 403, 404) else 502,
                            f"KB/KS 설명 조회 실패 (Search HTTP {status}). 정의 조회 권한과 구성을 확인하세요.") from None
    except (httpx.RequestError, ValueError, KeyError) as exc:
        logger.error("catalog_failed type=%s", type(exc).__name__)
        raise HTTPException(502, "KB/KS 구성을 읽지 못했습니다. Search 연결·설정을 확인하세요.") from None


@app.post("/api/chat")
async def chat(request: Request):
    session = session_for(request)
    check_csrf(request, session)
    from pydantic import ValidationError
    try:
        data = ChatRequest.model_validate(await request.json())
    except (ValueError, ValidationError):
        raise HTTPException(400, "KB, low/medium 추론 강도 및 1~6000자 질문을 확인하세요.") from None
    if session.get("busy"):
        raise HTTPException(429, "진행 중인 질문을 완료하거나 취소하세요.")
    session["busy"] = True
    prepared = False
    try:
        search = await asyncio.to_thread(user_token, session, "search")
        workiq = await asyncio.to_thread(user_token, session, "workiq") if data.kb == "quality" else ""
        endpoint = os.environ.get("HOSTED_AGENT_ENDPOINT", "")
        if not endpoint.startswith("https://") or urlparse(endpoint).hostname != urlparse(
            os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")
        ).hostname:
            raise HTTPException(503, "검증된 Hosted Agent endpoint를 설정하세요.")
        prepared = True
    finally:
        if not prepared:
            session["busy"] = False

    async def relay():
        from azure.core.exceptions import ClientAuthenticationError
        credential = backend_credential()
        try:
            async with credential:
                token = await credential.get_token("https://ai.azure.com/.default")
                headers = {"Authorization": f"Bearer {token.token}",
                           "x-client-search-authorization": search,
                           "x-client-workiq-authorization": workiq}
                async with httpx.AsyncClient(timeout=httpx.Timeout(600, connect=30)) as client:
                    async with client.stream("POST", endpoint, headers=headers, json=data.model_dump()) as response:
                        response.raise_for_status()
                        if "text/event-stream" not in response.headers.get("content-type", ""):
                            raise ValueError("Hosted Agent가 SSE를 반환하지 않았습니다.")
                        async for chunk in response.aiter_bytes():
                            yield chunk
        except (httpx.HTTPError, ClientAuthenticationError, ValueError) as exc:
            logger.error("hosted_call_failed type=%s", type(exc).__name__)
            yield b'event: error\ndata: {"code":"hosted_call_failed","message":"Hosted Agent connection failed."}\n\n'
        finally:
            session["busy"] = False

    return StreamingResponse(relay(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})
