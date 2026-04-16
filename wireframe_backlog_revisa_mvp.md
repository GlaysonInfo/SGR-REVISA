# Wireframe textual completo + backlog técnico por tela — REVISA MVP

## 1. Convenções usadas neste documento

### Estrutura por tela
Cada tela está organizada em 6 blocos:
- Frontend
- Backend
- Banco
- Validações
- Testes de aceite
- Wireframe textual

### Legenda de prioridade
- P0: essencial para o MVP
- P1: importante, mas pode entrar após o core
- P2: evolução

### Perfis citados
- Captador Mobile
- Operador de Polo
- Gestor de Polo
- Gestor Institucional REVISA
- Gestor do Vereador
- Super Admin

### Padrões globais
- Exclusão física não será usada no MVP. Usar inativação.
- Toda alteração sensível deve gerar auditoria.
- Escopo visual sempre respeita perfil + vereador + polo.
- Listas com paginação, filtros e ordenação.
- Campos de status usam enum padronizado.

---

# 2. APP MOBILE DE CAPTAÇÃO

## MOB-01 — Login
**Prioridade:** P0
**Perfis:** Captador Mobile

### Wireframe textual
```text
┌───────────────────────────────┐
│ REVISA                        │
│ Acesso Mobile                 │
├───────────────────────────────┤
│ Login                         │
│ [__________________________]  │
│ Senha                         │
│ [__________________________]  │
│                               │
│ [ Entrar ]                    │
│ Recuperar acesso              │
│ Status: Online / Offline      │
└───────────────────────────────┘
```

### Frontend
- Tela simples com campos login e senha.
- Indicador visual de conectividade.
- Estado de loading no botão Entrar.
- Mensagem de erro abaixo do formulário.
- Persistência segura de sessão local após autenticação.

### Backend
- `POST /auth/login`
- Validar credenciais, status do usuário e perfil autorizado para mobile.
- Retornar token, refresh token, perfil, escopo e expiração.
- Registrar tentativa de login e falhas.

### Banco
Tabelas envolvidas:
- `usuario`
- `perfil`
- `usuario_escopo`
- `auditoria` ou `log_autenticacao`

Campos críticos:
- `usuario.email_login`
- `usuario.senha_hash`
- `usuario.ativo`
- `usuario.ultimo_login`

### Validações
- Login obrigatório.
- Senha obrigatória.
- Usuário ativo.
- Perfil compatível com mobile.
- Conta bloqueada não pode autenticar.

### Testes de aceite
- Deve autenticar com credenciais válidas.
- Deve recusar senha incorreta com mensagem amigável.
- Deve bloquear usuário inativo.
- Deve bloquear perfil sem permissão mobile.
- Deve exibir loading até resposta do servidor.
- Deve persistir sessão válida após login.

---

## MOB-02 — Início
**Prioridade:** P0
**Perfis:** Captador Mobile

### Wireframe textual
```text
┌──────────────────────────────────────┐
│ Olá, [Nome do usuário]               │
│ Status: Online / Offline             │
├──────────────────────────────────────┤
│ [ Novo Cadastro ]                    │
├──────────────────────────────────────┤
│ Pendentes de sincronização: 12       │
│ Sincronizados hoje: 8                │
├──────────────────────────────────────┤
│ Cadastros recentes                   │
│ - Maria Aparecida      [Rascunho]    │
│ - João da Silva        [Sincronizado]│
│ - Ana Souza            [Erro]        │
├──────────────────────────────────────┤
│ [ Ir para Sincronização ]            │
└──────────────────────────────────────┘
```

### Frontend
- Home com cards resumidos.
- CTA principal: Novo Cadastro.
- Lista de últimos cadastros com status.
- Indicador de conexão persistente.
- Navegação para sincronização.

### Backend
- `GET /mobile/dashboard`
- `GET /mobile/cadastros/recentes`
- Possível composição com dados locais + dados remotos.

### Banco
- Base local do app para rascunhos e fila de sincronização.
- Remoto:
  - `beneficiario`
  - `sync_queue` (ou equivalente local)
  - `beneficiario_vereador`
  - `beneficiario_polo`

### Validações
- Apenas usuário autenticado pode acessar.
- Contadores devem refletir estado local + remoto conforme regra definida.

### Testes de aceite
- Deve exibir pendentes corretamente.
- Deve abrir novo cadastro em um toque.
- Deve mostrar cadastros recentes do usuário logado.
- Deve exibir banner quando offline.

---

## MOB-03 — Cadastro de Beneficiário
**Prioridade:** P0
**Perfis:** Captador Mobile

### Wireframe textual
```text
┌──────────────────────────────────────────────┐
│ Novo Cadastro > Beneficiário                 │
├──────────────────────────────────────────────┤
│ Nome completo*                               │
│ [________________________________________]   │
│ CPF                                          │
│ [______________]                             │
│ RG                                           │
│ [______________]                             │
│ Data de nascimento                           │
│ [__/__/____]                                 │
│ Sexo                                         │
│ [ selecione ▼ ]                              │
│ Telefone principal                           │
│ [______________]                             │
│ Telefone secundário                          │
│ [______________]                             │
│ E-mail                                       │
│ [________________________________________]   │
│ CEP / Logradouro / Número / Complemento      │
│ Bairro / Cidade                              │
│ Observações                                  │
│ [________________________________________]   │
├──────────────────────────────────────────────┤
│ [ Salvar rascunho ]   [ Avançar ]            │
└──────────────────────────────────────────────┘
```

### Frontend
- Formulário em etapas com máscara para CPF, telefone e CEP.
- Alerta inline para possível duplicidade.
- Busca opcional de endereço por CEP.
- Botão de salvar rascunho.
- Navegação para próxima etapa.

### Backend
- No MVP mobile, salvar localmente e sincronizar depois.
- Na sincronização: `POST /mobile/beneficiarios`
- Endpoint de consulta de duplicidade opcional: `GET /beneficiarios/duplicidade?cpf=...`

### Banco
Tabelas:
- `beneficiario`
- `arquivo_upload` (futuro, se houver documentos)

Campos críticos:
- `nome`
- `cpf`
- `rg`
- `data_nascimento`
- `sexo`
- `telefone`
- `email`
- `endereco`
- `bairro`
- `cidade`
- `observacoes`
- `status_cadastro`

### Validações
- Nome obrigatório, mínimo 5 caracteres.
- CPF válido quando informado.
- CPF único quando informado.
- Data de nascimento não futura.
- E-mail válido quando informado.
- Cidade recomendada, mesmo que não obrigatória no mobile.

### Testes de aceite
- Deve impedir avanço sem nome.
- Deve alertar CPF inválido.
- Deve alertar duplicidade potencial ao informar CPF já existente.
- Deve permitir salvar rascunho sem preencher campos opcionais.
- Deve manter dados digitados ao voltar da próxima tela.

---

## MOB-04 — Grupo Familiar / Responsável
**Prioridade:** P0
**Perfis:** Captador Mobile

### Wireframe textual
```text
┌──────────────────────────────────────────────┐
│ Novo Cadastro > Grupo Familiar               │
├──────────────────────────────────────────────┤
│ Responsável principal                        │
│ Nome*                                        │
│ [________________________________________]   │
│ Parentesco*                                  │
│ [ selecione ▼ ]                              │
│ Telefone                                     │
│ [______________]                             │
│ CPF                                          │
│ [______________]                             │
│ Observação                                   │
│ [________________________________________]   │
├──────────────────────────────────────────────┤
│ Integrantes familiares                       │
│ [+ Adicionar integrante]                     │
│ - José / irmão / 12 anos    [Editar] [X]    │
│ - Carla / mãe / 45 anos     [Editar] [X]    │
├──────────────────────────────────────────────┤
│ [ Voltar ] [ Salvar rascunho ] [ Avançar ]   │
└──────────────────────────────────────────────┘
```

### Frontend
- Formulário principal para responsável.
- Repeater/lista dinâmica para integrantes.
- Edição em modal ou subetapa.
- Estado visual para responsável principal.

### Backend
- Persistência local no app.
- Sincronização posterior:
  - `POST /mobile/responsaveis`
  - `POST /mobile/grupo-familiar`

### Banco
Tabelas:
- `responsavel`
- `grupo_familiar`
- `beneficiario_responsavel`

Campos críticos:
- `responsavel.nome`
- `responsavel.cpf`
- `responsavel.telefone`
- `beneficiario_responsavel.parentesco`
- `beneficiario_responsavel.principal`

### Validações
- Responsável principal obrigatório se beneficiário for menor de idade.
- Parentesco obrigatório quando houver responsável.
- CPF do responsável válido quando informado.

### Testes de aceite
- Deve permitir adicionar múltiplos integrantes.
- Deve permitir editar e remover integrante antes do envio.
- Deve exigir responsável principal para menor de idade.
- Deve associar os integrantes ao beneficiário correto.

---

## MOB-05 — Vínculo Inicial
**Prioridade:** P0
**Perfis:** Captador Mobile

### Wireframe textual
```text
┌──────────────────────────────────────────────┐
│ Novo Cadastro > Vínculo Inicial              │
├──────────────────────────────────────────────┤
│ Vereador*                                    │
│ [ selecione ▼ ]                              │
│ Polo*                                        │
│ [ selecione ▼ ]                              │
│ Área de interesse                            │
│ [ Saúde ▼ ]                                  │
│ Modalidade de interesse                      │
│ [ selecione ▼ ]                              │
│ Origem do cadastro*                          │
│ [ atendimento inicial ▼ ]                    │
│ Observação                                   │
│ [________________________________________]   │
├──────────────────────────────────────────────┤
│ [ Voltar ] [ Salvar rascunho ] [ Avançar ]   │
└──────────────────────────────────────────────┘
```

### Frontend
- Select encadeado vereador → polo → modalidade.
- Carregamento dependente por contexto.
- Mensagem quando não houver modalidades disponíveis.

### Backend
- `GET /vereadores`
- `GET /polos?vereador_id=`
- `GET /modalidades?polo_id=&area=`
- Sync final grava em:
  - `beneficiario_vereador`
  - `beneficiario_polo`

### Banco
Tabelas:
- `beneficiario_vereador`
- `beneficiario_polo`
- `modalidade`
- `polo`
- `vereador`

### Validações
- Vereador obrigatório.
- Polo obrigatório.
- Polo deve pertencer ao vereador escolhido.
- Modalidade, quando informada, deve estar ativa no polo.

### Testes de aceite
- Deve filtrar polos pelo vereador selecionado.
- Deve limpar polo ao trocar vereador.
- Deve permitir seguir sem modalidade, se essa regra for mantida.
- Deve gravar origem do cadastro.

---

## MOB-06 — Atendimento Inicial
**Prioridade:** P1
**Perfis:** Captador Mobile

### Wireframe textual
```text
┌──────────────────────────────────────────────┐
│ Novo Cadastro > Atendimento Inicial          │
├──────────────────────────────────────────────┤
│ [+ Adicionar registro]                       │
│                                              │
│ Registro 1                                   │
│ Tipo* [ demanda_imediata ▼ ]                 │
│ Categoria [ social ▼ ]                       │
│ Prioridade [ alta ▼ ]                        │
│ Descrição*                                   │
│ [________________________________________]   │
│ [Editar] [Excluir]                           │
│                                              │
│ Registro 2                                   │
│ Tipo* [ sugestao ▼ ]                         │
│ Categoria [ atendimento ▼ ]                  │
│ Descrição*                                   │
│ [________________________________________]   │
├──────────────────────────────────────────────┤
│ [ Voltar ] [ Salvar rascunho ] [ Avançar ]   │
└──────────────────────────────────────────────┘
```

### Frontend
- Lista dinâmica de registros qualitativos.
- Tipo condiciona exibição de prioridade.
- Possibilidade de múltiplos itens.

### Backend
- Persistência local.
- Sincronização posterior em:
  - `POST /mobile/demandas`
  - `POST /mobile/sugestoes-criticas`

### Banco
Tabelas:
- `demanda_imediata`
- `sugestao_critica`

### Validações
- Tipo obrigatório.
- Descrição obrigatória.
- Prioridade obrigatória para demanda imediata.

### Testes de aceite
- Deve permitir múltiplos registros.
- Deve exibir prioridade apenas para demanda imediata.
- Deve impedir salvar item sem descrição.

---

## MOB-07 — Resumo e Envio
**Prioridade:** P0
**Perfis:** Captador Mobile

### Wireframe textual
```text
┌──────────────────────────────────────────────┐
│ Novo Cadastro > Resumo                       │
├──────────────────────────────────────────────┤
│ Beneficiário        [Editar]                 │
│ Responsável/Família [Editar]                 │
│ Vínculo            [Editar]                  │
│ Atendimento Inicial [Editar]                 │
├──────────────────────────────────────────────┤
│ Status: Rascunho                              │
├──────────────────────────────────────────────┤
│ [ Voltar ] [ Salvar rascunho ] [ Enviar ]    │
└──────────────────────────────────────────────┘
```

### Frontend
- Cards recolhíveis com resumo por seção.
- Destaque de pendências obrigatórias.
- CTA final Enviar.

### Backend
- Envio para fila local de sincronização.
- `POST /mobile/cadastros/finalizar`

### Banco
- Fila local de sincronização.
- Remoto: todas as tabelas do fluxo de cadastro.

### Validações
- Nome obrigatório preenchido.
- Vereador e polo preenchidos.
- Estrutura mínima íntegra antes de envio.

### Testes de aceite
- Deve mostrar resumo de todas as seções.
- Deve permitir editar qualquer seção antes do envio.
- Deve marcar como pendente de sincronização após enviar localmente.

---

## MOB-08 — Sincronização
**Prioridade:** P0
**Perfis:** Captador Mobile

### Wireframe textual
```text
┌──────────────────────────────────────────────┐
│ Sincronização                                │
├──────────────────────────────────────────────┤
│ [Pendentes] [Sincronizados] [Com erro]       │
├──────────────────────────────────────────────┤
│ Maria Aparecida   10:32   [Pendente]         │
│ João da Silva     10:28   [Erro]             │
│ Ana Souza         09:50   [Sincronizado]     │
├──────────────────────────────────────────────┤
│ [ Sincronizar tudo ] [ Reenviar item ]       │
│ Motivo do erro: CPF duplicado                │
└──────────────────────────────────────────────┘
```

### Frontend
- Tabs por status.
- Ações em lote e por item.
- Bloqueio de clique duplo no envio.
- Detalhe de erro expandível.

### Backend
- `POST /mobile/sync`
- Tratamento idempotente com `client_generated_id` ou hash.
- Retorno detalhado por item.

### Banco
- Fila local: `sync_queue`
- Remoto: todas as tabelas alvo do cadastro
- Registro de idempotência

### Validações
- Não duplicar envio do mesmo item.
- Erro do servidor deve retornar motivo amigável.

### Testes de aceite
- Deve sincronizar itens pendentes.
- Deve mover item sincronizado para aba correta.
- Deve permitir reenviar item com erro.
- Deve evitar duplicidade em reenvio acidental.

---

# 3. GESTÃO DE POLOS

## POL-01 — Dashboard do Polo
**Prioridade:** P0
**Perfis:** Operador de Polo, Gestor de Polo

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Dashboard do Polo [Período ▼] [Modalidade ▼]              │
├────────────────────────────────────────────────────────────┤
│ Beneficiários ativos | Inscrições ativas | Frequência     │
│ Requisições abertas  | Ocorrências do período             │
├────────────────────────────────────────────────────────────┤
│ [Gráfico frequência]                                      │
├────────────────────────────────────────────────────────────┤
│ Requisições recentes                                      │
│ Ocorrências recentes                                      │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Cards clicáveis.
- Gráfico simples de linha ou barras.
- Lista resumida de pendências.
- Filtros por período e modalidade.

### Backend
- `GET /polos/{id}/dashboard`
- Agregações por período.
- Respeito ao escopo do usuário.

### Banco
Consultas sobre:
- `beneficiario_polo`
- `inscricao`
- `frequencia`
- `requisicao_compra`
- `ocorrencia`

### Validações
- Usuário só acessa dados do polo autorizado.
- Período padrão: mês atual.

### Testes de aceite
- Deve carregar apenas dados do polo do usuário.
- Deve atualizar indicadores ao mudar período.
- Cada card deve abrir a tela correspondente filtrada.

---

## POL-02 — Lista de Beneficiários
**Prioridade:** P0
**Perfis:** Operador de Polo, Gestor de Polo

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Beneficiários                                             │
├────────────────────────────────────────────────────────────┤
│ Busca [________________] CPF [__________] Status [▼]      │
│ Modalidade [▼] Polo [▼]            [Filtrar] [Novo]       │
├────────────────────────────────────────────────────────────┤
│ Nome | CPF | Nascimento | Polo(s) | Status | Ações        │
│ Ana  | ... | ...        | 2        | Ativo  | Ver Editar  │
│ ...                                                        │
├────────────────────────────────────────────────────────────┤
│ Paginação                                                  │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Listagem paginada com filtros persistidos na URL.
- Ações por linha: visualizar, editar, vincular, inscrever, histórico.
- Badge de duplicidade potencial.

### Backend
- `GET /beneficiarios`
- Filtros por nome, CPF, status, modalidade, polo, vereador via escopo.
- Paginação e ordenação.

### Banco
Tabelas:
- `beneficiario`
- `beneficiario_polo`
- `beneficiario_vereador`
- `inscricao`
- `turma`

Índices recomendados:
- `beneficiario(cpf)`
- `beneficiario(nome)`
- `beneficiario_polo(polo_id, status)`

### Validações
- Escopo de acesso obrigatório.
- CPF com máscara no filtro.

### Testes de aceite
- Deve buscar por nome parcial.
- Deve buscar por CPF exato.
- Deve listar apenas registros no escopo autorizado.
- Deve permitir abrir cadastro para edição.

---

## POL-03 — Cadastro/Edição de Beneficiário
**Prioridade:** P0
**Perfis:** Operador de Polo, Gestor de Polo

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Beneficiário > Editar                                      │
├────────────────────────────────────────────────────────────┤
│ Aba 1 Dados pessoais                                       │
│ Aba 2 Contato / Endereço                                   │
│ Aba 3 Vínculos                                              │
│ Aba 4 Observações / Histórico                               │
├────────────────────────────────────────────────────────────┤
│ [Campos do cadastro]                                        │
├────────────────────────────────────────────────────────────┤
│ [Salvar] [Salvar e continuar] [Inativar] [Histórico]        │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Formulário em abas.
- Histórico em drawer/modal lateral.
- Campo status com motivo de inativação quando necessário.

### Backend
- `GET /beneficiarios/{id}`
- `PUT /beneficiarios/{id}`
- `PATCH /beneficiarios/{id}/status`
- `GET /beneficiarios/{id}/historico`

### Banco
Tabelas:
- `beneficiario`
- `beneficiario_polo`
- `beneficiario_vereador`
- `auditoria`

### Validações
- CPF único quando alterado.
- Motivo obrigatório ao inativar.
- Edição só para perfis autorizados.

### Testes de aceite
- Deve salvar alterações válidas.
- Deve impedir CPF duplicado.
- Deve exigir motivo ao inativar.
- Deve registrar trilha de auditoria.

---

## POL-04 — Modalidades
**Prioridade:** P0
**Perfis:** Gestor de Polo, Gestor Institucional

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Modalidades                             [Nova Modalidade]  │
├────────────────────────────────────────────────────────────┤
│ Nome | Área | Status | Qtde turmas | Ações                │
│ Judô | Esportes | Ativa | 3         | Editar Inativar     │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Lista simples com modal lateral para criação/edição.
- Toggle para ativar/inativar.

### Backend
- `GET /modalidades`
- `POST /modalidades`
- `PUT /modalidades/{id}`
- `PATCH /modalidades/{id}/status`

### Banco
Tabelas:
- `area_modalidade`
- `modalidade`

### Validações
- Nome obrigatório.
- Área obrigatória.
- Não permitir exclusão física.
- Não permitir inativar sem aviso quando houver turmas ativas.

### Testes de aceite
- Deve criar modalidade válida.
- Deve impedir salvar sem área.
- Deve listar quantidade de turmas vinculadas.

---

## POL-05 — Turmas
**Prioridade:** P0
**Perfis:** Gestor de Polo

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Turmas                                   [Nova Turma]      │
├────────────────────────────────────────────────────────────┤
│ Modalidade | Nome | Horário | Capacidade | Status | Ações │
│ Judô       | T1   | 08-09h  | 20         | Ativa  | ...   │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Tabela de turmas com botão Nova Turma.
- Formulário em modal/drawer.
- Visualização rápida de inscritos.

### Backend
- `GET /turmas`
- `POST /turmas`
- `PUT /turmas/{id}`
- `PATCH /turmas/{id}/status`
- `GET /turmas/{id}/inscritos`

### Banco
Tabelas:
- `turma`
- `modalidade`
- `profissional`
- `turma_profissional` (se usar)

### Validações
- Modalidade obrigatória.
- Nome da turma obrigatório.
- Capacidade mínima 1 quando informada.
- Horário fim maior que início.

### Testes de aceite
- Deve criar turma ativa.
- Deve impedir horário inválido.
- Deve permitir inativar turma.
- Deve mostrar quantidade de inscritos.

---

## POL-06 — Inscrições
**Prioridade:** P0
**Perfis:** Operador de Polo, Gestor de Polo

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Nova Inscrição                                             │
├────────────────────────────────────────────────────────────┤
│ Beneficiário* [ buscar por nome/CPF __________ ]           │
│ Turma*        [ selecione ▼ ]                              │
│ Data*         [__/__/____]                                 │
│ Status*       [ ATIVA ▼ ]                                  │
│ Observação    [________________________________________]   │
│ Vagas restantes: 3                                         │
├────────────────────────────────────────────────────────────┤
│ [Salvar] [Cancelar]                                        │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Autocomplete para beneficiário.
- Exibir capacidade da turma e vagas restantes.
- Alerta visual de turma lotada.

### Backend
- `POST /inscricoes`
- `GET /turmas/{id}/capacidade`
- `PATCH /inscricoes/{id}/status`

### Banco
Tabelas:
- `inscricao`
- `turma`
- `beneficiario_polo`

### Validações
- Beneficiário obrigatório.
- Turma obrigatória.
- Não duplicar inscrição ativa na mesma turma.
- Beneficiário deve estar vinculado ao polo da turma.
- Respeitar capacidade salvo permissão especial.

### Testes de aceite
- Deve criar inscrição válida.
- Deve bloquear inscrição duplicada.
- Deve alertar turma lotada.
- Deve impedir inscrição de beneficiário fora do polo.

---

## POL-07 — Frequência
**Prioridade:** P0
**Perfis:** Operador de Polo, Gestor de Polo

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Frequência                                                 │
├────────────────────────────────────────────────────────────┤
│ Turma* [▼]   Data* [__/__/____] [Carregar]                 │
├────────────────────────────────────────────────────────────┤
│ Nome | Status inscrição | Presente | Observação           │
│ Ana  | Ativa            | [x]      | [___________]        │
│ João | Ativa            | [ ]      | [___________]        │
├────────────────────────────────────────────────────────────┤
│ [Marcar todos] [Limpar] [Salvar frequência]               │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Grade editável em lote.
- Botão marcar todos presentes.
- Bloqueio visual para registros já salvos.

### Backend
- `GET /frequencia/carga?turma_id=&data=`
- `POST /frequencia/lote`
- Idempotência por `inscricao_id + data_atividade`

### Banco
Tabelas:
- `frequencia`
- `inscricao`

Índice único:
- `(inscricao_id, data_atividade)`

### Validações
- Turma obrigatória.
- Data obrigatória.
- Não duplicar registro por inscrição e data.
- Só listar inscrições ativas.

### Testes de aceite
- Deve carregar inscritos ativos da turma.
- Deve salvar frequência em lote.
- Deve impedir duplicidade de frequência na mesma data.
- Deve permitir observação opcional por linha.

---

## POL-08 — Ocorrências
**Prioridade:** P1
**Perfis:** Operador de Polo, Gestor de Polo

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Nova Ocorrência                                            │
├────────────────────────────────────────────────────────────┤
│ Beneficiário* [ buscar __________ ]                        │
│ Tipo*         [ comportamento ▼ ]                          │
│ Data/Hora*    [__/__/____ __:__]                           │
│ Gravidade     [ média ▼ ]                                  │
│ Descrição*    [________________________________________]   │
│ Anexos        [Selecionar arquivo]                         │
├────────────────────────────────────────────────────────────┤
│ [Salvar] [Salvar e novo] [Cancelar]                        │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Formulário simples com upload opcional.
- Campo beneficiário com autocomplete.

### Backend
- `POST /ocorrencias`
- `GET /beneficiarios/search`
- Upload opcional para storage

### Banco
Tabelas:
- `ocorrencia`
- `arquivo_upload`

### Validações
- Beneficiário obrigatório.
- Tipo obrigatório.
- Data/hora obrigatória.
- Descrição obrigatória.

### Testes de aceite
- Deve registrar ocorrência com autor e timestamp.
- Deve permitir anexar arquivo válido.
- Deve manter histórico por beneficiário.

---

## POL-09 — Encaminhamentos
**Prioridade:** P1
**Perfis:** Operador de Polo, Gestor de Polo

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Novo Encaminhamento                                        │
├────────────────────────────────────────────────────────────┤
│ Beneficiário* [ buscar __________ ]                        │
│ Tipo*         [ psicologia ▼ ]                             │
│ Destino*      [________________________________________]   │
│ Data*         [__/__/____]                                 │
│ Status*       [ aberto ▼ ]                                 │
│ Retorno prev. [__/__/____]                                 │
│ Descrição*    [________________________________________]   │
├────────────────────────────────────────────────────────────┤
│ [Salvar] [Atualizar status] [Cancelar]                     │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Formulário com status e histórico.
- Timeline opcional para mudanças de status.

### Backend
- `POST /encaminhamentos`
- `PUT /encaminhamentos/{id}`
- `PATCH /encaminhamentos/{id}/status`

### Banco
Tabelas:
- `encaminhamento`

### Validações
- Beneficiário obrigatório.
- Tipo obrigatório.
- Destino obrigatório.
- Descrição obrigatória.

### Testes de aceite
- Deve salvar encaminhamento válido.
- Deve permitir atualizar status.
- Deve exibir histórico por beneficiário.

---

## POL-10 — Requisição de Compra
**Prioridade:** P0
**Perfis:** Gestor de Polo

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Nova Requisição de Compra                                  │
├────────────────────────────────────────────────────────────┤
│ Polo: Centro Betim             Vereador: Fulano           │
│ Prioridade* [ média ▼ ]                                  │
│ Descrição geral*                                         │
│ [______________________________________________]         │
│ Justificativa                                            │
│ [______________________________________________]         │
│ Anexo suporte [Selecionar arquivo]                       │
├────────────────────────────────────────────────────────────┤
│ Itens                                                     │
│ Descrição | Qtde | Unidade | Valor estimado | Obs | X    │
│ [_____]   [__]  [__]     [_____]          [__]          │
│ [+ Adicionar item]                                        │
├────────────────────────────────────────────────────────────┤
│ [Salvar rascunho] [Enviar requisição]                     │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Cabeçalho preenchido automaticamente com polo e vereador.
- Grid dinâmica de itens.
- Soma opcional do valor estimado total.

### Backend
- `POST /requisicoes-compra`
- `PUT /requisicoes-compra/{id}`
- `POST /requisicoes-compra/{id}/enviar`
- Upload opcional de suporte

### Banco
Tabelas:
- `requisicao_compra`
- `item_requisicao`
- `arquivo_upload`

### Validações
- Descrição geral obrigatória.
- Prioridade obrigatória.
- Pelo menos um item.
- Quantidade > 0.
- Vereador herdado do polo, sem edição manual.

### Testes de aceite
- Deve criar requisição com um ou mais itens.
- Deve vincular automaticamente ao polo e vereador corretos.
- Deve iniciar com status `ABERTA` ou `RASCUNHO` conforme fluxo decidido.
- Deve enviar requisição para análise.

---

## POL-11 — Minhas Requisições
**Prioridade:** P0
**Perfis:** Gestor de Polo

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Minhas Requisições                                         │
├────────────────────────────────────────────────────────────┤
│ Período [____] Status [▼] Prioridade [▼] [Filtrar]        │
├────────────────────────────────────────────────────────────┤
│ Nº | Data | Descrição | Prioridade | Status | Valor | Ações│
│ 12 | ...  | Materiais | Alta       | Em análise | ...     │
├────────────────────────────────────────────────────────────┤
│ Histórico da requisição selecionada                        │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Listagem com linha do tempo do status.
- Status em badges coloridos.
- Ação de duplicar requisição.

### Backend
- `GET /requisicoes-compra`
- `GET /requisicoes-compra/{id}/historico`
- `POST /requisicoes-compra/{id}/duplicar`

### Banco
Tabelas:
- `requisicao_compra`
- `item_requisicao`
- `aprovacao_requisicao` ou histórico embutido

### Validações
- Mostrar apenas requisições no escopo do polo.

### Testes de aceite
- Deve filtrar por status e período.
- Deve exibir histórico completo da requisição.
- Deve mostrar somente requisições do escopo do usuário.

---

## POL-12 — Relatórios do Polo
**Prioridade:** P1
**Perfis:** Operador de Polo, Gestor de Polo

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Relatórios do Polo                                         │
├────────────────────────────────────────────────────────────┤
│ Tipo [ frequência ▼ ] Período [____ a ____]               │
│ Modalidade [▼] Turma [▼] Status [▼] [Gerar]               │
├────────────────────────────────────────────────────────────┤
│ Prévia do relatório                                        │
├────────────────────────────────────────────────────────────┤
│ [Exportar PDF] [Exportar Excel]                            │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Tela única com filtros e prévia.
- Exportação PDF e Excel.

### Backend
- `GET /relatorios/polo/frequencia`
- `GET /relatorios/polo/inscritos`
- `GET /relatorios/polo/ocorrencias`
- `GET /relatorios/polo/requisicoes`
- Exportação assíncrona opcional em fases futuras.

### Banco
Consultas sobre:
- `beneficiario_polo`
- `inscricao`
- `frequencia`
- `ocorrencia`
- `requisicao_compra`

### Validações
- Tipo de relatório obrigatório.
- Período obrigatório para relatórios temporais.

### Testes de aceite
- Deve gerar relatório conforme filtros.
- Deve respeitar escopo do polo.
- Deve exportar PDF e Excel.

---

# 4. REVISA INSTITUCIONAL

## REV-01 — Dashboard Geral
**Prioridade:** P0
**Perfis:** Gestor Institucional, Gestor do Vereador, Super Admin

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Dashboard Geral                                            │
│ Período [____] Vereador [▼] Polo [▼] [Aplicar]            │
├────────────────────────────────────────────────────────────┤
│ Vereadores ativos | Polos ativos | Beneficiários          │
│ Emendas total     | Saldo disp.  | Req. pendentes         │
├────────────────────────────────────────────────────────────┤
│ [Gráfico por vereador] [Gráfico por tipo de gasto]        │
├────────────────────────────────────────────────────────────┤
│ Pendências críticas                                        │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Cards executivos.
- Gráficos básicos.
- Lista de pendências clicável.

### Backend
- `GET /dashboard/institucional`
- Agregações por vereador, polo, emenda e compras.

### Banco
Consultas sobre:
- `vereador`
- `polo`
- `beneficiario_vereador`
- `emenda`
- `requisicao_compra`
- `compra`

### Validações
- Escopo do usuário deve limitar vereador/polo disponíveis.

### Testes de aceite
- Deve exibir consolidados corretos.
- Deve atualizar com filtros.
- Deve respeitar escopo por perfil.

---

## REV-02 — Vereadores
**Prioridade:** P0
**Perfis:** Gestor Institucional, Super Admin

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Vereadores                               [Novo Vereador]   │
├────────────────────────────────────────────────────────────┤
│ Nome | CPF/CNPJ | Status | Polos | Emendas | Ações        │
│ ...                                                        │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Listagem com criação/edição em drawer.
- Ações: editar, inativar, ver polos, ver emendas.

### Backend
- `GET /vereadores`
- `POST /vereadores`
- `PUT /vereadores/{id}`
- `PATCH /vereadores/{id}/status`

### Banco
Tabelas:
- `vereador`
- `auditoria`

### Validações
- Nome obrigatório.
- Não permitir exclusão física com vínculos.

### Testes de aceite
- Deve criar vereador válido.
- Deve editar vereador existente.
- Deve inativar sem apagar histórico.

---

## REV-03 — Emendas
**Prioridade:** P0
**Perfis:** Gestor Institucional, Super Admin

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Emendas                                   [Nova Emenda]    │
├────────────────────────────────────────────────────────────┤
│ Vereador | Código | Ano | Valor total | Utilizado | Saldo │
│ ...                                                        │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Tabela com campos calculados.
- Detalhe de movimentações em drawer.

### Backend
- `GET /emendas`
- `POST /emendas`
- `PUT /emendas/{id}`
- `PATCH /emendas/{id}/status`
- `GET /emendas/{id}/movimentacoes`

### Banco
Tabelas:
- `emenda`
- `movimentacao_emenda`

### Validações
- Código obrigatório.
- Ano obrigatório.
- Valor total > 0.
- Código único por vereador/ano.

### Testes de aceite
- Deve criar emenda válida.
- Deve exibir utilizado e saldo calculados.
- Deve bloquear uso de saldo negativo.

---

## REV-04 — Polos
**Prioridade:** P0
**Perfis:** Gestor Institucional, Super Admin

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Polos                                      [Novo Polo]     │
├────────────────────────────────────────────────────────────┤
│ Nome | Vereador | Cidade | Status | Beneficiários | Ações │
│ ...                                                        │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Listagem com filtros por vereador e cidade.
- Drawer para cadastro/edição.

### Backend
- `GET /polos`
- `POST /polos`
- `PUT /polos/{id}`
- `PATCH /polos/{id}/status`

### Banco
Tabelas:
- `polo`
- `vereador`

### Validações
- Polo deve ter vereador.
- Nome obrigatório.
- Cidade obrigatória.

### Testes de aceite
- Deve criar polo vinculado a um vereador.
- Deve impedir polo sem vereador.
- Deve permitir inativação.

---

## REV-05 — Fila de Requisições
**Prioridade:** P0
**Perfis:** Gestor Institucional, Super Admin

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Fila de Requisições                                        │
├────────────────────────────────────────────────────────────┤
│ Status [▼] Prioridade [▼] Vereador [▼] Polo [▼]           │
│ Período [____] [Filtrar]                                   │
├────────────────────────────────────────────────────────────┤
│ Nº | Data | Polo | Vereador | Prioridade | Status | Ações │
│ ...                                                        │
├────────────────────────────────────────────────────────────┤
│ Detalhe da requisição                                      │
│ Parecer [______________________________________________]   │
│ [Aprovar] [Reprovar] [Devolver p/ ajuste]                 │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Tela mestre-detalhe.
- Timeline de eventos da requisição.
- Botões de decisão com confirmação.

### Backend
- `GET /requisicoes-compra/fila`
- `GET /requisicoes-compra/{id}`
- `POST /requisicoes-compra/{id}/aprovar`
- `POST /requisicoes-compra/{id}/reprovar`
- `POST /requisicoes-compra/{id}/devolver`

### Banco
Tabelas:
- `requisicao_compra`
- `item_requisicao`
- `aprovacao_requisicao` ou `historico_requisicao`
- `auditoria`

### Validações
- Parecer obrigatório para reprovação e devolução.
- Só requisições elegíveis podem ser aprovadas.
- Histórico de decisão obrigatório.

### Testes de aceite
- Deve listar requisições por status.
- Deve aprovar requisição e mudar status.
- Deve exigir parecer ao reprovar.
- Deve manter histórico completo da análise.

---

## REV-06 — Execução de Compra
**Prioridade:** P0
**Perfis:** Gestor Institucional, Super Admin

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Execução de Compra                                         │
├────────────────────────────────────────────────────────────┤
│ Requisição* [ buscar aprovadas ______ ]                    │
│ Fornecedor  [ selecione ▼ ] [Cadastro rápido]              │
│ Emenda*     [ selecione ▼ ]                                │
│ Data compra* [__/__/____]                                  │
│ Valor total* [________]                                    │
│ Observação   [________________________________________]    │
├────────────────────────────────────────────────────────────┤
│ Itens comprados                                            │
│ Descrição | Qtde | Vlr unit. | Vlr total                   │
│ ...                                                        │
├────────────────────────────────────────────────────────────┤
│ [Salvar compra] [Cancelar]                                 │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Formulário orientado por requisição aprovada.
- Itens herdados da requisição com ajuste permitido.
- Soma automática dos itens.

### Backend
- `GET /requisicoes-compra/aprovadas`
- `POST /compras`
- Criar movimentação em emenda no mesmo processo transacional.
- Validar saldo disponível.

### Banco
Tabelas:
- `compra`
- `compra_item`
- `fornecedor`
- `emenda`
- `movimentacao_emenda`
- `requisicao_compra`

### Validações
- Requisição obrigatória.
- Emenda obrigatória e compatível com vereador da requisição.
- Saldo suficiente.
- Soma dos itens = valor total.

### Testes de aceite
- Deve executar compra vinculada à requisição.
- Deve bloquear emenda de vereador incompatível.
- Deve bloquear quando saldo for insuficiente.
- Deve gerar movimentação da emenda.

---

## REV-07 — Upload de Nota Fiscal
**Prioridade:** P0
**Perfis:** Gestor Institucional, Super Admin

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Upload de Documento                                        │
├────────────────────────────────────────────────────────────┤
│ Compra*         [selecionada]                              │
│ Tipo documento* [ nota fiscal ▼ ]                          │
│ Número          [____________________]                     │
│ Chave acesso    [____________________]                     │
│ Arquivo*        [Selecionar arquivo]                       │
│ Observação      [______________________________________]   │
├────────────────────────────────────────────────────────────┤
│ [Enviar] [Cancelar]                                        │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Upload com preview básico e validação de extensão/tamanho.
- Lista de documentos já enviados para a compra.

### Backend
- `POST /compras/{id}/documentos`
- Armazenamento em storage.
- Persistência de metadados.

### Banco
Tabelas:
- `nota_fiscal`
- `arquivo_upload`
- `compra`

### Validações
- Compra obrigatória.
- Tipo documento obrigatório.
- Arquivo obrigatório.
- Restringir extensões permitidas.

### Testes de aceite
- Deve anexar documento válido à compra.
- Deve salvar metadados do arquivo.
- Deve permitir visualizar documentos já anexados.

---

## REV-08 — Controle de Emendas
**Prioridade:** P0
**Perfis:** Gestor Institucional, Gestor do Vereador, Super Admin

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Controle de Emendas                                        │
├────────────────────────────────────────────────────────────┤
│ Vereador [▼] Ano [▼] Status [▼] [Filtrar]                 │
├────────────────────────────────────────────────────────────┤
│ Código | Vereador | Total | Utilizado | Saldo | Status    │
│ ...                                                        │
├────────────────────────────────────────────────────────────┤
│ Detalhe de movimentações                                   │
│ Data | Tipo | Valor | Referência | Usuário                │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Tabela principal com detalhe expansível.
- Cores para alertar saldo baixo.

### Backend
- `GET /emendas/controle`
- `GET /emendas/{id}/movimentacoes`

### Banco
Tabelas:
- `emenda`
- `movimentacao_emenda`
- `compra`

### Validações
- Escopo por perfil.
- Saldos calculados no backend para evitar divergência.

### Testes de aceite
- Deve exibir valor total, utilizado e saldo.
- Deve listar movimentações da emenda.
- Deve respeitar escopo do vereador quando aplicável.

---

## REV-09 — Relatório por Vereador
**Prioridade:** P1
**Perfis:** Gestor Institucional, Gestor do Vereador, Super Admin

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Relatório por Vereador                                     │
├────────────────────────────────────────────────────────────┤
│ Vereador* [▼] Competência inicial* [__] final* [__]       │
│ [x] detalhes financeiros  [x] indicadores operacionais     │
│ [Gerar]                                                    │
├────────────────────────────────────────────────────────────┤
│ Prévia                                                     │
├────────────────────────────────────────────────────────────┤
│ [Exportar PDF] [Exportar Excel]                            │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Tela de filtros + preview.
- Exportação PDF/Excel.

### Backend
- `GET /relatorios/vereador`
- Agregações por vereador, polos, beneficiários, compras e saldo.

### Banco
Consultas sobre:
- `vereador`
- `polo`
- `beneficiario_vereador`
- `inscricao`
- `compra`
- `emenda`

### Validações
- Vereador obrigatório.
- Competência inicial e final obrigatórias.
- Intervalo de datas válido.

### Testes de aceite
- Deve consolidar dados do vereador correto.
- Deve permitir exportação.
- Deve respeitar escopo do gestor do vereador.

---

## REV-10 — Relatório por Polo
**Prioridade:** P1
**Perfis:** Gestor Institucional, Gestor de Polo, Gestor do Vereador, Super Admin

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Relatório por Polo                                         │
├────────────────────────────────────────────────────────────┤
│ Polo* [▼] Período* [____ a ____] Modalidade [▼] Turma [▼] │
│ [Gerar]                                                    │
├────────────────────────────────────────────────────────────┤
│ Prévia                                                     │
├────────────────────────────────────────────────────────────┤
│ [Exportar PDF] [Exportar Excel]                            │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Filtros com dependência entre polo, modalidade e turma.
- Preview e exportação.

### Backend
- `GET /relatorios/polo`

### Banco
Consultas sobre:
- `beneficiario_polo`
- `inscricao`
- `frequencia`
- `ocorrencia`
- `encaminhamento`
- `requisicao_compra`

### Validações
- Polo obrigatório.
- Período obrigatório.

### Testes de aceite
- Deve gerar consolidado do polo.
- Deve filtrar por modalidade/turma quando informados.
- Deve exportar corretamente.

---

## REV-11 — Prestação de Contas Mensal
**Prioridade:** P1
**Perfis:** Gestor Institucional, Super Admin

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Prestação de Contas Mensal                                 │
├────────────────────────────────────────────────────────────┤
│ Competência* [mm/aaaa] Vereador* [▼]                      │
│ [x] Incluir notas [x] Resumo operacional [x] Anexos       │
│ [Gerar prestação]                                          │
├────────────────────────────────────────────────────────────┤
│ Prévia do documento                                        │
├────────────────────────────────────────────────────────────┤
│ [Exportar PDF] [Salvar versão]                             │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Foco em geração documental.
- Prévia antes da exportação final.
- Histórico de versões emitidas.

### Backend
- `POST /prestacao-contas/gerar`
- `GET /prestacao-contas/{id}`
- `GET /prestacao-contas/{id}/versoes`

### Banco
Tabelas:
- `prestacao_contas` (recomendada)
- `prestacao_contas_versao` (recomendada)
- consultas em `compra`, `nota_fiscal`, `emenda`, `polo`

### Validações
- Competência obrigatória.
- Vereador obrigatório.
- Registrar versão gerada.

### Testes de aceite
- Deve gerar documento por competência e vereador.
- Deve incluir compras e saldo do período.
- Deve permitir salvar versão histórica.

---

## REV-12 — Usuários, Perfis e Permissões
**Prioridade:** P0
**Perfis:** Super Admin, Gestor Institucional

### Wireframe textual
```text
┌────────────────────────────────────────────────────────────┐
│ Usuários e Permissões                 [Novo Usuário]       │
├────────────────────────────────────────────────────────────┤
│ Nome | Login | Perfil | Escopo | Status | Ações           │
│ ...                                                        │
├────────────────────────────────────────────────────────────┤
│ Formulário                                                  │
│ Nome* / E-mail login* / Telefone                           │
│ Perfil* [▼]                                                 │
│ Vereador escopo [▼]                                         │
│ Polo escopo [multi ▼]                                       │
│ Ativo [toggle]                                              │
│ [Salvar] [Redefinir senha] [Inativar]                       │
└────────────────────────────────────────────────────────────┘
```

### Frontend
- Listagem + formulário lateral.
- Campos condicionados pelo perfil.
- Ação de redefinir senha.

### Backend
- `GET /usuarios`
- `POST /usuarios`
- `PUT /usuarios/{id}`
- `PATCH /usuarios/{id}/status`
- `POST /usuarios/{id}/reset-senha`

### Banco
Tabelas:
- `usuario`
- `perfil`
- `usuario_escopo`
- `auditoria`

### Validações
- Nome obrigatório.
- E-mail/login obrigatório e único.
- Perfil obrigatório.
- Escopo obrigatório conforme perfil.

### Testes de aceite
- Deve criar usuário com perfil e escopo.
- Deve impedir login duplicado.
- Deve restringir menus conforme perfil.
- Deve auditar mudança de perfil.

---

# 5. Backlog técnico consolidado por área

## 5.1 Frontend — backlog macro
### P0
- Fluxo mobile completo de cadastro e sincronização.
- Dashboard do polo.
- Lista e edição de beneficiários.
- Modalidades, turmas, inscrições, frequência.
- Requisição de compra e minhas requisições.
- Dashboard institucional.
- Cadastros de vereadores, emendas, polos.
- Fila de requisições.
- Execução de compra.
- Upload de nota fiscal.
- Controle de emendas.
- Usuários e permissões.

### P1
- Atendimento inicial mobile.
- Ocorrências e encaminhamentos.
- Relatórios por polo e vereador.
- Prestação de contas mensal.

## 5.2 Backend — backlog macro
### P0
- Autenticação JWT + refresh.
- RBAC e escopo por vereador/polo.
- CRUDs principais: usuário, vereador, emenda, polo, beneficiário, modalidade, turma.
- Vínculos beneficiário ↔ vereador e beneficiário ↔ polo.
- Inscrição e frequência em lote.
- Requisição de compra, aprovação e execução de compra.
- Upload de documentos.
- Movimentação de emenda.
- Auditoria mínima.

### P1
- Relatórios consolidados.
- Prestação de contas versionada.
- Histórico detalhado de encaminhamentos/ocorrências.

## 5.3 Banco — backlog macro
### P0
- Modelagem e migrações iniciais.
- Índices de CPF, nome, vínculo por polo, frequência, emenda.
- Constraints de unicidade e integridade.
- Storage metadata para arquivos.

### P1
- Tabelas de versão para prestação de contas.
- Otimizações para relatórios.

## 5.4 Validações — backlog macro
### P0
- CPF único quando informado.
- Beneficiário único por heurística auxiliar.
- Polo compatível com vereador.
- Emenda compatível com vereador da compra.
- Capacidade de turma.
- Frequência única por inscrição/data.
- Requisição com ao menos um item.
- Saldo suficiente em emenda.

### P1
- Alertas proativos de saldo baixo.
- Regras de inconsistência para relatórios.

## 5.5 Testes de aceite — backlog macro
### P0
- Login e controle de acesso.
- Cadastro de beneficiário.
- Vínculos múltiplos.
- Inscrição e frequência.
- Requisição, aprovação e compra.
- Upload de documentos.
- Controle de saldo de emenda.

### P1
- Relatórios e prestação de contas.
- Ocorrências e encaminhamentos.

---

# 6. Ordem recomendada de implementação por sprint

## Sprint 1
- Autenticação
- Usuários/perfis
- Vereadores
- Emendas
- Polos
- Base de beneficiários

## Sprint 2
- Mobile login/home/cadastro/resumo/sync
- Lista e edição de beneficiários no polo
- Modalidades e turmas

## Sprint 3
- Inscrições
- Frequência
- Dashboard do polo
- Requisição de compra

## Sprint 4
- Fila de requisições
- Execução de compra
- Upload de nota fiscal
- Controle de emendas

## Sprint 5
- Ocorrências
- Encaminhamentos
- Relatórios por polo/vereador
- Prestação de contas mensal

---

# 7. Definição de pronto por tela
Para considerar qualquer tela pronta no MVP, ela deve atender simultaneamente:
1. Wireframe implementado com navegação funcional.
2. Backend integrado com API real.
3. Persistência em banco validada.
4. Regras críticas de validação ativas.
5. Testes de aceite executados e aprovados.
6. Auditoria habilitada quando aplicável.
7. Controle de acesso respeitado.

---

# 8. Próximo documento recomendado
A continuação natural deste material é uma de duas opções:
1. transformar cada tela em user stories + subtarefas técnicas para Jira/ClickUp/Trello;
2. transformar isso em dicionário de APIs e contratos de payload para frontend e backend.

