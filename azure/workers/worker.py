"""Étudiant 3 · App « workers » (Azure Container Apps, mise à l'échelle KEDA sur Service Bus).

Consomme la file « batches » : pour chaque lot, écrit les mouvements de stock dans Cosmos DB
(idempotent : id = donationId:sku) et crée les alertes de péremption.
Un message qui échoue 3 fois part automatiquement en DLQ (MaxDeliveryCount).
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import date, timedelta

from azure.cosmos import CosmosClient
from azure.servicebus import ServiceBusClient

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("workers")

QUEUE = os.environ.get("SERVICEBUS_QUEUE", "batches")
EXPIRY_ALERT_DAYS = int(os.environ.get("EXPIRY_ALERT_DAYS", "3"))


def credential():
    from azure.identity import DefaultAzureCredential  # noqa: PLC0415
    return DefaultAzureCredential()


def cosmos():
    if key := os.environ.get("COSMOS_KEY"):          # émulateur local
        client = CosmosClient(os.environ["COSMOS_ENDPOINT"], credential=key, enable_endpoint_discovery=False)
    else:                                              # Azure : identité managée
        client = CosmosClient(os.environ["COSMOS_ENDPOINT"], credential=credential())
    return client.get_database_client(os.environ.get("COSMOS_DATABASE", "foodaid"))


def servicebus():
    if cs := os.environ.get("SERVICEBUS_CONNECTION_STRING"):
        return ServiceBusClient.from_connection_string(cs)
    return ServiceBusClient(os.environ["SERVICEBUS_NAMESPACE"], credential=credential())


def handle(db, msg: dict) -> None:
    lot = msg["lot"]
    stock, alerts = db.get_container_client("stock"), db.get_container_client("alerts")
    limit = date.today() + timedelta(days=EXPIRY_ALERT_DAYS)
    for it in lot["items"]:
        doc = {
            "id": f"{lot['donationId']}:{it['sku']}",
            "donationId": lot["donationId"], "partnerId": lot["partnerId"],
            "sku": it["sku"], "label": it["label"], "quantity": it["quantity"], "unit": it["unit"],
            "movement": it.get("movement", "IN"), "expiryDate": it.get("expiryDate"),
            "receivedAt": lot["receivedAt"], "blobPath": msg.get("blobPath"),
        }
        stock.upsert_item(doc)                                    # rapprochement : IN / OUT par partenaire
        exp = it.get("expiryDate")
        if exp and doc["movement"] == "IN" and date.fromisoformat(exp) <= limit:
            alerts.upsert_item({"id": f"exp:{doc['id']}", "partnerId": lot["partnerId"], "type": "expiry",
                                "sku": it["sku"], "expiryDate": exp, "quantity": it["quantity"]})
    # TODO (Étudiant 3) : prévisions de la demande + exports d'impact (Blob « exports »)
    log.info(json.dumps({"event": "lot_processed", "donationId": lot["donationId"], "items": len(lot["items"])}))


def main() -> None:
    for attempt in range(30):
        try:
            db = cosmos()
            db.read()
            break
        except Exception as e:
            log.info(f"En attente de Cosmos DB... ({e.__class__.__name__})")
            time.sleep(5)
    else:
        raise SystemExit("Cosmos DB indisponible")

    with servicebus() as sb, sb.get_queue_receiver(QUEUE, max_wait_time=30) as receiver:
        log.info(f"workers prêts, écoute la file {QUEUE}")
        while True:
            for m in receiver.receive_messages(max_message_count=10, max_wait_time=10):
                try:
                    handle(db, json.loads(str(m)))
                    receiver.complete_message(m)
                except Exception as e:
                    log.error(json.dumps({"event": "lot_failed", "error": str(e)}))
                    receiver.abandon_message(m)                   # réessai, puis DLQ après MaxDeliveryCount


if __name__ == "__main__":
    main()
