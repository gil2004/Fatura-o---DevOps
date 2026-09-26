import os

import requests

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