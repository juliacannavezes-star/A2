# app.py
import streamlit as st
import plotly.express as px
import pandas as pd
import pydeck as pdk
from utils import read_primary_dataframe

st.set_page_config(page_title="Perfil da Advocacia - Visualizador", layout="wide")

st.title("Perfil Demográfico da Advocacia Brasileira")
st.markdown("""
Aplicativo interativo que mostra composição por sexo, raça/cor, faixas etárias e distribuição regional.
Fonte dos dados: Perfil ADV — Estudo Demográfico da Advocacia Brasileira (OAB/FGV) e arquivos anexos. 
""")

@st.cache_data(show_spinner=False)
def load_data():
    df = read_primary_dataframe("data")
    return df

df = load_data()

st.sidebar.header("Filtros")
# filtros dinâmicos
sexo_sel = st.sidebar.multiselect("Sexo / Gênero", options=sorted(df["sexo"].dropna().unique()), default=sorted(df["sexo"].dropna().unique()))
cor_sel = st.sidebar.multiselect("Raça / Cor", options=sorted(df["cor_raca"].dropna().unique()), default=sorted(df["cor_raca"].dropna().unique()))
regiao_sel = st.sidebar.multiselect("Região", options=sorted(df["regiao"].dropna().unique()), default=sorted(df["regiao"].dropna().unique()))

# aplicar filtros
df_filt = df[df["sexo"].isin(sexo_sel) & df["cor_raca"].isin(cor_sel) & df["regiao"].isin(regiao_sel)]

# resumo numérico
col1, col2, col3 = st.columns(3)
col1.metric("Total de respondentes", df_filt.shape[0])
col2.metric("Média de idade (aprox.)", f"{int(df_filt['idade'].mean()):d}" if "idade" in df_filt.columns and not df_filt['idade'].isna().all() else "N/A")
col3.metric("Regiões selecionadas", len(df_filt["regiao"].unique()))

# Gráficos interativos
st.markdown("## Composição por Sexo")
fig_sexo = px.pie(df_filt, names="sexo", title="Distribuição por sexo", hole=0.35)
st.plotly_chart(fig_sexo, use_container_width=True)

st.markdown("## Composição por Raça/Cor")
fig_raca = px.bar(df_filt["cor_raca"].value_counts().reset_index().rename(columns={"index":"cor_raca","cor_raca":"count"}),
                  x="cor_raca", y="count", title="Contagem por raça/cor")
st.plotly_chart(fig_raca, use_container_width=True)

st.markdown("## Faixa etária")
if "faixa_etaria" in df_filt.columns:
    fig_faixa = px.histogram(df_filt, x="faixa_etaria", title="Distribuição por faixa etária", category_orders={"faixa_etaria": ["<=24","25-34","35-44","45-54","55-64","65+"]})
    st.plotly_chart(fig_faixa, use_container_width=True)
else:
    st.info("Coluna 'idade' não encontrada — não foi possível calcular faixas etárias.")

st.markdown("## Mapa / Distribuição regional")
# mapa por UF (se coluna 'uf' existir)
if "uf" in df_filt.columns:
    # agregação por UF
    agg = df_filt.groupby("uf").size().reset_index(name="count")
    # mapear sigla para centroide lat/lon (dicionário mínimo). Usuário pode substituir por base oficial.
    centroids = {
        "SP":(-23.5505, -46.6333),
        "RJ":(-22.9068, -43.1729),
        "MG":(-19.9191, -43.9386),
        "BA":(-12.9714, -38.5014),
        "DF":(-15.7942, -47.8822)
        # (adicionar todas as UFs conforme necessidade)
    }
    agg["lat"] = agg["uf"].map(lambda u: centroids.get(u, (None,None))[0])
    agg["lon"] = agg["uf"].map(lambda u: centroids.get(u, (None,None))[1])

    agg = agg.dropna(subset=["lat","lon"])
    if not agg.empty:
        st.write("Mapa pontual (centro aproximado por UF).")
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=agg,
            get_position='[lon, lat]',
            get_color='[200, 30, 0, 160]',
            get_radius='count*2000',
            pickable=True
        )
        view_state = pdk.ViewState(latitude= -15.0, longitude=-50.0, zoom=3)
        r = pdk.Deck(layers=[layer], initial_view_state=view_state, map_style='light')
        st.pydeck_chart(r)
    else:
        st.info("Não há centroides para as UFs encontradas. Atualize o dicionário de centroides no código.")

else:
    # fallback: mapa por região usando barras
    st.info("Coluna 'uf' não disponível. Exibindo distribuição por região.")
    fig_reg = px.bar(df_filt["regiao"].value_counts().reset_index().rename(columns={"index":"regiao","regiao":"count"}), x="regiao", y="count", title="Distribuição por região")
    st.plotly_chart(fig_reg, use_container_width=True)

# relatório automático (download)
st.markdown("## Relatório resumido")
def build_summary(df_summary):
    lines = []
    lines.append(f"Total respondentes: {df_summary.shape[0]}")
    if "sexo" in df_summary.columns:
        lines.append("\nDistribuição por sexo:")
        lines += [f" - {k}: {v}" for k,v in df_summary["sexo"].value_counts().items()]
    if "cor_raca" in df_summary.columns:
        lines.append("\nDistribuição por raça/cor:")
        lines += [f" - {k}: {v}" for k,v in df_summary["cor_raca"].value_counts().items()]
    if "faixa_etaria" in df_summary.columns:
        lines.append("\nFaixas etárias:")
        lines += [f" - {k}: {v}" for k,v in df_summary["faixa_etaria"].value_counts().sort_index().items()]
    return "\n".join(lines)

summary_text = build_summary(df_filt)
st.text_area("Resumo estatístico", value=summary_text, height=220)

# botão para baixar CSV filtrado
csv = df_filt.to_csv(index=False).encode('utf-8')
st.download_button("Baixar dados filtrados (CSV)", data=csv, file_name="perfil_adv_filtrado.csv", mime="text/csv")

st.markdown("---")
st.caption("Fonte: Perfil ADV — Estudo Demográfico da Advocacia Brasileira (dados anexos).")
