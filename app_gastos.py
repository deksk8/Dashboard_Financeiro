import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------
# Inicializa o estado da sessão
# ---------------------------
if 'df_picpay' not in st.session_state:
    st.session_state.df_picpay = None
if 'df_inter' not in st.session_state:
    st.session_state.df_inter = None
if 'df_nubank' not in st.session_state:
    st.session_state.df_nubank = None

# Flags de visibilidade de tabela por aba
if 'show_table_picpay' not in st.session_state:
    st.session_state.show_table_picpay = False
if 'show_table_inter' not in st.session_state:
    st.session_state.show_table_inter = False
if 'show_table_nubank' not in st.session_state:
    st.session_state.show_table_nubank = False

# ---------------------------
# Função central de processamento
# ---------------------------
def process_upload(uploaded_file):
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, dtype={'Valor': str}, decimal=',')
            # Limpeza e conversão de dados
            if 'Valor' in df.columns:
                df.dropna(subset=['Valor'], inplace=True)
                df['Valor'] = (
                    df['Valor']
                    .astype(str)
                    .str.replace('.', '', regex=False)
                    .str.replace(',', '.', regex=False)
                    .str.replace('R$', '', regex=False)
                )
                df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')
            # Exemplo simples de tag
            if 'Estabelecimento' in df.columns:
                df.loc[
                    df['Estabelecimento'].astype(str).str.contains('uber', case=False, na=False),
                    'Tags'
                ] = 'UBER'
            return df
        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
            st.info("Por favor, verifique se o arquivo CSV está no formato correto.")
            return None
    return None

# ---------------------------
# Layout
# ---------------------------
st.title('Dashboard de Análise de Gastos')
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs([
    "Análise Geral",
    "Análise por Cartão - PicPay",
    "Análise por Cartão - Inter",
    "Análise por Cartão - Nubank"
])

# ---------------------------
# Aba 1: Análise Geral
# ---------------------------
with tab1:
    st.header('Análise Geral de Gastos')
    st.info("Esta aba combina os dados de todos os cartões que foram carregados.")

    # Junta apenas os DataFrames que já existem
    dfs = [d for d in [st.session_state.df_picpay, st.session_state.df_inter, st.session_state.df_nubank] if d is not None]

    if dfs:
        df_combined = pd.concat(dfs, ignore_index=True)

        renda = st.number_input("Valor dos proventos deste mês (R$)", min_value=0.0, value=5000.0, step=100.0)

        # 1. Totais
        total_combined = df_combined['Valor'].sum(numeric_only=True)
        st.subheader('Movimentação Total dos Cartões')

        st.metric("Total de Compras", f'R$ {total_combined:,.2f}')
        st.metric("Renda Mensal", f'R$ {renda:,.2f}')
        saldo = renda - total_combined
        st.metric("Saldo", f'R$ {saldo:,.2f}', delta=f'R$ {renda - total_combined:,.2f}', delta_color="normal")

        # 2. Top 10 compras
        st.subheader('Ranking das 10 Maiores Compras')
        df_top10 = df_combined.sort_values(by='Valor', ascending=False).head(10).copy()

        total_top10 = df_top10['Valor'].sum(numeric_only=True)
        percentual_top10 = (total_top10 / total_combined * 100) if total_combined else 0.0

        df_top10['% do Total'] = (df_top10['Valor'] / total_combined * 100).round(2).astype(str) + '%'
        cols_top10 = [c for c in ['Data', 'Estabelecimento', 'Valor', '% do Total'] if c in df_top10.columns]
        st.dataframe(df_top10[cols_top10])

        st.markdown(f"**A soma das 10 maiores compras representa {percentual_top10:.2f}% do total de todas as faturas.**")

        # 3. Visão unificada por Tags
        st.subheader('Visão Unificada de Gastos')
        if 'Tags' in df_combined.columns:
            gastos_por_tag_geral = df_combined.groupby('Tags', dropna=False)['Valor'].sum().reset_index()
            gastos_por_tag_geral['Label'] = gastos_por_tag_geral['Tags'].astype(str) + ' - R$ ' + gastos_por_tag_geral['Valor'].map('{:,.2f}'.format)

            fig_pie_geral = px.pie(
                gastos_por_tag_geral,
                values='Valor',
                names='Label',
                title='Proporção Total de Gastos por Categoria (Todos os Cartões)',
                color='Tags'
            )
            st.plotly_chart(fig_pie_geral)

            fig_bar_geral = px.bar(
                gastos_por_tag_geral,
                x='Valor',
                y='Label',
                orientation='h',
                title='Soma Total de Gastos por Categoria - Todos os Cartões',
                labels={'Valor': 'Valor (R$)', 'Tags': 'Categoria'},
                color='Tags'
            )
            st.plotly_chart(fig_bar_geral)

        st.subheader('Tabela Geral de Compras')
        st.dataframe(df_combined)
    else:
        st.info("Por favor, carregue as faturas nas abas correspondentes para ver a análise geral.")

# ---------------------------
# Aba 2: PicPay
# ---------------------------
with tab2:
    st.header('Análise da Fatura - PicPay')
    uploaded_file_picpay = st.file_uploader("Escolha o arquivo CSV da sua fatura do PicPay", type=['csv'], key='uploader_picpay')

    df_temp = process_upload(uploaded_file_picpay)
    if df_temp is not None:
        st.session_state.df_picpay = df_temp
        st.success('Arquivo PicPay importado com sucesso!')

    if st.session_state.df_picpay is not None:
        df_compras = st.session_state.df_picpay
        total_compras = df_compras['Valor'].sum(numeric_only=True)
        st.info(f'Total de Compras: R$ {total_compras:,.2f}')

        if st.button('Mostrar/Ocultar Tabela de Compras PicPay', key='btn_picpay'):
            st.session_state.show_table_picpay = not st.session_state.show_table_picpay

        if st.session_state.show_table_picpay:
            st.subheader('Tabela de Compras')
            st.dataframe(df_compras)

        st.subheader('Análise de Gastos')
        if 'Tags' in df_compras.columns:
            gastos_por_tag = df_compras.groupby('Tags', dropna=False)['Valor'].sum().reset_index()
            gastos_por_tag['Label'] = gastos_por_tag['Tags'].astype(str) + ' - R$ ' + gastos_por_tag['Valor'].map('{:,.2f}'.format)

            fig_pie = px.pie(gastos_por_tag, values='Valor', names='Label', title='Proporção de Gastos por Categoria - PicPay', color='Tags')
            st.plotly_chart(fig_pie)

            fig_bar = px.bar(gastos_por_tag, x='Valor', y='Label', orientation='h',
                             title='Soma Total de Gastos por Categoria - PicPay',
                             labels={'Valor': 'Valor (R$)', 'Tags': 'Categoria'}, color='Tags')
            st.plotly_chart(fig_bar)

# ---------------------------
# Aba 3: Inter
# ---------------------------
with tab3:
    st.header('Análise da Fatura - Inter')
    uploaded_file_inter = st.file_uploader("Escolha o arquivo CSV da sua fatura do Inter", type=['csv'], key='uploader_inter')

    df_temp = process_upload(uploaded_file_inter)
    if df_temp is not None:
        st.session_state.df_inter = df_temp
        st.success('Arquivo Inter importado com sucesso!')

    if st.session_state.df_inter is not None:
        df_compras = st.session_state.df_inter
        total_compras = df_compras['Valor'].sum(numeric_only=True)
        st.info(f'Total de Compras: R$ {total_compras:,.2f}')

        if st.button('Mostrar/Ocultar Tabela de Compras Inter', key='btn_inter'):
            st.session_state.show_table_inter = not st.session_state.show_table_inter

        if st.session_state.show_table_inter:
            st.subheader('Tabela de Compras')
            st.dataframe(df_compras)

        st.subheader('Análise de Gastos')
        if 'Tags' in df_compras.columns:
            gastos_por_tag = df_compras.groupby('Tags', dropna=False)['Valor'].sum().reset_index()
            gastos_por_tag['Label'] = gastos_por_tag['Tags'].astype(str) + ' - R$ ' + gastos_por_tag['Valor'].map('{:,.2f}'.format)

            fig_pie = px.pie(gastos_por_tag, values='Valor', names='Label', title='Proporção de Gastos por Categoria - Inter')
            st.plotly_chart(fig_pie)

            fig_bar = px.bar(gastos_por_tag, x='Valor', y='Label', orientation='h',
                             title='Soma Total de Gastos por Categoria - Inter',
                             labels={'Valor': 'Valor (R$)', 'Tags': 'Categoria'}, color='Tags')
            st.plotly_chart(fig_bar)

# ---------------------------
# Aba 4: Nubank
# ---------------------------
with tab4:
    st.header('Análise da Fatura - Nubank')
    uploaded_file_nubank = st.file_uploader("Escolha o arquivo CSV da sua fatura do Nubank", type=['csv'], key='uploader_nubank')

    df_temp = process_upload(uploaded_file_nubank)
    if df_temp is not None:
        st.session_state.df_nubank = df_temp
        st.success('Arquivo Nubank importado com sucesso!')

    if st.session_state.df_nubank is not None:
        df_compras = st.session_state.df_nubank
        total_compras = df_compras['Valor'].sum(numeric_only=True)
        st.info(f'Total de Compras: R$ {total_compras:,.2f}')

        # Botão com label correto + key única (evita duplicação com outras abas)
        if st.button('Mostrar/Ocultar Tabela de Compras Nubank', key='btn_nubank'):
            st.session_state.show_table_nubank = not st.session_state.show_table_nubank

        if st.session_state.show_table_nubank:
            st.subheader('Tabela de Compras')
            st.dataframe(df_compras)

        st.subheader('Análise de Gastos')
        if 'Tags' in df_compras.columns:
            gastos_por_tag = df_compras.groupby('Tags', dropna=False)['Valor'].sum().reset_index()
            gastos_por_tag['Label'] = gastos_por_tag['Tags'].astype(str) + ' - R$ ' + gastos_por_tag['Valor'].map('{:,.2f}'.format)

            fig_pie = px.pie(gastos_por_tag, values='Valor', names='Label', title='Proporção de Gastos por Categoria - Nubank')
            st.plotly_chart(fig_pie)

            fig_bar = px.bar(gastos_por_tag, x='Valor', y='Label', orientation='h',
                             title='Soma Total de Gastos por Categoria - Nubank',
                             labels={'Valor': 'Valor (R$)', 'Tags': 'Categoria'}, color='Tags')
            st.plotly_chart(fig_bar)
