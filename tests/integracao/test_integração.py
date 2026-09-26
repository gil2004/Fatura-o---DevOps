import os 

import requests

CLIENTES_URL = os.getenv("CLIENTES_URL", "http://localhost:5001")
FATURAS_URL = os.getenv("FATURAS_URL", "http://localhost:5002")

LINHAS = [
    {"descricao": "Consultoria", "quantidade": 2, "preco_unitario": 100, "taxa_iva": 23},
]

def test_servicos_ativos():
    assert requests.get(f"{CLIENTES_URL}/health", timeout=5).status_code == 200
    assert requests.get(f"{FATURAS_URL}/health", timeout=5).status_code == 200

def test_fatura_usa_dados_cliente():
    r = requests.post(f"{FATURAS_URL}/api/faturas", json={"nif": "501964843", "linhas": LINHAS}, timeout=5)
    assert r.status_code == 201
    assert r.json()["cliente"]["nome"] == "Empresa Exemplo, Lda"
    assert r.json()["total"] == 246.0

def test_fatura_cliente_inexistente():
    r = requests.post(f"{FATURAS_URL}/api/faturas", json={"nif": "999999990", "linhas": LINHAS}, timeout=5)
    assert r.status_code == 404