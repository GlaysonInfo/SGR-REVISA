from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginIn(BaseModel):
    login: str = Field(min_length=3)
    senha: str = Field(min_length=3)


class StatusPatch(BaseModel):
    status: str
    motivo: str | None = None


class UserIn(BaseModel):
    nome: str
    email_login: EmailStr
    senha: str = Field(min_length=6)
    perfil: str
    vereador_id: int | None = None
    polo_id: int | None = None
    ativo: bool = True


class UserUpdate(BaseModel):
    nome: str | None = None
    email_login: EmailStr | None = None
    perfil: str | None = None
    vereador_id: int | None = None
    polo_id: int | None = None
    ativo: bool | None = None
    senha: str | None = Field(default=None, min_length=6)


class VereadorIn(BaseModel):
    nome: str
    cpf_cnpj: str | None = None
    status: str = "ATIVO"


class EmendaIn(BaseModel):
    vereador_id: int
    codigo: str
    ano: int
    valor_total: float = Field(ge=0)
    status: str = "ATIVA"


class PoloIn(BaseModel):
    vereador_id: int
    nome: str
    endereco: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    responsavel_local: str | None = None
    status: str = "ATIVO"


class BeneficiarioIn(BaseModel):
    nome: str
    cpf: str | None = None
    rg: str | None = None
    data_nascimento: date | None = None
    sexo: str | None = None
    telefone: str | None = None
    email: EmailStr | None = None
    endereco: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    observacoes: str | None = None
    origem_cadastro: str = "WEB"
    status_cadastro: str = "ATIVO"
    vereador_ids: list[int] = []
    polo_ids: list[int] = []


class AreaIn(BaseModel):
    nome: str


class ModalidadeIn(BaseModel):
    area_id: int | None = None
    area_nome: str | None = None
    nome: str
    ativa: bool = True


class TurmaIn(BaseModel):
    polo_id: int
    modalidade_id: int
    nome: str
    capacidade: int = Field(default=20, ge=1)
    dias_semana: str | None = None
    horario_inicio: str | None = None
    horario_fim: str | None = None
    ativa: bool = True


class InscricaoIn(BaseModel):
    beneficiario_id: int
    turma_id: int
    data_inscricao: date | None = None
    status: str = "ATIVA"


class FrequenciaItemIn(BaseModel):
    inscricao_id: int
    presente: bool
    observacao: str | None = None


class FrequenciaLoteIn(BaseModel):
    turma_id: int
    data_atividade: date
    registros: list[FrequenciaItemIn]


class OcorrenciaIn(BaseModel):
    beneficiario_id: int
    polo_id: int
    tipo: str
    descricao: str
    data_ocorrencia: date | None = None


class EncaminhamentoIn(BaseModel):
    beneficiario_id: int
    polo_id: int
    tipo: str
    destino: str
    descricao: str | None = None
    data_registro: date | None = None
    status: str = "ABERTO"


class FornecedorIn(BaseModel):
    nome: str
    cpf_cnpj: str | None = None
    telefone: str | None = None
    email: EmailStr | None = None
    ativo: bool = True


class ItemRequisicaoIn(BaseModel):
    descricao: str
    quantidade: float = Field(gt=0)
    unidade: str = "un"
    valor_estimado: float = Field(default=0, ge=0)


class RequisicaoIn(BaseModel):
    polo_id: int
    descricao: str
    prioridade: str = "NORMAL"
    status: str = "ABERTA"
    itens: list[ItemRequisicaoIn]


class CompraIn(BaseModel):
    requisicao_id: int
    fornecedor_id: int
    emenda_id: int
    valor_total: float = Field(gt=0)
    data_compra: date | None = None
    status: str = "EXECUTADA"


class NotaFiscalIn(BaseModel):
    numero: str
    chave_acesso: str | None = None
    nome_arquivo: str | None = None
    mime_type: str | None = None
    tamanho: int | None = None


class ResponsavelIn(BaseModel):
    nome: str
    cpf: str | None = None
    telefone: str | None = None
    parentesco: str | None = None
    observacoes: str | None = None


class MobileCadastroIn(BaseModel):
    beneficiario: BeneficiarioIn
    responsavel: ResponsavelIn | None = None
    grupo_familiar: str | None = None
    demanda_imediata: str | None = None
    demanda_prioridade: str = "NORMAL"
    sugestao_tipo: str | None = None
    sugestao_descricao: str | None = None


class SyncIn(BaseModel):
    cadastros: list[MobileCadastroIn]


class ReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
