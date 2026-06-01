import io
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from supabase import create_client, Client
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# =============================
# CONFIGURAÇÃO
# =============================
st.set_page_config(
    page_title="Pendências Marcos",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

STATUS_ATIVOS = ["Aberta", "Em andamento", "Aguardando informação"]
STATUS_TODOS = ["Aberta", "Em andamento", "Aguardando informação", "Concluída", "Cancelada"]

# =============================
# ESTILO MOBILE
# =============================
st.markdown(
    """
    <style>
    .main {background-color: #f7f9fc;}
    .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1050px;}
    h1, h2, h3 {color: #0b1f3a;}
    div[data-testid="stMetric"] {
        background: white;
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.07);
        border: 1px solid #e6edf7;
    }
    .card {
        background: white;
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.07);
        border-left: 6px solid #0b4ea2;
    }
    .card-andamento {border-left-color: #f59e0b;}
    .card-aguardando {border-left-color: #7c3aed;}
    .card-concluida {border-left-color: #16a34a;}
    .card-cancelada {border-left-color: #64748b;}
    .badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 700;
        background: #e7f0ff;
        color: #0b4ea2;
    }
    .small {color: #5b677a; font-size: 14px;}
    .desc {
        background: #f2f5f9;
        border-radius: 12px;
        padding: 10px;
        margin-top: 10px;
    }
    @media (max-width: 700px) {
        .block-container {padding-left: 0.8rem; padding-right: 0.8rem;}
        h1 {font-size: 1.7rem;}
        h2 {font-size: 1.3rem;}
        .card {padding: 15px;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# SUPABASE
# =============================
@st.cache_resource
def conectar_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = conectar_supabase()

# =============================
# FUNÇÕES
# =============================
def gerar_protocolo() -> str:
    return "MAR-" + datetime.now().strftime("%Y%m%d%H%M%S")

@st.cache_data(ttl=20)
def carregar_pendencias() -> pd.DataFrame:
    try:
        res = supabase.table("pendencias_marcos").select("*").order("criado_em", desc=True).execute()
        dados = res.data or []
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

def limpar_cache():
    st.cache_data.clear()

def criar_pendencia(nome: str, cidade: str, comunidade: str, descricao: str):
    dados = {
        "protocolo": gerar_protocolo(),
        "nome_solicitante": nome.strip(),
        "cidade": cidade.strip(),
        "comunidade": comunidade.strip(),
        "descricao": descricao.strip(),
        "status": "Aberta",
        "responsavel": "Marcos",
    }
    res = supabase.table("pendencias_marcos").insert(dados).execute()
    limpar_cache()
    return res.data[0] if res.data else dados

def atualizar_pendencia(item_id: int, status: str, observacao: str):
    dados = {
        "status": status,
        "observacao_retorno": observacao.strip() if observacao else None,
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
    }
    if status == "Concluída":
        dados["concluido_em"] = datetime.now(timezone.utc).isoformat()
    supabase.table("pendencias_marcos").update(dados).eq("id", item_id).execute()
    limpar_cache()


def formatar_data(valor):
    if not valor or pd.isna(valor):
        return "-"
    try:
        return pd.to_datetime(valor).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(valor)


def aplicar_filtros(df: pd.DataFrame, mostrar_concluidas: bool, cidade: str, comunidade: str, status: str) -> pd.DataFrame:
    if df.empty:
        return df
    filtrado = df.copy()
    if not mostrar_concluidas:
        filtrado = filtrado[filtrado["status"].isin(STATUS_ATIVOS)]
    if cidade != "Todas":
        filtrado = filtrado[filtrado["cidade"] == cidade]
    if comunidade != "Todas":
        filtrado = filtrado[filtrado["comunidade"] == comunidade]
    if status != "Todos":
        filtrado = filtrado[filtrado["status"] == status]
    return filtrado


def excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Pendencias")
    return output.getvalue()


def pdf_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    elementos = []
    elementos.append(Paragraph("Relatório de Pendências - Marcos", styles["Title"]))
    elementos.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    if df.empty:
        elementos.append(Paragraph("Nenhuma pendência encontrada.", styles["Normal"]))
    else:
        dados = [["Protocolo", "Cidade", "Comunidade", "Solicitante", "Status", "Abertura"]]
        for _, row in df.iterrows():
            dados.append([
                str(row.get("protocolo", "")),
                str(row.get("cidade", "")),
                str(row.get("comunidade", "")),
                str(row.get("nome_solicitante", "")),
                str(row.get("status", "")),
                formatar_data(row.get("criado_em", "")),
            ])
        tabela = Table(dados, repeatRows=1)
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b4ea2")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
        ]))
        elementos.append(tabela)

    doc.build(elementos)
    return output.getvalue()

# =============================
# APP
# =============================
st.title("✅ Pendências Marcos")
st.caption("Controle de pendências, ações e solicitações por cidade e comunidade.")

df = carregar_pendencias()

menu = st.sidebar.radio(
    "Menu",
    ["Nova Pendência", "Pendências do Marcos", "Relatórios"],
)

if menu == "Nova Pendência":
    st.header("📝 Abrir nova pendência")
    with st.form("form_nova_pendencia", clear_on_submit=True):
        nome = st.text_input("Nome do solicitante")
        cidade = st.text_input("Cidade")
        comunidade = st.text_input("Comunidade")
        descricao = st.text_area("Descrição da pendência", height=140)
        enviado = st.form_submit_button("Abrir pendência", use_container_width=True)

    if enviado:
        if not nome or not cidade or not comunidade or not descricao:
            st.warning("Preencha todos os campos: nome, cidade, comunidade e descrição.")
        else:
            criado = criar_pendencia(nome, cidade, comunidade, descricao)
            st.success(f"Pendência aberta com sucesso. Protocolo: {criado.get('protocolo')}")

elif menu == "Pendências do Marcos":
    st.header("📱 Pendências do Marcos")

    total_abertas = len(df[df["status"] == "Aberta"]) if not df.empty else 0
    total_andamento = len(df[df["status"] == "Em andamento"]) if not df.empty else 0
    total_aguardando = len(df[df["status"] == "Aguardando informação"]) if not df.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Abertas", total_abertas)
    c2.metric("Em andamento", total_andamento)
    c3.metric("Aguardando info.", total_aguardando)

    st.subheader("Filtros")
    mostrar_concluidas = st.checkbox("Mostrar concluídas e canceladas", value=False)

    cidades = ["Todas"] + sorted(df["cidade"].dropna().unique().tolist()) if not df.empty else ["Todas"]
    comunidades = ["Todas"] + sorted(df["comunidade"].dropna().unique().tolist()) if not df.empty else ["Todas"]

    f1, f2, f3 = st.columns(3)
    cidade_filtro = f1.selectbox("Cidade", cidades)
    comunidade_filtro = f2.selectbox("Comunidade", comunidades)
    status_filtro = f3.selectbox("Status", ["Todos"] + STATUS_TODOS)

    filtrado = aplicar_filtros(df, mostrar_concluidas, cidade_filtro, comunidade_filtro, status_filtro)

    if filtrado.empty:
        st.info("Nenhuma pendência encontrada com os filtros selecionados.")
    else:
        for _, row in filtrado.iterrows():
            status = row.get("status", "Aberta")
            classe = "card"
            if status == "Em andamento": classe += " card-andamento"
            if status == "Aguardando informação": classe += " card-aguardando"
            if status == "Concluída": classe += " card-concluida"
            if status == "Cancelada": classe += " card-cancelada"

            st.markdown(f"""
            <div class="{classe}">
                <div><b>{row.get('protocolo', '')}</b> <span class="badge">{status}</span></div>
                <div class="small">Cidade: <b>{row.get('cidade', '')}</b> | Comunidade: <b>{row.get('comunidade', '')}</b></div>
                <div class="small">Solicitante: <b>{row.get('nome_solicitante', '')}</b> | Aberta em: {formatar_data(row.get('criado_em'))}</div>
                <div class="desc">{row.get('descricao', '')}</div>
                <div class="small">Retorno: {row.get('observacao_retorno') or '-'}</div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"Atualizar {row.get('protocolo', '')}"):
                novo_status = st.selectbox(
                    "Novo status",
                    STATUS_TODOS,
                    index=STATUS_TODOS.index(status) if status in STATUS_TODOS else 0,
                    key=f"status_{row['id']}",
                )
                observacao = st.text_area(
                    "Observação / retorno",
                    value=row.get("observacao_retorno") or "",
                    key=f"obs_{row['id']}",
                )
                if st.button("Salvar atualização", key=f"salvar_{row['id']}", use_container_width=True):
                    atualizar_pendencia(int(row["id"]), novo_status, observacao)
                    st.success("Pendência atualizada.")
                    st.rerun()

elif menu == "Relatórios":
    st.header("📊 Relatórios")

    mostrar_concluidas = st.checkbox("Incluir concluídas e canceladas no relatório", value=True)
    cidades = ["Todas"] + sorted(df["cidade"].dropna().unique().tolist()) if not df.empty else ["Todas"]
    comunidades = ["Todas"] + sorted(df["comunidade"].dropna().unique().tolist()) if not df.empty else ["Todas"]

    r1, r2, r3 = st.columns(3)
    cidade_filtro = r1.selectbox("Cidade", cidades, key="rel_cidade")
    comunidade_filtro = r2.selectbox("Comunidade", comunidades, key="rel_comunidade")
    status_filtro = r3.selectbox("Status", ["Todos"] + STATUS_TODOS, key="rel_status")

    filtrado = aplicar_filtros(df, mostrar_concluidas, cidade_filtro, comunidade_filtro, status_filtro)

    st.write(f"Total encontrado: **{len(filtrado)}**")
    st.dataframe(filtrado, use_container_width=True, hide_index=True)

    col_excel, col_pdf = st.columns(2)
    col_excel.download_button(
        "⬇️ Baixar Excel",
        data=excel_bytes(filtrado),
        file_name="relatorio_pendencias_marcos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    col_pdf.download_button(
        "⬇️ Baixar PDF",
        data=pdf_bytes(filtrado),
        file_name="relatorio_pendencias_marcos.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
