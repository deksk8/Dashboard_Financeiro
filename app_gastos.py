import streamlit as st
import pandas as pd
import plotly.express as px

# Inicializa o estado da sessão para armazenar os DataFrames
if 'df_picpay' not in st.session_state:
    st.session_state.df_picpay = None
if 'df_inter' not in st.session_state:
    st.session_state.df_inter = None
if 'show_table' not in st.session_state:
    st.session_state.show_table = False


# --- FUNÇÃO CENTRAL DE PROCESSAMENTO ---
# Criamos uma função para evitar duplicar o código em cada aba
def process_upload(uploaded_file):
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, dtype={'Valor': str}, decimal=',')
            
            # Limpeza e conversão de dados
            df.dropna(subset=['Valor'], inplace=True)
            df['Valor'] = df['Valor'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.replace('R$', '', regex=False)
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')

            df.loc[df['Estabelecimento'].str.contains('uber', case=False, na=False), 'Tags'] = 'UBER'
            
            return df
        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
            st.info("Por favor, verifique se o arquivo CSV está no formato correto.")
            return None
    return None

st.title('Dashboard de Análise de Gastos')
st.markdown("---")

# Cria as abas
tab1, tab2, tab3 = st.tabs(["Análise Geral", "Análise por Cartão - PicPay", "Análise por Cartão - Inter"])

with tab1:
    st.header('Análise Geral de Gastos')
    st.info("Esta aba combina os dados de todos os cartões que foram carregados.")

    # Verifica se os dois DataFrames estão carregados no session_state
    if st.session_state.df_picpay is not None and st.session_state.df_inter is not None:
        # Concatena os DataFrames
        df_combined = pd.concat([st.session_state.df_picpay, st.session_state.df_inter], ignore_index=True)
        
        # --- NOVO CÓDIGO INÍCIO ---
        # 1. Total de todas as faturas
        total_combined = df_combined['Valor'].sum()
        st.subheader('Soma Total de Todas as Faturas')
        st.metric("Total de Compras", f'R$ {total_combined:,.2f}')

        # 2. Ranking das 10 maiores compras
        st.subheader('Ranking das 10 Maiores Compras')
        df_top10 = df_combined.sort_values(by='Valor', ascending=False).head(10)
        
        # 3. Porcentagem do valor total
        total_top10 = df_top10['Valor'].sum()
        percentual_top10 = (total_top10 / total_combined) * 100
        
        df_top10['% do Total'] = (df_top10['Valor'] / total_combined * 100).round(2).astype(str) + '%'
        
        st.dataframe(df_top10[['Data', 'Estabelecimento', 'Valor', '% do Total']])
        
        st.markdown(f"**A soma das 10 maiores compras representa {percentual_top10:.2f}% do total de todas as faturas.**")
        # --- NOVO CÓDIGO FIM ---

        st.subheader('Visão Unificada de Gastos')

        gastos_por_tag_geral = df_combined.groupby('Tags')['Valor'].sum().reset_index()
        gastos_por_tag_geral['Label'] = gastos_por_tag_geral['Tags'] + ' - R$ ' + gastos_por_tag_geral['Valor'].map('{:,.2f}'.format)
        
        # Gráfico de pizza combinado
        fig_pie_geral = px.pie(
            gastos_por_tag_geral,
            values='Valor',
            names='Label',
            title='Proporção Total de Gastos por Categoria (Todos os Cartões)',
            color='Tags'
        )
        st.plotly_chart(fig_pie_geral)

        fig_bar = px.bar(gastos_por_tag_geral, x='Valor', y='Label', orientation='h', title='Soma Total de Gastos por Categoria - PicPay', labels={'Valor': 'Valor (R$)', 'Tags': 'Categoria'}, color='Tags')
        st.plotly_chart(fig_bar)
        
        st.subheader('Tabela Geral de Compras')
        st.dataframe(df_combined)

    else:
        st.info("Por favor, carregue as faturas de ambos os cartões nas abas correspondentes para ver a análise geral.")

with tab2:
    st.header('Análise da Fatura - PicPay')
    uploaded_file_picpay = st.file_uploader("Escolha o arquivo CSV da sua fatura do PicPay", type=['csv'])

    # Processa o arquivo e armazena no session_state
    df_temp = process_upload(uploaded_file_picpay)
    if df_temp is not None:
        st.session_state.df_picpay = df_temp
        st.success('Arquivo PicPay importado com sucesso!')

    # Lógica de visualização para PicPay (se o df estiver no session_state)
    if st.session_state.df_picpay is not None:
        df_compras = st.session_state.df_picpay
        total_compras = df_compras['Valor'].sum()
        st.info(f'Total de Compras: R$ {total_compras:,.2f}')

        if st.button('Mostrar/Ocultar Tabela de Compras PicPay'):
            st.session_state.show_table = not st.session_state.show_table

        if st.session_state.show_table:
            st.subheader('Tabela de Compras')
            st.dataframe(df_compras)

        st.subheader('Análise de Gastos')
        gastos_por_tag = df_compras.groupby('Tags')['Valor'].sum().reset_index()

        # --- CÓDIGO ALTERADO PARA ADICIONAR VALORES NA LEGENDA ---
        gastos_por_tag['Label'] = gastos_por_tag['Tags'] + ' - R$ ' + gastos_por_tag['Valor'].map('{:,.2f}'.format)
        fig_pie = px.pie(gastos_por_tag, values='Valor', names='Label', title='Proporção de Gastos por Categoria - PicPay', color='Tags')
        st.plotly_chart(fig_pie)
        
        fig_bar = px.bar(gastos_por_tag, x='Valor', y='Label', orientation='h', title='Soma Total de Gastos por Categoria - PicPay', labels={'Valor': 'Valor (R$)', 'Tags': 'Categoria'}, color='Tags')
        st.plotly_chart(fig_bar)

with tab3:
    st.header('Análise da Fatura - Inter')
    uploaded_file_inter = st.file_uploader("Escolha o arquivo CSV da sua fatura do Inter", type=['csv'])

    # Processa o arquivo e armazena no session_state
    df_temp = process_upload(uploaded_file_inter)
    if df_temp is not None:
        st.session_state.df_inter = df_temp
        st.success('Arquivo Inter importado com sucesso!')

    # Lógica de visualização para Inter (se o df estiver no session_state)
    if st.session_state.df_inter is not None:
        df_compras = st.session_state.df_inter
        total_compras = df_compras['Valor'].sum()
        st.info(f'Total de Compras: R$ {total_compras:,.2f}')

        if st.button('Mostrar/Ocultar Tabela de Compras Inter'):
            st.session_state.show_table = not st.session_state.show_table

        if st.session_state.show_table:
            st.subheader('Tabela de Compras')
            st.dataframe(df_compras)

        st.subheader('Análise de Gastos')
        gastos_por_tag = df_compras.groupby('Tags')['Valor'].sum().reset_index()
        
        gastos_por_tag['Label'] = gastos_por_tag['Tags'] + ' - R$ ' + gastos_por_tag['Valor'].map('{:,.2f}'.format)
        fig_pie = px.pie(gastos_por_tag, values='Valor', names='Label', title='Proporção de Gastos por Categoria - Inter')
        st.plotly_chart(fig_pie)

        fig_bar = px.bar(gastos_por_tag, x='Valor', y='Label', orientation='h', title='Soma Total de Gastos por Categoria - Inter', labels={'Valor': 'Valor (R$)', 'Tags': 'Categoria'}, color='Tags')
        st.plotly_chart(fig_bar)
