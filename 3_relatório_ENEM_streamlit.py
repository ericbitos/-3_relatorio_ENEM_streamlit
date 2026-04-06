from sqlalchemy import create_engine
import pandas as pd
import streamlit as st
import plotly.express as px

# Configurações de conexão com o banco de dados

db_url = f'postgresql+psycopg2://{st.secrets["DB_USER"]}:{st.secrets["DB_PASS"]}@{st.secrets["DB_HOST"]}:{st.secrets["DB_PORT"]}/{st.secrets["DB_NAME"]}'

engine = create_engine(db_url)

@st.cache_data
def load_data():    
    freq_lingua = pd.read_sql('SELECT tp_lingua, COUNT(*) AS frequencia FROM public.ed_enem_2024_resultados GROUP BY tp_lingua ORDER BY frequencia DESC', engine)
    return freq_lingua

@st.cache_data
def load_uf():
    df_top5_uf = pd.read_sql('SELECT nome_uf_prova, COUNT(*) AS frequencia FROM public.ed_enem_2024_resultados GROUP BY nome_uf_prova ORDER BY frequencia DESC LIMIT 5', engine)
    df_bottom5_uf = pd.read_sql('SELECT nome_uf_prova, COUNT(*) AS frequencia FROM public.ed_enem_2024_resultados GROUP BY nome_uf_prova ORDER BY frequencia ASC LIMIT 5', engine)
    desc_uf = pd.read_sql('SELECT nome_uf_prova, COUNT(*) AS frequencia FROM public.ed_enem_2024_resultados GROUP BY nome_uf_prova ORDER BY frequencia DESC', engine)
    return df_top5_uf , df_bottom5_uf, desc_uf

@st.cache_data
def load_matematica():
    nota_mt = pd.read_sql('SELECT nota_mt_matematica FROM public.ed_enem_2024_resultados WHERE nota_mt_matematica IS NOT NULL', engine)
    desc_mt = pd.read_sql('''SELECT
    COUNT(*) AS count_not_null,
    AVG(nota_mt_matematica) AS mean,
    STDDEV_SAMP(nota_mt_matematica) AS stddev,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY nota_mt_matematica) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY nota_mt_matematica) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY nota_mt_matematica) AS p75,
    MAX(nota_mt_matematica) AS max
    FROM public.ed_enem_2024_resultados
    WHERE nota_mt_matematica IS NOT NULL''', engine)
    return nota_mt, desc_mt

@st.cache_data
def load_linguagens():
    nota_lc = pd.read_sql('SELECT nota_lc_linguagens_e_codigos FROM public.ed_enem_2024_resultados WHERE nota_lc_linguagens_e_codigos IS NOT NULL', engine)
    desc_lc = pd.read_sql('''SELECT
    COUNT(*) AS count_not_null,
    AVG(nota_lc_linguagens_e_codigos) AS mean,
    STDDEV_SAMP(nota_lc_linguagens_e_codigos) AS stddev,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY nota_lc_linguagens_e_codigos) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY nota_lc_linguagens_e_codigos) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY nota_lc_linguagens_e_codigos) AS p75,
    MAX(nota_lc_linguagens_e_codigos) AS max
    FROM public.ed_enem_2024_resultados
    WHERE nota_lc_linguagens_e_codigos IS NOT NULL''', engine)
    return nota_lc, desc_lc

freq_lingua= load_data()
df_top5, df_bottom5, desc_uf, = load_uf()
nota_mt, desc_mt = load_matematica()
nota_lc, desc_lc = load_linguagens()


st.title('Relatório ENEM 2024')
tab1, tab2, tab3, tab4 = st.tabs(['Frequência por Estado', 'Distribuição por Idioma', 'Notas de Matemática', 'Notas de Linguagens e Códigos'])

with tab1:
# Top 5 estados com maior frequência
    fig1 = px.bar(df_top5, x='nome_uf_prova', y='frequencia',
                title='Estados com maior frequência',
                color_discrete_sequence=['goldenrod'])
    fig1.update_traces(marker_line_color='black', marker_line_width=1)
    fig1.update_layout(xaxis_tickangle=-40)
    st.plotly_chart(fig1, width='stretch')

    # Top 5 estados com menor frequência
    fig2 = px.bar(df_bottom5, x='nome_uf_prova', y='frequencia',
                title='Estados com menor frequência',
                color_discrete_sequence=['steelblue'])
    fig2.update_traces(marker_line_color='black', marker_line_width=1)
    fig2.update_layout(xaxis_tickangle=-40)
    st.plotly_chart(fig2, width='stretch')

    # tabela de frequência, proporção, frequência acumulada e proporção acumulada da variavel nome_uf_prova
    desc_uf['proporcao'] = desc_uf['frequencia'] / desc_uf['frequencia'].sum()
    desc_uf['frequencia_acumulada'] = desc_uf['frequencia'].cumsum()
    desc_uf['proporcao_acumulada'] = desc_uf['proporcao'].cumsum()
    st.subheader('Tabela de Frequência por Estado')
    st.dataframe(desc_uf)

with tab2:
    # Gráfico de pizza da frequência da variável tp_lingua
    fig3 = px.pie(freq_lingua, values='frequencia', names='tp_lingua', title='Distribuição por Idioma')
    st.plotly_chart(fig3, width='stretch')

    #tabela de frequência, proporção, frequência acumulada e proporção acumulada da variavel tp_lingua
    freq_lingua['proporcao'] = freq_lingua['frequencia'] / freq_lingua['frequencia'].sum()
    freq_lingua['frequencia_acumulada'] = freq_lingua['frequencia'].cumsum()
    freq_lingua['proporcao_acumulada'] = freq_lingua['proporcao'].cumsum()
    st.subheader('Tabela de Frequência por Idioma')
    st.dataframe(freq_lingua)

with tab3:
    #histograma da nota_mt_matematica
    fig4 = px.histogram(nota_mt, x='nota_mt_matematica', nbins=30, title='Distribuição das Notas de Matemática')
    st.plotly_chart(fig4, width='stretch')

    #boxplot da nota_mt_matematica
    fig6 = px.box(nota_mt, y='nota_mt_matematica', title='Boxplot das Notas de Matemática')
    st.plotly_chart(fig6, width='stretch')

    #count mean std 25% 50% 75% max da nota_mt_matematica
    st.subheader('Estatísticas Descritivas da Nota de Matemática')
    st.dataframe(desc_mt)

with tab4:
    #histograma da nota_lc_linguagens_e_codigos
    fig5 = px.histogram(nota_lc, x='nota_lc_linguagens_e_codigos', nbins=30, title='Distribuição das Notas de Linguagens e Códigos')
    st.plotly_chart(fig5, width='stretch')

    #boxplot da nota_lc_linguagens_e_codigos
    fig7 = px.box(nota_lc, y='nota_lc_linguagens_e_codigos', title='Boxplot das Notas de Linguagens e Códigos')
    st.plotly_chart(fig7, width='stretch')

    #count mean std 25% 50% 75% max da nota_lc_linguagens_e_codigos
    st.subheader('Estatísticas Descritivas da Nota de Linguagens e Códigos')
    st.dataframe(desc_lc)
