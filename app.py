import streamlit as st
import pandas as pd
import plotly.express as px
import io
from utils import normalize_columns, ensure_age_groups, ensure_region, make_summary

st.set_page_config(layout="wide", page_title="Perfil da Advocacia — Dashboard")

st.title("Perfil da Advocacia Brasileira — Dashboard interativo")
st.markdown("""
Este app apresenta gráficos interativos a partir de dados do Estudo Demográfico da Advocacia (PerfilAdv).
Fonte: OAB / PerfilAdv (dados divulgados em 28/11/2023).  
Você pode fazer upload de um arquivo CSV / Excel contendo colunas como: `sexo`, `cor/raça`, `idade`, `estado`/`localidade`, `tempo_de_atuacao`.
""")

# upload / sample
st.sidebar.header("Dados")
uploaded = st.sidebar.file_uploader("Faça upload do CSV ou Excel com os dados (ou use amostra)", type=['csv', 'xlsx', 'xls'])
use_sample = st.sidebar.button("Usar dados de amostra do PerfilAdv (pequeno)")

def load_sample():
    # exemplo muito simples - substitua por seu CSV real
    data = {
        'sexo': ['Feminino']*55 + ['Masculino']*45,
        'cor/raça': ['Branca']*65 + ['Parda']*25 + ['Preta']*8 + ['Amarela']*1 + ['Indígena']*1,
        'idade': [30]*30 + [40]*30 + [28]*20 + [50]*20,
        'estado': ['SP']*40 + ['RJ']*20 + ['MG']*15 + ['BA']*10 + ['RS']*10 + ['PA']*5,
        'tempo_de_atuacao': [3]*40 + [12]*30 + [25]*20 + [6]*10,
        'ramo': ['Civil']*40 + ['Trabalhista']*20 + ['Previdenciario']*15 + ['Familia']*25
    }
    return pd.DataFrame(data)

if use_sample:
    df = load_sample()
elif uploaded is not None:
    try:
        if uploaded.type.startswith("text") or uploaded.name.endswith('.csv'):
            df = pd.read_csv(uploaded, encoding='utf-8', sep=None, engine='python')
        else:
            df = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        st.stop()
else:
    st.info("Faça upload de um arquivo CSV/Excel no menu lateral ou clique em 'Usar dados de amostra' para testar o app.")
    st.stop()

# limpeza e padronização
df = normalize_columns(df)
df = ensure_age_groups(df)
df = ensure_region(df)

# filtros
st.sidebar.header("Filtros")
gender_options = ['Todos']
if 'gender' in df.columns:
    gender_options = ['Todos'] + sorted(df['gender'].dropna().unique().tolist())
selected_gender = st.sidebar.selectbox("Gênero", gender_options)

region_options = ['Todos']
if 'region' in df.columns:
    region_options = ['Todos'] + sorted(df['region'].dropna().unique().tolist())
selected_region = st.sidebar.selectbox("Região", region_options)

age_groups = ['Todos']
if 'age_group' in df.columns:
    age_groups = ['Todos'] + sorted(df['age_group'].astype(str).dropna().unique().tolist())
selected_age = st.sidebar.selectbox("Faixa etária", age_groups)

# aplica filtros
df_filtered = df.copy()
if selected_gender != 'Todos':
    df_filtered = df_filtered[df_filtered['gender'] == selected_gender]
if selected_region != 'Todos':
    df_filtered = df_filtered[df_filtered['region'] == selected_region]
if selected_age != 'Todos':
    df_filtered = df_filtered[df_filtered['age_group'].astype(str) == selected_age]

st.markdown("## Visão Geral")
col1, col2, col3 = st.columns(3)
col1.metric("Registros (filtrados)", str(len(df_filtered)))
if 'gender' in df_filtered.columns:
    col2.metric("Gênero majoritário", df_filtered['gender'].mode().iat[0] if len(df_filtered)>0 and not df_filtered['gender'].mode().empty else "—")
if 'region' in df_filtered.columns:
    col3.metric("Região majoritária", df_filtered['region'].mode().iat[0] if len(df_filtered)>0 and not df_filtered['region'].mode().empty else "—")

# gráficos principais
st.markdown("### Distribuições")

charts_col1, charts_col2 = st.columns([1,1])

with charts_col1:
    if 'gender' in df_filtered.columns:
        fig = px.pie(df_filtered, names='gender', title='Distribuição por gênero', hole=.3)
        st.plotly_chart(fig, use_container_width=True)

    if 'race' in df_filtered.columns:
        fig = px.bar(df_filtered['race'].value_counts().reset_index().rename(columns={'index':'race','race':'count'}), 
                     x='race', y='count', title='Distribuição por raça/cor')
        st.plotly_chart(fig, use_container_width=True)

with charts_col2:
    if 'age' in df_filtered.columns:
        fig = px.histogram(df_filtered, x='age', nbins=20, title='Histograma de idades')
        st.plotly_chart(fig, use_container_width=True)
    elif 'age_group' in df_filtered.columns:
        fig = px.bar(df_filtered['age_group'].value_counts().sort_index().reset_index().rename(columns={'index':'age_group','age_group':'count'}), 
                     x='age_group', y='count', title='Faixas etárias')
        st.plotly_chart(fig, use_container_width=True)

# mapa/regioes
st.markdown("### Composição por região / estado")
map_col1, map_col2 = st.columns([2,1])
with map_col1:
    if 'state' in df_filtered.columns or 'region' in df_filtered.columns:
        # mostra contagem por estado se existir
        if 'state' in df_filtered.columns:
            counts = df_filtered['state'].fillna('Não informado').value_counts().reset_index().rename(columns={'index':'state','state':'count'})
            fig = px.bar(counts, x='state', y='count', title='Advogados por estado (contagem)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            counts = df_filtered['region'].fillna('Não informado').value_counts().reset_index().rename(columns={'index':'region','region':'count'})
            fig = px.bar(counts, x='region', y='count', title='Advogados por região (contagem)')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem coluna 'state' ou 'region' para mapa. Se possível, inclua uma coluna 'estado' ou 'state' com as siglas (ex: SP, RJ).")

with map_col2:
    if 'practice_area' in df_filtered.columns:
        top = df_filtered['practice_area'].value_counts().head(8).reset_index().rename(columns={'index':'area','practice_area':'count'})
        st.table(top)
    else:
        st.info("Sem coluna 'practice_area' (ramo) — carregue caso queira ver as áreas de atuação.")

# resumo estatístico e download
st.markdown("## Relatório resumido")
summary_df = make_summary(df_filtered)
st.dataframe(summary_df)

# botão para download do relatório resumido (CSV)
csv = summary_df.to_csv(index=False).encode('utf-8')
st.download_button("Baixar relatório resumido (CSV)", data=csv, file_name="perfiladv_resumo.csv", mime="text/csv")

# exportar dados filtrados
to_export = df_filtered.copy()
buf = io.BytesIO()
to_export.to_csv(buf, index=False, encoding='utf-8')
buf.seek(0)
st.download_button("Baixar dados filtrados (CSV)", data=buf, file_name="perfiladv_filtrado.csv", mime="text/csv")

st.markdown("---")
st.markdown("**Observação:** esse app espera colunas em português como `sexo`, `cor/raça`, `idade`, `estado`/`localidade` ou em inglês (`gender`,`race`,`age`,`state`). O utilitário de normalização tentará mapear automaticamente. Para reproduzir fielmente o estudo PerfilAdv use os relatórios oficiais da OAB/FGV e os CSV/planilhas geradas a partir deles.")
