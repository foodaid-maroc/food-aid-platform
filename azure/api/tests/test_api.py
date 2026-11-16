import hashlib
import hmac
import json
import pathlib
import sys
import time

from fastapi.testclient import TestClient

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import clients  # noqa: E402
import main  # noqa: E402

LOT = json.loads((pathlib.Path(__file__).resolve().parents[3] / "contracts/examples/lot-formulaire.json").read_text())


def signed(body: bytes, ts=None, nonce="n-1"):
    ts = ts or str(int(time.time()))
    sig = "sha256=" + hmac.new(b"dev-secret-change-me", f"{ts}.{nonce}.".encode() + body, hashlib.sha256).hexdigest()
    return {"X-Timestamp": ts, "X-Nonce": nonce, "X-Signature": sig, "Content-Type": "application/json"}


def fake_clients(monkeypatch):
    seen, published = set(), []
    monkeypatch.setattr(clients, "remember_nonce", lambda n: not (n in seen or seen.add(n)))
    monkeypatch.setattr(clients, "archive_raw", lambda d, b: f"raw/x/{d}.json")
    monkeypatch.setattr(clients, "publish_lot", lambda m: published.append(m))
    monkeypatch.setattr(clients, "query_stock", lambda partner_id: [{"partnerId": partner_id}])
    return published


def test_ingest_ok_puis_rejeu_refuse(monkeypatch):
    published = fake_clients(monkeypatch)
    c = TestClient(main.app)
    body = json.dumps(LOT).encode()
    h = signed(body)
    assert c.post("/ingest", content=body, headers=h).status_code == 202
    assert published[0]["donationId"] == LOT["donationId"]
    assert c.post("/ingest", content=body, headers=h).status_code == 401      # même nonce


def test_ingest_signature_fausse(monkeypatch):
    fake_clients(monkeypatch)
    body = json.dumps(LOT).encode()
    h = signed(body)
    h["X-Signature"] = "sha256=00"
    assert TestClient(main.app).post("/ingest", content=body, headers=h).status_code == 401


def test_ingest_expire(monkeypatch):
    fake_clients(monkeypatch)
    body = json.dumps(LOT).encode()
    h = signed(body, ts=str(int(time.time()) - 3600))
    assert TestClient(main.app).post("/ingest", content=body, headers=h).status_code == 401


def test_partner_ne_voit_que_ses_donnees(monkeypatch):
    fake_clients(monkeypatch)
    r = TestClient(main.app).get("/query?partnerId=P1", headers={"X-Dev-Role": "Partner", "X-Dev-Partner": "P2"})
    assert r.status_code == 200
    assert r.json()["items"] == [{"partnerId": "P2"}]        # P1 demandé dans l'URL, P2 imposé par le jeton


def test_sans_role_refuse(monkeypatch):
    fake_clients(monkeypatch)
    assert TestClient(main.app).get("/query").status_code == 401
