"""Étudiant 2 · Lambda de validation des lots (déclenchée par SQS).

Pour chaque message :
  1. valide et normalise le lot (contracts/lot.schema.json)
  2. réserve le donationId dans DynamoDB (écriture conditionnelle) -> idempotence
  3. signe le lot en HMAC (contracts/hmac.md) et l'envoie à POST /ingest sur Azure
Les messages en échec sont renvoyés à SQS (réponse partielle de lot) puis finissent en DLQ.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

log = logging.getLogger()
log.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("IDEMPOTENCY_TABLE", "foodaid-idempotency")
AZURE_INGEST_URL = os.environ.get("AZURE_INGEST_URL", "http://localhost:8080/ingest")
TTL_SECONDS = int(os.environ.get("IDEMPOTENCY_TTL_SECONDS", str(30 * 24 * 3600)))

REQUIRED = ("donationId", "source", "partnerId", "receivedAt", "items")
SOURCES = {"cmi_webhook", "partner_form"}
UNITS = {"kg", "l", "unite", "carton"}

_table = None
_secret: bytes | None = None


class InvalidLot(ValueError):
    """Lot définitivement invalide : inutile de le réessayer."""


def table():
    global _table
    if _table is None:
        endpoint = os.environ.get("DYNAMODB_ENDPOINT") or None
        _table = boto3.resource("dynamodb", endpoint_url=endpoint).Table(TABLE_NAME)
    return _table


def hmac_secret() -> bytes:
    """Clé HMAC : variable d'env en local, SSM Parameter Store (SecureString) sur AWS."""
    global _secret
    if _secret is None:
        param = os.environ.get("HMAC_SSM_PARAM")
        if param:
            value = boto3.client("ssm").get_parameter(Name=param, WithDecryption=True)["Parameter"]["Value"]
        else:
            value = os.environ.get("HMAC_SECRET", "dev-secret-change-me")
        _secret = value.encode()
    return _secret


def validate(lot: dict) -> None:
    missing = [k for k in REQUIRED if k not in lot]
    if missing:
        raise InvalidLot(f"champs manquants : {missing}")
    if lot["source"] not in SOURCES:
        raise InvalidLot(f"source inconnue : {lot['source']}")
    if not str(lot["partnerId"]).strip().upper().startswith("P"):
        raise InvalidLot("partnerId invalide")
    if not isinstance(lot["items"], list):
        raise InvalidLot("items doit être une liste")
    for it in lot["items"]:
        if it.get("unit") not in UNITS:
            raise InvalidLot(f"unité inconnue : {it.get('unit')}")
        if not isinstance(it.get("quantity"), (int, float)) or it["quantity"] <= 0:
            raise InvalidLot("quantité invalide")
    # TODO (Étudiant 2) : appliquer toutes les règles de contracts/lot.schema.json


def normalize(lot: dict) -> dict:
    out = {
        "donationId": str(lot["donationId"]).strip(),
        "source": lot["source"],
        "partnerId": str(lot["partnerId"]).strip().upper(),
        "donorId": lot.get("donorId"),
        "amountMad": lot.get("amountMad"),
        "receivedAt": lot["receivedAt"],
        "items": [],
    }
    for it in lot["items"]:
        out["items"].append({
            "sku": str(it["sku"]).strip().upper(),
            "label": str(it.get("label", it["sku"])).strip(),
            "quantity": it["quantity"],
            "unit": it["unit"],
            "expiryDate": it.get("expiryDate"),
            "movement": it.get("movement", "IN"),
        })
    return out


def claim(donation_id: str) -> bool:
    """True si ce donationId est nouveau ; False s'il a déjà été traité (doublon)."""
    try:
        table().put_item(
            Item={"pk": donation_id, "status": "SENDING", "expiresAt": int(time.time()) + TTL_SECONDS},
            ConditionExpression="attribute_not_exists(pk)",
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def release(donation_id: str) -> None:
    """Libère la réservation si l'envoi a échoué, pour permettre un nouvel essai."""
    table().delete_item(Key={"pk": donation_id})


def mark_sent(donation_id: str) -> None:
    table().update_item(
        Key={"pk": donation_id},
        UpdateExpression="SET #s = :s, sentAt = :t",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": "SENT", ":t": datetime.now(timezone.utc).isoformat()},
    )


def sign(body: bytes, timestamp: str, nonce: str) -> str:
    message = f"{timestamp}.{nonce}.".encode() + body
    return "sha256=" + hmac.new(hmac_secret(), message, hashlib.sha256).hexdigest()


def send_to_azure(lot: dict) -> None:
    body = json.dumps(lot, separators=(",", ":"), ensure_ascii=False).encode()
    ts, nonce = str(int(time.time())), str(uuid.uuid4())
    req = urllib.request.Request(
        AZURE_INGEST_URL, data=body, method="POST",
        headers={"Content-Type": "application/json", "X-Timestamp": ts,
                 "X-Nonce": nonce, "X-Signature": sign(body, ts, nonce)},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status not in (200, 202):
            raise RuntimeError(f"Azure a répondu {resp.status}")


def process(record_body: str) -> str:
    lot = json.loads(record_body)
    validate(lot)
    lot = normalize(lot)
    if not claim(lot["donationId"]):
        log.info(json.dumps({"event": "duplicate_ignored", "donationId": lot["donationId"]}))
        return "duplicate"
    try:
        send_to_azure(lot)
    except Exception:
        release(lot["donationId"])
        raise
    mark_sent(lot["donationId"])
    log.info(json.dumps({"event": "lot_sent", "donationId": lot["donationId"], "partnerId": lot["partnerId"]}))
    return "sent"


def handler(event, context):  # noqa: ARG001
    failures = []
    for record in event.get("Records", []):
        try:
            process(record["body"])
        except (InvalidLot, json.JSONDecodeError) as e:
            # Lot invalide : on le rejette vers la DLQ via un échec (inutile de l'envoyer à Azure)
            log.warning(json.dumps({"event": "invalid_lot", "error": str(e), "messageId": record.get("messageId")}))
            failures.append({"itemIdentifier": record["messageId"]})
        except (urllib.error.URLError, RuntimeError, ClientError) as e:
            log.error(json.dumps({"event": "send_failed", "error": str(e), "messageId": record.get("messageId")}))
            failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": failures}
