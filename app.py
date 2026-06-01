import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="Pendências Marcos",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# SUPABASE
# =========================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TABELA = "pendencias_marcos"

# =========================
# CSS MOBILE
# =========================
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 1100px;
    }
    .main-title {
        background: linear-gradient(135deg, #003366, #0055a5);
        color: white;
        padding: 18px;
        border-radius: 18px;
        text-align: center;
        margin-bottom: 20px;
    }
    .card {
        background: white;
        border-radius: 18px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.08);
        border-left: 6px solid #0055a5;
    }
    .card-andamento { border-left-color: #f39c12; }
    .card-aguardando { border-left-color: #8e44ad; }
    .card-concluida { border-left-color: #27ae60; }
    .card-cancelada { border-left-color: #7f8c8d; }
    .status {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 700;
        background: #eaf2ff;
        color: #0055a5;
    }
    .metric-card {
        background: #ffffff;
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.08);
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-number {
        font-size: 34px;
        font-weight: 800;
        color: #003366;
    }
    .small-text {
        color: #5f6b7a;
        font-size: 14px;
    }
    div.stButton > button {
        border-radius: 12px;
        min-height: 42px;
        font-weight: 700;
        width: 100%;
    }
    @media (max-width: 768px) {
        .main-title h1 { font-size: 24px; }
        .block-container { padding-left: .7rem; padding-right: .7rem; }
    }
</style>
""", unsafe_allow_html=True)

# =========================
# FUNÇÕES
# =========================
def criar_protocolo(id_registro: int) -> str:
    return f"PM-{id_registro:06d}"


def carregar_pendencias() -> pd.DataFrame:
    try:
        resp = supabase.table(TABELA).select("*").order("criado_em", desc=True).execute()
        dados = resp.data or []
        df = pd.DataFrame(dados)
        if df.empty:
            return pd.DataFrame(columns=[
                "id", "protocolo", "nome_solicitante", "cidade", "comunidade",
                "descricao", "status", "responsavel", "observacao_retorno",
                "criado_em", "atualizado_em", "concluido_em"
            ])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar pendências: {e}")
        return pd.DataFrame()


def abrir_pendencia(nome, cidade, comunidade, descricao):
    novo = {
        "nome_solicitante": nome.strip(),
        "cidade": cidade.strip(),
        "comunidade": comunidade.strip(),
        "descricao": descricao.strip(),
        "status": "Aberta",
        "responsavel": "Marcos",
        "criado_em": datetime.utcnow().isoformat(),
        "atualizado_em": datetime.utcnow().isoformat()
    }
    resp = supabase.table(TABELA).insert(novo).execute()
    registro = resp.data[0]
    protocolo = criar_protocolo(registro["id"])
    supabase.table(TABELA).update({"protocolo": protocolo}).eq("id", registro["id"]).execute()
    return protocolo


def atualizar_status(id_pendencia, status, observacao=""):
    dados = {
        "status": status,
        "observacao_retorno": observacao,
        "atualizado_em": datetime.utcnow().isoformat()
    }
    if status == "Concluída":
        dados["concluido_em"] = datetime.utcnow().isoformat()
    supabase.table(TABELA).update(dados).eq("id", id_pendencia).execute()


def filtrar_df(df, cidade, comunidade, status, mostrar_concluidas, data_inicio, data_fim):
    if df.empty:
        return df

    df2 = df.copy()
    df2["criado_em_dt"] = pd.to_datetime(df2["criado_em"], errors="coerce").dt.date

    if not mostrar_concluidas:
        df2 = df2[~df2["status"].isin(["Concluída", "Cancelada"])]

    if cidade != "Todas":
        df2 = df2[df2["cidade"] == cidade]

    if comunidade != "Todas":
        df2 = df2[df2["comunidade"] == comunidade]

    if status != "Todos":
        df2 = df2[df2["status"] == status]

    if data_inicio:
        df2 = df2[df2["criado_em_dt"] >= data_inicio]
    if data_fim:
        df2 = df2[df2["criado_em_dt"] <= data_fim]

    return df2


def gerar_excel(df):
    output = BytesIO()
    colunas = [
        "protocolo", "nome_solicitante", "cidade", "comunidade",
        "descricao", "status", "responsavel", "observacao_retorno",
        "criado_em", "concluido_em"
    ]
    df_export = df[[c for c in colunas if c in df.columns]].copy()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Pendências Marcos")
    output.seek(0)
    return output


def gerar_pdf(df):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4)
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("Relatório de Pendências - Marcos", styles["Title"]))
    elementos.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    if df.empty:
        elementos.append(Paragraph("Nenhuma pendência encontrada.", styles["Normal"]))
    else:
        dados = [["Protocolo", "Cidade", "Comunidade", "Solicitante", "Status"]]
        for _, row in df.iterrows():
            dados.append([
                str(row.get("protocolo", "")),
                str(row.get("cidade", ""))[:18],
                str(row.get("comunidade", ""))[:18],
                str(row.get("nome_solicitante", ""))[:18],
                str(row.get("status", ""))
            ])

        tabela = Table(dados, repeatRows=1)
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elementos.append(tabela)

    doc.build(elementos)
    output.seek(0)
    return output


def classe_card(status):
    if status == "Em andamento":
        return "card card-andamento"
    if status == "Aguardando informação":
        return "card card-aguardando"
    if status == "Concluída":
        return "card card-concluida"
    if status == "Cancelada":
        return "card card-cancelada"
    return "card"

# =========================
# CABEÇALHO
# =========================
st.markdown("""
<div class='main-title'>
    <h1>✅ Pendências Marcos</h1>
    <p>Controle de pendências por cidade e comunidade</p>
</div>
""", unsafe_allow_html=True)

# =========================
# MENU
# =========================
menu = st.sidebar.radio(
    "Menu",
    ["Nova Pendência", "Pendências do Marcos", "Relatórios"]
)

# =========================
# NOVA PENDÊNCIA
# =========================
if menu == "Nova Pendência":
    st.subheader("➕ Abrir nova pendência")

    with st.form("form_nova_pendencia"):
        nome = st.text_input("Nome do solicitante *")
        cidade = st.text_input("Cidade *")
        comunidade = st.text_input("Comunidade *")
        descricao = st.text_area("Descrição da pendência *", height=140)
        enviar = st.form_submit_button("Abrir pendência")

    if enviar:
        if not nome or not cidade or not comunidade or not descricao:
            st.warning("Preencha todos os campos obrigatórios.")
        else:
            try:
                protocolo = abrir_pendencia(nome, cidade, comunidade, descricao)
                st.success(f"Pendência aberta com sucesso! Protocolo: {protocolo}")
            except Exception as e:
                st.error(f"Erro ao abrir pendência: {e}")

# =========================
# PENDÊNCIAS DO MARCOS
# =========================
elif menu == "Pendências do Marcos":
    st.subheader("📋 Pendências do Marcos")
    df = carregar_pendencias()

    total_abertas = int((df["status"] == "Aberta").sum()) if not df.empty else 0
    total_andamento = int((df["status"] == "Em andamento").sum()) if not df.empty else 0
    total_aguardando = int((df["status"] == "Aguardando informação").sum()) if not df.empty else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='metric-card'><div class='metric-number'>{total_abertas}</div><div>Abertas</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><div class='metric-number'>{total_andamento}</div><div>Em andamento</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><div class='metric-number'>{total_aguardando}</div><div>Aguardando info.</div></div>", unsafe_allow_html=True)

    st.markdown("### Filtros")
    cidades = ["Todas"] + sorted(df["cidade"].dropna().unique().tolist()) if not df.empty else ["Todas"]
    comunidades = ["Todas"] + sorted(df["comunidade"].dropna().unique().tolist()) if not df.empty else ["Todas"]

    f1, f2 = st.columns(2)
    with f1:
        cidade_filtro = st.selectbox("Cidade", cidades)
    with f2:
        comunidade_filtro = st.selectbox("Comunidade", comunidades)

    f3, f4 = st.columns(2)
    with f3:
        status_filtro = st.selectbox("Status", ["Todos", "Aberta", "Em andamento", "Aguardando informação", "Concluída", "Cancelada"])
    with f4:
        mostrar_concluidas = st.checkbox("Mostrar concluídas/canceladas", value=False)

    df_filtrado = filtrar_df(df, cidade_filtro, comunidade_filtro, status_filtro, mostrar_concluidas, None, None)

    if df_filtrado.empty:
        st.info("Nenhuma pendência encontrada com esses filtros.")
    else:
        for _, row in df_filtrado.iterrows():
            status = row.get("status", "Aberta")
            criado = pd.to_datetime(row.get("criado_em"), errors="coerce")
            criado_txt = criado.strftime("%d/%m/%Y") if pd.notna(criado) else ""
            protocolo = row.get("protocolo") or criar_protocolo(int(row.get("id")))

            st.markdown(f"""
            <div class='{classe_card(status)}'>
                <h3>{protocolo} <span class='status'>{status}</span></h3>
                <p><b>Cidade:</b> {row.get('cidade','')}</p>
                <p><b>Comunidade:</b> {row.get('comunidade','')}</p>
                <p><b>Solicitante:</b> {row.get('nome_solicitante','')}</p>
                <p><b>Data:</b> {criado_txt}</p>
                <p><b>Descrição:</b><br>{row.get('descricao','')}</p>
                <p class='small-text'><b>Retorno:</b> {row.get('observacao_retorno') or '-'}</p>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"Atualizar {protocolo}"):
                novo_status = st.selectbox(
                    "Novo status",
                    ["Aberta", "Em andamento", "Aguardando informação", "Concluída", "Cancelada"],
                    index=["Aberta", "Em andamento", "Aguardando informação", "Concluída", "Cancelada"].index(status) if status in ["Aberta", "Em andamento", "Aguardando informação", "Concluída", "Cancelada"] else 0,
                    key=f"status_{row['id']}"
                )
                obs = st.text_area("Observação/retorno", value=row.get("observacao_retorno") or "", key=f"obs_{row['id']}")
                if st.button("Salvar atualização", key=f"btn_{row['id']}"):
                    atualizar_status(row["id"], novo_status, obs)
                    st.success("Pendência atualizada com sucesso!")
                    st.rerun()

# =========================
# RELATÓRIOS
# =========================
elif menu == "Relatórios":
    st.subheader("📊 Relatórios")
    df = carregar_pendencias()

    cidades = ["Todas"] + sorted(df["cidade"].dropna().unique().tolist()) if not df.empty else ["Todas"]
    comunidades = ["Todas"] + sorted(df["comunidade"].dropna().unique().tolist()) if not df.empty else ["Todas"]

    c1, c2 = st.columns(2)
    with c1:
        cidade_filtro = st.selectbox("Cidade", cidades, key="rel_cidade")
        data_inicio = st.date_input("Data inicial", value=date(date.today().year, date.today().month, 1))
    with c2:
        comunidade_filtro = st.selectbox("Comunidade", comunidades, key="rel_comunidade")
        data_fim = st.date_input("Data final", value=date.today())

    status_filtro = st.selectbox("Status", ["Todos", "Aberta", "Em andamento", "Aguardando informação", "Concluída", "Cancelada"], key="rel_status")
    mostrar_concluidas = st.checkbox("Incluir concluídas/canceladas", value=True, key="rel_concluidas")

    df_rel = filtrar_df(df, cidade_filtro, comunidade_filtro, status_filtro, mostrar_concluidas, data_inicio, data_fim)
    st.write(f"Total encontrado: **{len(df_rel)}**")

    if not df_rel.empty:
        st.dataframe(df_rel[["protocolo", "nome_solicitante", "cidade", "comunidade", "descricao", "status", "criado_em"]], use_container_width=True)

    excel = gerar_excel(df_rel)
    pdf = gerar_pdf(df_rel)

    c3, c4 = st.columns(2)
    with c3:
        st.download_button(
            "Baixar Excel",
            data=excel,
            file_name="pendencias_marcos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with c4:
        st.download_button(
            "Baixar PDF",
            data=pdf,
            file_name="pendencias_marcos.pdf",
            mime="application/pdf"
        )
