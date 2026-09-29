import os
import time
from datetime import datetime, timedelta, timezone

import requests

CLIENTES_URL = os.getenv("CLIENTES_URL", "http://localhost:5001")
FATURAS_URL = os.getenv("FATURAS_URL", "http://localhost:5002")
JAEGER_URL = os.getenv("JAEGER_URL", "http://localhost:16686")


def test_clientes_health():
    assert requests.get(f"{CLIENTES_URL}/health", timeout=5).json()["status"] == "ok"


def test_faturas_health():
    assert requests.get(f"{FATURAS_URL}/health", timeout=5).json()["status"] == "ok"


def test_fatura_ponta_a_ponta():
    linhas = [{"descricao": "Teste", "quantidade": 1, "preco_unitario": 10, "taxa_iva": 23}]
    r = requests.post(f"{FATURAS_URL}/api/faturas", json={"nif": "123456789", "linhas": linhas}, timeout=5)
    assert r.status_code == 201
    assert r.json()["total"] == 12.3


def test_trace_chega_ao_jaeger():
    linhas = [{"descricao": "Trace", "quantidade": 1, "preco_unitario": 10, "taxa_iva": 23}]
    r = requests.post(f"{FATURAS_URL}/api/faturas", json={"nif": "123456789", "linhas": linhas}, timeout=5)
    assert r.status_code == 201

    # os traces são enviados em lotes: tenta durante até 30 segundos
    for _ in range(15):
        time.sleep(2)
        agora = datetime.now(timezone.utc)
        resposta = requests.get(
            f"{JAEGER_URL}/api/v3/traces",
            params={
                "query.service_name": "faturas-service",
                "query.start_time_min": (agora - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "query.start_time_max": agora.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            timeout=5,
        )
        if resposta.status_code != 200:
            continue
        # recolhe o service.name de cada grupo de spans da resposta
        servicos = set()
        for rs in resposta.json()["result"]["resourceSpans"]:
            for attr in rs["resource"]["attributes"]:
                if attr["key"] == "service.name":
                    servicos.add(attr["value"]["stringValue"])
        if {"faturas-service", "clientes-service"} <= servicos:
            return
    raise AssertionError("Os dois serviços não enviaram traces ao Jaeger")