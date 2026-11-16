"""Étudiant 4 · Crée la base et les conteneurs (Cosmos DB) + les conteneurs Blob.

En local : exécuté automatiquement par le service `data-init` de docker compose.
Sur Azure : ces ressources sont créées par Terraform (infra/azure/modules/data) ; ce script sert de référence.
"""
import os
import time

from azure.cosmos import CosmosClient, PartitionKey
from azure.storage.blob import BlobServiceClient

DB = os.environ.get("COSMOS_DATABASE", "foodaid")
CONTAINERS = [
    # (nom, clé de partition, TTL par défaut : None = pas de TTL, -1 = TTL activé au niveau des documents)
    ("stock", "/partnerId", None),
    ("alerts", "/partnerId", None),
    ("nonces", "/id", -1),
]


def init_cosmos() -> None:
    for _ in range(40):
        try:
            client = CosmosClient(os.environ["COSMOS_ENDPOINT"], credential=os.environ["COSMOS_KEY"],
                                  enable_endpoint_discovery=False)
            db = client.create_database_if_not_exists(DB)
            break
        except Exception as e:
            print(f"En attente de l'émulateur Cosmos DB... ({e.__class__.__name__})", flush=True)
            time.sleep(5)
    else:
        raise SystemExit("Émulateur Cosmos DB indisponible")
    for name, pk, ttl in CONTAINERS:
        kwargs = {"default_ttl": ttl} if ttl is not None else {}
        db.create_container_if_not_exists(id=name, partition_key=PartitionKey(path=pk), **kwargs)
        print(f"Cosmos : {DB}/{name} ({pk})", flush=True)


def init_blob() -> None:
    svc = BlobServiceClient.from_connection_string(os.environ["BLOB_CONNECTION_STRING"])
    for name in ("raw", "exports"):
        try:
            svc.create_container(name)
        except Exception:
            pass
        print(f"Blob : {name}", flush=True)


if __name__ == "__main__":
    init_blob()
    init_cosmos()
    print("Données initialisées.", flush=True)
