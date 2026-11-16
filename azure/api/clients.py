"""Accès aux services Azure (Blob, Service Bus, Cosmos DB, Entra ID).

En local : chaînes de connexion des émulateurs (local/docker-compose.yml).
Sur Azure : identité managée (DefaultAzureCredential) -> aucun secret dans le code.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from functools import lru_cache

from azure.cosmos import CosmosClient, exceptions as cosmos_exc
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.storage.blob import BlobServiceClient

DB_NAME = os.environ.get("COSMOS_DATABASE", "foodaid")
QUEUE = os.environ.get("SERVICEBUS_QUEUE", "batches")
NONCE_TTL_S = 600


def _credential():
    from azure.identity import DefaultAzureCredential  # noqa: PLC0415
    return DefaultAzureCredential()


@lru_cache
def blob_service() -> BlobServiceClient:
    if cs := os.environ.get("BLOB_CONNECTION_STRING"):
        return BlobServiceClient.from_connection_string(cs)
    return BlobServiceClient(os.environ["BLOB_ACCOUNT_URL"], credential=_credential())


@lru_cache
def servicebus() -> ServiceBusClient:
    if cs := os.environ.get("SERVICEBUS_CONNECTION_STRING"):
        return ServiceBusClient.from_connection_string(cs)
    return ServiceBusClient(os.environ["SERVICEBUS_NAMESPACE"], credential=_credential())


@lru_cache
def cosmos_db():
    endpoint = os.environ["COSMOS_ENDPOINT"]
    if key := os.environ.get("COSMOS_KEY"):          # émulateur local
        client = CosmosClient(endpoint, credential=key, enable_endpoint_discovery=False)
    else:                                              # Azure : identité managée
        client = CosmosClient(endpoint, credential=_credential())
    return client.get_database_client(DB_NAME)


def archive_raw(donation_id: str, body: bytes) -> str:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    name = f"{day}/{donation_id}.json"
    blob_service().get_blob_client("raw", name).upload_blob(body, overwrite=True)
    return f"raw/{name}"


def publish_lot(message: dict) -> None:
    with servicebus().get_queue_sender(QUEUE) as sender:
        sender.send_messages(ServiceBusMessage(json.dumps(message), message_id=message["donationId"]))


def remember_nonce(nonce: str) -> bool:
    """True si le nonce est nouveau. Stocké dans Cosmos (conteneur nonces, TTL 600 s)."""
    try:
        cosmos_db().get_container_client("nonces").create_item({"id": nonce, "ttl": NONCE_TTL_S, "at": int(time.time())})
        return True
    except cosmos_exc.CosmosResourceExistsError:
        return False


def query_stock(partner_id: str | None) -> list[dict]:
    c = cosmos_db().get_container_client("stock")
    fields = "c.id, c.donationId, c.partnerId, c.sku, c.label, c.quantity, c.unit, c.movement, c.expiryDate, c.receivedAt"
    if partner_id:
        return list(c.query_items(f"SELECT {fields} FROM c", partition_key=partner_id))
    return list(c.query_items(f"SELECT {fields} FROM c", enable_cross_partition_query=True))


def donor_impact() -> list[dict]:
    """Quantités distribuées par denrée (agrégées en Python : simple et compatible avec l'émulateur).

    TODO (Étudiants 3 et 4) : filtrer sur les dons du donateur connecté (oid -> donorId).
    """
    c = cosmos_db().get_container_client("stock")
    rows = c.query_items("SELECT c.sku, c.label, c.quantity FROM c WHERE c.movement = 'OUT'",
                         enable_cross_partition_query=True)
    totals: dict[str, dict] = {}
    for r in rows:
        t = totals.setdefault(r["sku"], {"sku": r["sku"], "label": r["label"], "distribue": 0})
        t["distribue"] += r["quantity"]
    return list(totals.values())


@lru_cache
def _jwks_client():
    import jwt  # noqa: PLC0415
    tenant = os.environ["ENTRA_TENANT_ID"]
    return jwt.PyJWKClient(f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys")


def verify_entra_jwt(token: str) -> dict:
    """Vérifie signature, audience, émetteur et expiration d'un jeton Entra ID."""
    import jwt  # noqa: PLC0415
    from fastapi import HTTPException  # noqa: PLC0415

    tenant = os.environ["ENTRA_TENANT_ID"]
    try:
        key = _jwks_client().get_signing_key_from_jwt(token).key
        return jwt.decode(
            token, key, algorithms=["RS256"],
            audience=os.environ["ENTRA_API_AUDIENCE"],            # ex. api://<client-id>
            issuer=f"https://login.microsoftonline.com/{tenant}/v2.0",
        )
    except jwt.PyJWTError as e:
        raise HTTPException(401, f"jeton invalide : {e}") from None
