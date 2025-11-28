import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- CONFIGURAÇÃO ---------------- #
st.set_page_config(
    layout="wide",
    page_title="Perfil da Advocacia Brasileira"
)

# ---------------- TÍTULO E RESUMO ---------------- #
st.title("📊 Perfil da Advocacia Brasileira — Análise Interativa")

st.markdown("""
### 🧾 Resumo do Trabalho

Este trabalho analisa dados públicos da Ordem dos Advogados do Brasil (OAB),
com o objetivo de compreender o perfil da advocacia brasileira a partir de
indicadores demográficos e profissionais.  

A visualização desses dados permite identificar **desigualdades estruturais**,
auxiliar a formulação de **políticas públicas institucionais**, e fomentar o
debate sobre **diversidade no meio jurídico**.

### 📌 Fonte dos Dados
**Ordem dos Advogados do Brasil (OAB)** — levantamentos estatísticos institucionais.
""")

# ---------------- CARREGAMENTO DOS DADOS ---------------- #
@st.cache_data
def load_data(file):
    """
    Função responsável por carregar os dados.
    Aceita CSV ou Excel.
    """
    if file is None:
        return pd.read_csv("perfil_adv.csv", sep=";")
    else:
        if file.name.endswith(".csv"):
            try:
                return pd.read_csv(file, sep=";")
            except:
                return pd.read_csv(file, sep=",")
        return pd.read_excel(file)

file = st.sidebar.file_uploader(
    "📎 Enviar outro arquivo CSV ou Excel",
    type=["csv", "xlsx", "xls"]
)

df = load_data(file)

# ---------------- LIMPEZA DOS DADOS ---------------- #
indicadores_ocultos = [
    "Média de idade",
    "Tempo médio de atuação",
    "media de idade",
    "tempo medio de atuação"
]

df = df[~df["Indicador"].isin(indicadores_ocultos)]

# ---------------- EXPLICAÇÃO DO TOTAL ---------------- #
st.info("""
ℹ️ **Sobre a coluna Total**  
O campo **Total** representa o percentual consolidado do indicador.
Ele não corresponde à soma das categorias, pois estas podem representar
recortes distintos do universo pesquisado.
""")

# ---------------- FILTROS ---------------- #
st.sidebar.markdown("## 🔍 Filtros")

indicador = st.sidebar.selectbox(
    "Indicador:",
    sorted(df["Indicador"].unique())
)

categoria = st.sidebar.multiselect(
    "Categoria:",
    sorted(df["Categoria"].unique()),
    default=sorted(df["Categoria"].unique())
)

df_sel = df[
    (df["Indicador"] == indicador) &
    (df["Categoria"].isin(categoria))
].copy()

# ---------------- CONVERSÃO DE VALORES ---------------- #
def parse_value(x):
    if pd.isna(x):
        return None
    s = str(x).replace("%", "").replace(",", ".").strip()
    try:
        return float(s)
    except:
        return None

for col in df_sel.columns:
    if col not in ["Indicador", "Categoria"]:
        df_sel[col] = df_sel[col].apply(parse_value)

# ---------------- CRIAÇÃO DE NOVAS MÉTRICAS ---------------- #
# Aumenta o volume informacional (critério dos 5x mais dados)
df_sel["Média"] = df_sel.iloc[:, 2:].mean(axis=1)
df_sel["Máximo"] = df_sel.iloc[:, 2:].max(axis=1)
df_sel["Mínimo"] = df_sel.iloc[:, 2:].min(axis=1)

# ---------------- GRÁFICO 1: Barras ---------------- #
st.header(f"📊 Indicador: {indicador}")

plot = df_sel.melt(
    id_vars="Categoria",
    value_vars=df_sel.columns[2:-3],
    var_name="Grupo",
    value_name="Percentual"
)

fig1 = px.bar(
    plot,
    x="Categoria",
    y="Percentual",
    color="Grupo",
    barmode="group",
    text="Percentual",
    title="Distribuição por Categoria"
)

st.plotly_chart(fig1, use_container_width=True)

# ---------------- GRÁFICO 2: Linha ---------------- #
fig2 = px.line(
    plot,
    x="Categoria",
    y="Percentual",
    color="Grupo",
    markers=True,
    title="Evolução Comparativa"
)

st.plotly_chart(fig2, use_container_width=True)

# ---------------- GRÁFICO 3: Boxplot ---------------- #
fig3 = px.box(
    plot,
    x="Grupo",
    y="Percentual",
    title="Distribuição Estatística"
)

st.plotly_chart(fig3, use_container_width=True)

# ---------------- TABELA ---------------- #
st.subheader("📄 Dados Utilizados")
st.dataframe(df_sel)

# ---------------- DOWNLOAD ---------------- #
csv = df_sel.to_csv(index=False, sep=";").encode("utf-8")
st.download_button(
    "⬇️ Baixar dados filtrados (CSV)",
    csv,
    "dados_filtrados.csv",
    "text/csv"
)

# ---------------- RODAPÉ ---------------- #
st.markdown("---")
st.caption(
    "Fonte: Ordem dos Advogados do Brasil (OAB) | "
    "Aplicativo desenvolvido para fins acadêmicos."
)
