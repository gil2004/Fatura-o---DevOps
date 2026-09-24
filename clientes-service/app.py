"""clientes-service: gestão de clientes e validação de NIF."""
from flask import Flask, jsonify, request


def nif_valido(nif: str) -> bool:
    """Valida um NIF português (9 dígitos + dígito de controlo)."""
    if not (isinstance(nif, str) and len(nif) == 9 and nif.isdigit()):
        return False
    if nif[0] not in "1235689":
        return False
    soma = sum(int(nif[i]) * (9 - i) for i in range(8))
    controlo = 11 - soma % 11
    if controlo >= 10:
        controlo = 0
    return controlo == int(nif[8])


def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False
    clientes = {
        "501964843": {"nif": "501964843", "nome": "Empresa Exemplo, Lda", "email": "geral@exemplo.pt"},
        "123456789": {"nif": "123456789", "nome": "João Silva", "email": "joao@mail.pt"},
    }

    @app.get("/health")
    def health():
        return jsonify(status="ok", servico="clientes-service")

    @app.get("/api/clientes")
    def listar():
        return jsonify(list(clientes.values()))

    @app.get("/api/clientes/<nif>")
    def obter(nif):
        cliente = clientes.get(nif)
        if cliente is None:
            return jsonify(erro="Cliente não encontrado"), 404
        return jsonify(cliente)

    @app.post("/api/clientes")
    def criar():
        dados = request.get_json(silent=True) or {}
        nif = str(dados.get("nif", ""))
        nome = dados.get("nome")
        if not nome:
            return jsonify(erro="O campo 'nome' é obrigatório"), 400
        if not nif_valido(nif):
            return jsonify(erro="NIF inválido"), 400
        if nif in clientes:
            return jsonify(erro="Cliente já existe"), 409
        clientes[nif] = {"nif": nif, "nome": nome, "email": dados.get("email")}
        return jsonify(clientes[nif]), 201

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)