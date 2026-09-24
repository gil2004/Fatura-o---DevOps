import pytest
import requests

from app import CLIENTES_URL, calcular_totais, create_app

CLIENTE = {"nif": "501964843", "nome": "Empresa Exemplo, Lda", "email": "geral@exemplo.pt"}
LINHAS = [
    {"descricao": "Consultoria", "quantidade": 2, "preco_unitario": 100, "taxa_iva": 23},
    {"descricao": "Livro", "quantidade": 1, "preco_unitario": 10, "taxa_iva": 6},
]


@pytest.fixture
def client():
    return create_app().test_client()


def test_calcular_totais():
    _, subtotal, iva, total = calcular_totais(LINHAS)
    assert subtotal == 210.00
    assert iva == 46.60
    assert total == 256.60


@pytest.mark.parametrize("linhas", [
    [],
    [{"quantidade": 1, "preco_unitario": 10, "taxa_iva": 20}],
    [{"quantidade": 0, "preco_unitario": 10, "taxa_iva": 23}],
])
def test_calcular_totais_invalido(linhas):
    with pytest.raises(ValueError):
        calcular_totais(linhas)


def test_health(client):
    assert client.get("/health").get_json()["status"] == "ok"


def test_criar_fatura(client, requests_mock):
    requests_mock.get(f"{CLIENTES_URL}/api/clientes/501964843", json=CLIENTE)
    r = client.post("/api/faturas", json={"nif": "501964843", "linhas": LINHAS})
    assert r.status_code == 201
    assert r.get_json()["total"] == 256.60


def test_criar_fatura_cliente_inexistente(client, requests_mock):
    requests_mock.get(f"{CLIENTES_URL}/api/clientes/999999990", status_code=404)
    r = client.post("/api/faturas", json={"nif": "999999990", "linhas": LINHAS})
    assert r.status_code == 404


def test_criar_fatura_clientes_indisponivel(client, requests_mock):
    requests_mock.get(f"{CLIENTES_URL}/api/clientes/501964843", exc=requests.ConnectionError)
    r = client.post("/api/faturas", json={"nif": "501964843", "linhas": LINHAS})
    assert r.status_code == 503


def test_fatura_inexistente(client):
    assert client.get("/api/faturas/42").status_code == 404