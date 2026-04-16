const API = "/api/v1";

const state = {
  token: localStorage.getItem("sgr_token"),
  user: null,
  view: "dashboard",
  cadastros: {
    section: "vereadores",
    editing: { entity: null, id: null },
  },
  management: {
    beneficiarios: { id: null },
    usuarios: { id: null },
  },
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
  ["cadastros", "Cadastros", "Cadastros Estruturais"],
  ["operacao", "Operação", "Operação do Polo"],
  ["compras", "Compras", "Compras e Emendas"],
  ["relatorios", "Relatórios", "Relatórios e Prestação"],
  ["usuarios", "Usuários", "Perfis e Permissões"],
];

const cadastroSections = [
  ["vereadores", "Vereadores", "Representantes e escopos políticos."],
  ["polos", "Polos", "Unidades, responsáveis locais e território."],
  ["emendas", "Emendas", "Controle financeiro por vereador."],
  ["fornecedores", "Fornecedores", "Base de parceiros e compras."],
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

function getCadastrosState() {
  return state.cadastros;
}

function setCadastroSection(section) {
  const cadastros = getCadastrosState();
  cadastros.section = section;
  if (cadastros.editing.entity !== section) {
    cadastros.editing = { entity: null, id: null };
  }
}

function setCadastroEditing(entity, id) {
  const cadastros = getCadastrosState();
  cadastros.section = entity;
  cadastros.editing = { entity, id: Number(id) };
}

function clearCadastroEditing(entity = null) {
  const cadastros = getCadastrosState();
  if (!entity || cadastros.editing.entity === entity) {
    cadastros.editing = { entity: null, id: null };
  }
}

function activeCadastroEditing(entity) {
  const cadastros = getCadastrosState();
  return cadastros.editing.entity === entity ? Number(cadastros.editing.id) : null;
}

function findCadastroItem(entity, id) {
  return (state.base[entity] || []).find((item) => item.id === Number(id)) || null;
}

function optionsSelected(items, selectedValue, labelKey = "nome", valueKey = "id") {
  const selectedValues = Array.isArray(selectedValue) ? selectedValue.map((item) => String(item)) : [String(selectedValue ?? "")];
  return items
    .map((item) => {
      const selected = selectedValues.includes(String(item[valueKey])) ? " selected" : "";
      return `<option value="${item[valueKey]}"${selected}>${esc(item[labelKey])}</option>`;
    })
    .join("");
}

function setManagementEditing(entity, id) {
  state.management[entity] = { id: Number(id) };
}

function clearManagementEditing(entity) {
  state.management[entity] = { id: null };
}

function activeManagementEditing(entity) {
  return Number(state.management[entity]?.id || 0) || null;
}

function entityLabel(entity) {
  if (entity === "usuarios") return "Usuário";
  if (entity === "beneficiarios") return "Beneficiário";
  if (entity === "emendas") return "Emenda";
  if (entity === "polos") return "Polo";
  if (entity === "fornecedores") return "Fornecedor";
  return "Vereador";
}

function cadastroStatus(entity, item) {
  if (entity === "fornecedores") {
    return item.ativo ? "ATIVO" : "ARQUIVADO";
  }
  return item.status || "ATIVO";
}

function statusTone(status) {
  const normalized = String(status || "").toUpperCase();
  if (normalized.includes("ARQUIV") || normalized.includes("INATIV") || normalized.includes("REPROV")) return "bad";
  if (normalized.includes("ATIV") || normalized.includes("APROV") || normalized.includes("ONLINE")) return "good";
  return "warn";
}

function statusBadge(status) {
  return `<span class="status ${statusTone(status)}">${esc(status)}</span>`;
}

function iconSvg(name) {
  const icons = {
    edit: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 17.25V20h2.75L17.8 8.94l-2.75-2.75L4 17.25zm14.71-9.04a1.003 1.003 0 0 0 0-1.42l-1.5-1.5a1.003 1.003 0 0 0-1.42 0l-1.17 1.17 2.75 2.75 1.34-1.25z"></path></svg>',
    archive: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.54 5.23 19.15 3.55A1.99 1.99 0 0 0 17.61 3H6.39c-.59 0-1.15.26-1.54.71L3.46 5.23A2 2 0 0 0 3 6.53V19a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6.53c0-.47-.17-.92-.46-1.3ZM6.24 5h11.52l.81 1H5.43l.81-1ZM12 17l-4-4h2.5v-3h3v3H16l-4 4Z"></path></svg>',
    delete: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 7h12l-1 14H7L6 7Zm3-3h6l1 2h4v2H4V6h4l1-2Z"></path></svg>',
  };
  return icons[name] || "";
}

function actionIconButton(action, entity, id, title, tone = "", disabled = false) {
  const disabledAttr = disabled ? " disabled" : "";
  const toneClass = tone ? ` ${tone}` : "";
  return `
    <button
      type="button"
      class="icon-button cadastro-action${toneClass}"
      data-action="${action}"
      data-entity="${entity}"
      data-id="${id}"
      title="${esc(title)}"
      aria-label="${esc(title)}"
      ${disabledAttr}
    >
      ${iconSvg(action)}
    </button>
  `;
}

function cadastroActionButtons(entity, item) {
  const status = cadastroStatus(entity, item).toUpperCase();
  const archived = status.includes("ARQUIV") || status.includes("INATIV");
  return `
    <div class="table-actions">
      ${actionIconButton("edit", entity, item.id, "Editar registro")}
      ${actionIconButton("archive", entity, item.id, archived ? "Registro já arquivado" : "Arquivar registro", "warn", archived)}
      ${actionIconButton("delete", entity, item.id, "Excluir registro", "danger")}
    </div>
  `;
}

function cadastroPath(entity, id = null, suffix = "") {
  const base = `/${entity}`;
  return `${base}${id ? `/${id}` : ""}${suffix}`;
}

function cadastroArchiveStatus(entity) {
  if (entity === "emendas") return "ARQUIVADA";
  if (entity === "fornecedores") return "INATIVO";
  return "ARQUIVADO";
}

function cadastroPayload(entity, data) {
  if (entity === "vereadores") {
    return { nome: data.nome, cpf_cnpj: data.cpf_cnpj || null, status: data.status };
  }
  if (entity === "polos") {
    return {
      vereador_id: Number(data.vereador_id),
      nome: data.nome,
      endereco: data.endereco || null,
      bairro: data.bairro || null,
      cidade: data.cidade || null,
      responsavel_local: data.responsavel_local || null,
      status: data.status,
    };
  }
  if (entity === "emendas") {
    return {
      vereador_id: Number(data.vereador_id),
      codigo: data.codigo,
      ano: Number(data.ano),
      valor_total: Number(data.valor_total),
      status: data.status,
    };
  }
  return {
    nome: data.nome,
    cpf_cnpj: data.cpf_cnpj || null,
    telefone: data.telefone || null,
    email: data.email || null,
    ativo: data.status === "ATIVO",
  };
}

async function submitCadastroForm(entity, form) {
  const data = formData(form);
  const id = Number(data.id || 0) || null;
  const method = id ? "PUT" : "POST";
  const path = id ? cadastroPath(entity, id) : cadastroPath(entity);
  try {
    await api(path, { method, body: JSON.stringify(cadastroPayload(entity, data)) });
    clearCadastroEditing(entity);
    showToast(`${entity === "emendas" ? "Emenda" : entity === "polos" ? "Polo" : entity === "fornecedores" ? "Fornecedor" : "Vereador"} ${id ? "atualizado" : "salvo"}.`);
    await refreshBase();
    await render();
  } catch (error) {
    showToast(error.message);
  }
}

async function handleCadastroAction(entity, action, id) {
  const item = findCadastroItem(entity, id);
  if (!item) return;
  if (action === "edit") {
    setCadastroEditing(entity, id);
    await render();
    return;
  }
  if (action === "archive") {
    const confirmed = window.confirm("Arquivar este registro? Ele continuará visível, mas ficará fora do fluxo ativo.");
    if (!confirmed) return;
    try {
      await api(cadastroPath(entity, id, "/status"), { method: "PATCH", body: JSON.stringify({ status: cadastroArchiveStatus(entity) }) });
      clearCadastroEditing(entity);
      showToast("Registro arquivado.");
      await refreshBase();
      await render();
    } catch (error) {
      showToast(error.message);
    }
    return;
  }
  if (action === "delete") {
    const confirmed = window.confirm("Excluir este registro? Esta ação não pode ser desfeita.");
    if (!confirmed) return;
    try {
      await api(cadastroPath(entity, id), { method: "DELETE" });
      clearCadastroEditing(entity);
      showToast("Registro excluído.");
      await refreshBase();
      await render();
    } catch (error) {
      showToast(error.message);
    }
  }
}

function renderCadastroTabs(activeSection) {
  return `
    <div class="cadastro-switcher">
      ${cadastroSections
        .map(
          ([id, label]) => `
            <button type="button" class="cadastro-switch ${activeSection === id ? "active" : ""}" data-section="${id}">
              <span>${label}</span>
              <small>${(state.base[id] || []).length}</small>
            </button>
          `
        )
        .join("")}
    </div>
  `;
}

function renderVereadoresPanel() {
  const editing = findCadastroItem("vereadores", activeCadastroEditing("vereadores"));
  const rows = state.base.vereadores.map(
    (item) => `
      <tr>
        <td>${esc(item.nome)}</td>
        <td>${esc(item.cpf_cnpj || "")}</td>
        <td>${statusBadge(cadastroStatus("vereadores", item))}</td>
        <td>${cadastroActionButtons("vereadores", item)}</td>
      </tr>
    `
  );
  return `
    <div class="cadastro-layout">
      <form id="vereador-form" class="form-band cadastro-form">
        <input type="hidden" name="id" value="${editing?.id || ""}" />
        <div class="section-head">
          <div>
            <p class="eyebrow">Cadastro</p>
            <h3>${editing ? "Editar vereador" : "Novo vereador"}</h3>
          </div>
          <span class="pill ${editing ? "warn" : "good"}">${editing ? "Edição" : "Novo"}</span>
        </div>
        <label>Nome* <input name="nome" value="${esc(editing?.nome || "")}" required /></label>
        <label>CPF/CNPJ <input name="cpf_cnpj" value="${esc(editing?.cpf_cnpj || "")}" /></label>
        <label>Status
          <select name="status">
            <option value="ATIVO"${editing?.status === "ATIVO" || !editing ? " selected" : ""}>Ativo</option>
            <option value="ARQUIVADO"${editing?.status === "ARQUIVADO" ? " selected" : ""}>Arquivado</option>
          </select>
        </label>
        <div class="actions">
          <button class="primary" type="submit">${editing ? "Atualizar vereador" : "Salvar vereador"}</button>
          ${editing ? '<button type="button" class="ghost cadastro-cancel" data-entity="vereadores">Cancelar</button>' : ""}
        </div>
      </form>
      <div class="section cadastro-list-panel">
        <div class="section-head">
          <div>
            <p class="eyebrow">Listagem</p>
            <h3>Vereadores cadastrados</h3>
          </div>
          <span class="muted">Ações rápidas por registro</span>
        </div>
        ${table(["Nome", "CPF/CNPJ", "Status", "Ações"], rows)}
      </div>
    </div>
  `;
}

function renderPolosPanel() {
  const editing = findCadastroItem("polos", activeCadastroEditing("polos"));
  const rows = state.base.polos.map(
    (item) => `
      <tr>
        <td>${esc(item.nome)}</td>
        <td>${esc(item.vereador_nome || "")}</td>
        <td>${esc(item.bairro || "")}</td>
        <td>${statusBadge(cadastroStatus("polos", item))}</td>
        <td>${cadastroActionButtons("polos", item)}</td>
      </tr>
    `
  );
  return `
    <div class="cadastro-layout">
      <form id="polo-form" class="form-band cadastro-form">
        <input type="hidden" name="id" value="${editing?.id || ""}" />
        <div class="section-head">
          <div>
            <p class="eyebrow">Cadastro</p>
            <h3>${editing ? "Editar polo" : "Novo polo"}</h3>
          </div>
          <span class="pill ${editing ? "warn" : "good"}">${editing ? "Edição" : "Novo"}</span>
        </div>
        <label>Vereador* <select name="vereador_id" required>${optionsSelected(state.base.vereadores, editing?.vereador_id)}</select></label>
        <label>Nome* <input name="nome" value="${esc(editing?.nome || "")}" required /></label>
        <label>Endereço <input name="endereco" value="${esc(editing?.endereco || "")}" /></label>
        <div class="grid-2">
          <label>Bairro <input name="bairro" value="${esc(editing?.bairro || "")}" /></label>
          <label>Cidade <input name="cidade" value="${esc(editing?.cidade || "Betim")}" /></label>
        </div>
        <label>Responsável local <input name="responsavel_local" value="${esc(editing?.responsavel_local || "")}" /></label>
        <label>Status
          <select name="status">
            <option value="ATIVO"${editing?.status === "ATIVO" || !editing ? " selected" : ""}>Ativo</option>
            <option value="ARQUIVADO"${editing?.status === "ARQUIVADO" ? " selected" : ""}>Arquivado</option>
          </select>
        </label>
        <div class="actions">
          <button class="primary" type="submit">${editing ? "Atualizar polo" : "Salvar polo"}</button>
          ${editing ? '<button type="button" class="ghost cadastro-cancel" data-entity="polos">Cancelar</button>' : ""}
        </div>
      </form>
      <div class="section cadastro-list-panel">
        <div class="section-head">
          <div>
            <p class="eyebrow">Listagem</p>
            <h3>Polos cadastrados</h3>
          </div>
          <span class="muted">Separados do restante para leitura mais clara</span>
        </div>
        ${table(["Nome", "Vereador", "Bairro", "Status", "Ações"], rows)}
      </div>
    </div>
  `;
}

function renderEmendasPanel() {
  const editing = findCadastroItem("emendas", activeCadastroEditing("emendas"));
  const rows = state.base.emendas.map(
    (item) => `
      <tr>
        <td>${esc(item.codigo)}</td>
        <td>${esc(item.vereador_nome || "")}</td>
        <td>${item.ano}</td>
        <td>${money(item.valor_total)}</td>
        <td>${money(item.valor_disponivel)}</td>
        <td>${statusBadge(cadastroStatus("emendas", item))}</td>
        <td>${cadastroActionButtons("emendas", item)}</td>
      </tr>
    `
  );
  return `
    <div class="cadastro-layout">
      <form id="emenda-form" class="form-band cadastro-form">
        <input type="hidden" name="id" value="${editing?.id || ""}" />
        <div class="section-head">
          <div>
            <p class="eyebrow">Cadastro</p>
            <h3>${editing ? "Editar emenda" : "Nova emenda"}</h3>
          </div>
          <span class="pill ${editing ? "warn" : "good"}">${editing ? "Edição" : "Novo"}</span>
        </div>
        <label>Vereador* <select name="vereador_id" required>${optionsSelected(state.base.vereadores, editing?.vereador_id)}</select></label>
        <div class="grid-2">
          <label>Código* <input name="codigo" value="${esc(editing?.codigo || "")}" required /></label>
          <label>Ano* <input name="ano" type="number" value="${esc(editing?.ano || 2026)}" required /></label>
        </div>
        <label>Valor total* <input name="valor_total" type="number" step="0.01" value="${esc(editing?.valor_total || "")}" required /></label>
        <label>Status
          <select name="status">
            <option value="ATIVA"${editing?.status === "ATIVA" || !editing ? " selected" : ""}>Ativa</option>
            <option value="ARQUIVADA"${editing?.status === "ARQUIVADA" ? " selected" : ""}>Arquivada</option>
          </select>
        </label>
        <div class="actions">
          <button class="primary" type="submit">${editing ? "Atualizar emenda" : "Salvar emenda"}</button>
          ${editing ? '<button type="button" class="ghost cadastro-cancel" data-entity="emendas">Cancelar</button>' : ""}
        </div>
      </form>
      <div class="section cadastro-list-panel">
        <div class="section-head">
          <div>
            <p class="eyebrow">Listagem</p>
            <h3>Emendas cadastradas</h3>
          </div>
          <span class="muted">Valor total, saldo e ações no mesmo contexto</span>
        </div>
        ${table(["Código", "Vereador", "Ano", "Total", "Disponível", "Status", "Ações"], rows)}
      </div>
    </div>
  `;
}

function renderFornecedoresPanel() {
  const editing = findCadastroItem("fornecedores", activeCadastroEditing("fornecedores"));
  const rows = state.base.fornecedores.map(
    (item) => `
      <tr>
        <td>${esc(item.nome)}</td>
        <td>${esc(item.cpf_cnpj || "")}</td>
        <td>${esc(item.email || "")}</td>
        <td>${statusBadge(cadastroStatus("fornecedores", item))}</td>
        <td>${cadastroActionButtons("fornecedores", item)}</td>
      </tr>
    `
  );
  return `
    <div class="cadastro-layout">
      <form id="fornecedor-form" class="form-band cadastro-form">
        <input type="hidden" name="id" value="${editing?.id || ""}" />
        <div class="section-head">
          <div>
            <p class="eyebrow">Cadastro</p>
            <h3>${editing ? "Editar fornecedor" : "Novo fornecedor"}</h3>
          </div>
          <span class="pill ${editing ? "warn" : "good"}">${editing ? "Edição" : "Novo"}</span>
        </div>
        <label>Nome* <input name="nome" value="${esc(editing?.nome || "")}" required /></label>
        <div class="grid-2">
          <label>CPF/CNPJ <input name="cpf_cnpj" value="${esc(editing?.cpf_cnpj || "")}" /></label>
          <label>Telefone <input name="telefone" value="${esc(editing?.telefone || "")}" /></label>
        </div>
        <label>E-mail <input name="email" type="email" value="${esc(editing?.email || "")}" /></label>
        <label>Status
          <select name="status">
            <option value="ATIVO"${editing?.ativo || !editing ? " selected" : ""}>Ativo</option>
            <option value="ARQUIVADO"${editing && !editing.ativo ? " selected" : ""}>Arquivado</option>
          </select>
        </label>
        <div class="actions">
          <button class="primary" type="submit">${editing ? "Atualizar fornecedor" : "Salvar fornecedor"}</button>
          ${editing ? '<button type="button" class="ghost cadastro-cancel" data-entity="fornecedores">Cancelar</button>' : ""}
        </div>
      </form>
      <div class="section cadastro-list-panel">
        <div class="section-head">
          <div>
            <p class="eyebrow">Listagem</p>
            <h3>Fornecedores cadastrados</h3>
          </div>
          <span class="muted">Base pronta para edição e arquivamento</span>
        </div>
        ${table(["Nome", "CPF/CNPJ", "E-mail", "Status", "Ações"], rows)}
      </div>
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

function beneficiaryActionButtons(item) {
  const archived = String(item.status_cadastro || "").toUpperCase().includes("ARQUIV");
  return `
    <div class="table-actions">
      ${actionIconButton("edit", "beneficiarios", item.id, "Editar beneficiário")}
      ${actionIconButton("archive", "beneficiarios", item.id, archived ? "Beneficiário já arquivado" : "Arquivar beneficiário", "warn", archived)}
      ${actionIconButton("delete", "beneficiarios", item.id, "Excluir beneficiário", "danger")}
    </div>
  `;
}

function userActionButtons(item) {
  const archived = !item.ativo;
  const selfProtected = Number(item.id) === Number(state.user?.id);
  return `
    <div class="table-actions">
      ${actionIconButton("edit", "usuarios", item.id, "Editar usuário")}
      ${actionIconButton("archive", "usuarios", item.id, selfProtected || archived ? "Usuário indisponível para arquivar" : "Arquivar usuário", "warn", selfProtected || archived)}
      ${actionIconButton("delete", "usuarios", item.id, selfProtected ? "Você não pode excluir a própria conta" : "Excluir usuário", "danger", selfProtected)}
    </div>
  `;
}

function renderBeneficiariosPanel() {
  const editing = findCadastroItem("beneficiarios", activeManagementEditing("beneficiarios"));
  const rows = state.base.beneficiarios.map(
    (item) => `
      <tr>
        <td>${esc(item.nome)}</td>
        <td>${esc(item.cpf || "Sem CPF")}</td>
        <td>${esc(item.telefone || "")}</td>
        <td>${esc((item.polos || []).map((polo) => polo.nome).join(", "))}</td>
        <td>${statusBadge(item.status_cadastro)}</td>
        <td>${beneficiaryActionButtons(item)}</td>
      </tr>
    `
  );
  return `
    <section class="section">
      <div class="cadastro-layout">
        <form id="beneficiario-form" class="form-band cadastro-form">
          <input type="hidden" name="id" value="${editing?.id || ""}" />
          <div class="section-head">
            <div>
              <p class="eyebrow">Cadastro</p>
              <h3>${editing ? "Editar beneficiário" : "Novo beneficiário"}</h3>
            </div>
            <span class="pill ${editing ? "warn" : "good"}">${editing ? "Edição" : "Novo"}</span>
          </div>
          <div class="grid-3">
            <label>Nome completo* <input name="nome" value="${esc(editing?.nome || "")}" required /></label>
            <label>CPF <input name="cpf" value="${esc(editing?.cpf || "")}" /></label>
            <label>Nascimento <input name="data_nascimento" type="date" value="${esc(editing?.data_nascimento || "")}" /></label>
          </div>
          <div class="grid-4">
            <label>Telefone <input name="telefone" value="${esc(editing?.telefone || "")}" /></label>
            <label>E-mail <input name="email" type="email" value="${esc(editing?.email || "")}" /></label>
            <label>Bairro <input name="bairro" value="${esc(editing?.bairro || "")}" /></label>
            <label>Cidade <input name="cidade" value="${esc(editing?.cidade || "Betim")}" /></label>
          </div>
          <div class="grid-2">
            <label>Vereadores <select name="vereador_ids" multiple>${optionsSelected(state.base.vereadores, editing?.vereador_ids || [])}</select></label>
            <label>Polos <select name="polo_ids" multiple>${optionsSelected(state.base.polos, editing?.polo_ids || [])}</select></label>
          </div>
          <label>Status
            <select name="status_cadastro">
              <option value="ATIVO"${editing?.status_cadastro === "ATIVO" || !editing ? " selected" : ""}>Ativo</option>
              <option value="ARQUIVADO"${editing?.status_cadastro === "ARQUIVADO" ? " selected" : ""}>Arquivado</option>
            </select>
          </label>
          <label>Observações <textarea name="observacoes">${esc(editing?.observacoes || "")}</textarea></label>
          <div class="actions">
            <button class="primary" type="submit">${editing ? "Atualizar beneficiário" : "Salvar beneficiário"}</button>
            ${editing ? '<button type="button" class="ghost management-cancel" data-entity="beneficiarios">Cancelar</button>' : ""}
          </div>
        </form>
        <div class="section cadastro-list-panel">
          <div class="section-head">
            <div>
              <p class="eyebrow">Listagem</p>
              <h3>Beneficiários cadastrados</h3>
            </div>
            <span class="muted">Editar, arquivar ou excluir por linha</span>
          </div>
          ${table(["Nome", "CPF", "Telefone", "Polos", "Status", "Ações"], rows)}
        </div>
      </div>
    </section>
  `;
}

async function beneficiariosView() {
  await refreshBase();
  return renderBeneficiariosPanel();
}

async function cadastrosView() {
  await refreshBase();
  const cadastros = getCadastrosState();
  const activeSection = cadastros.section;
  const descriptions = Object.fromEntries(cadastroSections.map(([id, , description]) => [id, description]));
  const panels = {
    vereadores: renderVereadoresPanel(),
    polos: renderPolosPanel(),
    emendas: renderEmendasPanel(),
    fornecedores: renderFornecedoresPanel(),
  };
  return `
    <section class="section">
      <div class="item-card cadastro-overview">
        <div>
          <p class="eyebrow">Cadastros separados</p>
          <h3>${cadastroSections.find(([id]) => id === activeSection)?.[1] || "Cadastros"}</h3>
          <p class="muted">${descriptions[activeSection]}</p>
        </div>
        ${renderCadastroTabs(activeSection)}
      </div>
      ${panels[activeSection]}
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

function renderUsuariosPanel() {
  const editing = findCadastroItem("usuarios", activeManagementEditing("usuarios"));
  const rows = state.base.usuarios.map(
    (item) => `
      <tr>
        <td>${esc(item.nome)}</td>
        <td>${esc(item.email_login)}</td>
        <td>${esc(item.perfil)}</td>
        <td>${statusBadge(item.ativo ? "ATIVO" : "ARQUIVADO")}</td>
        <td>${userActionButtons(item)}</td>
      </tr>
    `
  );
  return `
    <section class="section">
      <div class="cadastro-layout">
        <form id="usuario-form" class="form-band cadastro-form">
          <input type="hidden" name="id" value="${editing?.id || ""}" />
          <div class="section-head">
            <div>
              <p class="eyebrow">Acesso</p>
              <h3>${editing ? "Editar usuário" : "Novo usuário"}</h3>
            </div>
            <span class="pill ${editing ? "warn" : "good"}">${editing ? "Edição" : "Novo"}</span>
          </div>
          <div class="grid-3">
            <label>Nome* <input name="nome" value="${esc(editing?.nome || "")}" required /></label>
            <label>Login* <input name="email_login" type="email" value="${esc(editing?.email_login || "")}" required /></label>
            <label>Senha${editing ? "" : "*"} <input name="senha" type="password" placeholder="${editing ? "Manter senha atual" : "revisa123"}" ${editing ? "" : 'value="revisa123" required'} /></label>
          </div>
          <div class="grid-3">
            <label>Perfil
              <select name="perfil">
                <option${editing?.perfil === "Super Admin" || !editing ? " selected" : ""}>Super Admin</option>
                <option${editing?.perfil === "Gestor Institucional REVISA" ? " selected" : ""}>Gestor Institucional REVISA</option>
                <option${editing?.perfil === "Gestor do Vereador" ? " selected" : ""}>Gestor do Vereador</option>
                <option${editing?.perfil === "Gestor de Polo" ? " selected" : ""}>Gestor de Polo</option>
                <option${editing?.perfil === "Operador de Polo" ? " selected" : ""}>Operador de Polo</option>
                <option${editing?.perfil === "Captador Mobile" ? " selected" : ""}>Captador Mobile</option>
              </select>
            </label>
            <label>Vereador <select name="vereador_id"><option value="">Sem escopo</option>${optionsSelected(state.base.vereadores, editing?.vereador_id ?? "")}</select></label>
            <label>Polo <select name="polo_id"><option value="">Sem escopo</option>${optionsSelected(state.base.polos, editing?.polo_id ?? "")}</select></label>
          </div>
          <label>Status
            <select name="ativo">
              <option value="true"${editing?.ativo || !editing ? " selected" : ""}>Ativo</option>
              <option value="false"${editing && !editing.ativo ? " selected" : ""}>Arquivado</option>
            </select>
          </label>
          <div class="actions">
            <button class="primary" type="submit">${editing ? "Atualizar usuário" : "Salvar usuário"}</button>
            ${editing ? '<button type="button" class="ghost management-cancel" data-entity="usuarios">Cancelar</button>' : ""}
          </div>
        </form>
        <div class="section cadastro-list-panel">
          <div class="section-head">
            <div>
              <p class="eyebrow">Permissões</p>
              <h3>Usuários cadastrados</h3>
            </div>
            <span class="muted">Controle completo de acesso por linha</span>
          </div>
          ${table(["Nome", "Login", "Perfil", "Status", "Ações"], rows)}
        </div>
      </div>
    </section>
  `;
}

async function usuariosView() {
  await refreshBase();
  return renderUsuariosPanel();
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

async function submitBeneficiarioForm(form) {
  const data = formData(form);
  const id = Number(data.id || 0) || null;
  const payload = {
    nome: data.nome,
    cpf: data.cpf || null,
    data_nascimento: data.data_nascimento || null,
    telefone: data.telefone || null,
    email: data.email || null,
    bairro: data.bairro || null,
    cidade: data.cidade || null,
    observacoes: data.observacoes || null,
    status_cadastro: data.status_cadastro || "ATIVO",
    vereador_ids: selectedValues(form.elements.vereador_ids),
    polo_ids: selectedValues(form.elements.polo_ids),
  };
  const path = id ? `/beneficiarios/${id}` : "/beneficiarios";
  const method = id ? "PUT" : "POST";
  try {
    const result = await api(path, { method, body: JSON.stringify(payload) });
    clearManagementEditing("beneficiarios");
    showToast(result?.alerta || `Beneficiário ${id ? "atualizado" : "salvo"}.`);
    await refreshBase();
    await render();
  } catch (error) {
    showToast(error.message);
  }
}

async function handleBeneficiarioAction(action, id) {
  if (action === "edit") {
    setManagementEditing("beneficiarios", id);
    await render();
    return;
  }
  if (action === "archive") {
    const confirmed = window.confirm("Arquivar este beneficiário? Ele sairá do fluxo ativo, mas continuará no histórico.");
    if (!confirmed) return;
    try {
      await api(`/beneficiarios/${id}/status`, { method: "PATCH", body: JSON.stringify({ status: "ARQUIVADO" }) });
      clearManagementEditing("beneficiarios");
      showToast("Beneficiário arquivado.");
      await refreshBase();
      await render();
    } catch (error) {
      showToast(error.message);
    }
    return;
  }
  const confirmed = window.confirm("Excluir este beneficiário? Esta ação é definitiva.");
  if (!confirmed) return;
  try {
    await api(`/beneficiarios/${id}`, { method: "DELETE" });
    clearManagementEditing("beneficiarios");
    showToast("Beneficiário excluído.");
    await refreshBase();
    await render();
  } catch (error) {
    showToast(error.message);
  }
}

async function submitUsuarioForm(form) {
  const data = formData(form);
  const id = Number(data.id || 0) || null;
  const payload = {
    nome: data.nome,
    email_login: data.email_login,
    perfil: data.perfil,
    vereador_id: data.vereador_id ? Number(data.vereador_id) : null,
    polo_id: data.polo_id ? Number(data.polo_id) : null,
    ativo: data.ativo === "true",
  };
  if (data.senha) payload.senha = data.senha;
  const path = id ? `/usuarios/${id}` : "/usuarios";
  const method = id ? "PUT" : "POST";
  if (!id && !payload.senha) {
    showToast("Senha é obrigatória para novo usuário.");
    return;
  }
  try {
    await api(path, { method, body: JSON.stringify(payload) });
    clearManagementEditing("usuarios");
    showToast(`Usuário ${id ? "atualizado" : "salvo"}.`);
    await refreshBase();
    await render();
  } catch (error) {
    showToast(error.message);
  }
}

async function handleUsuarioAction(action, id) {
  if (action === "edit") {
    setManagementEditing("usuarios", id);
    await render();
    return;
  }
  if (Number(id) === Number(state.user?.id)) {
    showToast("O usuário logado não pode alterar a própria conta por esta ação.");
    return;
  }
  if (action === "archive") {
    const confirmed = window.confirm("Arquivar este usuário? O acesso será bloqueado.");
    if (!confirmed) return;
    try {
      await api(`/usuarios/${id}/status`, { method: "PATCH", body: JSON.stringify({ status: "ARQUIVADO" }) });
      clearManagementEditing("usuarios");
      showToast("Usuário arquivado.");
      await refreshBase();
      await render();
    } catch (error) {
      showToast(error.message);
    }
    return;
  }
  const confirmed = window.confirm("Excluir este usuário? Esta ação não pode ser desfeita.");
  if (!confirmed) return;
  try {
    await api(`/usuarios/${id}`, { method: "DELETE" });
    clearManagementEditing("usuarios");
    showToast("Usuário excluído.");
    await refreshBase();
    await render();
  } catch (error) {
    showToast(error.message);
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
    beneficiarioForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      await submitBeneficiarioForm(beneficiarioForm);
    });
  }

  document.querySelectorAll('.cadastro-action[data-entity="beneficiarios"]').forEach((button) => {
    button.addEventListener("click", async () => {
      await handleBeneficiarioAction(button.dataset.action, Number(button.dataset.id));
    });
  });

  document.querySelectorAll('.cadastro-action[data-entity="usuarios"]').forEach((button) => {
    button.addEventListener("click", async () => {
      await handleUsuarioAction(button.dataset.action, Number(button.dataset.id));
    });
  });

  document.querySelectorAll(".management-cancel").forEach((button) => {
    button.addEventListener("click", async () => {
      clearManagementEditing(button.dataset.entity);
      await render();
    });
  });

  document.querySelectorAll(".cadastro-switch").forEach((button) => {
    button.addEventListener("click", async () => {
      setCadastroSection(button.dataset.section);
      await render();
    });
  });

  document.querySelectorAll(".cadastro-cancel").forEach((button) => {
    button.addEventListener("click", async () => {
      clearCadastroEditing(button.dataset.entity);
      await render();
    });
  });

  document.querySelectorAll('.cadastro-action[data-entity="vereadores"], .cadastro-action[data-entity="polos"], .cadastro-action[data-entity="emendas"], .cadastro-action[data-entity="fornecedores"]').forEach((button) => {
    button.addEventListener("click", async () => {
      await handleCadastroAction(button.dataset.entity, button.dataset.action, Number(button.dataset.id));
    });
  });

  const vereadorForm = $("#vereador-form");
  if (vereadorForm) {
    vereadorForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      await submitCadastroForm("vereadores", vereadorForm);
    });
  }

  const poloForm = $("#polo-form");
  if (poloForm) {
    poloForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      await submitCadastroForm("polos", poloForm);
    });
  }

  const emendaForm = $("#emenda-form");
  if (emendaForm) {
    emendaForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      await submitCadastroForm("emendas", emendaForm);
    });
  }

  const fornecedorForm = $("#fornecedor-form");
  if (fornecedorForm) {
    fornecedorForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      await submitCadastroForm("fornecedores", fornecedorForm);
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
    usuarioForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      await submitUsuarioForm(usuarioForm);
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
