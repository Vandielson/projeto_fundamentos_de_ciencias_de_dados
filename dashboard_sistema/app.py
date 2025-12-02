import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates

def formatar_valor_compacto(valor):
    if valor >= 1_000_000_000:
        return f"R$ {valor / 1_000_000_000:.1f} Bi"
    elif valor >= 1_000_000:
        return f"R$ {valor / 1_000_000:.1f} Mi"
    elif valor >= 1_000:
        return f"R$ {valor / 1_000:.0f} Mil"
    else:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
menu = st.sidebar.radio("📚 Navegação", ["Estoque", "Vendas", "Compras"])

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

@st.cache_data
def carregar_vendas():
    df_vendas = pd.read_csv("dados/FCD_vendas.csv", sep=";")
    df_vendas["data_venda"] = pd.to_datetime(df_vendas["data_venda"], dayfirst=True, errors="coerce")
    df_vendas["quantidade_vendida"] = pd.to_numeric(df_vendas["quantidade_vendida"], errors="coerce").fillna(0)
    df_vendas["valor_unitario"] = pd.to_numeric(df_vendas["valor_unitario"], errors="coerce").fillna(0)
    df_vendas["valor_total"] = pd.to_numeric(df_vendas["valor_total"], errors="coerce").fillna(
        df_vendas["quantidade_vendida"] * df_vendas["valor_unitario"]
    )
    return df_vendas

@st.cache_data
def carregar_clientes():
    try:
        return pd.read_csv("dados/FCD_clientes.csv", sep=";")
    except:
        return pd.DataFrame()


df = carregar_dados()
df_vendas = carregar_vendas()
df_clientes = carregar_clientes()

# ===============================
# ABA Estoque
# ===============================
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
    col3.metric("Valor Total em Estoque", formatar_valor_compacto(valor_total))
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

# ===============================
# ABA VENDAS
# ===============================
if menu == "Vendas":

    st.title("💸 Dashboard de Vendas")

    # ===============================
    # JOIN CORRETO COM PRODUTOS (SEM DUPLICAR)
    # ===============================

    # IMPORTANTE: usar df_produtos em vez de df (df contém múltiplas localizações)
    df_produtos = pd.read_csv("dados/FCD_produtos.csv", sep=";")

    df_v = df_vendas.merge(
        df_produtos[[
            "produto_id", "produto_nome", "categoria", "marca", "preco_unitario"
        ]],
        on="produto_id",
        how="left"
    )

    # JOIN COM CLIENTES
    if not df_clientes.empty:
        df_v = df_v.merge(
            df_clientes[["cliente_id", "nome"]],
            on="cliente_id",
            how="left"
        )
        df_v.rename(columns={"nome": "cliente_nome"}, inplace=True)

    # Coluna loja formatada
    df_v["loja"] = df_v["loja_id"].apply(lambda x: f"Loja {x}")

    # Converter datas
    df_v["data_venda"] = pd.to_datetime(df_v["data_venda"], dayfirst=True, errors="coerce")

    # ===============================
    # FILTROS
    # ===============================
    st.sidebar.header("Filtros — Vendas")

    lojas = sorted(df_v["loja"].dropna().unique())
    produtos = sorted(df_v["produto_nome"].dropna().unique())
    clientes = sorted(df_v["cliente_nome"].dropna().unique()) if "cliente_nome" in df_v.columns else []

    loja_sel = st.sidebar.multiselect("Loja", lojas)
    prod_sel = st.sidebar.multiselect("Produto", produtos)
    cli_sel = st.sidebar.multiselect("Cliente", clientes)

    # Período
    min_dt = df_v["data_venda"].min()
    max_dt = df_v["data_venda"].max()
    periodo = st.sidebar.date_input("Período", (min_dt, max_dt))

    if not loja_sel:
        loja_sel = lojas
    if not prod_sel:
        prod_sel = produtos
    if clientes and not cli_sel:
        cli_sel = clientes

    # Filtrar por período
    if isinstance(periodo, tuple) and len(periodo) == 2:
        start_dt, end_dt = periodo
        df_f = df_v[
            (df_v["data_venda"] >= pd.to_datetime(start_dt))
            & (df_v["data_venda"] <= pd.to_datetime(end_dt))
        ]
    else:
        df_f = df_v.copy()

    # Filtros restantes
    df_f = df_f[df_f["loja"].isin(loja_sel)]
    df_f = df_f[df_f["produto_nome"].isin(prod_sel)]
    if cli_sel:
        df_f = df_f[df_f["cliente_nome"].isin(cli_sel)]

    # ===============================
    # INDICADORES
    # ===============================
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Itens Vendidos", int(df_f["quantidade_vendida"].sum()))

    receita_total = df_f["valor_total"].sum()
    col2.metric("Receita Total", formatar_valor_compacto(receita_total))

    col3.metric("Transações", df_f.shape[0])

    col4.metric(
        "Ticket Médio",
        f"R$ {df_f['valor_total'].mean():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if df_f.shape[0] > 0 else "R$ 0,00"
    )

    st.divider()

    # ===============================
    # GRÁFICO — Série Temporal
    # ===============================
    st.subheader("📈 Vendas por Mês")

    df_f["ano_mes"] = df_f["data_venda"].dt.to_period("M")
    df_ts = df_f.groupby("ano_mes")["quantidade_vendida"].sum().reset_index()
    df_ts["ano_mes_dt"] = df_ts["ano_mes"].dt.to_timestamp()
    df_ts = df_ts.sort_values("ano_mes_dt")

    meses_map = {
        1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
        7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez"
    }

    fig, ax = plt.subplots(figsize=(8, 4), facecolor="#0E1117")
    ax.plot(df_ts["ano_mes_dt"], df_ts["quantidade_vendida"], marker="o", linewidth=2, color="#00BFFF")

    import matplotlib.ticker as ticker

    def formatar_mes(x, pos):
        try:
            dt = mdates.num2date(x)
            return f"{meses_map[dt.month]}/{str(dt.year)[2:]}"
        except:
            return ""

    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(formatar_mes))

    ax.set_title("Quantidade Vendida por Mês", color="white")
    ax.set_xlabel("Mês", color="white")
    ax.set_ylabel("Itens Vendidos", color="white")
    ax.tick_params(colors="white")

    fig.autofmt_xdate()
    ax.set_facecolor("#0E1117")
    fig.patch.set_facecolor("#0E1117")

    st.pyplot(fig, use_container_width=True)

    st.divider()

    # ===============================
    # TOP 10 Produtos
    # ===============================
    st.subheader("🏆 Top 10 Produtos Mais Vendidos")

    top10 = (
        df_f.groupby("produto_nome")["quantidade_vendida"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    fig2, ax2 = plt.subplots(figsize=(8, 4), facecolor="#0E1117")
    ax2.barh(top10.index[::-1], top10.values[::-1], color="#00BFFF")
    ax2.set_title("Top 10 Produtos", color="white")
    ax2.tick_params(colors="white")
    ax2.set_facecolor("#0E1117")
    fig2.patch.set_facecolor("#0E1117")

    st.pyplot(fig2, use_container_width=True)

    st.divider()

    # ===============================
    # Tabela
    # ===============================
    st.subheader("📋 Registros de Vendas")

    df_show = df_f[[
        "venda_id", "data_venda", "loja", "produto_nome",
        "cliente_nome", "quantidade_vendida",
        "valor_unitario", "valor_total", "forma_pagamento", "canal_venda"
    ]].copy()

    df_show["data_venda"] = df_show["data_venda"].dt.strftime("%d/%m/%Y")

    st.dataframe(df_show, use_container_width=True)

# ===============================
# ABA COMPRAS
# ===============================
if menu == "Compras":

    st.title("🛒 Dashboard de Compras & Fornecedores")

    # ===============================
    # Carregar compras
    # ===============================
    df_compras = pd.read_csv("dados/FCD_compras.csv", sep=";")

    # Converter tipos
    df_compras["data_compra"] = pd.to_datetime(df_compras["data_compra"], dayfirst=True, errors="coerce")
    df_compras["quantidade_comprada"] = pd.to_numeric(df_compras["quantidade_comprada"], errors="coerce").fillna(0)
    df_compras["valor_unitario"] = pd.to_numeric(df_compras["valor_unitario"], errors="coerce").fillna(0)

    # Se valor_total vier errado → recalcula
    df_compras["valor_total"] = pd.to_numeric(df_compras["valor_total"], errors="coerce")
    df_compras["valor_total"] = df_compras["valor_total"].fillna(
        df_compras["quantidade_comprada"] * df_compras["valor_unitario"]
    )

    # JOIN com produtos para nome/categoria
    df_produtos = pd.read_csv("dados/FCD_produtos.csv", sep=";")
    df_c = df_compras.merge(
        df_produtos[["produto_id", "produto_nome", "categoria", "marca"]],
        on="produto_id",
        how="left"
    )

    # ===============================
    # FILTROS
    # ===============================
    st.sidebar.header("Filtros — Compras")

    fornecedores = sorted(df_c["fornecedor"].dropna().unique())
    produtos = sorted(df_c["produto_nome"].dropna().unique())

    forn_sel = st.sidebar.multiselect("Fornecedor", fornecedores)
    prod_sel = st.sidebar.multiselect("Produto", produtos)

    # Período
    min_dt = df_c["data_compra"].min()
    max_dt = df_c["data_compra"].max()
    periodo = st.sidebar.date_input("Período", (min_dt, max_dt))

    # Defaults
    if not forn_sel:
        forn_sel = fornecedores
    if not prod_sel:
        prod_sel = produtos

    start_dt, end_dt = periodo

    df_f = df_c[
        (df_c["fornecedor"].isin(forn_sel)) &
        (df_c["produto_nome"].isin(prod_sel)) &
        (df_c["data_compra"] >= pd.to_datetime(start_dt)) &
        (df_c["data_compra"] <= pd.to_datetime(end_dt))
    ]

    # ===============================
    # INDICADORES
    # ===============================
    col1, col2, col3, col4 = st.columns(4)

    total_compras = df_f["compra_id"].count()
    total_gasto = df_f["valor_total"].sum()
    prazo_medio = df_f["prazo_entrega_dias"].mean()
    itens_comprados = df_f["quantidade_comprada"].sum()

    col1.metric("Total de Compras", total_compras)
    col2.metric("Gasto Total", formatar_valor_compacto(total_gasto))
    col3.metric("Prazo Médio (dias)", f"{prazo_medio:.1f}" if not pd.isna(prazo_medio) else "0")
    col4.metric("Itens Comprados", int(itens_comprados))

    st.divider()

    # Tema escuro dos gráficos
    plt.style.use("dark_background")
    sns.set_theme(style="darkgrid", palette="crest")

    # ===============================
    # Comparativo entre fornecedores
    # ===============================
    st.subheader("🏭 Comparativo entre Fornecedores (Preço Médio e Prazo Médio)")

    df_forn = df_f.groupby("fornecedor").agg({
        "valor_unitario": "mean",
        "prazo_entrega_dias": "mean"
    }).reset_index()

    if not df_forn.empty:
        fig, ax = plt.subplots(figsize=(9, 5), facecolor="#0E1117")

        ax.scatter(
            df_forn["valor_unitario"],
            df_forn["prazo_entrega_dias"],
            s=200,
            color="#00BFFF",
            alpha=0.8
        )

        for _, row in df_forn.iterrows():
            ax.text(
                row["valor_unitario"],
                row["prazo_entrega_dias"],
                row["fornecedor"],
                color="white",
                fontsize=8
            )

        ax.set_xlabel("Preço Médio (R$)", color="white")
        ax.set_ylabel("Prazo Médio de Entrega (dias)", color="white")
        ax.set_title("Comparativo de Fornecedores", color="white", fontsize=12)
        ax.tick_params(colors="white")
        ax.set_facecolor("#0E1117")
        fig.patch.set_facecolor("#0E1117")

        st.pyplot(fig, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para exibir o comparativo.")

    st.divider()

    # ===============================
    # Volume de Compras por Mês
    # ===============================
    st.subheader("📈 Volume de Compras por Mês")

    df_f["ano_mes"] = df_f["data_compra"].dt.to_period("M")
    df_ts = df_f.groupby("ano_mes")["valor_total"].sum().reset_index()
    df_ts["ano_mes_dt"] = df_ts["ano_mes"].dt.to_timestamp()

    meses_map = {
        1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
        7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez"
    }

    import matplotlib.ticker as ticker

    def formatar_mes(x, pos):
        try:
            dt = mdates.num2date(x)
            return f"{meses_map[dt.month]}/{str(dt.year)[2:]}"
        except:
            return ""

    if not df_ts.empty:
        fig2, ax2 = plt.subplots(figsize=(9, 4), facecolor="#0E1117")
        ax2.plot(df_ts["ano_mes_dt"], df_ts["valor_total"], marker="o", color="#00BFFF")

        ax2.xaxis.set_major_locator(mdates.MonthLocator())
        ax2.xaxis.set_major_formatter(ticker.FuncFormatter(formatar_mes))

        ax2.set_title("Volume de Compras por Mês", color="white")
        ax2.set_xlabel("Mês", color="white")
        ax2.set_ylabel("Valor (R$)", color="white")
        ax2.tick_params(colors="white")

        fig2.autofmt_xdate()
        ax2.set_facecolor("#0E1117")
        fig2.patch.set_facecolor("#0E1117")

        st.pyplot(fig2, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para gerar série temporal.")

    st.divider()

    # ===============================
    # Produtos com maior gasto
    # ===============================
    st.subheader("💰 Produtos com Maior Gasto em Compras")

    top_prod = (
        df_f.groupby("produto_nome")["valor_total"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    if not top_prod.empty:
        fig3, ax3 = plt.subplots(figsize=(9, 4), facecolor="#0E1117")
        ax3.barh(top_prod.index[::-1], top_prod.values[::-1], color="#00BFFF")

        ax3.set_title("Top 10 Produtos por Gasto", color="white")
        ax3.tick_params(colors="white")
        ax3.set_facecolor("#0E1117")
        fig3.patch.set_facecolor("#0E1117")

        st.pyplot(fig3, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para exibir ranking de produtos.")

    st.divider()

    # ===============================
    # Tabela final
    # ===============================
    st.subheader("📋 Registros de Compras")

    df_show = df_f.copy()
    df_show["data_compra"] = df_show["data_compra"].dt.strftime("%d/%m/%Y")

    st.dataframe(df_show, use_container_width=True)
