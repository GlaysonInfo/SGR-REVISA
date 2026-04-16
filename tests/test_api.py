import os
import tempfile

db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
db_file.close()
os.environ["SGR_DATABASE_URL"] = f"sqlite:///{db_file.name}"

from fastapi.testclient import TestClient

from apps.api.app.main import app


def auth(client: TestClient, login: str = "admin@sgr.local", senha: str = "admin123") -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"login": login, "senha": senha})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_login_and_dashboard():
    with TestClient(app) as client:
        headers = auth(client)
        response = client.get("/api/v1/dashboard/institucional", headers=headers)
        assert response.status_code == 200
        assert response.json()["total_beneficiarios"] >= 2


def test_scope_limits_polo_user_to_one_polo():
    with TestClient(app) as client:
        headers = auth(client, "polo@sgr.local", "polo123")
        response = client.get("/api/v1/polos", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1


def test_beneficiario_cpf_unique():
    with TestClient(app) as client:
        headers = auth(client)
        polos = client.get("/api/v1/polos", headers=headers).json()
        payload = {
            "nome": "Beneficiaria Teste",
            "cpf": "52998224725",
            "telefone": "31988887777",
            "polo_ids": [polos[0]["id"]],
        }
        created = client.post("/api/v1/beneficiarios", json=payload, headers=headers)
        assert created.status_code == 200, created.text
        duplicated = client.post("/api/v1/beneficiarios", json=payload, headers=headers)
        assert duplicated.status_code == 409


def test_mobile_sync_creates_beneficiario():
    with TestClient(app) as client:
        headers = auth(client, "mobile@sgr.local", "mobile123")
        payload = {
            "beneficiario": {
                "nome": "Cadastro Mobile Teste",
                "cpf": "15350946056",
                "telefone": "31977776666",
            },
            "responsavel": {"nome": "Responsavel Teste"},
            "demanda_imediata": "Acompanhamento inicial",
            "sugestao_tipo": "SUGESTAO",
            "sugestao_descricao": "Ampliar horarios",
        }
        response = client.post("/api/v1/mobile/beneficiarios", json=payload, headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "sincronizado"


def test_compra_consumes_emenda_balance():
    with TestClient(app) as client:
        headers = auth(client)
        polo = client.get("/api/v1/polos", headers=headers).json()[0]
        fornecedor = client.get("/api/v1/fornecedores", headers=headers).json()[0]
        emenda = client.get("/api/v1/emendas", headers=headers).json()[0]
        before = emenda["valor_disponivel"]
        req_payload = {
            "polo_id": polo["id"],
            "descricao": "Compra de teste automatizado",
            "prioridade": "NORMAL",
            "status": "ABERTA",
            "itens": [{"descricao": "Item teste", "quantidade": 1, "unidade": "un", "valor_estimado": 100}],
        }
        req = client.post("/api/v1/requisicoes-compra", json=req_payload, headers=headers)
        assert req.status_code == 200, req.text
        req_id = req.json()["id"]
        assert client.post(f"/api/v1/requisicoes-compra/{req_id}/aprovar", headers=headers).status_code == 200
        compra = client.post(
            "/api/v1/compras",
            json={"requisicao_id": req_id, "fornecedor_id": fornecedor["id"], "emenda_id": emenda["id"], "valor_total": 100},
            headers=headers,
        )
        assert compra.status_code == 200, compra.text
        after = [item for item in client.get("/api/v1/emendas", headers=headers).json() if item["id"] == emenda["id"]][0]
        assert after["valor_disponivel"] == before - 100
