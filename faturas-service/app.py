"""faturas-service: emissão de faturas com cálculo de IVA."""
import os
from decimal import ROUND_HALF_UP, Decimal

import requests
from flask import Flask, jsonify, request

CLIENTES_URL = os.getenv("CLIENTES_URL", "http://localhost:5001")
TAXAS_IVA = {0, 6, 13, 23}


def arredondar(valor: Decimal) -> float:
    return float(valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calcular_totais(linhas):
    """Devolve (linhas_calculadas, subtotal, iva, total). Lança ValueError se inválido."""
    if not linhas:
        raise ValueError("A fatura tem de ter pelo menos uma linha")
    subtotal = iva = Decimal(0)
    resultado = []
    for linha in linhas:
        quantidade = Decimal(str(linha.get("quantidade", 0)))
        preco = Decimal(str(linha.get("preco_unitario", 0)))
        taxa = int(linha.get("taxa_iva", 23))
        if quantidade <= 0 or preco < 0:
            raise ValueError("Quantidade e preço têm de ser positivos")
        if taxa not in TAXAS_IVA:
            raise ValueError(f"Taxa de IVA inválida: {taxa}")
        base = quantidade * preco
        valor_iva = base * taxa / 100
        subtotal += base
        iva += valor_iva
        resultado.append({
            "descricao": linha.get("descricao", ""),
            "quantidade": float(quantidade),
            "preco_unitario": float(preco),
            "taxa_iva": taxa,
            "base": arredondar(base),
            "iva": arredondar(valor_iva),
        })
    return resultado, arredondar(subtotal), arredondar(iva), arredondar(subtotal + iva)


def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False
    faturas = {}

    @app.get("/health")
    def health():
        return jsonify(status="ok", servico="faturas-service")

    @app.get("/api/faturas")
    def listar():
        return jsonify(list(faturas.values()))

    @app.get("/api/faturas/<int:fatura_id>")
    def obter(fatura_id):
        fatura = faturas.get(fatura_id)
        if fatura is None:
            return jsonify(erro="Fatura não encontrada"), 404
        return jsonify(fatura)

    @app.post("/api/faturas")
    def criar():
        dados = request.get_json(silent=True) or {}
        nif = str(dados.get("nif", ""))

        # Chamada ao outro microsserviço
        try:
            r = requests.get(f"{CLIENTES_URL}/api/clientes/{nif}", timeout=3)
        except requests.RequestException:
            return jsonify(erro="clientes-service indisponível"), 503
        if r.status_code == 404:
            return jsonify(erro="Cliente não encontrado"), 404
        if r.status_code != 200:
            return jsonify(erro="Erro no clientes-service"), 502
        cliente = r.json()

        try:
            linhas, subtotal, iva, total = calcular_totais(dados.get("linhas", []))
        except (ValueError, ArithmeticError) as e:
            return jsonify(erro=str(e)), 400

        fatura_id = len(faturas) + 1
        faturas[fatura_id] = {
            "id": fatura_id,
            "cliente": cliente,
            "linhas": linhas,
            "subtotal": subtotal,
            "iva": iva,
            "total": total,
        }
        return jsonify(faturas[fatura_id]), 201

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)