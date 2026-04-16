from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=func.now(), nullable=True)


class Vereador(TimestampMixin, Base):
    __tablename__ = "vereador"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    cpf_cnpj: Mapped[str] = mapped_column(String(24), unique=True, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="ATIVO", index=True)
    data_cadastro: Mapped[date] = mapped_column(Date, default=date.today)

    polos = relationship("Polo", back_populates="vereador")
    emendas = relationship("Emenda", back_populates="vereador")


class Emenda(TimestampMixin, Base):
    __tablename__ = "emenda"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vereador_id: Mapped[int] = mapped_column(ForeignKey("vereador.id"), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(80), nullable=False)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    valor_total: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    valor_utilizado: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    valor_disponivel: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(24), default="ATIVA", index=True)

    vereador = relationship("Vereador", back_populates="emendas")
    movimentacoes = relationship("MovimentacaoEmenda", back_populates="emenda")


class Polo(TimestampMixin, Base):
    __tablename__ = "polo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vereador_id: Mapped[int] = mapped_column(ForeignKey("vereador.id"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(180), nullable=False)
    endereco: Mapped[str] = mapped_column(String(240), nullable=True)
    bairro: Mapped[str] = mapped_column(String(120), nullable=True)
    cidade: Mapped[str] = mapped_column(String(120), nullable=True)
    responsavel_local: Mapped[str] = mapped_column(String(160), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="ATIVO", index=True)

    vereador = relationship("Vereador", back_populates="polos")
    turmas = relationship("Turma", back_populates="polo")
    requisicoes = relationship("RequisicaoCompra", back_populates="polo")
    relatorio_fotos = relationship("RelatorioMensalFoto", back_populates="polo")


class Usuario(TimestampMixin, Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    email_login: Mapped[str] = mapped_column(String(180), nullable=False, unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(180), nullable=False)
    perfil: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    vereador_id: Mapped[int] = mapped_column(ForeignKey("vereador.id"), index=True, nullable=True)
    polo_id: Mapped[int] = mapped_column(ForeignKey("polo.id"), index=True, nullable=True)
    ultimo_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    vereador = relationship("Vereador")
    polo = relationship("Polo")


class Beneficiario(TimestampMixin, Base):
    __tablename__ = "beneficiario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    cpf: Mapped[str] = mapped_column(String(14), unique=True, index=True, nullable=True)
    rg: Mapped[str] = mapped_column(String(32), nullable=True)
    data_nascimento: Mapped[date] = mapped_column(Date, nullable=True)
    sexo: Mapped[str] = mapped_column(String(32), nullable=True)
    telefone: Mapped[str] = mapped_column(String(32), index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(180), nullable=True)
    endereco: Mapped[str] = mapped_column(String(240), nullable=True)
    bairro: Mapped[str] = mapped_column(String(120), nullable=True)
    cidade: Mapped[str] = mapped_column(String(120), nullable=True)
    observacoes: Mapped[str] = mapped_column(Text, nullable=True)
    origem_cadastro: Mapped[str] = mapped_column(String(40), default="WEB")
    status_cadastro: Mapped[str] = mapped_column(String(32), default="ATIVO", index=True)

    vereadores = relationship("BeneficiarioVereador", back_populates="beneficiario", cascade="all, delete-orphan")
    polos = relationship("BeneficiarioPolo", back_populates="beneficiario", cascade="all, delete-orphan")
    inscricoes = relationship("Inscricao", back_populates="beneficiario")


class Responsavel(TimestampMixin, Base):
    __tablename__ = "responsavel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(180), nullable=False)
    cpf: Mapped[str] = mapped_column(String(14), nullable=True)
    telefone: Mapped[str] = mapped_column(String(32), nullable=True)
    parentesco: Mapped[str] = mapped_column(String(80), nullable=True)
    observacoes: Mapped[str] = mapped_column(Text, nullable=True)


class GrupoFamiliar(TimestampMixin, Base):
    __tablename__ = "grupo_familiar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beneficiario_id: Mapped[int] = mapped_column(ForeignKey("beneficiario.id"), nullable=False, index=True)
    responsavel_id: Mapped[int] = mapped_column(ForeignKey("responsavel.id"), index=True, nullable=True)
    composicao: Mapped[str] = mapped_column(Text, nullable=True)
    renda_familiar: Mapped[float] = mapped_column(Float, nullable=True)
    observacoes: Mapped[str] = mapped_column(Text, nullable=True)


class BeneficiarioVereador(TimestampMixin, Base):
    __tablename__ = "beneficiario_vereador"
    __table_args__ = (UniqueConstraint("beneficiario_id", "vereador_id", name="uq_beneficiario_vereador"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beneficiario_id: Mapped[int] = mapped_column(ForeignKey("beneficiario.id"), nullable=False, index=True)
    vereador_id: Mapped[int] = mapped_column(ForeignKey("vereador.id"), nullable=False, index=True)
    data_vinculo: Mapped[date] = mapped_column(Date, default=date.today)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    beneficiario = relationship("Beneficiario", back_populates="vereadores")
    vereador = relationship("Vereador")


class BeneficiarioPolo(TimestampMixin, Base):
    __tablename__ = "beneficiario_polo"
    __table_args__ = (UniqueConstraint("beneficiario_id", "polo_id", name="uq_beneficiario_polo"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beneficiario_id: Mapped[int] = mapped_column(ForeignKey("beneficiario.id"), nullable=False, index=True)
    polo_id: Mapped[int] = mapped_column(ForeignKey("polo.id"), nullable=False, index=True)
    data_entrada: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[str] = mapped_column(String(32), default="ATIVO", index=True)

    beneficiario = relationship("Beneficiario", back_populates="polos")
    polo = relationship("Polo")


class AreaModalidade(TimestampMixin, Base):
    __tablename__ = "area_modalidade"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)

    modalidades = relationship("Modalidade", back_populates="area")


class Modalidade(TimestampMixin, Base):
    __tablename__ = "modalidade"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("area_modalidade.id"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(140), nullable=False)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    area = relationship("AreaModalidade", back_populates="modalidades")
    turmas = relationship("Turma", back_populates="modalidade")


class Profissional(TimestampMixin, Base):
    __tablename__ = "profissional"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    documento: Mapped[str] = mapped_column(String(32), nullable=True)
    telefone: Mapped[str] = mapped_column(String(32), nullable=True)
    especialidade: Mapped[str] = mapped_column(String(120), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Turma(TimestampMixin, Base):
    __tablename__ = "turma"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    polo_id: Mapped[int] = mapped_column(ForeignKey("polo.id"), nullable=False, index=True)
    modalidade_id: Mapped[int] = mapped_column(ForeignKey("modalidade.id"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(140), nullable=False)
    capacidade: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    dias_semana: Mapped[str] = mapped_column(String(120), nullable=True)
    horario_inicio: Mapped[str] = mapped_column(String(16), nullable=True)
    horario_fim: Mapped[str] = mapped_column(String(16), nullable=True)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    polo = relationship("Polo", back_populates="turmas")
    modalidade = relationship("Modalidade", back_populates="turmas")
    inscricoes = relationship("Inscricao", back_populates="turma")


class Inscricao(TimestampMixin, Base):
    __tablename__ = "inscricao"
    __table_args__ = (UniqueConstraint("beneficiario_id", "turma_id", name="uq_beneficiario_turma"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beneficiario_id: Mapped[int] = mapped_column(ForeignKey("beneficiario.id"), nullable=False, index=True)
    turma_id: Mapped[int] = mapped_column(ForeignKey("turma.id"), nullable=False, index=True)
    data_inscricao: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[str] = mapped_column(String(32), default="ATIVA", index=True)

    beneficiario = relationship("Beneficiario", back_populates="inscricoes")
    turma = relationship("Turma", back_populates="inscricoes")
    frequencias = relationship("Frequencia", back_populates="inscricao")


class Frequencia(TimestampMixin, Base):
    __tablename__ = "frequencia"
    __table_args__ = (UniqueConstraint("inscricao_id", "data_atividade", name="uq_frequencia_data"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inscricao_id: Mapped[int] = mapped_column(ForeignKey("inscricao.id"), nullable=False, index=True)
    data_atividade: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    presente: Mapped[bool] = mapped_column(Boolean, default=False)
    observacao: Mapped[str] = mapped_column(Text, nullable=True)

    inscricao = relationship("Inscricao", back_populates="frequencias")


class Ocorrencia(TimestampMixin, Base):
    __tablename__ = "ocorrencia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beneficiario_id: Mapped[int] = mapped_column(ForeignKey("beneficiario.id"), nullable=False, index=True)
    polo_id: Mapped[int] = mapped_column(ForeignKey("polo.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(80), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    data_ocorrencia: Mapped[date] = mapped_column(Date, default=date.today)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), index=True, nullable=True)


class Encaminhamento(TimestampMixin, Base):
    __tablename__ = "encaminhamento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beneficiario_id: Mapped[int] = mapped_column(ForeignKey("beneficiario.id"), nullable=False, index=True)
    polo_id: Mapped[int] = mapped_column(ForeignKey("polo.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(80), nullable=False)
    destino: Mapped[str] = mapped_column(String(180), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=True)
    data_registro: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[str] = mapped_column(String(32), default="ABERTO", index=True)


class DemandaImediata(TimestampMixin, Base):
    __tablename__ = "demanda_imediata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beneficiario_id: Mapped[int] = mapped_column(ForeignKey("beneficiario.id"), nullable=False, index=True)
    polo_id: Mapped[int] = mapped_column(ForeignKey("polo.id"), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    prioridade: Mapped[str] = mapped_column(String(32), default="NORMAL")
    data_registro: Mapped[date] = mapped_column(Date, default=date.today)


class SugestaoCritica(TimestampMixin, Base):
    __tablename__ = "sugestao_critica"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beneficiario_id: Mapped[int] = mapped_column(ForeignKey("beneficiario.id"), nullable=False, index=True)
    polo_id: Mapped[int] = mapped_column(ForeignKey("polo.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(32), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    data_registro: Mapped[date] = mapped_column(Date, default=date.today)


class Fornecedor(TimestampMixin, Base):
    __tablename__ = "fornecedor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(180), nullable=False)
    cpf_cnpj: Mapped[str] = mapped_column(String(24), unique=True, nullable=True)
    telefone: Mapped[str] = mapped_column(String(32), nullable=True)
    email: Mapped[str] = mapped_column(String(180), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class RequisicaoCompra(TimestampMixin, Base):
    __tablename__ = "requisicao_compra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    polo_id: Mapped[int] = mapped_column(ForeignKey("polo.id"), nullable=False, index=True)
    vereador_id: Mapped[int] = mapped_column(ForeignKey("vereador.id"), nullable=False, index=True)
    solicitante_usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), index=True, nullable=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    prioridade: Mapped[str] = mapped_column(String(32), default="NORMAL", index=True)
    status: Mapped[str] = mapped_column(String(32), default="ABERTA", index=True)
    data_requisicao: Mapped[date] = mapped_column(Date, default=date.today)
    observacao: Mapped[str] = mapped_column(Text, nullable=True)

    polo = relationship("Polo", back_populates="requisicoes")
    vereador = relationship("Vereador")
    itens = relationship("ItemRequisicao", back_populates="requisicao", cascade="all, delete-orphan")
    compras = relationship("Compra", back_populates="requisicao")


class ItemRequisicao(TimestampMixin, Base):
    __tablename__ = "item_requisicao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requisicao_id: Mapped[int] = mapped_column(ForeignKey("requisicao_compra.id"), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(String(220), nullable=False)
    quantidade: Mapped[float] = mapped_column(Float, nullable=False)
    unidade: Mapped[str] = mapped_column(String(24), default="un")
    valor_estimado: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    requisicao = relationship("RequisicaoCompra", back_populates="itens")


class Compra(TimestampMixin, Base):
    __tablename__ = "compra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requisicao_id: Mapped[int] = mapped_column(ForeignKey("requisicao_compra.id"), nullable=False, index=True)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedor.id"), nullable=False, index=True)
    emenda_id: Mapped[int] = mapped_column(ForeignKey("emenda.id"), nullable=False, index=True)
    valor_total: Mapped[float] = mapped_column(Float, nullable=False)
    data_compra: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[str] = mapped_column(String(32), default="EXECUTADA", index=True)

    requisicao = relationship("RequisicaoCompra", back_populates="compras")
    fornecedor = relationship("Fornecedor")
    emenda = relationship("Emenda")
    notas = relationship("NotaFiscal", back_populates="compra")


class NotaFiscal(TimestampMixin, Base):
    __tablename__ = "nota_fiscal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    compra_id: Mapped[int] = mapped_column(ForeignKey("compra.id"), nullable=False, index=True)
    numero: Mapped[str] = mapped_column(String(80), nullable=False)
    chave_acesso: Mapped[str] = mapped_column(String(120), nullable=True)
    nome_arquivo: Mapped[str] = mapped_column(String(220), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(80), nullable=True)
    tamanho: Mapped[int] = mapped_column(Integer, nullable=True)
    data_upload: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    compra = relationship("Compra", back_populates="notas")


class MovimentacaoEmenda(TimestampMixin, Base):
    __tablename__ = "movimentacao_emenda"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    emenda_id: Mapped[int] = mapped_column(ForeignKey("emenda.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(32), nullable=False)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    referencia_tipo: Mapped[str] = mapped_column(String(80), nullable=True)
    referencia_id: Mapped[int] = mapped_column(Integer, nullable=True)
    data_movimento: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    emenda = relationship("Emenda", back_populates="movimentacoes")


class ArquivoUpload(TimestampMixin, Base):
    __tablename__ = "arquivo_upload"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome_original: Mapped[str] = mapped_column(String(220), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(80), nullable=True)
    tamanho: Mapped[int] = mapped_column(Integer, nullable=True)
    url_storage: Mapped[str] = mapped_column(String(320), nullable=True)
    hash_arquivo: Mapped[str] = mapped_column(String(128), nullable=True)
    usuario_upload_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    data_upload: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    relatorio_fotos = relationship("RelatorioMensalFoto", back_populates="arquivo")


class RelatorioMensalFoto(TimestampMixin, Base):
    __tablename__ = "relatorio_mensal_foto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    polo_id: Mapped[int] = mapped_column(ForeignKey("polo.id"), nullable=False, index=True)
    competencia: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    observacao: Mapped[str] = mapped_column(Text, nullable=True)
    arquivo_upload_id: Mapped[int] = mapped_column(ForeignKey("arquivo_upload.id"), nullable=False, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=True, index=True)

    polo = relationship("Polo", back_populates="relatorio_fotos")
    arquivo = relationship("ArquivoUpload", back_populates="relatorio_fotos")


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entidade: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entidade_id: Mapped[int] = mapped_column(Integer, index=True, nullable=True)
    acao: Mapped[str] = mapped_column(String(80), nullable=False)
    valor_anterior: Mapped[str] = mapped_column(Text, nullable=True)
    valor_novo: Mapped[str] = mapped_column(Text, nullable=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), index=True, nullable=True)
    data_evento: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
