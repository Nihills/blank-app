import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF

# -----------------------------
# Arquivo CSV para salvar dados
# -----------------------------
ARQUIVO = "financeiro.csv"
if not os.path.exists(ARQUIVO):
    df_vazio = pd.DataFrame(columns=["Data", "Tipo", "Descrição", "Valor"])
    df_vazio.to_csv(ARQUIVO, index=False)

# -----------------------------
# Carregar dados
# -----------------------------
df = pd.read_csv(ARQUIVO)

st.set_page_config(page_title="Controle Financeiro", layout="centered")
st.title("📊 Controle Financeiro Pessoal")

# -----------------------------
# Formulário de lançamento
# -----------------------------
st.header("➕ Novo Lançamento")
with st.form("novo_lancamento", clear_on_submit=True):
    data = st.date_input("Data", format="DD/MM/YYYY")
    tipo = st.radio("Tipo", ["Entrada", "Saída"], horizontal=True)
    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor (R$)", min_value=0.0, step=1.0, format="%.2f")
    salvar = st.form_submit_button("Adicionar")

    if salvar and descricao and valor > 0:
        novo = pd.DataFrame(
            [[data.strftime("%Y-%m-%d"), tipo, descricao, valor]],
            columns=["Data", "Tipo", "Descrição", "Valor"]
        )
        df = pd.concat([df, novo], ignore_index=True)
        df.to_csv(ARQUIVO, index=False)
        st.success("✅ Lançamento adicionado com sucesso!")

# -----------------------------
# Mostrar lançamentos
# -----------------------------
st.header("📅 Lançamentos")

if not df.empty:
    # Converter coluna Data para datetime
    df["Data"] = pd.to_datetime(df["Data"], format="%Y-%m-%d", errors="coerce")
    
    # Mapear meses para português
    MESES_PT = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    df["Mês"] = df["Data"].dt.month.map(MESES_PT)
    df["Ano"] = df["Data"].dt.year
    df["Data BR"] = df["Data"].dt.strftime("%d/%m/%Y")

    # Filtros por ano e mês
    col1, col2 = st.columns(2)
    with col1:
        ano_sel = st.selectbox("Ano", sorted(df["Ano"].dropna().unique()), index=0)
    with col2:
        meses = df[df["Ano"] == ano_sel]["Mês"].dropna().unique()
        mes_sel = st.selectbox("Mês", sorted(meses), index=0)

    df_filtrado = df[(df["Ano"] == ano_sel) & (df["Mês"] == mes_sel)]

    # Formatar valores como moeda BR
    df_formatado = df_filtrado.copy()
    df_formatado["Valor"] = df_formatado["Valor"].map(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

    # Mostrar tabela
    st.write(f"### Lançamentos de {mes_sel} / {ano_sel}")
    st.dataframe(df_formatado[["Data BR", "Tipo", "Descrição", "Valor"]], use_container_width=True)

    # Resumo financeiro
    entradas = df_filtrado[df_filtrado["Tipo"] == "Entrada"]["Valor"].sum()
    saidas = df_filtrado[df_filtrado["Tipo"] == "Saída"]["Valor"].sum()
    saldo = entradas - saidas

    st.subheader("📊 Resumo")
    st.markdown(
        f"<span style='color:green'>Entradas: R$ {entradas:,.2f}</span>"
        .replace(",", "X").replace(".", ",").replace("X", "."),
        unsafe_allow_html=True
    )
    st.markdown(
        f"<span style='color:red'>Saídas: R$ {saidas:,.2f}</span>"
        .replace(",", "X").replace(".", ",").replace("X", "."),
        unsafe_allow_html=True
    )
    cor_saldo = "green" if saldo >= 0 else "red"
    st.markdown(
        f"<b>Saldo:</b> <span style='color:{cor_saldo}'>R$ {saldo:,.2f}</span>"
        .replace(",", "X").replace(".", ",").replace("X", "."),
        unsafe_allow_html=True
    )

    # -----------------------------
    # Gráfico mensal
    # -----------------------------
    st.subheader("📈 Gráfico Mensal")
    df_grafico = df[df["Ano"] == ano_sel].groupby(["Mês", "Tipo"])["Valor"].sum().unstack().fillna(0)
    df_grafico = df_grafico.reindex(MESES_PT.values())
    fig, ax = plt.subplots(figsize=(8, 4))
    df_grafico.plot(kind="bar", ax=ax, color={"Entrada": "green", "Saída": "red"})
    plt.title(f"Entradas e Saídas - {ano_sel}")
    plt.xlabel("Meses")
    plt.ylabel("Valor (R$)")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # -----------------------------
    # Exportar relatório
    # -----------------------------
    st.subheader("📄 Exportar Relatório")

    # Exportar para Excel
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        df_formatado.to_excel(writer, index=False, sheet_name="Lançamentos")
    st.download_button(
        label="📥 Baixar Excel",
        data=excel_buffer.getvalue(),
        file_name=f"relatorio_{mes_sel}_{ano_sel}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Exportar para PDF
    pdf_buffer = BytesIO()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Relatório Financeiro - {mes_sel}/{ano_sel}", ln=True, align="C")
    pdf.ln(5)
    for i, row in df_formatado.iterrows():
        pdf.cell(0, 10, txt=f"{row['Data BR']} | {row['Tipo']} | {row['Descrição']} | {row['Valor']}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 10, txt=f"Entradas: R$ {entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
    pdf.cell(0, 10, txt=f"Saídas: R$ {saidas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
    pdf.cell(0, 10, txt=f"Saldo: R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
    pdf.output(pdf_buffer)
    st.download_button(
        label="📥 Baixar PDF",
        data=pdf_buffer.getvalue(),
        file_name=f"relatorio_{mes_sel}_{ano_sel}.pdf",
        mime="application/pdf"
    )

else:
    st.info("Ainda não há lançamentos cadastrados.")
