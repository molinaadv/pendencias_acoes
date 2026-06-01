import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(
    page_title="Pendências Ações",
    page_icon="✅",
    layout="centered",
    initial_sidebar_state="collapsed"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TABELA = "pendencias_acoes"

STATUS_ATIVOS = ["Aberta", "Em andamento", "Aguardando informação"]
TODOS_STATUS = ["Aberta", "Em andamento", "Aguardando informação", "Concluída", "Cancelada"]


st.markdown("""
<style>
[data-testid="stSidebar"] {display:none;}
[data-testid="stHeader"] {background:transparent;}
.block-container {padding:0 1rem 6rem 1rem; max-width:760px;}

html, body, .stApp, [data-testid="stAppViewContainer"] {
    background:#ffffff !important;
    color:#0f172a !important;
}

* {
    color:inherit;
}

.mobile-header {
    background:linear-gradient(135deg,#073763,#0b5394);
    padding:28px 22px 34px 22px;
    border-radius:0 0 28px 28px;
    color:white !important;
    margin:0 -1rem 24px -1rem;
    box-shadow:0 8px 18px rgba(7,55,99,.22);
}

.mobile-title {
    font-size:30px;
    font-weight:900;
    color:white !important;
    display:flex;
    align-items:center;
    gap:10px;
}

.mobile-subtitle {
    font-size:15px;
    color:white !important;
    opacity:.96;
    margin-top:8px;
}

.hello-card {
    display:flex;
    align-items:center;
    gap:14px;
    margin:20px 0 18px 0;
}

.avatar {
    width:58px;
    height:58px;
    border-radius:50%;
    background:#073763;
    color:white !important;
    display:flex;
    align-items:center;
    justify-content:center;
    font-weight:900;
    font-size:26px;
}

.hello-title {
    font-size:26px;
    font-weight:900;
    color:#0f172a !important;
}

.hello-subtitle {
    font-size:16px;
    color:#64748b !important;
}

.summary-grid {
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:12px;
    margin-bottom:24px;
}

.summary-card {
    border-radius:18px;
    padding:18px 12px;
    min-height:112px;
    border:1px solid #e5e7eb;
}

.summary-number {
    font-size:36px;
    font-weight:900;
    color:#0f172a !important;
}

.summary-label {
    font-size:14px;
    font-weight:900;
}

.blue-card {background:#eff6ff;color:#1d4ed8 !important;}
.orange-card {background:#fff7ed;color:#c2410c !important;}
.purple-card {background:#f5f3ff;color:#6d28d9 !important;}

.section-title {
    font-size:28px;
    font-weight:900;
    color:#0f172a !important;
    margin-top:8px;
}

.section-subtitle {
    color:#64748b !important;
    font-size:16px;
    margin-bottom:16px;
}

.filter-box {
    background:#ffffff;
    border:1px solid #d1d5db;
    border-radius:15px;
    padding:14px 16px;
    margin:12px 0 18px 0;
    color:#0f172a !important;
    font-size:18px;
}

.card {
    background:#ffffff !important;
    color:#0f172a !important;
    border:1px solid #e5e7eb;
    border-radius:22px;
    padding:20px;
    margin-bottom:14px;
    box-shadow:0 5px 16px rgba(15,23,42,.09);
    border-left:7px solid #2563eb;
}

.card.andamento-border {border-left-color:#f59e0b;}
.card.aguardando-border {border-left-color:#7c3aed;}
.card.concluida-border {border-left-color:#16a34a;}
.card.cancelada-border {border-left-color:#dc2626;}

.card * {
    color:#0f172a !important;
}

.protocolo {
    font-size:22px;
    font-weight:900;
    color:#0f172a !important;
}

.badge {
    padding:7px 14px;
    border-radius:20px;
    font-weight:900;
    font-size:14px;
    float:right;
}

.badge.aberta {background:#dbeafe;color:#1d4ed8 !important;}
.badge.andamento {background:#ffedd5;color:#c2410c !important;}
.badge.aguardando {background:#ede9fe;color:#6d28d9 !important;}
.badge.concluida {background:#dcfce7;color:#15803d !important;}
.badge.cancelada {background:#fee2e2;color:#b91c1c !important;}

.info-line {
    font-size:17px;
    line-height:1.8;
    color:#0f172a !important;
}

.info-line b {
    font-weight:900;
}

.desc-box {
    background:#f8fafc !important;
    color:#0f172a !important;
    padding:13px 15px;
    border-radius:14px;
    margin-top:14px;
    font-size:17px;
}

.bottom-nav {
    position:fixed;
    bottom:0;
    left:0;
    right:0;
    background:#ffffff;
    border-top:1px solid #e5e7eb;
    display:flex;
    justify-content:space-around;
    padding:9px 4px;
    z-index:9999;
}

.nav-item {
    text-align:center;
    font-size:13px;
    color:#334155 !important;
    font-weight:800;
}

.fab {
    position:fixed;
    right:24px;
    bottom:86px;
    width:64px;
    height:64px;
    border-radius:50%;
    background:#073763;
    color:white !important;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:42px;
    font-weight:300;
    box-shadow:0 8px 20px rgba(0,0,0,.28);
    z-index:9998;
}

.stButton > button {
    background:#ffffff !important;
    color:#0f172a !important;
    border:1px solid #d1d5db !important;
    border-radius:12px !important;
    font-weight:800 !important;
}

.stButton > button p {
    color:#0f172a !important;
}

input, textarea {
    background:#f1f5f9 !important;
    color:#0f172a !important;
    border-radius:12px !important;
}

label, p, span, div {
    color:inherit;
}

@media(max-width:768px){
    .block-container {padding:0 0.85rem 6rem 0.85rem;}
    .mobile-header {margin:0 -0.85rem 24px -0.85rem; padding:28px 22px 34px 22px;}
    .mobile-title {font-size:25px;}
    .mobile-subtitle {font-size:14px;}
    .summary-grid {grid-template-columns:repeat(3,1fr); gap:10px;}
    .summary-card {padding:14px 10px; min-height:100px;}
    .summary-number {font-size:32px;}
    .summary-label {font-size:12px;}
    .protocolo {font-size:20px;}
    .card {padding:18px;}
}
</style>
""", unsafe_allow_html=True)


def gerar_protocolo():
    return "PA-" + datetime.now().strftime("%Y%m%d%H%M%S")


def carregar_pendencias():
    try:
        res = supabase.table(TABELA).select("*").order("criado_em", desc=True).execute()
        return pd.DataFrame(res.data or [])
    except Exception as e:
        st.error(f"Erro ao carregar pendências: {e}")
        return pd.DataFrame()


def inserir_pendencia(nome, cidade, comunidade, descricao):
    protocolo = gerar_protocolo()
    dados = {
        "protocolo": protocolo,
        "nome_solicitante": nome.strip(),
        "cidade": cidade.strip(),
        "comunidade": comunidade.strip(),
        "descricao": descricao.strip(),
        "status": "Aberta",
        "responsavel": "Ações",
    }
    supabase.table(TABELA).insert(dados).execute()
    return protocolo


def atualizar_pendencia(id_pendencia, status, observacao):
    dados = {
        "status": status,
        "observacao_retorno": observacao,
        "atualizado_em": datetime.utcnow().isoformat()
    }
    if status == "Concluída":
        dados["concluido_em"] = datetime.utcnow().isoformat()
    supabase.table(TABELA).update(dados).eq("id", id_pendencia).execute()


def gerar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Pendências")
    output.seek(0)
    return output


def gerar_pdf(df):
    output = BytesIO()
    c = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    y = height - 45

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Relatório de Pendências - Ações")
    y -= 30
    c.setFont("Helvetica", 9)

    for _, row in df.iterrows():
        if y < 80:
            c.showPage()
            y = height - 45
            c.setFont("Helvetica", 9)

        linha = f"{row.get('protocolo','')} | {row.get('status','')} | {row.get('cidade','')} | {row.get('comunidade','')} | {row.get('nome_solicitante','')}"
        c.drawString(40, y, linha[:120])
        y -= 14

        desc = str(row.get("descricao", "")).replace("\n", " ")
        c.drawString(55, y, desc[:110])
        y -= 22

    c.save()
    output.seek(0)
    return output


def status_classe(status):
    return {
        "Aberta": "aberta",
        "Em andamento": "andamento",
        "Aguardando informação": "aguardando",
        "Concluída": "concluida",
        "Cancelada": "cancelada",
    }.get(status, "aberta")


def card_border(status):
    return {
        "Aberta": "",
        "Em andamento": "andamento-border",
        "Aguardando informação": "aguardando-border",
        "Concluída": "concluida-border",
        "Cancelada": "cancelada-border",
    }.get(status, "")


def get_page():
    return st.query_params.get("page", "pendencias")


def set_page(page):
    st.query_params["page"] = page
    st.rerun()


page = get_page()


st.markdown("""
<div class="mobile-header">
    <div class="mobile-title">✅ Pendências Ações</div>
    <div class="mobile-subtitle">Controle de pendências por cidade e comunidade</div>
</div>
""", unsafe_allow_html=True)


if page == "pendencias":
    df = carregar_pendencias()

    if df.empty:
        abertas = andamento = aguardando = 0
    else:
        abertas = int((df["status"] == "Aberta").sum())
        andamento = int((df["status"] == "Em andamento").sum())
        aguardando = int((df["status"] == "Aguardando informação").sum())

    st.markdown("""
    <div class="hello-card">
        <div class="avatar">A</div>
        <div>
            <div class="hello-title">Olá, Ações 👋</div>
            <div class="hello-subtitle">Aqui estão suas pendências</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="summary-grid">
        <div class="summary-card blue-card">
            <div class="summary-number">{abertas}</div>
            <div class="summary-label">Abertas</div>
        </div>
        <div class="summary-card orange-card">
            <div class="summary-number">{andamento}</div>
            <div class="summary-label">Em andamento</div>
        </div>
        <div class="summary-card purple-card">
            <div class="summary-number">{aguardando}</div>
            <div class="summary-label">Aguardando</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Pendências</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-subtitle'>Exibindo pendências ativas</div>", unsafe_allow_html=True)

    if df.empty:
        st.info("Nenhuma pendência cadastrada.")
    else:
        with st.expander("🔎 Filtros"):
            mostrar_concluidas = st.toggle("Mostrar concluídas e canceladas", value=False)

            cidades = ["Todas"] + sorted(df["cidade"].dropna().unique().tolist())
            comunidades = ["Todas"] + sorted(df["comunidade"].dropna().unique().tolist())

            cidade_f = st.selectbox("Cidade", cidades)
            comunidade_f = st.selectbox("Comunidade", comunidades)

            status_opcoes = TODOS_STATUS if mostrar_concluidas else STATUS_ATIVOS
            status_f = st.multiselect("Status", status_opcoes, default=status_opcoes)

        dff = df.copy()

        if not mostrar_concluidas:
            dff = dff[dff["status"].isin(STATUS_ATIVOS)]

        if cidade_f != "Todas":
            dff = dff[dff["cidade"] == cidade_f]

        if comunidade_f != "Todas":
            dff = dff[dff["comunidade"] == comunidade_f]

        if status_f:
            dff = dff[dff["status"].isin(status_f)]

        if dff.empty:
            st.warning("Nenhuma pendência encontrada.")
        else:
            for _, row in dff.iterrows():
                criado = str(row.get("criado_em", ""))[:10]
                status = row.get("status", "Aberta")

                st.markdown(f"""
                <div class="card {card_border(status)}">
                    <span class="protocolo">{row.get('protocolo','')}</span>
                    <span class="badge {status_classe(status)}">{status}</span>
                    <br><br>
                    <div class="info-line">🏢 <b>Cidade:</b> {row.get('cidade','')}</div>
                    <div class="info-line">👥 <b>Comunidade:</b> {row.get('comunidade','')}</div>
                    <div class="info-line">👤 <b>Solicitante:</b> {row.get('nome_solicitante','')}</div>
                    <div class="info-line">📅 <b>Data:</b> {criado}</div>
                    <div class="desc-box">{row.get('descricao','')}</div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f"Atualizar {row.get('protocolo','')}"):
                    status_atual = row.get("status", "Aberta")
                    if status_atual not in TODOS_STATUS:
                        status_atual = "Aberta"

                    novo_status = st.selectbox(
                        "Novo status",
                        TODOS_STATUS,
                        index=TODOS_STATUS.index(status_atual),
                        key=f"status_{row['id']}"
                    )

                    obs = st.text_area(
                        "Observação / retorno",
                        value=row.get("observacao_retorno") or "",
                        key=f"obs_{row['id']}"
                    )

                    if st.button("Salvar atualização", key=f"btn_{row['id']}"):
                        atualizar_pendencia(row["id"], novo_status, obs)
                        st.success("Pendência atualizada.")
                        st.rerun()

    if st.button("➕ Nova pendência"):
        set_page("nova")


elif page == "nova":
    st.markdown("<div class='section-title'>Nova Pendência</div>", unsafe_allow_html=True)

    with st.form("form_pendencia"):
        nome = st.text_input("Nome do solicitante")
        cidade = st.text_input("Cidade")
        comunidade = st.text_input("Comunidade")
        descricao = st.text_area("Descrição da pendência", height=140)
        enviar = st.form_submit_button("Abrir pendência")

    if enviar:
        if not nome or not cidade or not comunidade or not descricao:
            st.warning("Preencha todos os campos.")
        else:
            protocolo = inserir_pendencia(nome, cidade, comunidade, descricao)
            st.success(f"Pendência aberta com sucesso. Protocolo: {protocolo}")

    if st.button("Voltar para pendências"):
        set_page("pendencias")


elif page == "relatorios":
    st.markdown("<div class='section-title'>Relatórios / Admin</div>", unsafe_allow_html=True)

    df = carregar_pendencias()

    if df.empty:
        st.info("Nenhuma pendência cadastrada.")
    else:
        cidade_f = st.selectbox("Cidade", ["Todas"] + sorted(df["cidade"].dropna().unique().tolist()))
        comunidade_f = st.selectbox("Comunidade", ["Todas"] + sorted(df["comunidade"].dropna().unique().tolist()))
        status_f = st.multiselect("Status", TODOS_STATUS, default=TODOS_STATUS)

        dff = df.copy()

        if cidade_f != "Todas":
            dff = dff[dff["cidade"] == cidade_f]

        if comunidade_f != "Todas":
            dff = dff[dff["comunidade"] == comunidade_f]

        if status_f:
            dff = dff[dff["status"].isin(status_f)]

        st.dataframe(dff, use_container_width=True)

        st.download_button(
            "⬇️ Baixar Excel",
            data=gerar_excel(dff),
            file_name="pendencias_acoes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.download_button(
            "⬇️ Baixar PDF",
            data=gerar_pdf(dff),
            file_name="pendencias_acoes.pdf",
            mime="application/pdf"
        )


st.markdown("""
<div class="fab">+</div>
<div class="bottom-nav">
    <div class="nav-item">🏠<br>Pendências</div>
    <div class="nav-item">➕<br>Nova</div>
    <div class="nav-item">📊<br>Relatórios</div>
    <div class="nav-item">👤<br>Perfil</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏠 Pendências"):
        set_page("pendencias")

with col2:
    if st.button("➕ Nova"):
        set_page("nova")

with col3:
    if st.button("📊 Relatórios"):
        set_page("relatorios")
