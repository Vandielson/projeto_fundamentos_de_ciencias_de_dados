import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ===============================
# Configuração da página
# ===============================
st.set_page_config(
    page_title="Dashboard de Controle de Estoque & Vendas",
    layout="wide",
    page_icon="📦"
)

# ===============================
# Navegação do Sistema (Abas)
# ===============================
menu = st.sidebar.radio("📚 Navegação", ["Estoque", "Vendas"])

# ===============================
# Leitura dos Dados
# ===============================
@st.cache_data
def carregar_dados():
    df_estoque = pd.read_csv("dados/FCD_estoque.csv", sep=";")
    df_produtos = pd.read_csv("dados/FCD_produtos.csv", sep=";")

    # Garantir que o campo de localização exista
    if "localizacao" not in df_estoque.columns:
        st.warning("⚠️ A coluna 'localizacao' não foi encontrada em FCD_estoque.csv.")
        df_estoque["localizacao"] = "Não especificado"

    # Remover duplicações exatas: mesmo produto + mesma localização
    df_estoque = df_estoque.drop_duplicates(subset=["produto_id", "localizacao"])

    # Merge com produtos (mantendo granularidade de localização)
    df = df_estoque.merge(df_produtos, on="produto_id", how="left")

    # Calcular valor total por linha (produto x localização)
    df["valor_total"] = df["quantidade_estoque"] * df["preco_unitario"]

    # Criar status de estoque
    df["status_estoque"] = df.apply(
        lambda x: "Abaixo do mínimo" if x["quantidade_estoque"] < x["estoque_minimo"] else "OK",
        axis=1
    )

    return df


df = carregar_dados()

if menu == "Estoque":

    # ===============================
    # Sidebar - Filtros
    # ===============================
    st.sidebar.header("🔎 Filtros")

    categorias = sorted(df["categoria"].dropna().unique())
    marcas = sorted(df["marca"].dropna().unique())
    locais = sorted(df["localizacao"].dropna().unique())
    status_estoque = sorted(df["status_estoque"].dropna().unique())

    # Nenhum filtro selecionado por padrão
    categoria_sel = st.sidebar.multiselect("Categoria", categorias)
    marca_sel = st.sidebar.multiselect("Marca", marcas)
    local_sel = st.sidebar.multiselect("Localização", locais)
    status_estoque_sel = st.sidebar.multiselect("Status do Estoque", status_estoque)

    # Se nada for selecionado, mostrar tudo
    if len(categoria_sel) == 0:
        categoria_sel = df["categoria"].unique()
    if len(marca_sel) == 0:
        marca_sel = df["marca"].unique()
    if len(local_sel) == 0:
        local_sel = df["localizacao"].unique()
    if len(status_estoque_sel) == 0:
        status_estoque_sel = df["status_estoque"].unique()

    df_filtrado = df[
        (df["categoria"].isin(categoria_sel)) &
        (df["marca"].isin(marca_sel)) &
        (df["localizacao"].isin(local_sel)) &
        (df["status_estoque"].isin(status_estoque_sel))
    ]

    # ===============================
    # Indicadores Principais
    # ===============================
    st.title("📦 Dashboard de Controle de Estoque")

    col1, col2, col3, col4 = st.columns(4)

    total_produtos = df_filtrado["produto_id"].nunique()
    quantidade_total = int(df_filtrado["quantidade_estoque"].sum())
    valor_total = df_filtrado["valor_total"].sum()
    abaixo_minimo = df_filtrado[df_filtrado["status_estoque"] == "Abaixo do mínimo"]["produto_id"].nunique()

    col1.metric("Total de Produtos", total_produtos)
    col2.metric("Quantidade Total em Estoque", f"{quantidade_total:,}".replace(",", "."))
    col3.metric("Valor Total em Estoque (R$)", f"{valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col4.metric("Produtos Abaixo do Mínimo", abaixo_minimo)

    st.divider()

    # ===============================
    # Tema escuro dos gráficos
    # ===============================
    plt.style.use("dark_background")
    sns.set_theme(style="darkgrid", palette="crest")

    # ===============================
    # Gráficos
    # ===============================
    st.subheader("📊 Análises de Estoque")

    col_g1, col_g2 = st.columns(2)

    # --- Gráfico 1: Estoque Atual vs Estoque Mínimo ---
    with col_g1:
        st.markdown("#### 📉 Comparativo: Estoque Atual vs Estoque Mínimo")
        df_top = (
            df_filtrado.groupby("produto_nome", as_index=False)
            .agg({"quantidade_estoque": "sum", "estoque_minimo": "mean"})
            .sort_values(by="quantidade_estoque", ascending=False)
            .head(10)
        )
        if not df_top.empty:
            fig, ax = plt.subplots(figsize=(7, 5), facecolor="#0E1117")
            ax.barh(df_top["produto_nome"], df_top["quantidade_estoque"], label="Estoque Atual", color="#00BFFF")
            ax.barh(df_top["produto_nome"], df_top["estoque_minimo"], label="Estoque Mínimo", color="#FF6347", alpha=0.7)
            ax.invert_yaxis()
            ax.set_xlabel("Quantidade", color="white")
            ax.set_ylabel("")
            ax.legend(facecolor="#0E1117", labelcolor="white")
            ax.set_title("Top 10 Produtos: Estoque Atual x Estoque Mínimo", fontsize=11, fontweight="bold", color="white")
            ax.tick_params(colors="white")
            fig.patch.set_facecolor("#0E1117")
            st.pyplot(fig, use_container_width=True)
        else:
            st.info("Nenhum dado disponível.")

    # --- Gráfico 2: Distribuição de Produtos por Categoria ---
    with col_g2:
        st.markdown("#### 🧩 Distribuição de Produtos por Categoria")
        categoria_counts = df_filtrado["categoria"].value_counts().sort_values(ascending=False)
        if not categoria_counts.empty:
            fig2, ax2 = plt.subplots(figsize=(9, 5), facecolor="#0E1117")
            wedges, texts, autotexts = ax2.pie(
                categoria_counts,
                labels=categoria_counts.index,
                autopct="%1.1f%%",
                startangle=90,
                textprops={"fontsize": 9, "color": "white"}
            )
            ax2.axis("equal")
            ax2.set_title("Distribuição de Categorias", fontsize=11, fontweight="bold", color="white")
            fig2.patch.set_facecolor("#0E1117")
            st.pyplot(fig2, use_container_width=True)
        else:
            st.info("Nenhum dado disponível.")

    st.divider()

    # ===============================
    # Tabela Detalhada
    # ===============================
    st.subheader("📋 Detalhamento dos Produtos em Estoque por Localização")

    st.dataframe(
        df_filtrado[[
            "produto_id", "produto_nome", "categoria", "marca",
            "localizacao", "quantidade_estoque", "estoque_minimo",
            "preco_unitario", "valor_total", "status_estoque"
        ]].sort_values(by=["categoria", "produto_nome", "localizacao"], ascending=True),
        use_container_width=True
    )

    st.caption("📘 Dados combinados de estoque e produtos — Atualização dinâmica conforme filtros.")
