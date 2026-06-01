import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, date
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Pendências Marcos", page_icon="✅", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

STATUS_ATIVOS = ["Aberta", "Em andamento", "Aguardando informação"]
TODOS_STATUS = STATUS_ATIVOS + ["Concluída", "Cancelada"]

st.markdown("""
<style>
.block-container {padding-top: 2rem; max-width: 1100px;}
.card {background:#fff; border:1px solid #e5e7eb; border-radius:16px; padding:16px; margin-bottom:14px; box-shadow:0 1px 8px rgba(0,0,0,.04)}
.badge {padding:5px 10px; border-radius:14px; font-weight:700; font-size:13px;}
.aberta {background:#dbeafe;color:#1d4ed8}.andamento{background:#ffedd5;color:#c2410c}.aguardando{background:#ede9fe;color:#6d28d9}.concluida{background:#dcfce7;color:#15803d}.cancelada{background:#fee2e2;color:#b91c1c}
@media(max-width:768px){.block-container{padding:1rem}.stButton button{width:100%;height:44px}.stTextInput input{height:44px}}
</style>
""", unsafe_allow_html=True)


def gerar_protocolo():
    return "MAR-" + datetime.now().strftime("%Y%m%d%H%M%S")


def carregar_pendencias():
    res = supabase.table("pendencias_marcos").select("*").order("criado_em", desc=True).execute()
    return pd.DataFrame(res.data or [])


def inserir_pendencia(nome, cidade, comunidade, descricao):
    protocolo = gerar_protocolo()
    dados = {
        "protocolo": protocolo,
        "nome_solicitante": nome.strip(),
        "cidade": cidade.strip(),
        "comunidade": comunidade.strip(),
        "descricao": descricao.strip(),
        "status": "Aberta",
        "responsavel": "Marcos",
    }
    supabase.table("pendencias_marcos").insert(dados).execute()
    return protocolo


def atualizar_pendencia(id_pendencia, status, observacao):
    dados = {"status": status, "observacao_retorno": observacao, "atualizado_em": datetime.utcnow().isoformat()}
    if status == "Concluída":
        dados["concluido_em"] = datetime.utcnow().isoformat()
    supabase.table("pendencias_marcos").update(dados).eq("id", id_pendencia).execute()


def gerar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Pendencias")
    output.seek(0)
    return output


def gerar_pdf(df):
    output = BytesIO()
    c = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    y = height - 45
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Relatório de Pendências - Marcos")
    y -= 30
    c.setFont("Helvetica", 9)
    for _, row in df.iterrows():
        if y < 80:
            c.showPage(); y = height - 45; c.setFont("Helvetica", 9)
        texto = f"{row.get('protocolo','')} | {row.get('status','')} | {row.get('cidade','')} | {row.get('comunidade','')} | {row.get('nome_solicitante','')}"
        c.drawString(40, y, texto[:120]); y -= 14
        desc = str(row.get('descricao','')).replace('\n',' ')
        c.drawString(55, y, desc[:110]); y -= 22
    c.save(); output.seek(0)
    return output


def status_classe(status):
    return {
        "Aberta":"aberta", "Em andamento":"andamento", "Aguardando informação":"aguardando",
        "Concluída":"concluida", "Cancelada":"cancelada"
    }.get(status, "aberta")

st.title("✅ Pendências Marcos")
st.caption("Controle de pendências, ações e solicitações por cidade e comunidade.")

menu = st.sidebar.radio("Menu", ["➕ Abrir Pendência", "📋 Painel do Marcos", "📊 Relatórios / Admin"])

if menu == "➕ Abrir Pendência":
    st.header("📝 Abrir nova pendência")
    with st.form("form_pendencia"):
        nome = st.text_input("Nome do solicitante")
        cidade = st.text_input("Cidade")
        comunidade = st.text_input("Comunidade")
        descricao = st.text_area("Descrição da pendência", height=130)
        enviar = st.form_submit_button("Abrir pendência")
    if enviar:
        if not nome or not cidade or not comunidade or not descricao:
            st.warning("Preencha todos os campos.")
        else:
            protocolo = inserir_pendencia(nome, cidade, comunidade, descricao)
            st.success(f"Pendência aberta com sucesso. Protocolo: {protocolo}")

elif menu == "📋 Painel do Marcos":
    st.header("📋 Painel do Marcos")
    df = carregar_pendencias()
    if df.empty:
        st.info("Nenhuma pendência cadastrada.")
        st.stop()

    mostrar_concluidas = st.toggle("Mostrar concluídas e canceladas", value=False)
    cidades = ["Todas"] + sorted(df["cidade"].dropna().unique().tolist())
    comunidades = ["Todas"] + sorted(df["comunidade"].dropna().unique().tolist())
    col1, col2, col3 = st.columns(3)
    cidade_f = col1.selectbox("Filtrar por cidade", cidades)
    comunidade_f = col2.selectbox("Filtrar por comunidade", comunidades)
    status_opcoes = TODOS_STATUS if mostrar_concluidas else STATUS_ATIVOS
    status_f = col3.multiselect("Status", status_opcoes, default=status_opcoes)

    dff = df.copy()
    if not mostrar_concluidas:
        dff = dff[dff["status"].isin(STATUS_ATIVOS)]
    if cidade_f != "Todas": dff = dff[dff["cidade"] == cidade_f]
    if comunidade_f != "Todas": dff = dff[dff["comunidade"] == comunidade_f]
    if status_f: dff = dff[dff["status"].isin(status_f)]

    c1, c2, c3 = st.columns(3)
    c1.metric("Abertas", int((df["status"] == "Aberta").sum()))
    c2.metric("Em andamento", int((df["status"] == "Em andamento").sum()))
    c3.metric("Aguardando info.", int((df["status"] == "Aguardando informação").sum()))

    for _, row in dff.iterrows():
        with st.container():
            st.markdown(f"""
            <div class='card'>
                <b style='font-size:18px;color:#0f172a'>{row.get('protocolo','')}</b>
                <span class='badge {status_classe(row.get('status',''))}' style='float:right'>{row.get('status','')}</span><br><br>
                <b>Cidade:</b> {row.get('cidade','')} &nbsp; | &nbsp; <b>Comunidade:</b> {row.get('comunidade','')}<br>
                <b>Solicitante:</b> {row.get('nome_solicitante','')}<br><br>
                {row.get('descricao','')}
            </div>
            """, unsafe_allow_html=True)
            with st.expander("Atualizar esta pendência"):
                novo_status = st.selectbox("Novo status", TODOS_STATUS, index=TODOS_STATUS.index(row.get("status", "Aberta")), key=f"st_{row['id']}")
                obs = st.text_area("Observação / retorno", value=row.get("observacao_retorno") or "", key=f"obs_{row['id']}")
                if st.button("Salvar atualização", key=f"btn_{row['id']}"):
                    atualizar_pendencia(row["id"], novo_status, obs)
                    st.success("Pendência atualizada.")
                    st.rerun()

elif menu == "📊 Relatórios / Admin":
    st.header("📊 Relatórios / Admin")
    df = carregar_pendencias()
    if df.empty:
        st.info("Nenhuma pendência cadastrada.")
        st.stop()
    col1, col2, col3 = st.columns(3)
    cidade_f = col1.selectbox("Cidade", ["Todas"] + sorted(df["cidade"].dropna().unique().tolist()))
    comunidade_f = col2.selectbox("Comunidade", ["Todas"] + sorted(df["comunidade"].dropna().unique().tolist()))
    status_f = col3.multiselect("Status", TODOS_STATUS, default=TODOS_STATUS)
    dff = df.copy()
    if cidade_f != "Todas": dff = dff[dff["cidade"] == cidade_f]
    if comunidade_f != "Todas": dff = dff[dff["comunidade"] == comunidade_f]
    if status_f: dff = dff[dff["status"].isin(status_f)]
    st.dataframe(dff, use_container_width=True)
    st.download_button("⬇️ Baixar Excel", data=gerar_excel(dff), file_name="pendencias_marcos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button("⬇️ Baixar PDF", data=gerar_pdf(dff), file_name="pendencias_marcos.pdf", mime="application/pdf")
