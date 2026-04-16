# SGR MVP - Sistema de Gestão Integrada REVISA

MVP funcional criado a partir dos documentos `Concepção MVP SGR.docx` e `wireframe_backlog_revisa_mvp.md`.

## O que foi implementado

- API FastAPI versionada em `/api/v1`.
- Banco SQLite local em `data/sgr_mvp.db`, com estrutura preparada para migração posterior para PostgreSQL.
- Autenticação JWT, perfis e escopo por vereador/polo.
- Cadastros de usuários, vereadores, emendas, polos, beneficiários, modalidades, turmas e fornecedores.
- Fluxo de captação mobile com sincronização.
- Inscrições, frequência, ocorrências e encaminhamentos.
- Requisições de compra, aprovação/reprovação, execução de compra, movimentação de emenda e nota fiscal.
- Dashboards, relatórios por polo/vereador, controle de emendas e auditoria.
- Frontend web estático servido pela própria API.

## Como executar

```powershell
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Abra:

```text
http://127.0.0.1:8000
```

Documentação da API:

```text
http://127.0.0.1:8000/docs
```

## Acessos de teste

```text
admin@sgr.local / admin123
revisa@sgr.local / revisa123
vereador@sgr.local / vereador123
polo@sgr.local / polo123
operador@sgr.local / operador123
mobile@sgr.local / mobile123
```

## Testes

```powershell
python -m pytest
```

## Estrutura

```text
apps/
  api/
    app/
      main.py       # rotas e regras de negócio
      models.py     # modelo relacional SQLAlchemy
      schemas.py    # contratos de entrada
      auth.py       # senha e JWT
      seed.py       # dados iniciais
  web/
    index.html
    styles.css
    app.js
tests/
  test_api.py
```

## Observações

O MVP usa SQLite para rodar imediatamente no workspace. A documentação recomenda PostgreSQL para produção; a camada SQLAlchemy já deixa essa troca concentrada em `SGR_DATABASE_URL`.
