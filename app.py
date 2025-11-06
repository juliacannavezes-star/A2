import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Perfil da Advocacia Brasileira")

st.title("📊 Perfil da Advocacia Brasileira — Visualização Interativa")
st.markdown("""
Este aplicativo apresenta gráficos com base nos dados divulgados pela OAB sobre o perfil da advocacia brasileira.
Você pode usar o arquivo padrão (`perfil_adv.csv`) ou enviar outro arquivo CSV/Excel no menu lateral.
""")

@st.cache_data
def load_data(file):
    if file is None:
        return pd.read_csv("perfil_adv.csv", sep=";")
    else:
        name = file.name.lower()
        if name.endswith(".csv"):
            try:
                return pd.read_csv(file, sep=";")
            except:
                return pd.read_csv(file, sep=",")
        else:
            return pd.read_excel(file)

# → UPLOAD OPCIONAL
file = st.sidebar.file_uploader("📎 Enviar outro arquivo CSV ou Excel", type=["csv","xlsx","xls"])
df = load_data(file)

# → REMOVE Indicadores indesejados
indicadores_ocultos = ["Média de idade", "Tempo médio de atuação", "media de idade", "tempo medio de atuação"]
df = df[~df["Indicador"].isin(indicadores_ocultos)]

# → MENU SELEÇÃO DE INDICADOR
st.sidebar.markdown("### 🔍 Filtro")
indicadores = sorted(df["Indicador"].unique())
indicador = st.sidebar.selectbox("Escolha o indicador:", indicadores)

df_sel = df[df["Indicador"] == indicador].copy()

# → Função inteligente para converter percentuais e números
def parse_value(x):
    if pd.isna(x):
        return None
    s = str(x).strip().lower()
    if "%" in s:
        return float(s.replace("%","").replace(",","."))
    try:
        return float(s.replace(",","."))
    except:
        return None

# → Converte todas as colunas numéricas
for col in df_sel.columns:
    if col not in ["Indicador", "Categoria"]:
        df_sel[col + "_num"] = df_sel[col].apply(parse_value)

# → Prepara dados para o gráfico
value_cols = [c for c in df_sel.columns if c.endswith("_num")]
plot = df_sel.melt(id_vars="Categoria", value_vars=value_cols, var_name="Grupo", value_name="Percentual")
plot["Grupo"] = plot["Grupo"].str.replace("_num","")

# → Gráfico
st.header(f"Indicador: **{indicador}**")

fig = px.bar(plot, x="Categoria", y="Percentual", color="Grupo", barmode="group", text="Percentual")
fig.update_layout(xaxis_tickangle=-45, yaxis_title="Percentual (%)")
st.plotly_chart(fig, use_container_width=True)

# → Tabela
st.subheader("📄 Dados utilizados")
st.dataframe(df_sel)

# → Download CSV
csv = df_sel.to_csv(index=False, sep=";").encode("utf-8")
st.download_button("⬇️ Baixar dados filtrados (CSV)", csv, "dados_filtrados.csv", "text/csv")

st.markdown("---")
st.caption("Fonte: OAB — Aplicativo desenvolvido para análise e promoção da diversidade na advocacia.")
