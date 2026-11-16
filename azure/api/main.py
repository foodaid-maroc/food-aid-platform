"""Étudiant 3 · App « api » (Azure Container Apps).

POST /ingest : lot signé venant de la Lambda AWS  -> vérifie HMAC + nonce -> archive dans Blob -> publie sur Service Bus
GET  /query  : requête du portail (JWT Entra ID)  -> vérifie le jeton + le rôle -> données filtrées depuis Cosmos DB
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import clients

log = logging.getLogger("api")
logging.basicConfig(level=logging.INFO, format="%(message)s")

AUTH_MODE = os.environ.get("AUTH_MODE", "dev")          # dev | entra
TIME_WINDOW_S = 300
ROLES = {"Staff", "Partner", "Donor", "Auditor"}

app = FastAPI(title="Food Aid API")

# CORS : seulement l'origine du portail (utile en plan Free, quand le portail appelle l'API directement)
if origins := [o for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o]:
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET"],
                       allow_headers=["Authorization", "Content-Type"])


# ---------- utilitaires ----------
def hmac_secret() -> bytes:
    # En Azure : injecté depuis Key Vault (référence de secret Container Apps -> identité managée)
    return os.environ.get("HMAC_SECRET", "dev-secret-change-me").encode()


def expected_signature(body: bytes, ts: str, nonce: str) -> str:
    return "sha256=" + hmac.new(hmac_secret(), f"{ts}.{nonce}.".encode() + body, hashlib.sha256).hexdigest()


def audit(event: str, **fields) -> None:
    log.info(json.dumps({"event": event, "at": datetime.now(timezone.utc).isoformat(), **fields}))


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- POST /ingest (depuis AWS) ----------
@app.post("/ingest", status_code=202)
async def ingest(request: Request):
    body = await request.body()
    ts = request.headers.get("X-Timestamp", "")
    nonce = request.headers.get("X-Nonce", "")
    sig = request.headers.get("X-Signature", "")

    # 1. signature
    if not (ts and nonce and sig) or not hmac.compare_digest(sig, expected_signature(body, ts, nonce)):
        audit("ingest_rejected", reason="bad_signature")
        raise HTTPException(401, "signature invalide")
    # 2. fraîcheur
    try:
        if abs(time.time() - int(ts)) > TIME_WINDOW_S:
            raise ValueError
    except ValueError:
        audit("ingest_rejected", reason="expired")
        raise HTTPException(401, "requête expirée") from None
    # 3. anti-rejeu
    if not clients.remember_nonce(nonce):
        audit("ingest_rejected", reason="replay", nonce=nonce)
        raise HTTPException(401, "nonce déjà utilisé")

    try:
        lot = json.loads(body)
        donation_id, partner_id = lot["donationId"], lot["partnerId"]
    except (ValueError, KeyError):
        raise HTTPException(400, "lot invalide") from None

    blob_path = clients.archive_raw(donation_id, body)
    clients.publish_lot({"type": "lot.received", "donationId": donation_id,
                         "partnerId": partner_id, "blobPath": blob_path, "lot": lot})
    audit("ingest_accepted", donationId=donation_id, partnerId=partner_id)
    return {"status": "accepted", "donationId": donation_id}


# ---------- authentification du portail ----------
def principal_from_request(request: Request) -> dict:
    """Retourne {'roles': [...], 'partnerId': str|None, 'user': str}."""
    if AUTH_MODE == "dev":
        role = request.headers.get("X-Dev-Role")
        if role:
            return {"roles": [role], "partnerId": request.headers.get("X-Dev-Partner"), "user": "dev"}
        # format envoyé par le CLI Static Web Apps (swa start) et par le proxy SWA
        raw = request.headers.get("x-ms-client-principal")
        if raw:
            p = json.loads(base64.b64decode(raw))
            return {"roles": p.get("userRoles", []), "partnerId": None, "user": p.get("userDetails", "?")}
        raise HTTPException(401, "rôle absent (en local : en-tête X-Dev-Role)")

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "jeton absent")
    claims = clients.verify_entra_jwt(auth.removeprefix("Bearer "))
    return {"roles": claims.get("roles", []), "partnerId": claims.get("partnerId"), "user": claims.get("oid", "?")}


# ---------- GET /query (depuis le portail) ----------
@app.get("/query")
def query(request: Request, partnerId: str | None = None):  # noqa: N803
    who = principal_from_request(request)
    roles = set(who["roles"]) & ROLES
    if not roles:
        raise HTTPException(403, "aucun rôle autorisé")

    if "Staff" in roles or "Auditor" in roles:
        items = clients.query_stock(partner_id=partnerId)
    elif "Partner" in roles:
        if not who["partnerId"]:
            raise HTTPException(403, "partnerId manquant dans le jeton")
        items = clients.query_stock(partner_id=who["partnerId"])     # imposé par le jeton, jamais par l'URL
    else:  # Donor
        items = clients.donor_impact()

    audit("query", user=who["user"], roles=sorted(roles), count=len(items))
    return JSONResponse({"roles": sorted(roles), "items": items})
