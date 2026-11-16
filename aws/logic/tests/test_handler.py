import hashlib
import hmac
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import handler  # noqa: E402

EVENT = json.loads((pathlib.Path(__file__).resolve().parents[1] / "events" / "sqs-event.json").read_text())


def lot():
    return json.loads(EVENT["Records"][0]["body"])


def test_normalize_met_en_majuscules():
    out = handler.normalize(lot())
    assert out["partnerId"] == "P2"
    assert out["items"][0]["sku"] == "FARINE-25KG"
    assert out["items"][0]["movement"] == "IN"


def test_validate_rejette_unite_inconnue():
    bad = lot()
    bad["items"][0]["unit"] = "tonne"
    with pytest.raises(handler.InvalidLot):
        handler.validate(bad)


def test_signature_conforme_au_contrat(monkeypatch):
    monkeypatch.setattr(handler, "_secret", b"dev-secret-change-me")
    body = b'{"a":1}'
    expected = hmac.new(b"dev-secret-change-me", b"1794700000.n." + body, hashlib.sha256).hexdigest()
    assert handler.sign(body, "1794700000", "n") == "sha256=" + expected


def test_doublon_ignore(monkeypatch):
    monkeypatch.setattr(handler, "claim", lambda _id: False)
    sent = []
    monkeypatch.setattr(handler, "send_to_azure", lambda l: sent.append(l))
    assert handler.process(EVENT["Records"][0]["body"]) == "duplicate"
    assert sent == []


def test_echec_envoi_libere_la_reservation(monkeypatch):
    released = []
    monkeypatch.setattr(handler, "claim", lambda _id: True)
    monkeypatch.setattr(handler, "release", lambda i: released.append(i))

    def boom(_):
        raise RuntimeError("Azure indisponible")

    monkeypatch.setattr(handler, "send_to_azure", boom)
    result = handler.handler(EVENT, None)
    assert result["batchItemFailures"] == [{"itemIdentifier": EVENT["Records"][0]["messageId"]}]
    assert released == ["FORM-P2-0001"]
