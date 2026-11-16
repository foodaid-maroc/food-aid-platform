"""Envoie un don de test : en local dans ElasticMQ (SQS), ou sur la vraie API Gateway.

Usage :
  python aws/ingest/send_test_donation.py --local [--file contracts/examples/lot-cmi.json]
  python aws/ingest/send_test_donation.py --url https://<api>/dev/donations
"""
import argparse
import json
import pathlib
import urllib.request
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_FILE = ROOT / "contracts" / "examples" / "lot-formulaire.json"


def main() -> None:
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--local", action="store_true", help="envoyer dans ElasticMQ (localhost:9324)")
    g.add_argument("--url", help="URL de l'API Gateway déployée")
    p.add_argument("--file", default=str(DEFAULT_FILE))
    p.add_argument("--new-id", action="store_true", help="générer un donationId unique (sinon : test d'idempotence)")
    a = p.parse_args()

    lot = json.loads(pathlib.Path(a.file).read_text(encoding="utf-8"))
    if a.new_id:
        lot["donationId"] = f"TEST-{uuid.uuid4().hex[:12]}"
    body = json.dumps(lot)

    if a.local:
        import boto3  # noqa: PLC0415

        sqs = boto3.client(
            "sqs", endpoint_url="http://localhost:9324", region_name="eu-west-3",
            aws_access_key_id="local", aws_secret_access_key="local",
        )
        url = sqs.get_queue_url(QueueName="foodaid-lots")["QueueUrl"]
        r = sqs.send_message(QueueUrl=url, MessageBody=body)
        print(f"Envoyé dans SQS local : {lot['donationId']} (MessageId={r['MessageId']})")
    else:
        req = urllib.request.Request(a.url, data=body.encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(resp.status, resp.read().decode())


if __name__ == "__main__":
    main()
