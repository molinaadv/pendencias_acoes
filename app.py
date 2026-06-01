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
    layout="wide"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TABELA = "pendencias_acoes"

STATUS_ATIVOS = ["Aberta", "Em andamento", "Aguardando informação"]
TODOS_STATUS = ["Aberta", "Em andamento", "Aguardando informação", "Concluída", "Cancelada"]

st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    max-width: 1100px;
}

.card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 14px;
    box-shadow: 0 1px 8px rgba(0,0,0,.04);
}

.badge {
    padding: 5px 10px;
    border-radius: 14px;
    font-weight: 700;
    font-size: 13px;
}

.aberta {
    background: #dbeafe;
    color: #1d4ed8;
}

.andamento {
    background: #ffedd5;
    color: #c2410c;
}

.aguardando {
    background: #ede9fe;
    color: #6d28d9;
}

.concluida {
    background: #dcfce7;
    color: #15803d;
}

.cancelada {
    background: #fee2e2;
    color: #b91c1c;
}

@media(max-width:768px) {
    .block-container {
        padding: 1rem;
    }

    .stButton button {
        width: 100%;
        height: 44px;
    }

    .stTextInput input {
        height: 44px;
    }
}
</style>
""", unsafe_allow_html=True)


def gerar_protocolo():
    return "PA-" + datetime.now().strftime("%Y%m%d%H%M%S")


def carregar_pendencias():
    try:
        res = (
            supabase
            .table(TABELA)
            .select("*")
            .order("criado_em", desc=True)
            .execute()
        )
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

        linha = (
            f"{row.get('protocolo', '')} | "
            f"{row.get('status', '')} | "
            f"{row.get('cidade', '')} | "
            f"{row.get('comunidade', '')} | "
            f"{row.get('nome_solicitante', '')}"
        )

        c.drawString(40, y, linha[:120])
        y -= 14

        descricao = str(row.get("descricao", "")).replace("\n", " ")
        c.drawString(55, y, descricao[:110])
        y -= 22

    c.save()
    output.seek(0)
    return output


def status_classe(status):
    mapa = {
        "Aberta": "aberta",
        "Em andamento": "andamento",
        "Aguardando informação": "aguardando",
        "Concluída": "concluida",
        "Cancelada": "cancelada"
    }

    return mapa.get(status, "aberta")


st.title("✅ Pendências Ações")
st.caption("Controle de pendências, ações e solicitações por cidade e comunidade.")

menu = st.sidebar.radio(
    "Menu",
    [
        "➕ Abrir Pendência",
        "📋 Painel de Pendências",
        "📊 Relatórios / Admin"
    ]
)

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
            try:
                protocolo = inserir_pendencia(nome, cidade, comunidade, descricao)
                st.success(f"Pendência aberta com sucesso. Protocolo: {protocolo}")
            except Exception as e:
                st.error(f"Erro ao abrir pendência: {e}")


elif menu == "📋 Painel de Pendências":
    st.header("📋 Painel de Pendências")

    df = carregar_pendencias()

    if df.empty:
        st.info("Nenhuma pendência cadastrada.")
        st.stop()

    mostrar_concluidas = st.toggle(
        "Mostrar concluídas e canceladas",
        value=False
    )

    cidades = ["Todas"] + sorted(df["cidade"].dropna().unique().tolist())
    comunidades = ["Todas"] + sorted(df["comunidade"].dropna().unique().tolist())

    col1, col2, col3 = st.columns(3)

    cidade_f = col1.selectbox("Filtrar por cidade", cidades)
    comunidade_f = col2.selectbox("Filtrar por comunidade", comunidades)

    status_opcoes = TODOS_STATUS if mostrar_concluidas else STATUS_ATIVOS
    status_f = col3.multiselect(
        "Status",
        status_opcoes,
        default=status_opcoes
    )

    dff = df.copy()

    if not mostrar_concluidas:
        dff = dff[dff["status"].isin(STATUS_ATIVOS)]

    if cidade_f != "Todas":
        dff = dff[dff["cidade"] == cidade_f]

    if comunidade_f != "Todas":
        dff = dff[dff["comunidade"] == comunidade_f]

    if status_f:
        dff = dff[dff["status"].isin(status_f)]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Abertas", int((df["status"] == "Aberta").sum()))
    c2.metric("Em andamento", int((df["status"] == "Em andamento").sum()))
    c3.metric("Aguardando info.", int((df["status"] == "Aguardando informação").sum()))
    c4.metric("Concluídas", int((df["status"] == "Concluída").sum()))

    st.divider()

    if dff.empty:
        st.warning("Nenhuma pendência encontrada com os filtros selecionados.")
    else:
        for _, row in dff.iterrows():
            with st.container():
                st.markdown(f"""
                <div class='card'>
                    <b style='font-size:18px;color:#0f172a'>{row.get('protocolo', '')}</b>
                    <span class='badge {status_classe(row.get('status', ''))}' style='float:right'>
                        {row.get('status', '')}
                    </span>
                    <br><br>
                    <b>Cidade:</b> {row.get('cidade', '')}
                    &nbsp; | &nbsp;
                    <b>Comunidade:</b> {row.get('comunidade', '')}
                    <br>
                    <b>Solicitante:</b> {row.get('nome_solicitante', '')}
                    <br><br>
                    {row.get('descricao', '')}
                </div>
                """, unsafe_allow_html=True)

                with st.expander("Atualizar esta pendência"):
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
                        try:
                            atualizar_pendencia(row["id"], novo_status, obs)
                            st.success("Pendência atualizada.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar pendência: {e}")


elif menu == "📊 Relatórios / Admin":
    st.header("📊 Relatórios / Admin")

    df = carregar_pendencias()

    if df.empty:
        st.info("Nenhuma pendência cadastrada.")
        st.stop()

    col1, col2, col3 = st.columns(3)

    cidade_f = col1.selectbox(
        "Cidade",
        ["Todas"] + sorted(df["cidade"].dropna().unique().tolist())
    )

    comunidade_f = col2.selectbox(
        "Comunidade",
        ["Todas"] + sorted(df["comunidade"].dropna().unique().tolist())
    )

    status_f = col3.multiselect(
        "Status",
        TODOS_STATUS,
        default=TODOS_STATUS
    )

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
