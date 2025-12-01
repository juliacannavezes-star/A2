import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- CONFIGURAÇÃO ---------------- #
st.set_page_config(
    page_title="Perfil da Advocacia Brasileira",
    layout="wide"
)

st.title("📊 Perfil da Advocacia Brasileira")
st.markdown("""
Análise interativa de dados públicos da **Ordem dos Advogados do Brasil (OAB)**,
com foco em indicadores demográficos e profissionais.

O objetivo é **compreender padrões**, **identificar desigualdades estruturais**
e **estimular reflexão crítica** sobre a advocacia no Brasil.
""")

# ---------------- CARREGAMENTO ---------------- #
@st.cache_data
def load_data():
    return pd.read_csv("perfil_adv.csv", sep=";")

df = load_data()

# ---------------- LIMPEZA ---------------- #
df.columns = ["Indicador", "Categoria", "Valor"]

def parse_percent(x):
    try:
        return float(str(x).replace("%", "").replace(",", "."))
    except:
        return None

df["Valor"] = df["Valor"].apply(parse_percent)

df = df.dropna(subset=["Valor"])

# ---------------- FILTROS ---------------- #
st.sidebar.header("🔎 Filtros")

indicador = st.sidebar.selectbox(
    "Indicador",
    sorted(df["Indicador"].unique())
)

df_ind = df[df["Indicador"] == indicador]

categorias = sorted(df_ind["Categoria"].unique())

categoria_sel = st.sidebar.multiselect(
    "Categorias",
    categorias,
    default=categorias
)

df_filtrado = df_ind[df_ind["Categoria"].isin(categoria_sel)]

# ---------------- SEPARAÇÃO DO TOTAL ---------------- #
df_total = df_filtrado[df_filtrado["Categoria"].str.contains("Total", case=False)]
df_cat = df_filtrado[~df_filtrado["Categoria"].str.contains("Total", case=False)]

# ---------------- VISÃO GERAL ---------------- #
st.subheader(f"📌 {indicador}")

if not df_total.empty:
    st.metric(
        label="🔹 Percentual Total",
        value=f"{df_total['Valor'].iloc[0]:.1f}%"
    )

# ---------------- GRÁFICO PRINCIPAL ---------------- #
fig_bar = px.bar(
    df_cat,
    x="Categoria",
    y="Valor",
    text=df_cat["Valor"].map(lambda x: f"{x:.1f}%"),
    title="Distribuição Percentual por Categoria",
    labels={"Valor": "Percentual (%)"},
)

fig_bar.update_layout(
    xaxis_tickangle=-30,
    uniformtext_minsize=10,
    uniformtext_mode='hide'
)

st.plotly_chart(fig_bar, use_container_width=True)

# ---------------- ANÁLISE ESTATÍSTICA ---------------- #
st.subheader("📈 Análise Estatística")

col1, col2, col3 = st.columns(3)

col1.metric("Média", f"{df_cat['Valor'].mean():.1f}%")
col2.metric("Máximo", f"{df_cat['Valor'].max():.1f}%")
col3.metric("Mínimo", f"{df_cat['Valor'].min():.1f}%")

# ---------------- BOXPLOT ---------------- #
fig_box = px.box(
    df_cat,
    y="Valor",
    title="Distribuição Estatística das Categorias",
    labels={"Valor": "Percentual (%)"}
)

st.plotly_chart(fig_box, use_container_width=True)

# ---------------- TABELA ---------------- #
st.subheader("📄 Dados Filtrados")
st.dataframe(df_cat.sort_values(by="Valor", ascending=False))

# ---------------- DOWNLOAD ---------------- #
st.download_button(
    "⬇️ Baixar CSV",
    df_cat.to_csv(index=False, sep=";").encode("utf-8"),
    "dados_filtrados.csv",
    "text/csv"
)

# ---------------- RODAPÉ ---------------- #
st.markdown("---")
st.caption("Fonte: Ordem dos Advogados do Brasil (OAB) | Projeto acadêmico de visualização de dados.")
