from datetime import date, datetime
import json
import re
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from jwt import PyJWTError
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from .auth import create_access_token, decode_token, hash_password, verify_password
from .database import Base, ROOT_DIR, engine, get_db
from .models import (
    AreaModalidade,
    ArquivoUpload,
    Auditoria,
    Beneficiario,
    BeneficiarioPolo,
    BeneficiarioVereador,
    Compra,
    DemandaImediata,
    Emenda,
    Encaminhamento,
    Fornecedor,
    Frequencia,
    GrupoFamiliar,
    Inscricao,
    ItemRequisicao,
    Modalidade,
    MovimentacaoEmenda,
    NotaFiscal,
    Ocorrencia,
    Polo,
    RequisicaoCompra,
    Responsavel,
    SugestaoCritica,
    Turma,
    Usuario,
    Vereador,
)
from .schemas import (
    AreaIn,
    BeneficiarioIn,
    CompraIn,
    EmendaIn,
    EncaminhamentoIn,
    FornecedorIn,
    FrequenciaLoteIn,
    InscricaoIn,
    LoginIn,
    MobileCadastroIn,
    ModalidadeIn,
    NotaFiscalIn,
    OcorrenciaIn,
    PoloIn,
    RequisicaoIn,
    StatusPatch,
    SyncIn,
    TurmaIn,
    UserIn,
    UserUpdate,
    VereadorIn,
)
from .seed import seed_database


ADMIN_ROLES = {"Super Admin", "Gestor Institucional REVISA"}
POLO_ROLES = {"Gestor de Polo", "Operador de Polo", "Captador Mobile"}
FINANCE_ROLES = {"Super Admin", "Gestor Institucional REVISA"}
security = HTTPBearer(auto_error=False)
api = APIRouter(prefix="/api/v1")


def create_app() -> FastAPI:
    app = FastAPI(
        title="SGR MVP - Sistema de Gestao Integrada REVISA",
        version="0.1.0",
        description="MVP funcional baseado na documentacao REVISA.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api)

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)
        db = next(get_db())
        try:
            seed_database(db)
        finally:
            db.close()

    assets_dir = ROOT_DIR / "Imagens"
    web_dir = ROOT_DIR / "apps" / "web"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    if web_dir.exists():
        app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")
    return app


@api.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


def only_digits(value: str | None) -> str | None:
    if value is None:
        return None
    digits = re.sub(r"\D", "", value)
    return digits or None


def validate_cpf(cpf: str | None) -> str | None:
    digits = only_digits(cpf)
    if not digits:
        return None
    if len(digits) != 11 or len(set(digits)) == 1:
        raise HTTPException(status_code=422, detail="CPF invalido.")
    numbers = [int(d) for d in digits]
    for length in (9, 10):
        total = sum(numbers[i] * ((length + 1) - i) for i in range(length))
        check = (total * 10) % 11
        if check == 10:
            check = 0
        if check != numbers[length]:
            raise HTTPException(status_code=422, detail="CPF invalido.")
    return digits


def value_for_json(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def as_dict(obj: Any, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    data = {column.name: value_for_json(getattr(obj, column.name)) for column in obj.__table__.columns}
    if extra:
        data.update(extra)
    return data


def audit(
    db: Session,
    user: Usuario | None,
    entidade: str,
    entidade_id: int | None,
    acao: str,
    before: Any = None,
    after: Any = None,
) -> None:
    db.add(
        Auditoria(
            entidade=entidade,
            entidade_id=entidade_id,
            acao=acao,
            valor_anterior=json.dumps(before, ensure_ascii=False, default=str) if before is not None else None,
            valor_novo=json.dumps(after, ensure_ascii=False, default=str) if after is not None else None,
            usuario_id=user.id if user else None,
        )
    )


def has_records(db: Session, model: Any, *criteria: Any) -> bool:
    return bool(db.scalar(select(func.count()).select_from(model).where(*criteria)))


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> Usuario:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticacao obrigatoria.")
    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido.")
    user = db.get(Usuario, user_id)
    if not user or not user.ativo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inativo ou inexistente.")
    return user


def require_admin(user: Usuario) -> None:
    if user.perfil not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Perfil sem permissao para esta acao.")


def require_finance(user: Usuario) -> None:
    if user.perfil not in FINANCE_ROLES:
        raise HTTPException(status_code=403, detail="Perfil sem permissao financeira.")


def can_see_all(user: Usuario) -> bool:
    return user.perfil in ADMIN_ROLES


def scoped_polo_ids(db: Session, user: Usuario) -> list[int]:
    if can_see_all(user):
        return db.execute(select(Polo.id)).scalars().all()
    if user.polo_id:
        return [user.polo_id]
    if user.vereador_id:
        return db.execute(select(Polo.id).where(Polo.vereador_id == user.vereador_id)).scalars().all()
    return []


def scoped_vereador_ids(db: Session, user: Usuario) -> list[int]:
    if can_see_all(user):
        return db.execute(select(Vereador.id)).scalars().all()
    if user.vereador_id:
        return [user.vereador_id]
    if user.polo_id:
        polo = db.get(Polo, user.polo_id)
        return [polo.vereador_id] if polo else []
    return []


def ensure_polo_in_scope(db: Session, user: Usuario, polo_id: int) -> Polo:
    polo = db.get(Polo, polo_id)
    if not polo:
        raise HTTPException(status_code=404, detail="Polo nao encontrado.")
    if not can_see_all(user) and polo_id not in scoped_polo_ids(db, user):
        raise HTTPException(status_code=403, detail="Polo fora do escopo do usuario.")
    return polo


def ensure_vereador_in_scope(db: Session, user: Usuario, vereador_id: int) -> Vereador:
    vereador = db.get(Vereador, vereador_id)
    if not vereador:
        raise HTTPException(status_code=404, detail="Vereador nao encontrado.")
    if not can_see_all(user) and vereador_id not in scoped_vereador_ids(db, user):
        raise HTTPException(status_code=403, detail="Vereador fora do escopo do usuario.")
    return vereador


def beneficiary_visible(db: Session, user: Usuario, beneficiario_id: int) -> bool:
    if can_see_all(user):
        return True
    polo_ids = scoped_polo_ids(db, user)
    if not polo_ids:
        return False
    exists = db.scalar(
        select(BeneficiarioPolo.id).where(
            BeneficiarioPolo.beneficiario_id == beneficiario_id,
            BeneficiarioPolo.polo_id.in_(polo_ids),
        )
    )
    return exists is not None


def serialize_beneficiario(beneficiario: Beneficiario) -> dict[str, Any]:
    vereadores = [{"id": link.vereador_id, "nome": link.vereador.nome, "ativo": link.ativo} for link in beneficiario.vereadores]
    polos = [{"id": link.polo_id, "nome": link.polo.nome, "status": link.status} for link in beneficiario.polos]
    return as_dict(
        beneficiario,
        {
            "vereador_ids": [item["id"] for item in vereadores],
            "polo_ids": [item["id"] for item in polos],
            "vereadores": vereadores,
            "polos": polos,
        },
    )


def serialize_turma(turma: Turma) -> dict[str, Any]:
    ativos = [insc for insc in turma.inscricoes if insc.status == "ATIVA"]
    return as_dict(
        turma,
        {
            "polo_nome": turma.polo.nome if turma.polo else None,
            "modalidade_nome": turma.modalidade.nome if turma.modalidade else None,
            "area_nome": turma.modalidade.area.nome if turma.modalidade and turma.modalidade.area else None,
            "inscritos_ativos": len(ativos),
            "vagas_disponiveis": max(turma.capacidade - len(ativos), 0),
        },
    )


def serialize_requisicao(requisicao: RequisicaoCompra) -> dict[str, Any]:
    total_estimado = sum((item.quantidade or 0) * (item.valor_estimado or 0) for item in requisicao.itens)
    return as_dict(
        requisicao,
        {
            "polo_nome": requisicao.polo.nome if requisicao.polo else None,
            "vereador_nome": requisicao.vereador.nome if requisicao.vereador else None,
            "total_estimado": total_estimado,
            "itens": [as_dict(item) for item in requisicao.itens],
        },
    )


def set_beneficiario_links(db: Session, beneficiario: Beneficiario, vereador_ids: list[int], polo_ids: list[int]) -> None:
    all_vereador_ids = set(vereador_ids)
    for polo_id in polo_ids:
        polo = db.get(Polo, polo_id)
        if not polo:
            raise HTTPException(status_code=404, detail=f"Polo {polo_id} nao encontrado.")
        all_vereador_ids.add(polo.vereador_id)

    for vereador_id in all_vereador_ids:
        if not db.get(Vereador, vereador_id):
            raise HTTPException(status_code=404, detail=f"Vereador {vereador_id} nao encontrado.")
        existing = db.scalar(
            select(BeneficiarioVereador).where(
                BeneficiarioVereador.beneficiario_id == beneficiario.id,
                BeneficiarioVereador.vereador_id == vereador_id,
            )
        )
        if existing:
            existing.ativo = True
        else:
            db.add(BeneficiarioVereador(beneficiario_id=beneficiario.id, vereador_id=vereador_id))

    for polo_id in polo_ids:
        existing = db.scalar(
            select(BeneficiarioPolo).where(
                BeneficiarioPolo.beneficiario_id == beneficiario.id,
                BeneficiarioPolo.polo_id == polo_id,
            )
        )
        if existing:
            existing.status = "ATIVO"
        else:
            db.add(BeneficiarioPolo(beneficiario_id=beneficiario.id, polo_id=polo_id))


def ensure_unique_beneficiario(db: Session, payload: BeneficiarioIn, current_id: int | None = None) -> None:
    cpf = validate_cpf(payload.cpf)
    if cpf:
        query = select(Beneficiario).where(Beneficiario.cpf == cpf)
        if current_id:
            query = query.where(Beneficiario.id != current_id)
        if db.scalar(query):
            raise HTTPException(status_code=409, detail="CPF ja cadastrado para outro beneficiario.")


def potential_duplicates(db: Session, payload: BeneficiarioIn, current_id: int | None = None) -> list[Beneficiario]:
    filters = [func.lower(Beneficiario.nome) == payload.nome.lower()]
    if payload.data_nascimento:
        filters.append(Beneficiario.data_nascimento == payload.data_nascimento)
    if payload.telefone:
        filters.append(Beneficiario.telefone == only_digits(payload.telefone))
    query = select(Beneficiario).where(and_(*filters))
    if current_id:
        query = query.where(Beneficiario.id != current_id)
    return db.execute(query.limit(5)).scalars().all()


@api.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@api.post("/auth/login")
def login(payload: LoginIn, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = db.scalar(select(Usuario).where(func.lower(Usuario.email_login) == payload.login.lower()))
    if not user or not verify_password(payload.senha, user.senha_hash):
        raise HTTPException(status_code=401, detail="Credenciais invalidas.")
    if not user.ativo:
        raise HTTPException(status_code=403, detail="Usuario inativo.")
    user.ultimo_login = datetime.utcnow()
    audit(db, user, "usuario", user.id, "LOGIN")
    db.commit()
    token = create_access_token(str(user.id), user.perfil)
    return {
        "access_token": token,
        "token_type": "bearer",
        "perfil": user.perfil,
        "usuario": as_dict(user, {"senha_hash": None}),
        "escopo": {"vereador_id": user.vereador_id, "polo_id": user.polo_id},
    }


@api.get("/me")
def me(user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    return as_dict(user, {"senha_hash": None})


@api.get("/dashboard/institucional")
def dashboard_institucional(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    vereador_ids = scoped_vereador_ids(db, user)
    polo_ids = scoped_polo_ids(db, user)
    beneficiaries_query = select(func.count(Beneficiario.id))
    if not can_see_all(user):
        beneficiaries_query = (
            select(func.count(func.distinct(Beneficiario.id)))
            .join(BeneficiarioPolo)
            .where(BeneficiarioPolo.polo_id.in_(polo_ids or [-1]))
        )
    total_emendas = db.scalar(select(func.coalesce(func.sum(Emenda.valor_total), 0)).where(Emenda.vereador_id.in_(vereador_ids or [-1])))
    saldo = db.scalar(select(func.coalesce(func.sum(Emenda.valor_disponivel), 0)).where(Emenda.vereador_id.in_(vereador_ids or [-1])))
    compras_total = db.scalar(select(func.coalesce(func.sum(Compra.valor_total), 0)).join(Emenda).where(Emenda.vereador_id.in_(vereador_ids or [-1])))
    reqs = db.execute(
        select(RequisicaoCompra.status, func.count(RequisicaoCompra.id))
        .where(RequisicaoCompra.vereador_id.in_(vereador_ids or [-1]))
        .group_by(RequisicaoCompra.status)
    ).all()
    return {
        "total_beneficiarios": db.scalar(beneficiaries_query) or 0,
        "polos_ativos": db.scalar(select(func.count(Polo.id)).where(Polo.id.in_(polo_ids or [-1]), Polo.status == "ATIVO")) or 0,
        "vereadores": len(vereador_ids),
        "valor_emendas": total_emendas or 0,
        "saldo_emendas": saldo or 0,
        "compras_executadas": compras_total or 0,
        "requisicoes_por_status": [{"status": req_status, "total": total} for req_status, total in reqs],
        "alertas": ["Requisicoes em analise aguardam aprovacao.", "Saldo de emendas deve ser acompanhado antes de executar compras."],
    }


@api.get("/polos/{polo_id}/dashboard")
def dashboard_polo(polo_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    polo = ensure_polo_in_scope(db, user, polo_id)
    turma_ids = db.execute(select(Turma.id).where(Turma.polo_id == polo_id)).scalars().all()
    inscritos = db.scalar(select(func.count(Inscricao.id)).where(Inscricao.turma_id.in_(turma_ids or [-1]))) or 0
    presentes = db.scalar(select(func.count(Frequencia.id)).join(Inscricao).where(Inscricao.turma_id.in_(turma_ids or [-1]), Frequencia.presente.is_(True))) or 0
    total_freq = db.scalar(select(func.count(Frequencia.id)).join(Inscricao).where(Inscricao.turma_id.in_(turma_ids or [-1]))) or 0
    return {
        "polo": as_dict(polo),
        "beneficiarios": db.scalar(select(func.count(BeneficiarioPolo.id)).where(BeneficiarioPolo.polo_id == polo_id)) or 0,
        "turmas": len(turma_ids),
        "inscricoes": inscritos,
        "frequencia_percentual": round((presentes / total_freq) * 100, 1) if total_freq else 0,
        "ocorrencias": db.scalar(select(func.count(Ocorrencia.id)).where(Ocorrencia.polo_id == polo_id)) or 0,
        "requisicoes": db.scalar(select(func.count(RequisicaoCompra.id)).where(RequisicaoCompra.polo_id == polo_id)) or 0,
    }


@api.get("/usuarios")
def list_usuarios(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    if can_see_all(user):
        usuarios = db.execute(select(Usuario).order_by(Usuario.nome)).scalars().all()
    else:
        usuarios = [user]
    return [as_dict(item, {"senha_hash": None}) for item in usuarios]


@api.post("/usuarios")
def create_usuario(payload: UserIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_admin(user)
    if db.scalar(select(Usuario).where(Usuario.email_login == payload.email_login)):
        raise HTTPException(status_code=409, detail="Login ja cadastrado.")
    novo = Usuario(
        nome=payload.nome,
        email_login=payload.email_login,
        senha_hash=hash_password(payload.senha),
        perfil=payload.perfil,
        vereador_id=payload.vereador_id,
        polo_id=payload.polo_id,
        ativo=payload.ativo,
    )
    db.add(novo)
    db.flush()
    audit(db, user, "usuario", novo.id, "CRIAR", after=as_dict(novo, {"senha_hash": None}))
    db.commit()
    db.refresh(novo)
    return as_dict(novo, {"senha_hash": None})


@api.put("/usuarios/{usuario_id}")
def update_usuario(usuario_id: int, payload: UserUpdate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_admin(user)
    alvo = db.get(Usuario, usuario_id)
    if not alvo:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")
    before = as_dict(alvo, {"senha_hash": None})
    data = payload.model_dump(exclude_unset=True)
    if "senha" in data and data["senha"]:
        alvo.senha_hash = hash_password(data.pop("senha"))
    for key, value in data.items():
        setattr(alvo, key, value)
    audit(db, user, "usuario", alvo.id, "ATUALIZAR", before=before, after=as_dict(alvo, {"senha_hash": None}))
    db.commit()
    db.refresh(alvo)
    return as_dict(alvo, {"senha_hash": None})


@api.patch("/usuarios/{usuario_id}/status")
def patch_usuario_status(usuario_id: int, payload: StatusPatch, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_admin(user)
    alvo = db.get(Usuario, usuario_id)
    if not alvo:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")
    before = as_dict(alvo, {"senha_hash": None})
    alvo.ativo = payload.status.upper() in {"ATIVO", "ATIVA", "TRUE", "1"}
    audit(db, user, "usuario", alvo.id, "ALTERAR_STATUS", before=before, after=as_dict(alvo, {"senha_hash": None}))
    db.commit()
    return as_dict(alvo, {"senha_hash": None})


@api.delete("/usuarios/{usuario_id}")
def delete_usuario(usuario_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, str]:
    require_admin(user)
    alvo = db.get(Usuario, usuario_id)
    if not alvo:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")
    if alvo.id == user.id:
        raise HTTPException(status_code=409, detail="O usuário logado não pode excluir a própria conta.")
    if any(
        [
            has_records(db, RequisicaoCompra, RequisicaoCompra.solicitante_usuario_id == usuario_id),
            has_records(db, Ocorrencia, Ocorrencia.usuario_id == usuario_id),
            has_records(db, ArquivoUpload, ArquivoUpload.usuario_upload_id == usuario_id),
            has_records(db, Auditoria, Auditoria.usuario_id == usuario_id),
        ]
    ):
        raise HTTPException(status_code=409, detail="Usuário possui histórico operacional e não pode ser excluído. Arquive o registro.")
    before = as_dict(alvo, {"senha_hash": None})
    db.delete(alvo)
    audit(db, user, "usuario", usuario_id, "EXCLUIR", before=before)
    db.commit()
    return {"status": "ok"}


@api.post("/usuarios/{usuario_id}/reset-senha")
def reset_senha(usuario_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, str]:
    require_admin(user)
    alvo = db.get(Usuario, usuario_id)
    if not alvo:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")
    alvo.senha_hash = hash_password("revisa123")
    audit(db, user, "usuario", alvo.id, "RESET_SENHA")
    db.commit()
    return {"senha_temporaria": "revisa123"}


@api.get("/vereadores")
def list_vereadores(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    ids = scoped_vereador_ids(db, user)
    items = db.execute(select(Vereador).where(Vereador.id.in_(ids or [-1])).order_by(Vereador.nome)).scalars().all()
    return [as_dict(item) for item in items]


@api.post("/vereadores")
def create_vereador(payload: VereadorIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_admin(user)
    item = Vereador(**payload.model_dump())
    db.add(item)
    db.flush()
    audit(db, user, "vereador", item.id, "CRIAR", after=as_dict(item))
    db.commit()
    db.refresh(item)
    return as_dict(item)


@api.put("/vereadores/{vereador_id}")
def update_vereador(vereador_id: int, payload: VereadorIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_admin(user)
    item = db.get(Vereador, vereador_id)
    if not item:
        raise HTTPException(status_code=404, detail="Vereador nao encontrado.")
    before = as_dict(item)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    audit(db, user, "vereador", item.id, "ATUALIZAR", before=before, after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.patch("/vereadores/{vereador_id}/status")
def patch_vereador_status(vereador_id: int, payload: StatusPatch, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_admin(user)
    item = db.get(Vereador, vereador_id)
    if not item:
        raise HTTPException(status_code=404, detail="Vereador nao encontrado.")
    before = as_dict(item)
    item.status = payload.status.upper()
    audit(db, user, "vereador", item.id, "ALTERAR_STATUS", before=before, after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.delete("/vereadores/{vereador_id}")
def delete_vereador(vereador_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, str]:
    require_admin(user)
    item = db.get(Vereador, vereador_id)
    if not item:
        raise HTTPException(status_code=404, detail="Vereador nao encontrado.")
    if any(
        [
            has_records(db, Polo, Polo.vereador_id == vereador_id),
            has_records(db, Emenda, Emenda.vereador_id == vereador_id),
            has_records(db, Usuario, Usuario.vereador_id == vereador_id),
            has_records(db, BeneficiarioVereador, BeneficiarioVereador.vereador_id == vereador_id),
            has_records(db, RequisicaoCompra, RequisicaoCompra.vereador_id == vereador_id),
        ]
    ):
        raise HTTPException(status_code=409, detail="Vereador possui vínculos e não pode ser excluído. Arquive o registro em vez de excluir.")
    before = as_dict(item)
    db.delete(item)
    audit(db, user, "vereador", vereador_id, "EXCLUIR", before=before)
    db.commit()
    return {"status": "ok"}


@api.get("/emendas/controle")
def controle_emendas(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    vereador_ids = scoped_vereador_ids(db, user)
    items = (
        db.execute(select(Emenda).options(joinedload(Emenda.vereador)).where(Emenda.vereador_id.in_(vereador_ids or [-1])))
        .scalars()
        .all()
    )
    return [
        as_dict(
            item,
            {
                "vereador_nome": item.vereador.nome,
                "percentual_utilizado": round((item.valor_utilizado / item.valor_total) * 100, 1) if item.valor_total else 0,
            },
        )
        for item in items
    ]


@api.get("/emendas")
def list_emendas(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    vereador_ids = scoped_vereador_ids(db, user)
    items = (
        db.execute(
            select(Emenda)
            .options(joinedload(Emenda.vereador))
            .where(Emenda.vereador_id.in_(vereador_ids or [-1]))
            .order_by(Emenda.ano.desc())
        )
        .scalars()
        .all()
    )
    return [as_dict(item, {"vereador_nome": item.vereador.nome}) for item in items]


@api.post("/emendas")
def create_emenda(payload: EmendaIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_finance(user)
    ensure_vereador_in_scope(db, user, payload.vereador_id)
    item = Emenda(**payload.model_dump(), valor_utilizado=0, valor_disponivel=payload.valor_total)
    db.add(item)
    db.flush()
    audit(db, user, "emenda", item.id, "CRIAR", after=as_dict(item))
    db.commit()
    db.refresh(item)
    return as_dict(item)


@api.put("/emendas/{emenda_id}")
def update_emenda(emenda_id: int, payload: EmendaIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_finance(user)
    item = db.get(Emenda, emenda_id)
    if not item:
        raise HTTPException(status_code=404, detail="Emenda nao encontrada.")
    ensure_vereador_in_scope(db, user, payload.vereador_id)
    before = as_dict(item)
    item.vereador_id = payload.vereador_id
    item.codigo = payload.codigo
    item.ano = payload.ano
    item.valor_total = payload.valor_total
    item.status = payload.status
    item.valor_disponivel = max(item.valor_total - item.valor_utilizado, 0)
    audit(db, user, "emenda", item.id, "ATUALIZAR", before=before, after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.patch("/emendas/{emenda_id}/status")
def patch_emenda_status(emenda_id: int, payload: StatusPatch, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_finance(user)
    item = db.get(Emenda, emenda_id)
    if not item:
        raise HTTPException(status_code=404, detail="Emenda nao encontrada.")
    ensure_vereador_in_scope(db, user, item.vereador_id)
    before = as_dict(item)
    item.status = payload.status.upper()
    audit(db, user, "emenda", item.id, "ALTERAR_STATUS", before=before, after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.delete("/emendas/{emenda_id}")
def delete_emenda(emenda_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, str]:
    require_finance(user)
    item = db.get(Emenda, emenda_id)
    if not item:
        raise HTTPException(status_code=404, detail="Emenda nao encontrada.")
    ensure_vereador_in_scope(db, user, item.vereador_id)
    if item.valor_utilizado > 0 or any(
        [
            has_records(db, MovimentacaoEmenda, MovimentacaoEmenda.emenda_id == emenda_id),
            has_records(db, Compra, Compra.emenda_id == emenda_id),
        ]
    ):
        raise HTTPException(status_code=409, detail="Emenda com utilização ou movimentações não pode ser excluída. Arquive o registro.")
    before = as_dict(item)
    db.delete(item)
    audit(db, user, "emenda", emenda_id, "EXCLUIR", before=before)
    db.commit()
    return {"status": "ok"}


@api.get("/emendas/{emenda_id}/movimentacoes")
def list_movimentacoes_emenda(emenda_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    emenda = db.get(Emenda, emenda_id)
    if not emenda:
        raise HTTPException(status_code=404, detail="Emenda nao encontrada.")
    ensure_vereador_in_scope(db, user, emenda.vereador_id)
    items = db.execute(
        select(MovimentacaoEmenda).where(MovimentacaoEmenda.emenda_id == emenda_id).order_by(MovimentacaoEmenda.data_movimento.desc())
    ).scalars().all()
    return [as_dict(item) for item in items]


@api.get("/polos")
def list_polos(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    ids = scoped_polo_ids(db, user)
    items = (
        db.execute(select(Polo).options(joinedload(Polo.vereador)).where(Polo.id.in_(ids or [-1])).order_by(Polo.nome))
        .scalars()
        .all()
    )
    return [as_dict(item, {"vereador_nome": item.vereador.nome}) for item in items]


@api.post("/polos")
def create_polo(payload: PoloIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_admin(user)
    ensure_vereador_in_scope(db, user, payload.vereador_id)
    item = Polo(**payload.model_dump())
    db.add(item)
    db.flush()
    audit(db, user, "polo", item.id, "CRIAR", after=as_dict(item))
    db.commit()
    db.refresh(item)
    return as_dict(item)


@api.put("/polos/{polo_id}")
def update_polo(polo_id: int, payload: PoloIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    item = ensure_polo_in_scope(db, user, polo_id)
    if user.perfil not in ADMIN_ROLES | {"Gestor de Polo"}:
        raise HTTPException(status_code=403, detail="Perfil sem permissao.")
    before = as_dict(item)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    audit(db, user, "polo", item.id, "ATUALIZAR", before=before, after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.patch("/polos/{polo_id}/status")
def patch_polo_status(polo_id: int, payload: StatusPatch, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_admin(user)
    item = ensure_polo_in_scope(db, user, polo_id)
    before = as_dict(item)
    item.status = payload.status.upper()
    audit(db, user, "polo", item.id, "ALTERAR_STATUS", before=before, after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.delete("/polos/{polo_id}")
def delete_polo(polo_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, str]:
    require_admin(user)
    item = ensure_polo_in_scope(db, user, polo_id)
    if any(
        [
            has_records(db, Turma, Turma.polo_id == polo_id),
            has_records(db, Usuario, Usuario.polo_id == polo_id),
            has_records(db, BeneficiarioPolo, BeneficiarioPolo.polo_id == polo_id),
            has_records(db, RequisicaoCompra, RequisicaoCompra.polo_id == polo_id),
            has_records(db, Ocorrencia, Ocorrencia.polo_id == polo_id),
            has_records(db, Encaminhamento, Encaminhamento.polo_id == polo_id),
            has_records(db, DemandaImediata, DemandaImediata.polo_id == polo_id),
            has_records(db, SugestaoCritica, SugestaoCritica.polo_id == polo_id),
        ]
    ):
        raise HTTPException(status_code=409, detail="Polo possui vínculos operacionais e não pode ser excluído. Arquive o registro.")
    before = as_dict(item)
    db.delete(item)
    audit(db, user, "polo", polo_id, "EXCLUIR", before=before)
    db.commit()
    return {"status": "ok"}


@api.get("/beneficiarios/duplicidade")
def check_duplicidade(
    cpf: str | None = None,
    nome: str | None = None,
    data_nascimento: date | None = None,
    telefone: str | None = None,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> dict[str, Any]:
    if cpf:
        normalized = validate_cpf(cpf)
        match = db.scalar(select(Beneficiario).where(Beneficiario.cpf == normalized))
        if match and beneficiary_visible(db, user, match.id):
            return {"duplicado": True, "tipo": "CPF", "beneficiarios": [serialize_beneficiario(match)]}
    if nome:
        payload = BeneficiarioIn(nome=nome, data_nascimento=data_nascimento, telefone=telefone)
        matches = [item for item in potential_duplicates(db, payload) if beneficiary_visible(db, user, item.id)]
        return {"duplicado": bool(matches), "tipo": "HEURISTICA", "beneficiarios": [serialize_beneficiario(item) for item in matches]}
    return {"duplicado": False, "beneficiarios": []}


@api.get("/beneficiarios/search")
def search_beneficiarios(q: str = Query(default=""), db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    query = select(Beneficiario).options(
        joinedload(Beneficiario.vereadores).joinedload(BeneficiarioVereador.vereador),
        joinedload(Beneficiario.polos).joinedload(BeneficiarioPolo.polo),
    )
    if q:
        pattern = f"%{q.lower()}%"
        query = query.where(or_(func.lower(Beneficiario.nome).like(pattern), Beneficiario.cpf.like(f"%{only_digits(q) or q}%")))
    if not can_see_all(user):
        query = query.join(BeneficiarioPolo).where(BeneficiarioPolo.polo_id.in_(scoped_polo_ids(db, user) or [-1]))
    items = db.execute(query.limit(20)).unique().scalars().all()
    return [serialize_beneficiario(item) for item in items]


@api.get("/beneficiarios")
def list_beneficiarios(
    nome: str | None = None,
    cpf: str | None = None,
    status_cadastro: str | None = None,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> list[dict[str, Any]]:
    query = select(Beneficiario).options(
        joinedload(Beneficiario.vereadores).joinedload(BeneficiarioVereador.vereador),
        joinedload(Beneficiario.polos).joinedload(BeneficiarioPolo.polo),
    )
    if nome:
        query = query.where(func.lower(Beneficiario.nome).like(f"%{nome.lower()}%"))
    if cpf:
        query = query.where(Beneficiario.cpf == only_digits(cpf))
    if status_cadastro:
        query = query.where(Beneficiario.status_cadastro == status_cadastro)
    if not can_see_all(user):
        query = query.join(BeneficiarioPolo).where(BeneficiarioPolo.polo_id.in_(scoped_polo_ids(db, user) or [-1]))
    items = db.execute(query.order_by(Beneficiario.nome)).unique().scalars().all()
    return [serialize_beneficiario(item) for item in items]


@api.post("/beneficiarios")
def create_beneficiario(payload: BeneficiarioIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    ensure_unique_beneficiario(db, payload)
    cpf = validate_cpf(payload.cpf)
    polo_ids = payload.polo_ids or ([user.polo_id] if user.polo_id else [])
    vereador_ids = payload.vereador_ids or ([user.vereador_id] if user.vereador_id else [])
    for polo_id in polo_ids:
        ensure_polo_in_scope(db, user, polo_id)
    for vereador_id in vereador_ids:
        ensure_vereador_in_scope(db, user, vereador_id)
    item = Beneficiario(
        nome=payload.nome,
        cpf=cpf,
        rg=payload.rg,
        data_nascimento=payload.data_nascimento,
        sexo=payload.sexo,
        telefone=only_digits(payload.telefone),
        email=payload.email,
        endereco=payload.endereco,
        bairro=payload.bairro,
        cidade=payload.cidade,
        observacoes=payload.observacoes,
        origem_cadastro=payload.origem_cadastro,
        status_cadastro=payload.status_cadastro,
    )
    db.add(item)
    db.flush()
    set_beneficiario_links(db, item, vereador_ids, polo_ids)
    warning = None
    if not cpf and potential_duplicates(db, payload, current_id=item.id):
        warning = "Possivel duplicidade por nome, nascimento e telefone."
    audit(db, user, "beneficiario", item.id, "CRIAR", after=as_dict(item))
    db.commit()
    db.refresh(item)
    return {"beneficiario": serialize_beneficiario(item), "alerta": warning}


@api.get("/beneficiarios/{beneficiario_id}")
def get_beneficiario(beneficiario_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    item = db.get(Beneficiario, beneficiario_id)
    if not item:
        raise HTTPException(status_code=404, detail="Beneficiario nao encontrado.")
    if not beneficiary_visible(db, user, beneficiario_id):
        raise HTTPException(status_code=403, detail="Beneficiario fora do escopo.")
    return serialize_beneficiario(item)


@api.put("/beneficiarios/{beneficiario_id}")
def update_beneficiario(beneficiario_id: int, payload: BeneficiarioIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    item = db.get(Beneficiario, beneficiario_id)
    if not item:
        raise HTTPException(status_code=404, detail="Beneficiario nao encontrado.")
    if not beneficiary_visible(db, user, beneficiario_id):
        raise HTTPException(status_code=403, detail="Beneficiario fora do escopo.")
    ensure_unique_beneficiario(db, payload, current_id=beneficiario_id)
    before = serialize_beneficiario(item)
    item.nome = payload.nome
    item.cpf = validate_cpf(payload.cpf)
    item.rg = payload.rg
    item.data_nascimento = payload.data_nascimento
    item.sexo = payload.sexo
    item.telefone = only_digits(payload.telefone)
    item.email = payload.email
    item.endereco = payload.endereco
    item.bairro = payload.bairro
    item.cidade = payload.cidade
    item.observacoes = payload.observacoes
    item.origem_cadastro = payload.origem_cadastro
    item.status_cadastro = payload.status_cadastro
    set_beneficiario_links(db, item, payload.vereador_ids, payload.polo_ids)
    audit(db, user, "beneficiario", item.id, "ATUALIZAR", before=before, after=as_dict(item))
    db.commit()
    return serialize_beneficiario(item)


@api.patch("/beneficiarios/{beneficiario_id}/status")
def patch_beneficiario_status(beneficiario_id: int, payload: StatusPatch, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    item = db.get(Beneficiario, beneficiario_id)
    if not item:
        raise HTTPException(status_code=404, detail="Beneficiario nao encontrado.")
    if not beneficiary_visible(db, user, beneficiario_id):
        raise HTTPException(status_code=403, detail="Beneficiario fora do escopo.")
    before = as_dict(item)
    item.status_cadastro = payload.status.upper()
    audit(db, user, "beneficiario", item.id, "ALTERAR_STATUS", before=before, after=as_dict(item))
    db.commit()
    return serialize_beneficiario(item)


@api.delete("/beneficiarios/{beneficiario_id}")
def delete_beneficiario(beneficiario_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, str]:
    item = db.get(Beneficiario, beneficiario_id)
    if not item:
        raise HTTPException(status_code=404, detail="Beneficiario nao encontrado.")
    if not beneficiary_visible(db, user, beneficiario_id):
        raise HTTPException(status_code=403, detail="Beneficiario fora do escopo.")
    if any(
        [
            has_records(db, Inscricao, Inscricao.beneficiario_id == beneficiario_id),
            has_records(db, GrupoFamiliar, GrupoFamiliar.beneficiario_id == beneficiario_id),
            has_records(db, Ocorrencia, Ocorrencia.beneficiario_id == beneficiario_id),
            has_records(db, Encaminhamento, Encaminhamento.beneficiario_id == beneficiario_id),
            has_records(db, DemandaImediata, DemandaImediata.beneficiario_id == beneficiario_id),
            has_records(db, SugestaoCritica, SugestaoCritica.beneficiario_id == beneficiario_id),
        ]
    ):
        raise HTTPException(status_code=409, detail="Beneficiário possui histórico operacional e não pode ser excluído. Arquive o registro.")
    before = serialize_beneficiario(item)
    db.delete(item)
    audit(db, user, "beneficiario", beneficiario_id, "EXCLUIR", before=before)
    db.commit()
    return {"status": "ok"}


@api.get("/areas")
def list_areas(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [as_dict(item) for item in db.execute(select(AreaModalidade).order_by(AreaModalidade.nome)).scalars().all()]


@api.post("/areas")
def create_area(payload: AreaIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    if user.perfil not in ADMIN_ROLES | {"Gestor de Polo"}:
        raise HTTPException(status_code=403, detail="Perfil sem permissao.")
    item = AreaModalidade(nome=payload.nome)
    db.add(item)
    db.flush()
    audit(db, user, "area_modalidade", item.id, "CRIAR", after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.get("/modalidades")
def list_modalidades(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    items = db.execute(select(Modalidade).options(joinedload(Modalidade.area)).order_by(Modalidade.nome)).scalars().all()
    return [as_dict(item, {"area_nome": item.area.nome if item.area else None}) for item in items]


@api.post("/modalidades")
def create_modalidade(payload: ModalidadeIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    if user.perfil not in ADMIN_ROLES | {"Gestor de Polo"}:
        raise HTTPException(status_code=403, detail="Perfil sem permissao.")
    area_id = payload.area_id
    if not area_id:
        area_name = payload.area_nome or "Geral"
        area = db.scalar(select(AreaModalidade).where(func.lower(AreaModalidade.nome) == area_name.lower()))
        if not area:
            area = AreaModalidade(nome=area_name)
            db.add(area)
            db.flush()
        area_id = area.id
    item = Modalidade(area_id=area_id, nome=payload.nome, ativa=payload.ativa)
    db.add(item)
    db.flush()
    audit(db, user, "modalidade", item.id, "CRIAR", after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.put("/modalidades/{modalidade_id}")
def update_modalidade(modalidade_id: int, payload: ModalidadeIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    if user.perfil not in ADMIN_ROLES | {"Gestor de Polo"}:
        raise HTTPException(status_code=403, detail="Perfil sem permissao.")
    item = db.get(Modalidade, modalidade_id)
    if not item:
        raise HTTPException(status_code=404, detail="Modalidade nao encontrada.")
    before = as_dict(item)
    item.nome = payload.nome
    item.ativa = payload.ativa
    if payload.area_id:
        item.area_id = payload.area_id
    audit(db, user, "modalidade", item.id, "ATUALIZAR", before=before, after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.patch("/modalidades/{modalidade_id}/status")
def patch_modalidade_status(modalidade_id: int, payload: StatusPatch, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    item = db.get(Modalidade, modalidade_id)
    if not item:
        raise HTTPException(status_code=404, detail="Modalidade nao encontrada.")
    before = as_dict(item)
    item.ativa = payload.status.upper() in {"ATIVA", "ATIVO", "TRUE", "1"}
    audit(db, user, "modalidade", item.id, "ALTERAR_STATUS", before=before, after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.get("/turmas")
def list_turmas(polo_id: int | None = None, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    ids = scoped_polo_ids(db, user)
    query = (
        select(Turma)
        .options(joinedload(Turma.polo), joinedload(Turma.modalidade).joinedload(Modalidade.area), joinedload(Turma.inscricoes))
        .where(Turma.polo_id.in_(ids or [-1]))
    )
    if polo_id:
        ensure_polo_in_scope(db, user, polo_id)
        query = query.where(Turma.polo_id == polo_id)
    items = db.execute(query.order_by(Turma.nome)).unique().scalars().all()
    return [serialize_turma(item) for item in items]


@api.post("/turmas")
def create_turma(payload: TurmaIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    ensure_polo_in_scope(db, user, payload.polo_id)
    item = Turma(**payload.model_dump())
    db.add(item)
    db.flush()
    audit(db, user, "turma", item.id, "CRIAR", after=as_dict(item))
    db.commit()
    db.refresh(item)
    return as_dict(item)


@api.put("/turmas/{turma_id}")
def update_turma(turma_id: int, payload: TurmaIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    item = db.get(Turma, turma_id)
    if not item:
        raise HTTPException(status_code=404, detail="Turma nao encontrada.")
    ensure_polo_in_scope(db, user, item.polo_id)
    before = as_dict(item)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    audit(db, user, "turma", item.id, "ATUALIZAR", before=before, after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.patch("/turmas/{turma_id}/status")
def patch_turma_status(turma_id: int, payload: StatusPatch, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    item = db.get(Turma, turma_id)
    if not item:
        raise HTTPException(status_code=404, detail="Turma nao encontrada.")
    ensure_polo_in_scope(db, user, item.polo_id)
    before = as_dict(item)
    item.ativa = payload.status.upper() in {"ATIVA", "ATIVO", "TRUE", "1"}
    audit(db, user, "turma", item.id, "ALTERAR_STATUS", before=before, after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.delete("/turmas/{turma_id}")
def delete_turma(turma_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, str]:
    item = db.get(Turma, turma_id)
    if not item:
        raise HTTPException(status_code=404, detail="Turma nao encontrada.")
    ensure_polo_in_scope(db, user, item.polo_id)
    if any(
        [
            has_records(db, Inscricao, Inscricao.turma_id == turma_id),
            has_records(db, Frequencia, Frequencia.inscricao_id.in_(select(Inscricao.id).where(Inscricao.turma_id == turma_id))),
        ]
    ):
        raise HTTPException(status_code=409, detail="Turma possui inscrições ou frequência registrada e não pode ser excluída. Arquive o registro.")
    before = as_dict(item)
    db.delete(item)
    audit(db, user, "turma", turma_id, "EXCLUIR", before=before)
    db.commit()
    return {"status": "ok"}


@api.get("/turmas/{turma_id}/inscritos")
def turma_inscritos(turma_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    turma = db.get(Turma, turma_id)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma nao encontrada.")
    ensure_polo_in_scope(db, user, turma.polo_id)
    items = db.execute(select(Inscricao).options(joinedload(Inscricao.beneficiario)).where(Inscricao.turma_id == turma_id)).scalars().all()
    return [as_dict(item, {"beneficiario_nome": item.beneficiario.nome}) for item in items]


@api.post("/inscricoes")
def create_inscricao(payload: InscricaoIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    turma = db.get(Turma, payload.turma_id)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma nao encontrada.")
    ensure_polo_in_scope(db, user, turma.polo_id)
    if not beneficiary_visible(db, user, payload.beneficiario_id):
        raise HTTPException(status_code=403, detail="Beneficiario fora do escopo.")
    existing = db.scalar(select(Inscricao).where(Inscricao.beneficiario_id == payload.beneficiario_id, Inscricao.turma_id == payload.turma_id))
    if existing:
        raise HTTPException(status_code=409, detail="Beneficiario ja inscrito nesta turma.")
    active_count = db.scalar(select(func.count(Inscricao.id)).where(Inscricao.turma_id == payload.turma_id, Inscricao.status == "ATIVA")) or 0
    if active_count >= turma.capacidade:
        raise HTTPException(status_code=409, detail="Capacidade da turma atingida.")
    item = Inscricao(
        beneficiario_id=payload.beneficiario_id,
        turma_id=payload.turma_id,
        data_inscricao=payload.data_inscricao or date.today(),
        status=payload.status,
    )
    db.add(item)
    db.flush()
    audit(db, user, "inscricao", item.id, "CRIAR", after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.patch("/inscricoes/{inscricao_id}/status")
def patch_inscricao_status(inscricao_id: int, payload: StatusPatch, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    item = db.get(Inscricao, inscricao_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inscricao nao encontrada.")
    ensure_polo_in_scope(db, user, item.turma.polo_id)
    before = as_dict(item)
    item.status = payload.status.upper()
    audit(db, user, "inscricao", item.id, "ALTERAR_STATUS", before=before, after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.get("/frequencia/carga")
def frequencia_carga(turma_id: int, data: date, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    turma = db.get(Turma, turma_id)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma nao encontrada.")
    ensure_polo_in_scope(db, user, turma.polo_id)
    inscricoes = db.execute(
        select(Inscricao).options(joinedload(Inscricao.beneficiario)).where(Inscricao.turma_id == turma_id, Inscricao.status == "ATIVA")
    ).scalars().all()
    freq_by_inscricao = {
        freq.inscricao_id: freq
        for freq in db.execute(
            select(Frequencia).where(Frequencia.inscricao_id.in_([i.id for i in inscricoes] or [-1]), Frequencia.data_atividade == data)
        ).scalars().all()
    }
    return {
        "turma": serialize_turma(turma),
        "data_atividade": data.isoformat(),
        "registros": [
            {
                "inscricao_id": inscricao.id,
                "beneficiario_id": inscricao.beneficiario_id,
                "beneficiario_nome": inscricao.beneficiario.nome,
                "presente": freq_by_inscricao.get(inscricao.id).presente if inscricao.id in freq_by_inscricao else False,
                "observacao": freq_by_inscricao.get(inscricao.id).observacao if inscricao.id in freq_by_inscricao else None,
            }
            for inscricao in inscricoes
        ],
    }


@api.post("/frequencia/lote")
def save_frequencia_lote(payload: FrequenciaLoteIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    turma = db.get(Turma, payload.turma_id)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma nao encontrada.")
    ensure_polo_in_scope(db, user, turma.polo_id)
    saved = []
    for registro in payload.registros:
        inscricao = db.get(Inscricao, registro.inscricao_id)
        if not inscricao or inscricao.turma_id != payload.turma_id:
            raise HTTPException(status_code=422, detail=f"Inscricao {registro.inscricao_id} nao pertence a turma.")
        item = db.scalar(select(Frequencia).where(Frequencia.inscricao_id == registro.inscricao_id, Frequencia.data_atividade == payload.data_atividade))
        if not item:
            item = Frequencia(inscricao_id=registro.inscricao_id, data_atividade=payload.data_atividade)
            db.add(item)
        item.presente = registro.presente
        item.observacao = registro.observacao
        saved.append(item)
    audit(db, user, "frequencia", payload.turma_id, "SALVAR_LOTE", after={"data": payload.data_atividade.isoformat(), "registros": len(saved)})
    db.commit()
    return {"salvos": len(saved)}


@api.get("/ocorrencias")
def list_ocorrencias(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    query = select(Ocorrencia).order_by(Ocorrencia.data_ocorrencia.desc())
    if not can_see_all(user):
        query = query.where(Ocorrencia.polo_id.in_(scoped_polo_ids(db, user) or [-1]))
    return [as_dict(item) for item in db.execute(query).scalars().all()]


@api.post("/ocorrencias")
def create_ocorrencia(payload: OcorrenciaIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    ensure_polo_in_scope(db, user, payload.polo_id)
    if not beneficiary_visible(db, user, payload.beneficiario_id):
        raise HTTPException(status_code=403, detail="Beneficiario fora do escopo.")
    item = Ocorrencia(
        beneficiario_id=payload.beneficiario_id,
        polo_id=payload.polo_id,
        tipo=payload.tipo,
        descricao=payload.descricao,
        data_ocorrencia=payload.data_ocorrencia or date.today(),
        usuario_id=user.id,
    )
    db.add(item)
    db.flush()
    audit(db, user, "ocorrencia", item.id, "CRIAR", after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.get("/encaminhamentos")
def list_encaminhamentos(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    query = select(Encaminhamento).order_by(Encaminhamento.data_registro.desc())
    if not can_see_all(user):
        query = query.where(Encaminhamento.polo_id.in_(scoped_polo_ids(db, user) or [-1]))
    return [as_dict(item) for item in db.execute(query).scalars().all()]


@api.post("/encaminhamentos")
def create_encaminhamento(payload: EncaminhamentoIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    ensure_polo_in_scope(db, user, payload.polo_id)
    item = Encaminhamento(
        beneficiario_id=payload.beneficiario_id,
        polo_id=payload.polo_id,
        tipo=payload.tipo,
        destino=payload.destino,
        descricao=payload.descricao,
        data_registro=payload.data_registro or date.today(),
        status=payload.status,
    )
    db.add(item)
    db.flush()
    audit(db, user, "encaminhamento", item.id, "CRIAR", after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.put("/encaminhamentos/{encaminhamento_id}")
def update_encaminhamento(encaminhamento_id: int, payload: EncaminhamentoIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    item = db.get(Encaminhamento, encaminhamento_id)
    if not item:
        raise HTTPException(status_code=404, detail="Encaminhamento nao encontrado.")
    ensure_polo_in_scope(db, user, item.polo_id)
    before = as_dict(item)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    audit(db, user, "encaminhamento", item.id, "ATUALIZAR", before=before, after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.patch("/encaminhamentos/{encaminhamento_id}/status")
def patch_encaminhamento_status(encaminhamento_id: int, payload: StatusPatch, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    item = db.get(Encaminhamento, encaminhamento_id)
    if not item:
        raise HTTPException(status_code=404, detail="Encaminhamento nao encontrado.")
    ensure_polo_in_scope(db, user, item.polo_id)
    before = as_dict(item)
    item.status = payload.status.upper()
    audit(db, user, "encaminhamento", item.id, "ALTERAR_STATUS", before=before, after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.delete("/encaminhamentos/{encaminhamento_id}")
def delete_encaminhamento(encaminhamento_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, str]:
    item = db.get(Encaminhamento, encaminhamento_id)
    if not item:
        raise HTTPException(status_code=404, detail="Encaminhamento nao encontrado.")
    ensure_polo_in_scope(db, user, item.polo_id)
    before = as_dict(item)
    db.delete(item)
    audit(db, user, "encaminhamento", encaminhamento_id, "EXCLUIR", before=before)
    db.commit()
    return {"status": "ok"}


@api.get("/fornecedores")
def list_fornecedores(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    items = db.execute(select(Fornecedor).order_by(Fornecedor.nome)).scalars().all()
    return [as_dict(item) for item in items]


@api.post("/fornecedores")
def create_fornecedor(payload: FornecedorIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_finance(user)
    item = Fornecedor(**payload.model_dump())
    db.add(item)
    db.flush()
    audit(db, user, "fornecedor", item.id, "CRIAR", after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.put("/fornecedores/{fornecedor_id}")
def update_fornecedor(fornecedor_id: int, payload: FornecedorIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_finance(user)
    item = db.get(Fornecedor, fornecedor_id)
    if not item:
        raise HTTPException(status_code=404, detail="Fornecedor nao encontrado.")
    before = as_dict(item)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    audit(db, user, "fornecedor", item.id, "ATUALIZAR", before=before, after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.patch("/fornecedores/{fornecedor_id}/status")
def patch_fornecedor_status(fornecedor_id: int, payload: StatusPatch, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_finance(user)
    item = db.get(Fornecedor, fornecedor_id)
    if not item:
        raise HTTPException(status_code=404, detail="Fornecedor nao encontrado.")
    before = as_dict(item)
    item.ativo = payload.status.upper() in {"ATIVO", "ATIVA", "TRUE", "1"}
    audit(db, user, "fornecedor", item.id, "ALTERAR_STATUS", before=before, after=as_dict(item))
    db.commit()
    return as_dict(item)


@api.delete("/fornecedores/{fornecedor_id}")
def delete_fornecedor(fornecedor_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, str]:
    require_finance(user)
    item = db.get(Fornecedor, fornecedor_id)
    if not item:
        raise HTTPException(status_code=404, detail="Fornecedor nao encontrado.")
    if has_records(db, Compra, Compra.fornecedor_id == fornecedor_id):
        raise HTTPException(status_code=409, detail="Fornecedor já foi usado em compras e não pode ser excluído. Arquive o registro.")
    before = as_dict(item)
    db.delete(item)
    audit(db, user, "fornecedor", fornecedor_id, "EXCLUIR", before=before)
    db.commit()
    return {"status": "ok"}


@api.get("/requisicoes-compra/fila")
def fila_requisicoes(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    require_finance(user)
    vereador_ids = scoped_vereador_ids(db, user)
    items = (
        db.execute(
            select(RequisicaoCompra)
            .options(joinedload(RequisicaoCompra.polo), joinedload(RequisicaoCompra.vereador), joinedload(RequisicaoCompra.itens))
            .where(RequisicaoCompra.vereador_id.in_(vereador_ids or [-1]), RequisicaoCompra.status.in_(["ABERTA", "EM_ANALISE", "DEVOLVIDA"]))
            .order_by(RequisicaoCompra.data_requisicao.desc())
        )
        .unique()
        .scalars()
        .all()
    )
    return [serialize_requisicao(item) for item in items]


@api.get("/requisicoes-compra/aprovadas")
def requisicoes_aprovadas(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    require_finance(user)
    vereador_ids = scoped_vereador_ids(db, user)
    items = (
        db.execute(
            select(RequisicaoCompra)
            .options(joinedload(RequisicaoCompra.polo), joinedload(RequisicaoCompra.vereador), joinedload(RequisicaoCompra.itens))
            .where(RequisicaoCompra.vereador_id.in_(vereador_ids or [-1]), RequisicaoCompra.status == "APROVADA")
            .order_by(RequisicaoCompra.data_requisicao.desc())
        )
        .unique()
        .scalars()
        .all()
    )
    return [serialize_requisicao(item) for item in items]


@api.get("/requisicoes-compra")
def list_requisicoes(status_filter: str | None = Query(default=None, alias="status"), db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    query = select(RequisicaoCompra).options(joinedload(RequisicaoCompra.polo), joinedload(RequisicaoCompra.vereador), joinedload(RequisicaoCompra.itens))
    if status_filter:
        query = query.where(RequisicaoCompra.status == status_filter)
    if not can_see_all(user):
        query = query.where(RequisicaoCompra.polo_id.in_(scoped_polo_ids(db, user) or [-1]))
    items = db.execute(query.order_by(RequisicaoCompra.data_requisicao.desc())).unique().scalars().all()
    return [serialize_requisicao(item) for item in items]


@api.post("/requisicoes-compra")
def create_requisicao(payload: RequisicaoIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    if not payload.itens:
        raise HTTPException(status_code=422, detail="Requisicao deve possuir ao menos um item.")
    polo = ensure_polo_in_scope(db, user, payload.polo_id)
    item = RequisicaoCompra(
        polo_id=polo.id,
        vereador_id=polo.vereador_id,
        solicitante_usuario_id=user.id,
        descricao=payload.descricao,
        prioridade=payload.prioridade,
        status=payload.status,
        data_requisicao=date.today(),
    )
    db.add(item)
    db.flush()
    for req_item in payload.itens:
        db.add(ItemRequisicao(requisicao_id=item.id, **req_item.model_dump()))
    audit(db, user, "requisicao_compra", item.id, "CRIAR", after=as_dict(item))
    db.commit()
    db.refresh(item)
    return serialize_requisicao(item)


@api.put("/requisicoes-compra/{requisicao_id}")
def update_requisicao(requisicao_id: int, payload: RequisicaoIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    item = db.get(RequisicaoCompra, requisicao_id)
    if not item:
        raise HTTPException(status_code=404, detail="Requisicao nao encontrada.")
    ensure_polo_in_scope(db, user, item.polo_id)
    novo_polo = ensure_polo_in_scope(db, user, payload.polo_id)
    before = serialize_requisicao(item)
    item.polo_id = novo_polo.id
    item.vereador_id = novo_polo.vereador_id
    item.descricao = payload.descricao
    item.prioridade = payload.prioridade
    item.status = payload.status
    db.query(ItemRequisicao).filter(ItemRequisicao.requisicao_id == item.id).delete()
    for req_item in payload.itens:
        db.add(ItemRequisicao(requisicao_id=item.id, **req_item.model_dump()))
    audit(db, user, "requisicao_compra", item.id, "ATUALIZAR", before=before, after=as_dict(item))
    db.commit()
    db.refresh(item)
    return serialize_requisicao(item)


@api.delete("/requisicoes-compra/{requisicao_id}")
def delete_requisicao(requisicao_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, str]:
    item = db.get(RequisicaoCompra, requisicao_id)
    if not item:
        raise HTTPException(status_code=404, detail="Requisicao nao encontrada.")
    ensure_polo_in_scope(db, user, item.polo_id)
    if has_records(db, Compra, Compra.requisicao_id == requisicao_id):
        raise HTTPException(status_code=409, detail="Requisição já executada em compra e não pode ser excluída.")
    before = serialize_requisicao(item)
    db.delete(item)
    audit(db, user, "requisicao_compra", requisicao_id, "EXCLUIR", before=before)
    db.commit()
    return {"status": "ok"}


@api.get("/requisicoes-compra/{requisicao_id}/historico")
def requisicao_historico(requisicao_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    item = db.get(RequisicaoCompra, requisicao_id)
    if not item:
        raise HTTPException(status_code=404, detail="Requisicao nao encontrada.")
    ensure_polo_in_scope(db, user, item.polo_id)
    rows = db.execute(
        select(Auditoria).where(Auditoria.entidade == "requisicao_compra", Auditoria.entidade_id == requisicao_id).order_by(Auditoria.data_evento.desc())
    ).scalars().all()
    return [as_dict(row) for row in rows]


@api.post("/requisicoes-compra/{requisicao_id}/enviar")
def enviar_requisicao(requisicao_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    item = db.get(RequisicaoCompra, requisicao_id)
    if not item:
        raise HTTPException(status_code=404, detail="Requisicao nao encontrada.")
    ensure_polo_in_scope(db, user, item.polo_id)
    before = as_dict(item)
    item.status = "EM_ANALISE"
    audit(db, user, "requisicao_compra", item.id, "ENVIAR", before=before, after=as_dict(item))
    db.commit()
    return serialize_requisicao(item)


@api.post("/requisicoes-compra/{requisicao_id}/duplicar")
def duplicar_requisicao(requisicao_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    item = db.get(RequisicaoCompra, requisicao_id)
    if not item:
        raise HTTPException(status_code=404, detail="Requisicao nao encontrada.")
    ensure_polo_in_scope(db, user, item.polo_id)
    nova = RequisicaoCompra(
        polo_id=item.polo_id,
        vereador_id=item.vereador_id,
        solicitante_usuario_id=user.id,
        descricao=f"Duplicada: {item.descricao}",
        prioridade=item.prioridade,
        status="RASCUNHO",
        data_requisicao=date.today(),
    )
    db.add(nova)
    db.flush()
    for req_item in item.itens:
        db.add(
            ItemRequisicao(
                requisicao_id=nova.id,
                descricao=req_item.descricao,
                quantidade=req_item.quantidade,
                unidade=req_item.unidade,
                valor_estimado=req_item.valor_estimado,
            )
        )
    audit(db, user, "requisicao_compra", nova.id, "DUPLICAR", after={"origem": item.id})
    db.commit()
    return serialize_requisicao(nova)


def alterar_status_requisicao(requisicao_id: int, status_final: str, acao: str, db: Session, user: Usuario) -> dict[str, Any]:
    require_finance(user)
    item = db.get(RequisicaoCompra, requisicao_id)
    if not item:
        raise HTTPException(status_code=404, detail="Requisicao nao encontrada.")
    ensure_vereador_in_scope(db, user, item.vereador_id)
    before = as_dict(item)
    item.status = status_final
    audit(db, user, "requisicao_compra", item.id, acao, before=before, after=as_dict(item))
    db.commit()
    return serialize_requisicao(item)


@api.post("/requisicoes-compra/{requisicao_id}/aprovar")
def aprovar_requisicao(requisicao_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    return alterar_status_requisicao(requisicao_id, "APROVADA", "APROVAR", db, user)


@api.post("/requisicoes-compra/{requisicao_id}/reprovar")
def reprovar_requisicao(requisicao_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    return alterar_status_requisicao(requisicao_id, "REPROVADA", "REPROVAR", db, user)


@api.post("/requisicoes-compra/{requisicao_id}/devolver")
def devolver_requisicao(requisicao_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    return alterar_status_requisicao(requisicao_id, "DEVOLVIDA", "DEVOLVER", db, user)


@api.post("/compras")
def create_compra(payload: CompraIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_finance(user)
    requisicao = db.get(RequisicaoCompra, payload.requisicao_id)
    if not requisicao:
        raise HTTPException(status_code=404, detail="Requisicao nao encontrada.")
    ensure_vereador_in_scope(db, user, requisicao.vereador_id)
    if requisicao.status != "APROVADA":
        raise HTTPException(status_code=409, detail="Compra exige requisicao aprovada.")
    emenda = db.get(Emenda, payload.emenda_id)
    if not emenda:
        raise HTTPException(status_code=404, detail="Emenda nao encontrada.")
    if emenda.vereador_id != requisicao.vereador_id:
        raise HTTPException(status_code=409, detail="Emenda incompativel com o vereador da requisicao.")
    if emenda.valor_disponivel < payload.valor_total:
        raise HTTPException(status_code=409, detail="Saldo insuficiente na emenda.")
    fornecedor = db.get(Fornecedor, payload.fornecedor_id)
    if not fornecedor or not fornecedor.ativo:
        raise HTTPException(status_code=404, detail="Fornecedor inativo ou nao encontrado.")
    item = Compra(
        requisicao_id=payload.requisicao_id,
        fornecedor_id=payload.fornecedor_id,
        emenda_id=payload.emenda_id,
        valor_total=payload.valor_total,
        data_compra=payload.data_compra or date.today(),
        status=payload.status,
    )
    db.add(item)
    db.flush()
    requisicao.status = "EXECUTADA"
    emenda.valor_utilizado += payload.valor_total
    emenda.valor_disponivel = max(emenda.valor_total - emenda.valor_utilizado, 0)
    mov = MovimentacaoEmenda(emenda_id=emenda.id, tipo="SAIDA", valor=payload.valor_total, referencia_tipo="compra", referencia_id=item.id)
    db.add(mov)
    audit(db, user, "compra", item.id, "EXECUTAR", after=as_dict(item))
    audit(db, user, "emenda", emenda.id, "MOVIMENTAR", after=as_dict(emenda))
    db.commit()
    db.refresh(item)
    return as_dict(item, {"fornecedor_nome": fornecedor.nome, "emenda_codigo": emenda.codigo})


@api.get("/compras")
def list_compras(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    vereador_ids = scoped_vereador_ids(db, user)
    items = (
        db.execute(
            select(Compra)
            .options(joinedload(Compra.fornecedor), joinedload(Compra.emenda))
            .join(Emenda)
            .where(Emenda.vereador_id.in_(vereador_ids or [-1]))
            .order_by(Compra.data_compra.desc())
        )
        .unique()
        .scalars()
        .all()
    )
    return [as_dict(item, {"fornecedor_nome": item.fornecedor.nome, "emenda_codigo": item.emenda.codigo}) for item in items]


@api.post("/compras/{compra_id}/documentos")
def upload_nota_fiscal(compra_id: int, payload: NotaFiscalIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_finance(user)
    compra = db.get(Compra, compra_id)
    if not compra:
        raise HTTPException(status_code=404, detail="Compra nao encontrada.")
    ensure_vereador_in_scope(db, user, compra.emenda.vereador_id)
    item = NotaFiscal(compra_id=compra_id, **payload.model_dump())
    db.add(item)
    db.flush()
    audit(db, user, "nota_fiscal", item.id, "UPLOAD", after=as_dict(item))
    db.commit()
    return as_dict(item)


def create_mobile_cadastro(db: Session, user: Usuario, payload: MobileCadastroIn) -> dict[str, Any]:
    beneficiario_payload = payload.beneficiario
    beneficiario_payload.origem_cadastro = "MOBILE"
    if not beneficiario_payload.polo_ids and user.polo_id:
        beneficiario_payload.polo_ids = [user.polo_id]
    if not beneficiario_payload.vereador_ids and user.vereador_id:
        beneficiario_payload.vereador_ids = [user.vereador_id]
    ensure_unique_beneficiario(db, beneficiario_payload)
    cpf = validate_cpf(beneficiario_payload.cpf)
    beneficiario = Beneficiario(
        nome=beneficiario_payload.nome,
        cpf=cpf,
        rg=beneficiario_payload.rg,
        data_nascimento=beneficiario_payload.data_nascimento,
        sexo=beneficiario_payload.sexo,
        telefone=only_digits(beneficiario_payload.telefone),
        email=beneficiario_payload.email,
        endereco=beneficiario_payload.endereco,
        bairro=beneficiario_payload.bairro,
        cidade=beneficiario_payload.cidade,
        observacoes=beneficiario_payload.observacoes,
        origem_cadastro="MOBILE",
        status_cadastro="SINCRONIZADO",
    )
    db.add(beneficiario)
    db.flush()
    set_beneficiario_links(db, beneficiario, beneficiario_payload.vereador_ids, beneficiario_payload.polo_ids)
    polo_id = beneficiario_payload.polo_ids[0] if beneficiario_payload.polo_ids else user.polo_id
    if payload.responsavel:
        responsavel = Responsavel(**payload.responsavel.model_dump())
        db.add(responsavel)
        db.flush()
        db.add(GrupoFamiliar(beneficiario_id=beneficiario.id, responsavel_id=responsavel.id, composicao=payload.grupo_familiar))
    if polo_id and payload.demanda_imediata:
        db.add(DemandaImediata(beneficiario_id=beneficiario.id, polo_id=polo_id, descricao=payload.demanda_imediata, prioridade=payload.demanda_prioridade))
    if polo_id and payload.sugestao_tipo and payload.sugestao_descricao:
        db.add(SugestaoCritica(beneficiario_id=beneficiario.id, polo_id=polo_id, tipo=payload.sugestao_tipo, descricao=payload.sugestao_descricao))
    audit(db, user, "beneficiario", beneficiario.id, "SYNC_MOBILE", after=as_dict(beneficiario))
    return serialize_beneficiario(beneficiario)


@api.get("/mobile/dashboard")
def mobile_dashboard(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    if user.perfil not in POLO_ROLES | ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Perfil sem acesso mobile.")
    polo_ids = scoped_polo_ids(db, user)
    recentes = (
        db.execute(
            select(Beneficiario)
            .options(joinedload(Beneficiario.vereadores).joinedload(BeneficiarioVereador.vereador), joinedload(Beneficiario.polos).joinedload(BeneficiarioPolo.polo))
            .join(BeneficiarioPolo)
            .where(BeneficiarioPolo.polo_id.in_(polo_ids or [-1]))
            .order_by(Beneficiario.created_at.desc())
            .limit(5)
        )
        .unique()
        .scalars()
        .all()
    )
    return {
        "usuario": user.nome,
        "pendentes_sincronizacao": 0,
        "sincronizados_hoje": db.scalar(select(func.count(Beneficiario.id)).where(Beneficiario.origem_cadastro == "MOBILE")) or 0,
        "recentes": [serialize_beneficiario(item) for item in recentes],
        "online": True,
    }


@api.get("/mobile/cadastros/recentes")
def mobile_recentes(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    return mobile_dashboard(db, user)["recentes"]


@api.post("/mobile/beneficiarios")
def mobile_beneficiario(payload: MobileCadastroIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    if user.perfil not in POLO_ROLES | ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Perfil sem acesso mobile.")
    beneficiario = create_mobile_cadastro(db, user, payload)
    db.commit()
    return {"status": "sincronizado", "beneficiario": beneficiario}


@api.post("/mobile/sync")
def mobile_sync(payload: SyncIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    if user.perfil not in POLO_ROLES | ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Perfil sem acesso mobile.")
    results = []
    errors = []
    for index, cadastro in enumerate(payload.cadastros):
        try:
            results.append(create_mobile_cadastro(db, user, cadastro))
        except HTTPException as exc:
            errors.append({"index": index, "erro": exc.detail})
    if errors:
        db.rollback()
        return {"sincronizados": 0, "erros": errors}
    db.commit()
    return {"sincronizados": len(results), "erros": [], "beneficiarios": results}


@api.get("/relatorios/polo")
def relatorio_polo(polo_id: int | None = None, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    polo_ids = [polo_id] if polo_id else scoped_polo_ids(db, user)
    for item in polo_ids:
        ensure_polo_in_scope(db, user, item)
    turmas = db.execute(select(Turma).where(Turma.polo_id.in_(polo_ids or [-1]))).scalars().all()
    turma_ids = [item.id for item in turmas]
    inscritos = db.scalar(select(func.count(Inscricao.id)).where(Inscricao.turma_id.in_(turma_ids or [-1]))) or 0
    presentes = db.scalar(select(func.count(Frequencia.id)).join(Inscricao).where(Inscricao.turma_id.in_(turma_ids or [-1]), Frequencia.presente.is_(True))) or 0
    total_freq = db.scalar(select(func.count(Frequencia.id)).join(Inscricao).where(Inscricao.turma_id.in_(turma_ids or [-1]))) or 0
    return {
        "polos": polo_ids,
        "beneficiarios": db.scalar(select(func.count(BeneficiarioPolo.id)).where(BeneficiarioPolo.polo_id.in_(polo_ids or [-1]))) or 0,
        "turmas": len(turmas),
        "inscricoes": inscritos,
        "frequencia_percentual": round((presentes / total_freq) * 100, 1) if total_freq else 0,
        "ocorrencias": db.scalar(select(func.count(Ocorrencia.id)).where(Ocorrencia.polo_id.in_(polo_ids or [-1]))) or 0,
        "requisicoes": db.scalar(select(func.count(RequisicaoCompra.id)).where(RequisicaoCompra.polo_id.in_(polo_ids or [-1]))) or 0,
    }


@api.get("/relatorios/vereador")
def relatorio_vereador(vereador_id: int | None = None, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    vereador_ids = [vereador_id] if vereador_id else scoped_vereador_ids(db, user)
    for item in vereador_ids:
        ensure_vereador_in_scope(db, user, item)
    polo_ids = db.execute(select(Polo.id).where(Polo.vereador_id.in_(vereador_ids or [-1]))).scalars().all()
    return {
        "vereadores": vereador_ids,
        "polos": len(polo_ids),
        "beneficiarios": db.scalar(select(func.count(func.distinct(BeneficiarioVereador.beneficiario_id))).where(BeneficiarioVereador.vereador_id.in_(vereador_ids or [-1]))) or 0,
        "valor_emendas": db.scalar(select(func.coalesce(func.sum(Emenda.valor_total), 0)).where(Emenda.vereador_id.in_(vereador_ids or [-1]))) or 0,
        "saldo_emendas": db.scalar(select(func.coalesce(func.sum(Emenda.valor_disponivel), 0)).where(Emenda.vereador_id.in_(vereador_ids or [-1]))) or 0,
        "compras": db.scalar(select(func.coalesce(func.sum(Compra.valor_total), 0)).join(Emenda).where(Emenda.vereador_id.in_(vereador_ids or [-1]))) or 0,
        "requisicoes": db.scalar(select(func.count(RequisicaoCompra.id)).where(RequisicaoCompra.vereador_id.in_(vereador_ids or [-1]))) or 0,
    }


@api.post("/prestacao-contas/gerar")
def gerar_prestacao_contas(competencia: str, vereador_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    require_finance(user)
    base = relatorio_vereador(vereador_id=vereador_id, db=db, user=user)
    return {"id": f"pc-{vereador_id}-{competencia}", "competencia": competencia, "gerado_em": datetime.utcnow().isoformat(), "status": "GERADO", "resumo": base}


@api.get("/prestacao-contas/{prestacao_id}")
def get_prestacao(prestacao_id: str, user: Usuario = Depends(get_current_user)) -> dict[str, Any]:
    return {"id": prestacao_id, "status": "GERADO", "versao": 1}


@api.get("/prestacao-contas/{prestacao_id}/versoes")
def get_prestacao_versoes(prestacao_id: str, user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [{"id": prestacao_id, "versao": 1, "gerado_em": datetime.utcnow().isoformat()}]


@api.get("/auditoria")
def list_auditoria(entidade: str | None = None, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[dict[str, Any]]:
    require_admin(user)
    query = select(Auditoria).order_by(Auditoria.data_evento.desc())
    if entidade:
        query = query.where(Auditoria.entidade == entidade)
    rows = db.execute(query.limit(200)).scalars().all()
    return [as_dict(row) for row in rows]


app = create_app()
