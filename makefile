# Makefile — Projeto Final DevOps
VENV := venv
PY   := "$(CURDIR)/$(VENV)/bin/python"
FATURA := '{"nif":"501964843","linhas":[{"descricao":"Consultoria","quantidade":2,"preco_unitario":100,"taxa_iva":23}]}'

.PHONY: help venv testes-unitarios servicos-local repositorio pipeline docker jaeger limpeza

help:
	@echo "Passos, por ordem:"
	@echo "  make venv              - criar o venv e instalar dependencias"
	@echo "  make testes-unitarios  - lint e testes unitarios"
	@echo "  make servicos-local    - comunicacao entre os servicos (sem Docker)"
	@echo "  make repositorio       - estado do repositorio Git"
	@echo "  make pipeline          - enviar para o GitHub (DEV -> STG -> PRD)"
	@echo "  make docker            - Docker Compose + testes de integracao"
	@echo "  make jaeger            - smoke tests + verificacao do tracing"
	@echo "  make limpeza           - paragem, destruicao e limpeza"

venv:
	python3 -m venv $(VENV)
	$(PY) -m pip install -r requirements.txt

testes-unitarios:
	$(PY) -m ruff check .
	cd clientes-service && $(PY) -m pytest -v --cov=app
	cd faturas-service && $(PY) -m pytest -v --cov=app

servicos-local:
	$(PY) -m gunicorn --chdir clientes-service -b 127.0.0.1:5001 --daemon --pid "$(CURDIR)/.clientes.pid" app:app
	$(PY) -m gunicorn --chdir faturas-service -b 127.0.0.1:5002 --daemon --pid "$(CURDIR)/.faturas.pid" app:app
	sleep 3
	curl -s -X POST localhost:5002/api/faturas -H "Content-Type: application/json" -d $(FATURA); echo
	kill $$(cat .clientes.pid) $$(cat .faturas.pid)
	rm -f .clientes.pid .faturas.pid

docker:
	docker compose up -d --build
	docker compose ps
	sleep 5
	curl -s -X POST localhost:5002/api/faturas -H "Content-Type: application/json" -d $(FATURA); echo
	$(PY) -m pytest -v tests/integracao

jaeger:
	$(PY) -m pytest -v tests/smoke
	@echo "Interface do Jaeger: http://localhost:16686"

limpeza:
	docker compose down --rmi all -v
	docker builder prune -f
	docker ps -a
	docker images
	rm -rf $(VENV) .pytest_cache .ruff_cache
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name ".coverage" -delete