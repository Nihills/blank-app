import streamlit as st
import pandas as pd
import os

# Arquivo CSV para salvar os dados
ARQUIVO = "financeiro.csv"

# Se o arquivo não existir, cria um novo
if not os.path.exists(ARQUIVO):
    df_vazio = pd.DataFrame(columns=["Data", "Tipo", "Descrição", "Valor"])
    df_vazio.to_csv(ARQUIVO, index=False)

# Carrega os dados
df = pd.read_csv(ARQUIVO)

st.set_page_config(page_title="Controle Financeiro", layout="centered")

st.title("📊 Controle Financeiro de ZigZig")

# ---- Formulário de lançamento ----
st.header("➕ Novo Lançamento")

with st.form("novo_lancamento", clear_on_submit=True):
    data = st.date_input("Data", format="DD/MM/YYYY")
    tipo = st.radio("Tipo", ["Entrada", "Saída"], horizontal=True)
    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
    salvar = st.form_submit_button("Adicionar")

    if salvar and descricao and valor > 0:
        novo = pd.DataFrame(
            [[data.strftime("%Y-%m-%d"), tipo, descricao, valor]],
            columns=["Data", "Tipo", "Descrição", "Valor"]
        )
        df = pd.concat([df, novo], ignore_index=True)
        df.to_csv(ARQUIVO, index=False)
        st.success("✅ Lançamento adicionado com sucesso!")

# ---- Exibição de lançamentos ----
st.header("📅 Lançamentos")

if not df.empty:
    # Converter datas para o formato brasileiro
    df["Data"] = pd.to_datetime(df["Data"], format="%Y-%m-%d", errors="coerce")
    df["Data BR"] = df["Data"].dt.strftime("%d/%m/%Y")

    # Criar colunas auxiliares para filtro
    df["Ano"] = df["Data"].dt.year
    df["Mês"] = df["Data"].dt.month_name(locale="pt_BR")

    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        ano_sel = st.selectbox("Ano", sorted(df["Ano"].dropna().unique()), index=0)
    with col2:
        meses = df[df["Ano"] == ano_sel]["Mês"].dropna().unique()
        mes_sel = st.selectbox("Mês", sorted(meses), index=0)

    # Filtrar pelos valores escolhidos
    df_filtrado = df[(df["Ano"] == ano_sel) & (df["Mês"] == mes_sel)]

    # Formatar valores como moeda BRL
    df_formatado = df_filtrado.copy()
    df_formatado["Valor"] = df_formatado["Valor"].map(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Mostrar lançamentos
    st.write(f"### Lançamentos de {mes_sel} / {ano_sel}")
    st.dataframe(df_formatado[["Data BR", "Tipo", "Descrição", "Valor"]], use_container_width=True)

    # Resumo
    entradas = df_filtrado[df_filtrado["Tipo"] == "Entrada"]["Valor"].sum()
    saidas = df_filtrado[df_filtrado["Tipo"] == "Saída"]["Valor"].sum()
    saldo = entradas - saidas

    st.subheader("📊 Resumo")
    st.markdown(f"<span style='color:green'>Entradas: R$ {entradas:,.2f}</span>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
    st.markdown(f"<span style='color:red'>Saídas: R$ {saidas:,.2f}</span>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)

    cor_saldo = "green" if saldo >= 0 else "red"
    st.markdown(f"<b>Saldo:</b> <span style='color:{cor_saldo}'>R$ {saldo:,.2f}</span>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)

else:
    st.info("Ainda não há lançamentos cadastrados.")
