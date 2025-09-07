"""FastAPI application exposing WhatsApp webhook and RAG endpoint."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

from .config import settings
from .rag import rag_engine
from .wa import send_message, verify_signature

app = FastAPI()


@app.get("/wa/webhook")
async def verify(mode: str, token: str, challenge: str):
    if token == settings.whatsapp_verify_token:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Invalid token")


@app.post("/wa/webhook")
async def webhook(request: Request):
    signature = request.headers.get("X-Hub-Signature-256", "").split("=")[-1]
    body = await request.body()
    if not verify_signature(signature, body, settings.whatsapp_verify_token):
        raise HTTPException(status_code=403, detail="Invalid signature")
    data = await request.json()
    try:
        entry = data["entry"][0]["changes"][0]["value"]
        message = entry["messages"][0]["text"]["body"]
        sender = entry["messages"][0]["from"]
        phone_id = entry["metadata"]["phone_number_id"]
    except Exception:
        return {"status": "ignored"}
    answer, _ = rag_engine.answer(message)
    send_message(phone_id, sender, answer)
    return {"status": "ok"}


@app.post("/ask")
async def ask(payload: dict):
    question = payload.get("question", "")
    k = payload.get("k")
    answer, sources = rag_engine.answer(question, k)
    return {"answer": answer, "sources": sources}


@app.post("/admin/reindex")
async def reindex(payload: dict):
    secret = payload.get("secret", "")
    if secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    from admin.ingest import ingest

    ingest()
    rag_engine._load_artifacts()
    return {"status": "reindexed"}


@app.get("/admin/health")
async def health():
    return {"status": "ok"}
