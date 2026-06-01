import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Pendências Ações", page_icon="✅", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TABELA = "pendencias_acoes"

STATUS_ATIVOS = ["Aberta", "Em andamento", "Aguardando informação"]
TODOS_STATUS = STATUS_ATIVOS + ["Concluída", "Cancelada"]


st.markdown("""
<style>
[data-testid="stSidebar"] {display: none;}
.block-container {padding-top: 0.5rem; max-width: 760px;}

.mobile-header {
    background: linear-gradient(135deg,#073763,#0b5394);
    padding: 22px 20px 26px 20px;
    border-radius: 0 0 24px 24px;
    color: white;
    margin-bottom: 20px;
}

.mobile-title {
    font-size: 28px;
    font-weight: 800;
}

.mobile-subtitle {
    font-size: 14px;
    opacity: .9;
}

.hello-card {
    display:flex;
    align-items:center;
    gap:14px;
    margin: 12px 0 18px 0;
}

.avatar {
    width:55px;
    height:55px;
    border-radius:50%;
    background:#073763;
    color:white;
    display:flex;
    align-items:center;
    justify-content:center;
    font-weight:800;
    font-size:24px;
}

.summary-grid {
    display:grid;
    grid-template-columns: repeat(3, 1fr);
    gap:12px;
    margin-bottom:22px;
}

.summary-card {
    border-radius:18px;
    padding:16px 12px;
    border:1px solid #e5e7eb;
    min-height:105px;
}

.summary-number {
    font-size:34px;
    font-weight:900;
    color:#0f172a;
}

.summary-label {
    font-size:14px;
    font-weight:800;
}

.blue-card {background:#eff6ff; color:#1d4ed8;}
.orange-card {background:#fff7ed; color:#c2410c;}
.purple-card {background:#f5f3ff; color:#6d28d9;}

.section-title {
    font-size:26px;
    font-weight:900;
    margin-top:8px;
}

.card {
    background:#fff;
    border:1px solid #e5e7eb;
    border-radius:20px;
    padding:18px;
    margin-bottom:14px;
    box-shadow:0 4px 14px rgba(15,23,42,.08);
    border-left:6px solid #1d4ed8;
}

.card.andamento-border {border-left-color:#f59e0b;}
.card.aguardando-border {border-left-color:#7c3aed;}
.card.concluida-border {border-left-color:#16a34a;}
.card.cancelada-border {border-left-color:#dc2626;}

.protocolo {
    font-size:20px;
    font-weight:900;
    color:#0f172a;
}

.badge {
    padding:6px 12px;
    border-radius:18px;
    font-weight:800;
    font-size:13px;
    float:right;
}

.aberta {background:#dbeafe;color:#1d4ed8}
.andamento{background:#ffedd5;color:#c2410c}
.aguardando{background:#ede9fe;color:#6d28d9}
.concluida{background:#dcfce7;color:#15803d}
.cancelada{background:#fee2e2;color:#b91c1c}

.desc-box {
    background:#f8fafc;
    padding:10px;
    border-radius:12px;
    margin-top:10px;
    color:#334155;
}

.bottom-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
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
    color:#334155;
    font-weight:700;
}

.fab {
    position: fixed;
    right: 24px;
    bottom: 82px;
    width:62px;
    height:62px;
    border-radius:50%;
    background:#073763;
    color:white;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:38px;
    font-weight:300;
    box-shadow:0 8px 18px rgba(0,0,0,.25);
    z-index:9999;
}

@media(max-width:768px){
    .block-container {padding:0 0.8rem 5.5rem 0.8rem;}
    .summary-grid {grid-template-columns: repeat(3, 1fr);}
    .summary-card {padding:12px 8px; min-height:95px;}
    .summary-number {font-size:30px;}
    .summary-label {font-size:12px;}
    .mobile-title {font-size:24px;}
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


def get_query_page():
    try:
        return st.query_params.get("page", "pendencias")
    except Exception:
        return "pendencias"


def set_page(page):
    st.query_params["page"] = page
    st.rerun()


page = get_query_page()


st.markdown("""
<div class="mobile-header">
    <div class="mobile-title">✅ Pendências Ações</div>
    <div class="mobile-subtitle">Controle de pendências por cidade e comunidade</div>
</div>
""", unsafe_allow_html=True)


if page == "pendencias":
    df = carregar_pendencias()

    if df.empty:
        abertas = andamento = aguardando = concluidas = 0
    else:
        abertas = int((df["status"] == "Aberta").sum())
        andamento = int((df["status"] == "Em andamento").sum())
        aguardando = int((df["status"] == "Aguardando informação").sum())
        concluidas = int((df["status"] == "Concluída").sum())

    st.markdown("""
    <div class="hello-card">
        <div class="avatar">A</div>
        <div>
            <div style="font-size:25px;font-weight:900;color:#0f172a;">Olá, Ações 👋</div>
            <div style="font-size:15px;color:#64748b;">Aqui estão suas pendências</div>
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
    st.caption("Exibindo pendências ativas")

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
                st.markdown(f"""
                <div class="card {card_border(row.get('status',''))}">
                    <span class="protocolo">{row.get('protocolo','')}</span>
                    <span class="badge {status_classe(row.get('status',''))}">{row.get('status','')}</span>
                    <br><br>
                    <b>Cidade:</b> {row.get('cidade','')}<br>
                    <b>Comunidade:</b> {row.get('comunidade','')}<br>
                    <b>Solicitante:</b> {row.get('nome_solicitante','')}<br>
                    <b>Data:</b> {criado}
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

col_nav1, col_nav2, col_nav3 = st.columns(3)

with col_nav1:
    if st.button("🏠 Pendências"):
        set_page("pendencias")

with col_nav2:
    if st.button("➕ Nova"):
        set_page("nova")

with col_nav3:
    if st.button("📊 Relatórios"):
        set_page("relatorios")
