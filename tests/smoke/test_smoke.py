import os

import requests

import time

JAEGER_URL = os.getenv("JAEGER_URL", "http://localhost:16686")
CLIENTES_URL = os.getenv("CLIENTES_URL", "http://localhost:5001")
FATURAS_URL = os.getenv("FATURAS_URL", "http://localhost:5002")

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
        resposta = requests.get(
            f"{JAEGER_URL}/api/traces",
            params={"service": "faturas-service", "operation": "POST /api/faturas", "limit": 5},
            timeout=5,
        ).json()
        for t in resposta.get("data", []):
            servicos = {p["serviceName"] for p in t["processes"].values()}
            if {"faturas-service", "clientes-service"} <= servicos:
                return
    raise AssertionError("Nenhum trace com os dois serviços chegou ao Jaeger")