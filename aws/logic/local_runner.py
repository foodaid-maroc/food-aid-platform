"""En local seulement : remplace le déclencheur SQS -> Lambda.

Lit la file ElasticMQ en boucle, appelle handler() avec un événement au format SQS,
et supprime les messages traités avec succès.
"""
import os
import time

import boto3

import handler as lambda_handler

SQS_ENDPOINT = os.environ.get("SQS_ENDPOINT", "http://elasticmq:9324")
QUEUE = os.environ.get("QUEUE_NAME", "foodaid-lots")


def ensure_table() -> None:
    ddb = boto3.client("dynamodb", endpoint_url=os.environ["DYNAMODB_ENDPOINT"])
    name = lambda_handler.TABLE_NAME
    if name not in ddb.list_tables()["TableNames"]:
        ddb.create_table(
            TableName=name,
            AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}],
            KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"Table DynamoDB locale créée : {name}", flush=True)


def main() -> None:
    sqs = boto3.client("sqs", endpoint_url=SQS_ENDPOINT)
    for _ in range(30):
        try:
            ensure_table()
            url = sqs.get_queue_url(QueueName=QUEUE)["QueueUrl"]
            break
        except Exception as e:  # émulateurs pas encore prêts
            print(f"En attente des émulateurs... ({e.__class__.__name__})", flush=True)
            time.sleep(2)
    else:
        raise SystemExit("Émulateurs indisponibles")

    print(f"lambda-runner prêt, écoute {QUEUE}", flush=True)
    while True:
        msgs = sqs.receive_message(QueueUrl=url, MaxNumberOfMessages=10, WaitTimeSeconds=10).get("Messages", [])
        if not msgs:
            continue
        event = {"Records": [{"messageId": m["MessageId"], "body": m["Body"], "eventSource": "aws:sqs"} for m in msgs]}
        result = lambda_handler.handler(event, None)
        failed = {f["itemIdentifier"] for f in result["batchItemFailures"]}
        for m in msgs:
            if m["MessageId"] not in failed:
                sqs.delete_message(QueueUrl=url, ReceiptHandle=m["ReceiptHandle"])
        print(f"lot traité : {len(msgs) - len(failed)} ok, {len(failed)} en échec", flush=True)


if __name__ == "__main__":
    main()
