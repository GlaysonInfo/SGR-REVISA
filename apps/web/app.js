const API = "/api/v1";

const state = {
  token: localStorage.getItem("sgr_token"),
  user: null,
  view: "dashboard",
  base: {
    vereadores: [],
    polos: [],
    emendas: [],
    modalidades: [],
    turmas: [],
    beneficiarios: [],
    fornecedores: [],
    usuarios: [],
  },
};

const views = [
  ["dashboard", "Dashboard", "Dashboard Geral"],
  ["mobile", "Mobile", "Captação Mobile"],
  ["beneficiarios", "Beneficiários", "Base de Beneficiários"],
  ["cadastros", "Cadastros", "Vereadores, Emendas e Polos"],
  ["operacao", "Operação", "Operação do Polo"],
  ["compras", "Compras", "Compras e Emendas"],
  ["relatorios", "Relatórios", "Relatórios e Prestação"],
  ["usuarios", "Usuários", "Perfis e Permissões"],
];

const $ = (selector) => document.querySelector(selector);

function money(value) {
  return Number(value || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 4200);
}

function selectedValues(select) {
  return Array.from(select.selectedOptions).map((option) => Number(option.value)).filter(Boolean);
}

function options(items, labelKey = "nome", valueKey = "id") {
  return items.map((item) => `<option value="${item[valueKey]}">${esc(item[labelKey])}</option>`).join("");
}

function table(headers, rows) {
  if (!rows.length) {
    return `<div class="item-card"><p class="muted">Sem registros para exibir.</p></div>`;
  }
  return `
    <div class="table-wrap">
      <table>
        <thead><tr>${headers.map((item) => `<th>${esc(item)}</th>`).join("")}</tr></thead>
        <tbody>${rows.join("")}</tbody>
      </table>
    </div>
  `;
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(`${API}${path}`, { ...options, headers });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = data?.detail;
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join(", ") : detail || "Erro na requisição.");
  }
  return data;
}

function showLogin() {
  $("#login-screen").classList.remove("hidden");
  $("#app-shell").classList.add("hidden");
}

function showApp() {
  $("#login-screen").classList.add("hidden");
  $("#app-shell").classList.remove("hidden");
}

function renderNav() {
  $("#main-nav").innerHTML = views
    .map(([id, label]) => `<button class="${state.view === id ? "active" : ""}" data-view="${id}">${label}</button>`)
    .join("");
  $("#main-nav").querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.view = button.dataset.view;
      render();
    });
  });
}

async function refreshBase() {
  const endpoints = [
    ["vereadores", "/vereadores"],
    ["polos", "/polos"],
    ["emendas", "/emendas"],
    ["modalidades", "/modalidades"],
    ["turmas", "/turmas"],
    ["beneficiarios", "/beneficiarios"],
    ["fornecedores", "/fornecedores"],
    ["usuarios", "/usuarios"],
  ];
  const settled = await Promise.allSettled(endpoints.map(([, path]) => api(path)));
  settled.forEach((result, index) => {
    const key = endpoints[index][0];
    state.base[key] = result.status === "fulfilled" ? result.value : [];
  });
}

async function bootstrap() {
  try {
    state.user = await api("/me");
    await refreshBase();
    showApp();
    render();
  } catch (error) {
    localStorage.removeItem("sgr_token");
    state.token = null;
    showLogin();
  }
}

function metric(label, value, tone = "") {
  return `<article class="metric ${tone}"><span class="muted">${esc(label)}</span><strong>${esc(value)}</strong></article>`;
}

function renderShellTitle() {
  const current = views.find(([id]) => id === state.view) || views[0];
  $("#view-title").textContent = current[2];
  $("#profile-line").textContent = `${state.user?.nome || ""} · ${state.user?.perfil || ""}`;
}

async function render() {
  renderNav();
  renderShellTitle();
  const view = $("#app-view");
  view.innerHTML = `<div class="item-card"><p class="muted">Carregando...</p></div>`;
  try {
    if (state.view === "dashboard") view.innerHTML = await dashboardView();
    if (state.view === "mobile") view.innerHTML = await mobileView();
    if (state.view === "beneficiarios") view.innerHTML = await beneficiariosView();
    if (state.view === "cadastros") view.innerHTML = await cadastrosView();
    if (state.view === "operacao") view.innerHTML = await operacaoView();
    if (state.view === "compras") view.innerHTML = await comprasView();
    if (state.view === "relatorios") view.innerHTML = await relatoriosView();
    if (state.view === "usuarios") view.innerHTML = await usuariosView();
    bindViewEvents();
  } catch (error) {
    view.innerHTML = `<div class="item-card"><p class="error">${esc(error.message)}</p></div>`;
  }
}

async function dashboardView() {
  const data = await api("/dashboard/institucional");
  const reqRows = (data.requisicoes_por_status || []).map(
    (item) => `<tr><td>${esc(item.status)}</td><td>${item.total}</td></tr>`
  );
  return `
    <section class="section">
      <div class="metric-grid">
        ${metric("Beneficiários", data.total_beneficiarios)}
        ${metric("Polos ativos", data.polos_ativos)}
        ${metric("Saldo de emendas", money(data.saldo_emendas))}
        ${metric("Compras executadas", money(data.compras_executadas))}
      </div>
      <div class="grid-2">
        <div class="section">
          <div class="section-head"><h3>Requisições por status</h3></div>
          ${table(["Status", "Total"], reqRows)}
        </div>
        <div class="section">
          <div class="section-head"><h3>Alertas</h3></div>
          ${(data.alertas || []).map((item) => `<article class="item-card"><p>${esc(item)}</p></article>`).join("")}
        </div>
      </div>
    </section>
  `;
}

async function mobileView() {
  const data = await api("/mobile/dashboard");
  const recentes = (data.recentes || []).map(
    (item) => `<tr><td>${esc(item.nome)}</td><td>${esc(item.cpf || "Sem CPF")}</td><td><span class="status good">${esc(item.status_cadastro)}</span></td></tr>`
  );
  return `
    <section class="grid-2">
      <div class="mobile-frame">
        <div class="mobile-top">
          <div>
            <p class="eyebrow">Olá, ${esc(data.usuario)}</p>
            <h3>Novo cadastro</h3>
          </div>
          <span class="pill good">${data.online ? "Online" : "Offline"}</span>
        </div>
        <div class="image-strip"></div>
        <form id="mobile-form" class="stack" style="margin-top:1rem">
          <label>Nome completo* <input name="nome" required /></label>
          <div class="grid-2">
            <label>CPF <input name="cpf" /></label>
            <label>Nascimento <input name="data_nascimento" type="date" /></label>
          </div>
          <div class="grid-2">
            <label>Telefone <input name="telefone" /></label>
            <label>Sexo <select name="sexo"><option>Feminino</option><option>Masculino</option><option>Outro</option></select></label>
          </div>
          <label>Endereço <input name="endereco" /></label>
          <label>Responsável principal <input name="responsavel_nome" /></label>
          <label>Demanda imediata <textarea name="demanda_imediata"></textarea></label>
          <label>Sugestão ou crítica <textarea name="sugestao_descricao"></textarea></label>
          <button class="primary" type="submit">Sincronizar cadastro</button>
        </form>
      </div>
      <div class="section">
        <div class="metric-grid">
          ${metric("Pendentes", data.pendentes_sincronizacao)}
          ${metric("Sincronizados", data.sincronizados_hoje)}
        </div>
        <div class="section">
          <div class="section-head"><h3>Cadastros recentes</h3></div>
          ${table(["Nome", "CPF", "Status"], recentes)}
        </div>
      </div>
    </section>
  `;
}

async function beneficiariosView() {
  await refreshBase();
  const rows = state.base.beneficiarios.map(
    (item) => `
      <tr>
        <td>${esc(item.nome)}</td>
        <td>${esc(item.cpf || "Sem CPF")}</td>
        <td>${esc(item.telefone || "")}</td>
        <td>${esc((item.polos || []).map((polo) => polo.nome).join(", "))}</td>
        <td><span class="status good">${esc(item.status_cadastro)}</span></td>
      </tr>
    `
  );
  return `
    <section class="section">
      <form id="beneficiario-form" class="form-band">
        <h3>Novo beneficiário</h3>
        <div class="grid-3">
          <label>Nome completo* <input name="nome" required /></label>
          <label>CPF <input name="cpf" /></label>
          <label>Nascimento <input name="data_nascimento" type="date" /></label>
        </div>
        <div class="grid-4">
          <label>Telefone <input name="telefone" /></label>
          <label>E-mail <input name="email" type="email" /></label>
          <label>Bairro <input name="bairro" /></label>
          <label>Cidade <input name="cidade" value="Betim" /></label>
        </div>
        <div class="grid-2">
          <label>Vereadores <select name="vereador_ids" multiple>${options(state.base.vereadores)}</select></label>
          <label>Polos <select name="polo_ids" multiple>${options(state.base.polos)}</select></label>
        </div>
        <label>Observações <textarea name="observacoes"></textarea></label>
        <div class="actions"><button class="primary" type="submit">Salvar beneficiário</button></div>
      </form>
      ${table(["Nome", "CPF", "Telefone", "Polos", "Status"], rows)}
    </section>
  `;
}

async function cadastrosView() {
  await refreshBase();
  const vereadorRows = state.base.vereadores.map((item) => `<tr><td>${esc(item.nome)}</td><td>${esc(item.cpf_cnpj || "")}</td><td>${esc(item.status)}</td></tr>`);
  const poloRows = state.base.polos.map((item) => `<tr><td>${esc(item.nome)}</td><td>${esc(item.vereador_nome || "")}</td><td>${esc(item.bairro || "")}</td><td>${esc(item.status)}</td></tr>`);
  const emendaRows = state.base.emendas.map((item) => `<tr><td>${esc(item.codigo)}</td><td>${esc(item.vereador_nome || "")}</td><td>${item.ano}</td><td>${money(item.valor_total)}</td><td>${money(item.valor_disponivel)}</td></tr>`);
  const fornecedorRows = state.base.fornecedores.map((item) => `<tr><td>${esc(item.nome)}</td><td>${esc(item.cpf_cnpj || "")}</td><td>${esc(item.email || "")}</td></tr>`);
  return `
    <section class="section">
      <div class="grid-2">
        <form id="vereador-form" class="form-band">
          <h3>Novo vereador</h3>
          <label>Nome* <input name="nome" required /></label>
          <label>CPF/CNPJ <input name="cpf_cnpj" /></label>
          <button class="primary" type="submit">Salvar vereador</button>
        </form>
        <form id="polo-form" class="form-band">
          <h3>Novo polo</h3>
          <label>Vereador* <select name="vereador_id" required>${options(state.base.vereadores)}</select></label>
          <label>Nome* <input name="nome" required /></label>
          <div class="grid-2">
            <label>Bairro <input name="bairro" /></label>
            <label>Cidade <input name="cidade" value="Betim" /></label>
          </div>
          <label>Responsável local <input name="responsavel_local" /></label>
          <button class="primary" type="submit">Salvar polo</button>
        </form>
      </div>
      <div class="grid-2">
        <form id="emenda-form" class="form-band">
          <h3>Nova emenda</h3>
          <label>Vereador* <select name="vereador_id" required>${options(state.base.vereadores)}</select></label>
          <div class="grid-3">
            <label>Código* <input name="codigo" required /></label>
            <label>Ano* <input name="ano" type="number" value="2026" required /></label>
            <label>Valor total* <input name="valor_total" type="number" step="0.01" required /></label>
          </div>
          <button class="primary" type="submit">Salvar emenda</button>
        </form>
        <form id="fornecedor-form" class="form-band">
          <h3>Novo fornecedor</h3>
          <label>Nome* <input name="nome" required /></label>
          <div class="grid-2">
            <label>CPF/CNPJ <input name="cpf_cnpj" /></label>
            <label>E-mail <input name="email" type="email" /></label>
          </div>
          <button class="primary" type="submit">Salvar fornecedor</button>
        </form>
      </div>
      <div class="grid-2">
        <div class="section"><h3>Vereadores</h3>${table(["Nome", "CPF/CNPJ", "Status"], vereadorRows)}</div>
        <div class="section"><h3>Polos</h3>${table(["Nome", "Vereador", "Bairro", "Status"], poloRows)}</div>
      </div>
      <div class="grid-2">
        <div class="section"><h3>Emendas</h3>${table(["Código", "Vereador", "Ano", "Total", "Disponível"], emendaRows)}</div>
        <div class="section"><h3>Fornecedores</h3>${table(["Nome", "CPF/CNPJ", "E-mail"], fornecedorRows)}</div>
      </div>
    </section>
  `;
}

async function operacaoView() {
  await refreshBase();
  const turmaRows = state.base.turmas.map(
    (item) => `<tr><td>${esc(item.nome)}</td><td>${esc(item.polo_nome || "")}</td><td>${esc(item.modalidade_nome || "")}</td><td>${item.inscritos_ativos}/${item.capacidade}</td><td>${item.ativa ? "Ativa" : "Inativa"}</td></tr>`
  );
  const ocorrencias = await api("/ocorrencias").catch(() => []);
  const encaminhamentos = await api("/encaminhamentos").catch(() => []);
  const ocorrenciaRows = ocorrencias.map((item) => `<tr><td>${esc(item.tipo)}</td><td>${esc(item.descricao)}</td><td>${esc(item.data_ocorrencia)}</td></tr>`);
  const encaminhamentoRows = encaminhamentos.map((item) => `<tr><td>${esc(item.tipo)}</td><td>${esc(item.destino)}</td><td>${esc(item.status)}</td></tr>`);
  return `
    <section class="section">
      <div class="grid-2">
        <form id="turma-form" class="form-band">
          <h3>Nova turma</h3>
          <div class="grid-2">
            <label>Polo* <select name="polo_id" required>${options(state.base.polos)}</select></label>
            <label>Modalidade* <select name="modalidade_id" required>${options(state.base.modalidades)}</select></label>
          </div>
          <div class="grid-3">
            <label>Nome* <input name="nome" required /></label>
            <label>Capacidade <input name="capacidade" type="number" value="20" /></label>
            <label>Dias <input name="dias_semana" placeholder="Segunda e quarta" /></label>
          </div>
          <button class="primary" type="submit">Salvar turma</button>
        </form>
        <form id="inscricao-form" class="form-band">
          <h3>Nova inscrição</h3>
          <label>Beneficiário* <select name="beneficiario_id" required>${options(state.base.beneficiarios)}</select></label>
          <label>Turma* <select name="turma_id" required>${options(state.base.turmas)}</select></label>
          <button class="primary" type="submit">Inscrever</button>
        </form>
      </div>
      <form id="frequencia-loader" class="form-band">
        <h3>Frequência diária</h3>
        <div class="grid-3">
          <label>Turma <select name="turma_id">${options(state.base.turmas)}</select></label>
          <label>Data <input name="data" type="date" value="${today()}" /></label>
          <button class="secondary" type="submit">Carregar lista</button>
        </div>
        <div id="frequencia-area"></div>
      </form>
      <div class="grid-2">
        <form id="ocorrencia-form" class="form-band">
          <h3>Ocorrência</h3>
          <label>Beneficiário <select name="beneficiario_id">${options(state.base.beneficiarios)}</select></label>
          <label>Polo <select name="polo_id">${options(state.base.polos)}</select></label>
          <label>Tipo <input name="tipo" value="Atendimento" /></label>
          <label>Descrição <textarea name="descricao" required></textarea></label>
          <button class="primary" type="submit">Registrar ocorrência</button>
        </form>
        <form id="encaminhamento-form" class="form-band">
          <h3>Encaminhamento</h3>
          <label>Beneficiário <select name="beneficiario_id">${options(state.base.beneficiarios)}</select></label>
          <label>Polo <select name="polo_id">${options(state.base.polos)}</select></label>
          <div class="grid-2">
            <label>Tipo <input name="tipo" value="Serviço social" /></label>
            <label>Destino <input name="destino" value="CRAS" /></label>
          </div>
          <label>Descrição <textarea name="descricao"></textarea></label>
          <button class="primary" type="submit">Registrar encaminhamento</button>
        </form>
      </div>
      <div class="section"><h3>Turmas</h3>${table(["Nome", "Polo", "Modalidade", "Inscritos", "Status"], turmaRows)}</div>
      <div class="grid-2">
        <div class="section"><h3>Ocorrências</h3>${table(["Tipo", "Descrição", "Data"], ocorrenciaRows)}</div>
        <div class="section"><h3>Encaminhamentos</h3>${table(["Tipo", "Destino", "Status"], encaminhamentoRows)}</div>
      </div>
    </section>
  `;
}

async function comprasView() {
  await refreshBase();
  const requisicoes = await api("/requisicoes-compra").catch(() => []);
  const aprovadas = await api("/requisicoes-compra/aprovadas").catch(() => []);
  const compras = await api("/compras").catch(() => []);
  const reqRows = requisicoes.map(
    (item) => `
      <tr>
        <td>${esc(item.descricao)}</td>
        <td>${esc(item.polo_nome || "")}</td>
        <td><span class="status ${item.status === "APROVADA" ? "good" : item.status === "REPROVADA" ? "bad" : "warn"}">${esc(item.status)}</span></td>
        <td>${money(item.total_estimado)}</td>
        <td>
          <div class="actions">
            <button class="ghost req-action" data-id="${item.id}" data-action="enviar">Enviar</button>
            <button class="secondary req-action" data-id="${item.id}" data-action="aprovar">Aprovar</button>
            <button class="danger req-action" data-id="${item.id}" data-action="reprovar">Reprovar</button>
          </div>
        </td>
      </tr>
    `
  );
  const compraRows = compras.map((item) => `<tr><td>${item.id}</td><td>${esc(item.fornecedor_nome || "")}</td><td>${esc(item.emenda_codigo || "")}</td><td>${money(item.valor_total)}</td><td>${esc(item.status)}</td></tr>`);
  return `
    <section class="section">
      <div class="grid-2">
        <form id="requisicao-form" class="form-band">
          <h3>Nova requisição</h3>
          <label>Polo* <select name="polo_id" required>${options(state.base.polos)}</select></label>
          <label>Descrição* <textarea name="descricao" required></textarea></label>
          <div class="grid-2">
            <label>Prioridade <select name="prioridade"><option>NORMAL</option><option>ALTA</option><option>URGENTE</option></select></label>
            <label>Status <select name="status"><option>ABERTA</option><option>RASCUNHO</option></select></label>
          </div>
          <h3>Item</h3>
          <div class="grid-4">
            <label>Descrição* <input name="item_descricao" required /></label>
            <label>Quantidade* <input name="item_quantidade" type="number" value="1" step="0.01" required /></label>
            <label>Unidade <input name="item_unidade" value="un" /></label>
            <label>Valor estimado <input name="item_valor" type="number" value="0" step="0.01" /></label>
          </div>
          <button class="primary" type="submit">Abrir requisição</button>
        </form>
        <form id="compra-form" class="form-band">
          <h3>Execução de compra</h3>
          <label>Requisição aprovada <select name="requisicao_id">${options(aprovadas, "descricao")}</select></label>
          <label>Fornecedor <select name="fornecedor_id">${options(state.base.fornecedores)}</select></label>
          <label>Emenda <select name="emenda_id">${state.base.emendas.map((item) => `<option value="${item.id}">${esc(item.codigo)} · ${money(item.valor_disponivel)}</option>`).join("")}</select></label>
          <label>Valor total <input name="valor_total" type="number" step="0.01" required /></label>
          <button class="primary" type="submit">Executar compra</button>
        </form>
      </div>
      <form id="nota-form" class="form-band">
        <h3>Upload de nota fiscal</h3>
        <div class="grid-4">
          <label>Compra <select name="compra_id">${compras.map((item) => `<option value="${item.id}">Compra #${item.id} · ${money(item.valor_total)}</option>`).join("")}</select></label>
          <label>Número <input name="numero" required /></label>
          <label>Chave de acesso <input name="chave_acesso" /></label>
          <label>Nome do arquivo <input name="nome_arquivo" placeholder="nota.pdf" /></label>
        </div>
        <button class="secondary" type="submit">Registrar documento</button>
      </form>
      <div class="section"><h3>Requisições</h3>${table(["Descrição", "Polo", "Status", "Estimado", "Ações"], reqRows)}</div>
      <div class="section"><h3>Compras executadas</h3>${table(["ID", "Fornecedor", "Emenda", "Valor", "Status"], compraRows)}</div>
    </section>
  `;
}

async function relatoriosView() {
  const geral = await api("/dashboard/institucional");
  const relPolo = await api("/relatorios/polo").catch(() => ({}));
  const relVereador = await api("/relatorios/vereador").catch(() => ({}));
  const emendas = await api("/emendas/controle").catch(() => []);
  const auditoria = await api("/auditoria").catch(() => []);
  const emendaRows = emendas.map((item) => `<tr><td>${esc(item.codigo)}</td><td>${esc(item.vereador_nome)}</td><td>${money(item.valor_total)}</td><td>${money(item.valor_utilizado)}</td><td>${money(item.valor_disponivel)}</td></tr>`);
  const auditRows = auditoria.slice(0, 20).map((item) => `<tr><td>${esc(item.data_evento)}</td><td>${esc(item.entidade)}</td><td>${esc(item.acao)}</td><td>${esc(item.entidade_id || "")}</td></tr>`);
  return `
    <section class="section">
      <div class="metric-grid">
        ${metric("Beneficiários", geral.total_beneficiarios)}
        ${metric("Frequência polo", `${relPolo.frequencia_percentual || 0}%`)}
        ${metric("Saldo disponível", money(relVereador.saldo_emendas || geral.saldo_emendas))}
        ${metric("Requisições", relVereador.requisicoes || 0)}
      </div>
      <form id="prestacao-form" class="form-band">
        <h3>Prestação de contas mensal</h3>
        <div class="grid-3">
          <label>Competência <input name="competencia" type="month" required /></label>
          <label>Vereador <select name="vereador_id">${options(state.base.vereadores)}</select></label>
          <button class="primary" type="submit">Gerar resumo</button>
        </div>
        <pre id="prestacao-output" class="item-card muted"></pre>
      </form>
      <div class="section"><h3>Controle de emendas</h3>${table(["Código", "Vereador", "Total", "Utilizado", "Disponível"], emendaRows)}</div>
      <div class="section"><h3>Auditoria</h3>${table(["Data", "Entidade", "Ação", "Registro"], auditRows)}</div>
    </section>
  `;
}

async function usuariosView() {
  await refreshBase();
  const rows = state.base.usuarios.map((item) => `<tr><td>${esc(item.nome)}</td><td>${esc(item.email_login)}</td><td>${esc(item.perfil)}</td><td>${item.ativo ? "Ativo" : "Inativo"}</td></tr>`);
  return `
    <section class="section">
      <form id="usuario-form" class="form-band">
        <h3>Novo usuário</h3>
        <div class="grid-3">
          <label>Nome* <input name="nome" required /></label>
          <label>Login* <input name="email_login" type="email" required /></label>
          <label>Senha* <input name="senha" type="password" value="revisa123" required /></label>
        </div>
        <div class="grid-3">
          <label>Perfil
            <select name="perfil">
              <option>Super Admin</option>
              <option>Gestor Institucional REVISA</option>
              <option>Gestor do Vereador</option>
              <option>Gestor de Polo</option>
              <option>Operador de Polo</option>
              <option>Captador Mobile</option>
            </select>
          </label>
          <label>Vereador <select name="vereador_id"><option value="">Sem escopo</option>${options(state.base.vereadores)}</select></label>
          <label>Polo <select name="polo_id"><option value="">Sem escopo</option>${options(state.base.polos)}</select></label>
        </div>
        <button class="primary" type="submit">Salvar usuário</button>
      </form>
      ${table(["Nome", "Login", "Perfil", "Status"], rows)}
    </section>
  `;
}

function formData(form) {
  return Object.fromEntries(new FormData(form).entries());
}

async function submitJson(form, path, payloadFactory, successMessage) {
  const button = form.querySelector("button[type='submit']");
  button.disabled = true;
  try {
    await api(path, { method: "POST", body: JSON.stringify(payloadFactory(formData(form), form)) });
    showToast(successMessage);
    await refreshBase();
    await render();
  } catch (error) {
    showToast(error.message);
  } finally {
    button.disabled = false;
  }
}

function bindViewEvents() {
  const mobileForm = $("#mobile-form");
  if (mobileForm) {
    mobileForm.addEventListener("submit", (event) => {
      event.preventDefault();
      submitJson(
        mobileForm,
        "/mobile/beneficiarios",
        (data) => ({
          beneficiario: {
            nome: data.nome,
            cpf: data.cpf || null,
            data_nascimento: data.data_nascimento || null,
            sexo: data.sexo,
            telefone: data.telefone || null,
            endereco: data.endereco || null,
          },
          responsavel: data.responsavel_nome ? { nome: data.responsavel_nome } : null,
          demanda_imediata: data.demanda_imediata || null,
          sugestao_tipo: data.sugestao_descricao ? "SUGESTAO" : null,
          sugestao_descricao: data.sugestao_descricao || null,
        }),
        "Cadastro sincronizado."
      );
    });
  }

  const beneficiarioForm = $("#beneficiario-form");
  if (beneficiarioForm) {
    beneficiarioForm.addEventListener("submit", (event) => {
      event.preventDefault();
      submitJson(
        beneficiarioForm,
        "/beneficiarios",
        (data, form) => ({
          nome: data.nome,
          cpf: data.cpf || null,
          data_nascimento: data.data_nascimento || null,
          telefone: data.telefone || null,
          email: data.email || null,
          bairro: data.bairro || null,
          cidade: data.cidade || null,
          observacoes: data.observacoes || null,
          vereador_ids: selectedValues(form.elements.vereador_ids),
          polo_ids: selectedValues(form.elements.polo_ids),
        }),
        "Beneficiário salvo."
      );
    });
  }

  const vereadorForm = $("#vereador-form");
  if (vereadorForm) {
    vereadorForm.addEventListener("submit", (event) => {
      event.preventDefault();
      submitJson(vereadorForm, "/vereadores", (data) => ({ nome: data.nome, cpf_cnpj: data.cpf_cnpj || null }), "Vereador salvo.");
    });
  }

  const poloForm = $("#polo-form");
  if (poloForm) {
    poloForm.addEventListener("submit", (event) => {
      event.preventDefault();
      submitJson(
        poloForm,
        "/polos",
        (data) => ({
          vereador_id: Number(data.vereador_id),
          nome: data.nome,
          bairro: data.bairro || null,
          cidade: data.cidade || null,
          responsavel_local: data.responsavel_local || null,
        }),
        "Polo salvo."
      );
    });
  }

  const emendaForm = $("#emenda-form");
  if (emendaForm) {
    emendaForm.addEventListener("submit", (event) => {
      event.preventDefault();
      submitJson(
        emendaForm,
        "/emendas",
        (data) => ({ vereador_id: Number(data.vereador_id), codigo: data.codigo, ano: Number(data.ano), valor_total: Number(data.valor_total) }),
        "Emenda salva."
      );
    });
  }

  const fornecedorForm = $("#fornecedor-form");
  if (fornecedorForm) {
    fornecedorForm.addEventListener("submit", (event) => {
      event.preventDefault();
      submitJson(
        fornecedorForm,
        "/fornecedores",
        (data) => ({ nome: data.nome, cpf_cnpj: data.cpf_cnpj || null, email: data.email || null }),
        "Fornecedor salvo."
      );
    });
  }

  const turmaForm = $("#turma-form");
  if (turmaForm) {
    turmaForm.addEventListener("submit", (event) => {
      event.preventDefault();
      submitJson(
        turmaForm,
        "/turmas",
        (data) => ({
          polo_id: Number(data.polo_id),
          modalidade_id: Number(data.modalidade_id),
          nome: data.nome,
          capacidade: Number(data.capacidade || 20),
          dias_semana: data.dias_semana || null,
        }),
        "Turma salva."
      );
    });
  }

  const inscricaoForm = $("#inscricao-form");
  if (inscricaoForm) {
    inscricaoForm.addEventListener("submit", (event) => {
      event.preventDefault();
      submitJson(
        inscricaoForm,
        "/inscricoes",
        (data) => ({ beneficiario_id: Number(data.beneficiario_id), turma_id: Number(data.turma_id) }),
        "Inscrição registrada."
      );
    });
  }

  const frequenciaLoader = $("#frequencia-loader");
  if (frequenciaLoader) {
    frequenciaLoader.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = formData(frequenciaLoader);
      try {
        const carga = await api(`/frequencia/carga?turma_id=${data.turma_id}&data=${data.data}`);
        $("#frequencia-area").innerHTML = `
          <div class="table-wrap" style="margin-top:1rem">
            <table>
              <thead><tr><th>Beneficiário</th><th>Presente</th><th>Observação</th></tr></thead>
              <tbody>
                ${carga.registros
                  .map(
                    (item) => `
                      <tr>
                        <td>${esc(item.beneficiario_nome)}</td>
                        <td><input type="checkbox" data-inscricao="${item.inscricao_id}" ${item.presente ? "checked" : ""} /></td>
                        <td><input data-observacao="${item.inscricao_id}" value="${esc(item.observacao || "")}" /></td>
                      </tr>
                    `
                  )
                  .join("")}
              </tbody>
            </table>
          </div>
          <div class="actions" style="margin-top:0.8rem"><button type="button" id="save-frequencia" class="primary">Salvar frequência</button></div>
        `;
        $("#save-frequencia").addEventListener("click", async () => {
          const registros = Array.from($("#frequencia-area").querySelectorAll("[data-inscricao]")).map((checkbox) => ({
            inscricao_id: Number(checkbox.dataset.inscricao),
            presente: checkbox.checked,
            observacao: $(`[data-observacao="${checkbox.dataset.inscricao}"]`).value || null,
          }));
          await api("/frequencia/lote", {
            method: "POST",
            body: JSON.stringify({ turma_id: Number(data.turma_id), data_atividade: data.data, registros }),
          });
          showToast("Frequência salva.");
        });
      } catch (error) {
        showToast(error.message);
      }
    });
  }

  const ocorrenciaForm = $("#ocorrencia-form");
  if (ocorrenciaForm) {
    ocorrenciaForm.addEventListener("submit", (event) => {
      event.preventDefault();
      submitJson(
        ocorrenciaForm,
        "/ocorrencias",
        (data) => ({ beneficiario_id: Number(data.beneficiario_id), polo_id: Number(data.polo_id), tipo: data.tipo, descricao: data.descricao }),
        "Ocorrência registrada."
      );
    });
  }

  const encaminhamentoForm = $("#encaminhamento-form");
  if (encaminhamentoForm) {
    encaminhamentoForm.addEventListener("submit", (event) => {
      event.preventDefault();
      submitJson(
        encaminhamentoForm,
        "/encaminhamentos",
        (data) => ({ beneficiario_id: Number(data.beneficiario_id), polo_id: Number(data.polo_id), tipo: data.tipo, destino: data.destino, descricao: data.descricao || null }),
        "Encaminhamento registrado."
      );
    });
  }

  const requisicaoForm = $("#requisicao-form");
  if (requisicaoForm) {
    requisicaoForm.addEventListener("submit", (event) => {
      event.preventDefault();
      submitJson(
        requisicaoForm,
        "/requisicoes-compra",
        (data) => ({
          polo_id: Number(data.polo_id),
          descricao: data.descricao,
          prioridade: data.prioridade,
          status: data.status,
          itens: [{ descricao: data.item_descricao, quantidade: Number(data.item_quantidade), unidade: data.item_unidade, valor_estimado: Number(data.item_valor || 0) }],
        }),
        "Requisição aberta."
      );
    });
  }

  document.querySelectorAll(".req-action").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await api(`/requisicoes-compra/${button.dataset.id}/${button.dataset.action}`, { method: "POST", body: "{}" });
        showToast("Status atualizado.");
        await render();
      } catch (error) {
        showToast(error.message);
      }
    });
  });

  const compraForm = $("#compra-form");
  if (compraForm) {
    compraForm.addEventListener("submit", (event) => {
      event.preventDefault();
      submitJson(
        compraForm,
        "/compras",
        (data) => ({ requisicao_id: Number(data.requisicao_id), fornecedor_id: Number(data.fornecedor_id), emenda_id: Number(data.emenda_id), valor_total: Number(data.valor_total) }),
        "Compra executada."
      );
    });
  }

  const notaForm = $("#nota-form");
  if (notaForm) {
    notaForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = formData(notaForm);
      try {
        await api(`/compras/${data.compra_id}/documentos`, {
          method: "POST",
          body: JSON.stringify({ numero: data.numero, chave_acesso: data.chave_acesso || null, nome_arquivo: data.nome_arquivo || null }),
        });
        showToast("Documento registrado.");
        await render();
      } catch (error) {
        showToast(error.message);
      }
    });
  }

  const prestacaoForm = $("#prestacao-form");
  if (prestacaoForm) {
    prestacaoForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = formData(prestacaoForm);
      try {
        const result = await api(`/prestacao-contas/gerar?competencia=${encodeURIComponent(data.competencia)}&vereador_id=${data.vereador_id}`, {
          method: "POST",
          body: "{}",
        });
        $("#prestacao-output").textContent = JSON.stringify(result, null, 2);
      } catch (error) {
        showToast(error.message);
      }
    });
  }

  const usuarioForm = $("#usuario-form");
  if (usuarioForm) {
    usuarioForm.addEventListener("submit", (event) => {
      event.preventDefault();
      submitJson(
        usuarioForm,
        "/usuarios",
        (data) => ({
          nome: data.nome,
          email_login: data.email_login,
          senha: data.senha,
          perfil: data.perfil,
          vereador_id: data.vereador_id ? Number(data.vereador_id) : null,
          polo_id: data.polo_id ? Number(data.polo_id) : null,
        }),
        "Usuário salvo."
      );
    });
  }
}

$("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("#login-error").textContent = "";
  const data = formData(event.currentTarget);
  try {
    const result = await api("/auth/login", { method: "POST", body: JSON.stringify(data) });
    state.token = result.access_token;
    localStorage.setItem("sgr_token", state.token);
    await bootstrap();
  } catch (error) {
    $("#login-error").textContent = error.message;
  }
});

$("#logout-button").addEventListener("click", () => {
  localStorage.removeItem("sgr_token");
  state.token = null;
  state.user = null;
  showLogin();
});

window.addEventListener("online", () => {
  $("#connection-pill").textContent = "Online";
  $("#connection-pill").className = "pill good";
});

window.addEventListener("offline", () => {
  $("#connection-pill").textContent = "Offline";
  $("#connection-pill").className = "pill bad";
});

bootstrap();
