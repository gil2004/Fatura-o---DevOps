import pytest
from app import create_app, nif_valido


@pytest.fixture
def client():
    return create_app().test_client()


@pytest.mark.parametrize("nif", ["501964843", "123456789", "234567899"])
def test_nif_valido(nif):
    assert nif_valido(nif)


@pytest.mark.parametrize("nif", ["501964840", "12345678", "abcdefghi", "423456789", ""])
def test_nif_invalido(nif):
    assert not nif_valido(nif)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_listar_clientes(client):
    r = client.get("/api/clientes")
    assert r.status_code == 200
    assert len(r.get_json()) == 2


def test_obter_cliente_existente(client):
    r = client.get("/api/clientes/501964843")
    assert r.status_code == 200
    assert r.get_json()["nome"] == "Empresa Exemplo, Lda"


def test_obter_cliente_inexistente(client):
    assert client.get("/api/clientes/234567899").status_code == 404


def test_criar_cliente(client):
    r = client.post("/api/clientes", json={"nif": "234567899", "nome": "Maria Costa"})
    assert r.status_code == 201


def test_criar_cliente_nif_invalido(client):
    r = client.post("/api/clientes", json={"nif": "111111111", "nome": "X"})
    assert r.status_code == 400


def test_criar_cliente_duplicado(client):
    r = client.post("/api/clientes", json={"nif": "501964843", "nome": "Outra"})
    assert r.status_code == 409