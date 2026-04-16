from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import hash_password
from .models import (
    AreaModalidade,
    Beneficiario,
    BeneficiarioPolo,
    BeneficiarioVereador,
    Emenda,
    Fornecedor,
    ItemRequisicao,
    Modalidade,
    Polo,
    RequisicaoCompra,
    Turma,
    Usuario,
    Vereador,
)


def seed_database(db: Session) -> None:
    existing_user = db.scalar(select(Usuario).where(Usuario.email_login == "admin@sgr.local"))
    if existing_user:
        return

    vereador_1 = Vereador(nome="Vereadora Ana Paula", cpf_cnpj="11111111000191", status="ATIVO")
    vereador_2 = Vereador(nome="Vereador Marcos Lima", cpf_cnpj="22222222000182", status="ATIVO")
    db.add_all([vereador_1, vereador_2])
    db.flush()

    polo_1 = Polo(
        vereador_id=vereador_1.id,
        nome="Polo Reviva Betim Centro",
        endereco="Rua das Acacias, 100",
        bairro="Centro",
        cidade="Betim",
        responsavel_local="Carla Mendes",
        status="ATIVO",
    )
    polo_2 = Polo(
        vereador_id=vereador_1.id,
        nome="Polo Esporte e Cidadania",
        endereco="Av. Amazonas, 501",
        bairro="Industrial",
        cidade="Betim",
        responsavel_local="Rafael Torres",
        status="ATIVO",
    )
    polo_3 = Polo(
        vereador_id=vereador_2.id,
        nome="Polo Social Norte",
        endereco="Rua Ipatinga, 20",
        bairro="Norte",
        cidade="Betim",
        responsavel_local="Mariana Costa",
        status="ATIVO",
    )
    db.add_all([polo_1, polo_2, polo_3])
    db.flush()

    db.add_all(
        [
            Emenda(
                vereador_id=vereador_1.id,
                codigo="EM-2026-REVIVA-001",
                ano=2026,
                valor_total=150000,
                valor_utilizado=0,
                valor_disponivel=150000,
                status="ATIVA",
            ),
            Emenda(
                vereador_id=vereador_2.id,
                codigo="EM-2026-SOCIAL-014",
                ano=2026,
                valor_total=90000,
                valor_utilizado=0,
                valor_disponivel=90000,
                status="ATIVA",
            ),
        ]
    )

    area_esporte = AreaModalidade(nome="Esportes")
    area_social = AreaModalidade(nome="Social")
    area_saude = AreaModalidade(nome="Saude")
    db.add_all([area_esporte, area_social, area_saude])
    db.flush()

    yoga = Modalidade(area_id=area_saude.id, nome="Yoga", ativa=True)
    futebol = Modalidade(area_id=area_esporte.id, nome="Futebol", ativa=True)
    oficinas = Modalidade(area_id=area_social.id, nome="Oficinas sociais", ativa=True)
    db.add_all([yoga, futebol, oficinas])
    db.flush()

    db.add_all(
        [
            Turma(
                polo_id=polo_1.id,
                modalidade_id=yoga.id,
                nome="Yoga Manha",
                capacidade=25,
                dias_semana="Segunda e quarta",
                horario_inicio="08:00",
                horario_fim="09:00",
                ativa=True,
            ),
            Turma(
                polo_id=polo_2.id,
                modalidade_id=futebol.id,
                nome="Futebol Sub-15",
                capacidade=30,
                dias_semana="Terca e quinta",
                horario_inicio="15:00",
                horario_fim="17:00",
                ativa=True,
            ),
        ]
    )

    ben_1 = Beneficiario(
        nome="Maria Aparecida Santos",
        cpf="12345678909",
        data_nascimento=date(1988, 5, 12),
        sexo="Feminino",
        telefone="31999990001",
        bairro="Centro",
        cidade="Betim",
        origem_cadastro="MOBILE",
        status_cadastro="ATIVO",
    )
    ben_2 = Beneficiario(
        nome="Joao da Silva",
        cpf="98765432100",
        data_nascimento=date(2012, 9, 2),
        sexo="Masculino",
        telefone="31999990002",
        bairro="Industrial",
        cidade="Betim",
        origem_cadastro="WEB",
        status_cadastro="ATIVO",
    )
    db.add_all([ben_1, ben_2])
    db.flush()
    db.add_all(
        [
            BeneficiarioVereador(beneficiario_id=ben_1.id, vereador_id=vereador_1.id),
            BeneficiarioVereador(beneficiario_id=ben_2.id, vereador_id=vereador_1.id),
            BeneficiarioPolo(beneficiario_id=ben_1.id, polo_id=polo_1.id),
            BeneficiarioPolo(beneficiario_id=ben_2.id, polo_id=polo_2.id),
        ]
    )

    fornecedor = Fornecedor(
        nome="Fornecedor Reviva Materiais",
        cpf_cnpj="33333333000173",
        telefone="3133330000",
        email="compras@fornecedor.local",
        ativo=True,
    )
    db.add(fornecedor)

    req = RequisicaoCompra(
        polo_id=polo_1.id,
        vereador_id=vereador_1.id,
        descricao="Materiais para atividades coletivas do polo",
        prioridade="ALTA",
        status="EM_ANALISE",
        data_requisicao=date.today(),
    )
    db.add(req)
    db.flush()
    db.add_all(
        [
            ItemRequisicao(requisicao_id=req.id, descricao="Colchonete", quantidade=20, unidade="un", valor_estimado=70),
            ItemRequisicao(requisicao_id=req.id, descricao="Garrafa de agua", quantidade=40, unidade="un", valor_estimado=18),
        ]
    )

    users = [
        Usuario(nome="Super Admin", email_login="admin@sgr.local", senha_hash=hash_password("admin123"), perfil="Super Admin", ativo=True),
        Usuario(nome="Equipe REVISA", email_login="revisa@sgr.local", senha_hash=hash_password("revisa123"), perfil="Gestor Institucional REVISA", ativo=True),
        Usuario(nome="Gestor do Vereador", email_login="vereador@sgr.local", senha_hash=hash_password("vereador123"), perfil="Gestor do Vereador", vereador_id=vereador_1.id, ativo=True),
        Usuario(nome="Gestora do Polo", email_login="polo@sgr.local", senha_hash=hash_password("polo123"), perfil="Gestor de Polo", vereador_id=vereador_1.id, polo_id=polo_1.id, ativo=True),
        Usuario(nome="Operador de Polo", email_login="operador@sgr.local", senha_hash=hash_password("operador123"), perfil="Operador de Polo", vereador_id=vereador_1.id, polo_id=polo_1.id, ativo=True),
        Usuario(nome="Captador Mobile", email_login="mobile@sgr.local", senha_hash=hash_password("mobile123"), perfil="Captador Mobile", vereador_id=vereador_1.id, polo_id=polo_1.id, ativo=True),
    ]
    db.add_all(users)
    db.commit()
