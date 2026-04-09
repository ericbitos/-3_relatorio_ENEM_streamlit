from sqlalchemy import create_engine
import pandas as pd
import streamlit as st
import plotly.express as px

# ── Conexão ──────────────────────────────────────────────────────────────────
db_url = (
    f'postgresql+psycopg2://{st.secrets["DB_USER"]}:{st.secrets["DB_PASS"]}'
    f'@{st.secrets["DB_HOST"]}:{st.secrets["DB_PORT"]}/{st.secrets["DB_NAME"]}'
)
engine = create_engine(db_url)


# ── Carga dos dados brutos (uma única query traz tudo) ────────────────────────
@st.cache_data
def load_raw() -> pd.DataFrame:
    """Retorna a tabela completa com as colunas necessárias para todos os gráficos."""
    return pd.read_sql(
        """
        SELECT
            sg_uf_prova,
            nome_uf_prova,
            tp_lingua,
            nota_mt_matematica,
            nota_lc_linguagens_e_codigos
        FROM public.ed_enem_2024_resultados_amos_per
        """,
        engine,
    )


# ── Helpers de agregação ──────────────────────────────────────────────────────
def freq_table(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Frequência + proporção + acumulados para uma coluna categórica."""
    t = (
        df[col]
        .value_counts()
        .reset_index()
        .rename(columns={"index": col, "count": "frequencia", col: col})
    )
    # value_counts já retorna col e 'count'; ajustamos os nomes
    t.columns = [col, "frequencia"]
    t = t.sort_values("frequencia", ascending=False).reset_index(drop=True)
    t["proporcao"] = t["frequencia"] / t["frequencia"].sum()
    t["frequencia_acumulada"] = t["frequencia"].cumsum()
    t["proporcao_acumulada"] = t["proporcao"].cumsum()
    return t


def desc_stats(series: pd.Series) -> pd.DataFrame:
    """Estatísticas descritivas equivalentes à query SQL original."""
    s = series.dropna()
    return pd.DataFrame(
        {
            "count": [len(s)],
            "mean": [s.mean()],
            "std": [s.std()],
            "p25": [s.quantile(0.25)],
            "p50": [s.quantile(0.50)],
            "p75": [s.quantile(0.75)],
            "max": [s.max()],
        }
    )


# ── Carrega dados ─────────────────────────────────────────────────────────────
df_raw = load_raw()

# ── Sidebar — Filtro de UF ────────────────────────────────────────────────────
st.sidebar.title("🔎 Filtros")

ufs_disponiveis = sorted(df_raw["sg_uf_prova"].dropna().unique().tolist())

ufs_selecionadas = st.sidebar.multiselect(
    label="Selecione a(s) UF(s)",
    options=ufs_disponiveis,
    default=ufs_disponiveis,       # começa com todas selecionadas
    placeholder="Digite ou escolha uma UF…",
)

# Garante que ao menos uma UF esteja selecionada
if not ufs_selecionadas:
    st.sidebar.warning("Selecione ao menos uma UF para exibir os dados.")
    st.stop()

# Botão para resetar o filtro
if st.sidebar.button("↺  Limpar filtro"):
    ufs_selecionadas = ufs_disponiveis
    st.rerun()

# Indicador de seleção atual
total_registros = len(df_raw)
df = df_raw[df_raw["sg_uf_prova"].isin(ufs_selecionadas)].copy()
registros_filtrados = len(df)

st.sidebar.markdown("---")
st.sidebar.metric(
    "Registros selecionados",
    f"{registros_filtrados:,}".replace(",", "."),
    delta=f"{registros_filtrados - total_registros:,}".replace(",", "."),
    delta_color="off",
)
st.sidebar.caption(
    f"{registros_filtrados / total_registros:.1%} do total ({total_registros:,})".replace(",", ".")
)

# ── Agrega dados já filtrados ─────────────────────────────────────────────────
desc_uf   = freq_table(df, "nome_uf_prova")
freq_lingua = freq_table(df, "tp_lingua")

nota_mt   = df[["nota_mt_matematica"]].dropna()
desc_mt   = desc_stats(df["nota_mt_matematica"])

nota_lc   = df[["nota_lc_linguagens_e_codigos"]].dropna()
desc_lc   = desc_stats(df["nota_lc_linguagens_e_codigos"])

TOP_N = 5
df_top5   = desc_uf.nlargest(TOP_N,  "frequencia")[["nome_uf_prova", "frequencia"]]
df_bottom5 = desc_uf.nsmallest(TOP_N, "frequencia")[["nome_uf_prova", "frequencia"]]

# ── Layout principal ──────────────────────────────────────────────────────────
filtro_label = (
    ", ".join(ufs_selecionadas)
    if len(ufs_selecionadas) <= 5
    else f"{len(ufs_selecionadas)} UFs selecionadas"
)
st.title("Relatório ENEM 2024")
st.caption(f"📍 Filtro ativo: **{filtro_label}**")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Frequência por Estado", "Distribuição por Idioma",
     "Notas de Matemática", "Notas de Linguagens e Códigos"]
)

# ── Tab 1 — Frequência por Estado ─────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        fig1 = px.bar(
            df_top5, x="nome_uf_prova", y="frequencia",
            title=f"Top {TOP_N} estados — maior frequência",
            color_discrete_sequence=["lightgreen"],
        )
        fig1.update_traces(marker_line_color="black", marker_line_width=1)
        fig1.update_layout(xaxis_tickangle=-40)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.bar(
            df_bottom5, x="nome_uf_prova", y="frequencia",
            title=f"Top {TOP_N} estados — menor frequência",
            color_discrete_sequence=["steelblue"],
        )
        fig2.update_traces(marker_line_color="black", marker_line_width=1)
        fig2.update_layout(xaxis_tickangle=-40)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Tabela de Frequência por Estado")
    st.dataframe(desc_uf, use_container_width=True)

# ── Tab 2 — Distribuição por Idioma ──────────────────────────────────────────
with tab2:
    fig3 = px.pie(
        freq_lingua, values="frequencia", names="tp_lingua",
        title="Distribuição por Idioma",
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Tabela de Frequência por Idioma")
    st.dataframe(freq_lingua, use_container_width=True)

# ── Tab 3 — Notas de Matemática ───────────────────────────────────────────────
with tab3:
    fig4 = px.histogram(
        nota_mt, x="nota_mt_matematica", nbins=30,
        title="Distribuição das Notas de Matemática",
        labels={"nota_mt_matematica": "Nota de Matemática", "count": "Frequência"},
    )
    fig4.update_traces(
        marker=dict(color="#4F8EF7", line=dict(color="#1A5FC8", width=1.2))
    )
    st.plotly_chart(fig4, use_container_width=True)

    fig6 = px.box(nota_mt, y="nota_mt_matematica", title="Boxplot das Notas de Matemática")
    st.plotly_chart(fig6, use_container_width=True)

    st.subheader("Estatísticas Descritivas — Matemática")
    st.dataframe(desc_mt, use_container_width=True)

# ── Tab 4 — Notas de Linguagens e Códigos ────────────────────────────────────
with tab4:
    fig5 = px.histogram(
        nota_lc, x="nota_lc_linguagens_e_codigos", nbins=30,
        title="Distribuição das Notas de Linguagens e Códigos",
        labels={"nota_lc_linguagens_e_codigos": "Nota de Linguagens e Códigos", "count": "Frequência"},
    )
    fig5.update_traces(
        marker=dict(color="#4F8EF7", line=dict(color="#1A5FC8", width=1.2))
    )
    st.plotly_chart(fig5, use_container_width=True)

    fig7 = px.box(nota_lc, y="nota_lc_linguagens_e_codigos", title="Boxplot das Notas de Linguagens e Códigos")
    st.plotly_chart(fig7, use_container_width=True)

    st.subheader("Estatísticas Descritivas — Linguagens e Códigos")
    st.dataframe(desc_lc, use_container_width=True)